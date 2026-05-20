import json
from datetime import date, datetime
from difflib import SequenceMatcher
from pathlib import Path


DATA_DIR = Path(__file__).parent / "data"
MEMORY_FILE = DATA_DIR / "memory.json"
RECENT_MESSAGE_KEEP_LIMIT = 12
SUMMARY_TRIGGER_LIMIT = 20
DAY_PART_RANGES = {
    "morning": (5 * 60, 12 * 60),
    "afternoon": (12 * 60, 18 * 60),
    "evening": (18 * 60, 24 * 60),
}


def _default_memory():
    return {
        "profile_memory": {
            "preferred_language": "en",
            "wake_up_time": "09:00",
            "sleep_time": "23:30",
            "planning_style": "realistic",
        },
        "working_memory": {
            "current_plan": None,
            "plans_by_date": {},
            "recent_messages": [],
        },
        "summary_memory": {
            "summary": "",
            "updated_at": None,
        },
    }


def _ensure_memory_file():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not MEMORY_FILE.exists():
        _write_memory(_default_memory())


def _write_memory(memory):
    MEMORY_FILE.write_text(json.dumps(memory, ensure_ascii=False, indent=2), encoding="utf-8")


def _normalize_schedule(schedule):
    normalized = []
    by_key = {}
    status_rank = {"not_started": 0, "missed": 1, "partial": 2, "done": 3}
    for item in schedule or []:
        next_item = dict(item)
        next_item.setdefault("status", "not_started")
        key = _schedule_identity(next_item)
        existing = by_key.get(key)
        if existing:
            if status_rank.get(next_item.get("status"), 0) > status_rank.get(existing.get("status"), 0):
                existing["status"] = next_item.get("status")
                if next_item.get("completed_date"):
                    existing["completed_date"] = next_item.get("completed_date")
                if next_item.get("status_updated_at"):
                    existing["status_updated_at"] = next_item.get("status_updated_at")
            continue
        by_key[key] = next_item
        normalized.append(next_item)
    return normalized


def _schedule_identity(item, fallback_date=None):
    return (
        item.get("date") or fallback_date,
        str(item.get("start", "")),
        str(item.get("end", "")),
        str(item.get("activity", "")).strip().lower(),
        str(item.get("type", "task")).strip().lower(),
    )


def _merge_schedule_progress(existing_schedule, next_schedule, fallback_date=None):
    progress_by_key = {}
    for item in _normalize_schedule(existing_schedule):
        key = _schedule_identity(item, fallback_date)
        progress_by_key[key] = {
            "status": item.get("status", "not_started"),
            "completed_date": item.get("completed_date"),
            "status_updated_at": item.get("status_updated_at"),
        }

    merged = []
    for item in _normalize_schedule(next_schedule):
        next_item = dict(item)
        progress = progress_by_key.get(_schedule_identity(next_item, fallback_date))
        if progress:
            next_item["status"] = progress["status"]
            if progress.get("completed_date"):
                next_item["completed_date"] = progress["completed_date"]
            if progress.get("status_updated_at"):
                next_item["status_updated_at"] = progress["status_updated_at"]
        merged.append(next_item)
    return merged


def _schedule_to_plan_text(schedule):
    lines = []
    for item in _normalize_schedule(schedule):
        start = item.get("start", "")
        end = item.get("end", "")
        activity = item.get("activity", "")
        if start and end and activity:
            lines.append(f"{start}-{end} {activity}")
    return "\n".join(lines)


def _refresh_plan(plan):
    plan["schedule"] = sorted(
        _normalize_schedule(plan.get("schedule", [])),
        key=lambda item: (item.get("date") or plan.get("plan_date", ""), item.get("start", ""), item.get("end", "")),
    )
    plan["plan_text"] = _schedule_to_plan_text(plan["schedule"])
    plan["updated_at"] = datetime.now().isoformat(timespec="seconds")


def _sync_current_plan(memory, changed_dates):
    current_plan = memory["working_memory"].get("current_plan")
    if not current_plan:
        return

    current_date = current_plan.get("plan_date")
    plans_by_date = memory["working_memory"].setdefault("plans_by_date", {})
    if current_date in changed_dates:
        memory["working_memory"]["current_plan"] = plans_by_date.get(current_date)


def _text_similarity(left, right):
    return SequenceMatcher(None, left, right).ratio()


def _normalize_text(value):
    return "".join(str(value or "").strip().lower().split())


def _time_to_minutes(value):
    if not value or ":" not in str(value):
        return None
    try:
        hour, minute = str(value).split(":", 1)
        return int(hour) * 60 + int(minute)
    except ValueError:
        return None


def _overlaps(start, end, range_start, range_end):
    if start is None or end is None:
        return False
    return max(start, range_start) < min(end, range_end)


def _requested_day_part(operation):
    time_hint = operation.get("time_hint")
    if not isinstance(time_hint, dict):
        return None

    part_of_day = str(time_hint.get("part_of_day") or "").strip().lower()
    if part_of_day in DAY_PART_RANGES:
        return part_of_day
    return None


def _target_type(operation):
    return _normalize_text(operation.get("target_type"))


def _item_type(item):
    return _normalize_text(item.get("type") or "task")


def _item_match_score(item, operation):
    item_match = _normalize_text(operation.get("item_match"))
    activity = _normalize_text(item.get("activity"))
    item_type = _normalize_text(item.get("type"))
    score = 0

    if item_match:
        if item_match == activity:
            score += 100
        elif item_match in activity or activity in item_match:
            score += 80
        else:
            score += int(_text_similarity(item_match, activity) * 60)

        if item_match == item_type or item_match in item_type or item_type in item_match:
            score += 35

    target_type = _target_type(operation)
    item_type = _item_type(item)
    if target_type and target_type == item_type:
        score += 90
    elif target_type and item_type and _text_similarity(target_type, item_type) >= 0.78:
        score += 60

    day_part = _requested_day_part(operation)
    if day_part:
        start = _time_to_minutes(item.get("start"))
        end = _time_to_minutes(item.get("end"))
        range_start, range_end = DAY_PART_RANGES[day_part]
        if _overlaps(start, end, range_start, range_end):
            score += 35
        else:
            score -= 20

    changes = operation.get("changes")
    if isinstance(changes, dict):
        if changes.get("start") and changes.get("start") == item.get("start"):
            score += 20
        if changes.get("end") and changes.get("end") == item.get("end"):
            score += 20

    time_hint = operation.get("time_hint")
    if isinstance(time_hint, dict):
        if time_hint.get("start") and time_hint.get("start") == item.get("start"):
            score += 35
        if time_hint.get("end") and time_hint.get("end") == item.get("end"):
            score += 35

    return score


def _find_schedule_item_index(plan, operation):
    schedule = _normalize_schedule(plan.get("schedule", []))
    item_index = operation.get("item_index")
    if isinstance(item_index, int) and 0 <= item_index < len(schedule):
        return item_index

    if not operation.get("item_match") and not operation.get("target_type") and not _requested_day_part(operation):
        return None

    scored = [
        (_item_match_score(item, operation), index)
        for index, item in enumerate(schedule)
    ]
    scored = [(score, index) for score, index in scored if score >= 45]
    if not scored:
        return None

    scored.sort(reverse=True)
    best_score, best_index = scored[0]
    if len(scored) > 1 and scored[1][0] == best_score:
        return None

    return best_index


def get_memory():
    _ensure_memory_file()
    try:
        memory = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        memory = _default_memory()

    default = _default_memory()
    for section, value in default.items():
        memory.setdefault(section, value)
    memory["working_memory"].setdefault("current_plan", None)
    memory["working_memory"].setdefault("plans_by_date", {})
    memory["working_memory"].setdefault("recent_messages", [])
    memory["summary_memory"].setdefault("summary", "")
    memory["summary_memory"].setdefault("updated_at", None)

    current_plan = memory["working_memory"].get("current_plan")
    if current_plan and current_plan.get("plan_date"):
        _save_plan_to_memory(memory, current_plan)

    repaired = False
    for plan in memory["working_memory"].get("plans_by_date", {}).values():
        normalized_schedule = sorted(
            _normalize_schedule(plan.get("schedule", [])),
            key=lambda item: (item.get("date") or plan.get("plan_date", ""), item.get("start", ""), item.get("end", "")),
        )
        if plan.get("schedule", []) != normalized_schedule:
            plan["schedule"] = normalized_schedule
            repaired = True

        expected_plan_text = _schedule_to_plan_text(plan.get("schedule", []))
        if plan.get("plan_text") != expected_plan_text:
            plan["plan_text"] = expected_plan_text
            repaired = True

    current_plan = memory["working_memory"].get("current_plan")
    if current_plan:
        plan_date = current_plan.get("plan_date")
        repaired_current = memory["working_memory"].get("plans_by_date", {}).get(plan_date)
        if repaired_current and current_plan != repaired_current:
            memory["working_memory"]["current_plan"] = repaired_current
            repaired = True

    if repaired:
        _write_memory(memory)
    return memory


def reset_memory():
    memory = _default_memory()
    _write_memory(memory)
    return memory


def save_current_plan(plan_data):
    memory = get_memory()
    memory["working_memory"]["current_plan"] = plan_data
    _save_plan_to_memory(memory, plan_data)
    plan_date = plan_data.get("plan_date")
    if plan_date:
        memory["working_memory"]["current_plan"] = memory["working_memory"]["plans_by_date"].get(plan_date)
    _write_memory(memory)
    return memory


def _save_plan_to_memory(memory, plan_data, status=None):
    plan_date = plan_data.get("plan_date")
    if not plan_date:
        return

    plans_by_date = memory["working_memory"].setdefault("plans_by_date", {})
    existing = plans_by_date.get(plan_date, {})
    schedule = _merge_schedule_progress(
        existing.get("schedule", []),
        plan_data.get("schedule", []),
        plan_date,
    )
    plans_by_date[plan_date] = {
        "plan_text": plan_data.get("plan_text", ""),
        "plan_date": plan_date,
        "schedule": schedule,
        "summary": plan_data.get("summary", ""),
        "status": status or existing.get("status", "planned"),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }


def get_plans_by_date():
    memory = get_memory()
    return memory["working_memory"].get("plans_by_date", {})


def mark_plan_reviewed(plan_date):
    memory = get_memory()
    plans_by_date = memory["working_memory"].setdefault("plans_by_date", {})
    if plan_date in plans_by_date:
        plans_by_date[plan_date]["status"] = "reviewed"
        plans_by_date[plan_date]["reviewed_at"] = datetime.now().isoformat(timespec="seconds")
    _write_memory(memory)
    return memory


def delete_plan(plan_date):
    memory = get_memory()
    plans_by_date = memory["working_memory"].setdefault("plans_by_date", {})
    deleted = plans_by_date.pop(plan_date, None) is not None

    current_plan = memory["working_memory"].get("current_plan")
    if current_plan and current_plan.get("plan_date") == plan_date:
        remaining_plans = sorted(plans_by_date.values(), key=lambda plan: plan.get("updated_at", ""))
        memory["working_memory"]["current_plan"] = remaining_plans[-1] if remaining_plans else None

    _write_memory(memory)
    return {"deleted": deleted, "plans_by_date": plans_by_date, "current_plan": memory["working_memory"]["current_plan"]}


def delete_schedule_item(plan_date, item_index):
    memory = get_memory()
    plans_by_date = memory["working_memory"].setdefault("plans_by_date", {})
    plan = plans_by_date.get(plan_date)
    if not plan:
        return {
            "deleted": False,
            "reason": "plan_not_found",
            "plans_by_date": plans_by_date,
            "current_plan": memory["working_memory"].get("current_plan"),
        }

    schedule = _normalize_schedule(plan.get("schedule", []))
    if item_index < 0 or item_index >= len(schedule):
        return {
            "deleted": False,
            "reason": "item_not_found",
            "plans_by_date": plans_by_date,
            "current_plan": memory["working_memory"].get("current_plan"),
        }

    schedule.pop(item_index)
    plan["schedule"] = schedule
    _refresh_plan(plan)

    current_plan = memory["working_memory"].get("current_plan")
    if current_plan and current_plan.get("plan_date") == plan_date:
        memory["working_memory"]["current_plan"] = plan

    _write_memory(memory)
    return {
        "deleted": True,
        "plans_by_date": plans_by_date,
        "current_plan": memory["working_memory"].get("current_plan"),
    }


def update_schedule_item_status(plan_date, item_index, item_status, completed_date=None):
    memory = get_memory()
    plans_by_date = memory["working_memory"].setdefault("plans_by_date", {})
    plan = plans_by_date.get(plan_date)
    if not plan:
        return {
            "updated": False,
            "reason": "plan_not_found",
            "plans_by_date": plans_by_date,
            "current_plan": memory["working_memory"].get("current_plan"),
        }

    schedule = _normalize_schedule(plan.get("schedule", []))
    if item_index < 0 or item_index >= len(schedule):
        return {
            "updated": False,
            "reason": "item_not_found",
            "plans_by_date": plans_by_date,
            "current_plan": memory["working_memory"].get("current_plan"),
        }

    schedule[item_index]["status"] = item_status
    schedule[item_index]["status_updated_at"] = datetime.now().isoformat(timespec="seconds")
    if item_status == "done":
        schedule[item_index]["completed_date"] = completed_date or date.today().isoformat()
    else:
        schedule[item_index].pop("completed_date", None)
    plan["schedule"] = schedule
    _refresh_plan(plan)

    current_plan = memory["working_memory"].get("current_plan")
    if current_plan and current_plan.get("plan_date") == plan_date:
        memory["working_memory"]["current_plan"] = plan

    _write_memory(memory)
    return {
        "updated": True,
        "plans_by_date": plans_by_date,
        "current_plan": memory["working_memory"].get("current_plan"),
    }


def update_schedule_item(plan_date, item_index, updates):
    memory = get_memory()
    plans_by_date = memory["working_memory"].setdefault("plans_by_date", {})
    plan = plans_by_date.get(plan_date)
    if not plan:
        return {
            "updated": False,
            "reason": "plan_not_found",
            "plans_by_date": plans_by_date,
            "current_plan": memory["working_memory"].get("current_plan"),
        }

    schedule = _normalize_schedule(plan.get("schedule", []))
    if item_index < 0 or item_index >= len(schedule):
        return {
            "updated": False,
            "reason": "item_not_found",
            "plans_by_date": plans_by_date,
            "current_plan": memory["working_memory"].get("current_plan"),
        }

    item = schedule.pop(item_index)
    for field in ["date", "start", "end", "activity", "type", "due_date"]:
        if field in updates:
            value = updates[field]
            if field == "due_date" and value == "":
                value = None
            if isinstance(value, str):
                value = value.strip()
            if value is not None or field in {"date", "due_date"}:
                item[field] = value

    target_date = item.get("date") or plan_date
    item["date"] = target_date
    if not item.get("start") or not item.get("end") or not item.get("activity"):
        return {
            "updated": False,
            "reason": "invalid_item",
            "plans_by_date": plans_by_date,
            "current_plan": memory["working_memory"].get("current_plan"),
        }

    plan["schedule"] = schedule
    _refresh_plan(plan)

    changed_dates = {plan_date}
    target_plan = plan
    if target_date != plan_date:
        changed_dates.add(target_date)
        target_plan = plans_by_date.setdefault(
            target_date,
            {
                "plan_text": "",
                "plan_date": target_date,
                "schedule": [],
                "summary": f"Items moved to {target_date}.",
                "status": "planned",
                "updated_at": datetime.now().isoformat(timespec="seconds"),
            },
        )

    target_schedule = _normalize_schedule(target_plan.get("schedule", []))
    target_schedule.append(item)
    target_plan["schedule"] = target_schedule
    _refresh_plan(target_plan)
    _sync_current_plan(memory, changed_dates)

    _write_memory(memory)
    return {
        "updated": True,
        "plans_by_date": plans_by_date,
        "current_plan": memory["working_memory"].get("current_plan"),
    }


def add_schedule_item(plan_date, item_data):
    memory = get_memory()
    plans_by_date = memory["working_memory"].setdefault("plans_by_date", {})
    plan = plans_by_date.setdefault(
        plan_date,
        {
            "plan_text": "",
            "plan_date": plan_date,
            "schedule": [],
            "summary": f"Items added to {plan_date}.",
            "status": "planned",
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        },
    )

    item = dict(item_data or {})
    item.setdefault("date", plan_date)
    item.setdefault("type", "task")
    item.setdefault("status", "not_started")
    if not item.get("start") or not item.get("end") or not item.get("activity"):
        return {
            "added": False,
            "reason": "invalid_item",
            "plans_by_date": plans_by_date,
            "current_plan": memory["working_memory"].get("current_plan"),
        }

    plan["schedule"] = _normalize_schedule(plan.get("schedule", [])) + [item]
    _refresh_plan(plan)
    _sync_current_plan(memory, {plan_date})
    _write_memory(memory)
    return {
        "added": True,
        "plans_by_date": plans_by_date,
        "current_plan": memory["working_memory"].get("current_plan"),
    }


def apply_plan_operations(operations):
    results = []
    memory = get_memory()
    plans_by_date = memory["working_memory"].setdefault("plans_by_date", {})

    for operation in operations or []:
        action = operation.get("action")
        plan_date = operation.get("plan_date")
        result = {
            "action": action,
            "plan_date": plan_date,
            "applied": False,
        }

        if not action or not plan_date:
            result["reason"] = "invalid_operation"
            results.append(result)
            continue

        if action == "add_item":
            add_result = add_schedule_item(plan_date, operation.get("item", {}))
            result["applied"] = add_result.get("added", False)
            result["reason"] = add_result.get("reason")
            results.append(result)
            continue

        plans_by_date = get_plans_by_date()
        plan = plans_by_date.get(plan_date)
        if not plan:
            result["reason"] = "plan_not_found"
            results.append(result)
            continue

        item_index = _find_schedule_item_index(plan, operation)
        if item_index is None:
            result["reason"] = "item_not_found"
            results.append(result)
            continue

        if action == "update_item":
            update_result = update_schedule_item(plan_date, item_index, operation.get("changes", {}))
            result["applied"] = update_result.get("updated", False)
            result["reason"] = update_result.get("reason")
        elif action == "delete_item":
            delete_result = delete_schedule_item(plan_date, item_index)
            result["applied"] = delete_result.get("deleted", False)
            result["reason"] = delete_result.get("reason")
        elif action == "set_status":
            status = operation.get("status")
            if status:
                status_result = update_schedule_item_status(
                    plan_date,
                    item_index,
                    status,
                    operation.get("completed_date"),
                )
                result["applied"] = status_result.get("updated", False)
                result["reason"] = status_result.get("reason")
            else:
                result["reason"] = "missing_status"
        else:
            result["reason"] = "unsupported_action"

        results.append(result)

    final_memory = get_memory()
    return {
        "operation_results": results,
        "plans_by_date": final_memory["working_memory"].get("plans_by_date", {}),
        "current_plan": final_memory["working_memory"].get("current_plan"),
    }


def save_profile_preferences(language=None, user_profile=None):
    memory = get_memory()
    if language:
        memory["profile_memory"]["preferred_language"] = language
    if user_profile:
        memory["profile_memory"]["wake_up_time"] = user_profile.wake_up_time
        memory["profile_memory"]["sleep_time"] = user_profile.sleep_time
        memory["profile_memory"]["planning_style"] = user_profile.planning_style
    _write_memory(memory)
    return memory


def save_chat_turn(user_message, assistant_reply, language, response_data):
    memory = get_memory()
    timestamp = datetime.now().isoformat(timespec="seconds")
    recent_messages = memory["working_memory"].get("recent_messages", [])
    recent_messages.extend(
        [
            {
                "role": "user",
                "content": user_message,
                "language": language,
                "timestamp": timestamp,
            },
            {
                "role": "assistant",
                "content": assistant_reply,
                "language": language,
                "timestamp": timestamp,
                "extracted_items": response_data.get("extracted_items", []),
            },
        ]
    )
    memory["working_memory"]["recent_messages"] = recent_messages
    plan_text = response_data.get("plan_text", "")
    schedule = _normalize_schedule(response_data.get("schedule", []))
    if plan_text or schedule:
        memory["working_memory"]["current_plan"] = {
            "plan_text": plan_text,
            "plan_date": response_data.get("plan_date"),
            "schedule": schedule,
            "summary": response_data.get("summary", ""),
        }
        _save_plan_to_memory(memory, memory["working_memory"]["current_plan"])
        plan_date = memory["working_memory"]["current_plan"].get("plan_date")
        if plan_date:
            memory["working_memory"]["current_plan"] = memory["working_memory"]["plans_by_date"].get(plan_date)
    memory["profile_memory"]["preferred_language"] = language
    _write_memory(memory)
    return memory


def should_summarize(memory):
    return len(memory["working_memory"].get("recent_messages", [])) > SUMMARY_TRIGGER_LIMIT


def get_messages_to_summarize(memory):
    recent_messages = memory["working_memory"].get("recent_messages", [])
    if len(recent_messages) <= RECENT_MESSAGE_KEEP_LIMIT:
        return []
    return recent_messages[:-RECENT_MESSAGE_KEEP_LIMIT]


def apply_summary(summary):
    memory = get_memory()
    recent_messages = memory["working_memory"].get("recent_messages", [])
    memory["working_memory"]["recent_messages"] = recent_messages[-RECENT_MESSAGE_KEEP_LIMIT:]
    memory["summary_memory"]["summary"] = summary
    memory["summary_memory"]["updated_at"] = datetime.now().isoformat(timespec="seconds")
    _write_memory(memory)
    return memory
