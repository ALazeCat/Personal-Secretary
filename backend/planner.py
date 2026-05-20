import json
import re

from llm_client import call_llm
from prompts import (
    build_adjust_plan_prompt,
    build_chat_secretary_prompt,
    build_daily_review_prompt,
    build_generate_plan_prompt,
    build_memory_summary_prompt,
)
from schemas import AdjustPlanResponse, ChatResponse, DailyReviewResponse, GeneratePlanResponse


TIME_BLOCK_PATTERN = re.compile(
    r"^\s*(?:[-*]\s*)?(?P<start>[0-2]?\d:[0-5]\d)\s*(?:-|–|—|to|~)\s*"
    r"(?P<end>[0-2]?\d:[0-5]\d)\s*(?P<activity>.+?)\s*$",
    re.IGNORECASE,
)


def _extract_json(text: str):
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned.removeprefix("```json").removesuffix("```").strip()
    elif cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```").removesuffix("```").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                return None
    return None


def _call_llm(prompt: str, json_mode: bool = False):
    return call_llm(prompt, json_mode=json_mode)


def _safe_schedule_items(items):
    safe_items = []
    seen = set()
    for item in items or []:
        if not isinstance(item, dict):
            continue
        if not item.get("start") or not item.get("end") or not item.get("activity"):
            continue
        safe_item = {
            "date": item.get("date"),
            "start": str(item.get("start")),
            "end": str(item.get("end")),
            "activity": str(item.get("activity")),
            "type": str(item.get("type", "task")),
            "due_date": item.get("due_date"),
            "status": item.get("status", "not_started"),
            "completed_date": item.get("completed_date"),
        }
        key = (
            safe_item.get("date"),
            safe_item["start"],
            safe_item["end"],
            safe_item["activity"].strip().lower(),
            safe_item["type"].strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        safe_items.append(safe_item)
    return safe_items


def _normalize_time(value):
    hour, minute = value.split(":", 1)
    return f"{int(hour):02d}:{minute}"


def _guess_schedule_type(activity):
    lowered = activity.lower()
    if "break" in lowered or "休息" in activity:
        return "break"
    if "exam" in lowered or "考试" in activity:
        return "exam"
    if "lunch" in lowered or "dinner" in lowered or "breakfast" in lowered or "午餐" in activity or "晚餐" in activity or "早餐" in activity:
        return "meal"
    if "ielts" in lowered or "english" in lowered or "英语" in activity or "口语" in activity:
        return "english"
    if "study" in lowered or "learn" in lowered or "学习" in activity or "复习" in activity:
        return "study"
    if "project" in lowered or "readme" in lowered or "项目" in activity:
        return "project"
    return "task"


def _clean_activity_text(activity):
    cleaned = activity.strip()
    cleaned = re.sub(r"^[\s:：\-–—]+", "", cleaned)
    return cleaned.strip()


def _extract_schedule_from_text(plan_text, plan_date=None):
    repaired_items = []
    for line in (plan_text or "").splitlines():
        match = TIME_BLOCK_PATTERN.match(line)
        if not match:
            continue

        activity = _clean_activity_text(match.group("activity"))
        if not activity:
            continue

        repaired_items.append(
            {
                "date": plan_date,
                "start": _normalize_time(match.group("start")),
                "end": _normalize_time(match.group("end")),
                "activity": activity,
                "type": _guess_schedule_type(activity),
                "due_date": None,
                "status": "not_started",
            }
        )
    return repaired_items


def _repair_schedule(plan_text, schedule, plan_date=None):
    safe_items = _safe_schedule_items(schedule)
    existing_keys = {
        (
            item.get("date") or plan_date,
            item["start"],
            item["end"],
            item["activity"].strip().lower(),
        )
        for item in safe_items
    }

    for item in _extract_schedule_from_text(plan_text, plan_date):
        key = (
            item.get("date") or plan_date,
            item["start"],
            item["end"],
            item["activity"].strip().lower(),
        )
        if key not in existing_keys:
            safe_items.append(item)
            existing_keys.add(key)

    return sorted(safe_items, key=lambda item: (item.get("date") or "", item["start"], item["end"]))


def _safe_extracted_items(items):
    safe_items = []
    allowed_kinds = {"task", "fixed_event", "note"}
    for item in items or []:
        if not isinstance(item, dict) or not item.get("title"):
            continue

        kind = str(item.get("kind", "task"))
        if kind == "event":
            kind = "fixed_event"
        if kind not in allowed_kinds:
            kind = "note"

        safe_items.append(
            {
                "kind": kind,
                "title": str(item.get("title")),
                "date": item.get("date"),
                "start": item.get("start"),
                "end": item.get("end"),
                "estimated_minutes": item.get("estimated_minutes"),
                "priority": str(item.get("priority", "medium")),
                "category": str(item.get("category", "general")),
                "due_date": item.get("due_date"),
                "notes": item.get("notes"),
            }
        )
    return safe_items


def _safe_plan_operations(operations):
    safe_operations = []
    allowed_actions = {"update_item", "delete_item", "set_status", "add_item"}
    allowed_statuses = {"not_started", "done", "partial", "missed"}
    allowed_change_fields = {"date", "start", "end", "activity", "type", "due_date"}
    allowed_item_fields = allowed_change_fields | {"status", "completed_date"}

    for operation in operations or []:
        if not isinstance(operation, dict):
            continue

        action = operation.get("action")
        plan_date = operation.get("plan_date")
        if action not in allowed_actions or not plan_date:
            continue

        safe_operation = {
            "action": action,
            "plan_date": str(plan_date),
            "item_match": operation.get("item_match"),
            "item_index": operation.get("item_index"),
            "target_type": operation.get("target_type"),
            "time_hint": operation.get("time_hint") if isinstance(operation.get("time_hint"), dict) else {},
            "changes": {},
            "item": {},
            "status": None,
            "completed_date": operation.get("completed_date"),
        }

        if isinstance(operation.get("changes"), dict):
            safe_operation["changes"] = {
                field: value
                for field, value in operation["changes"].items()
                if field in allowed_change_fields
            }

        if isinstance(operation.get("item"), dict):
            safe_operation["item"] = {
                field: value
                for field, value in operation["item"].items()
                if field in allowed_item_fields
            }

        if operation.get("status") in allowed_statuses:
            safe_operation["status"] = operation.get("status")

        safe_operations.append(safe_operation)

    return safe_operations


def generate_plan(request):
    prompt = build_generate_plan_prompt(request)
    content, error = _call_llm(prompt, json_mode=True)
    if error:
        return GeneratePlanResponse(
            plan_text=error,
            plan_date=request.plan_date,
            schedule=[],
            summary="Plan was not generated.",
        )

    parsed = _extract_json(content)
    if parsed:
        plan_text = parsed.get("plan_text", content)
        plan_date = parsed.get("plan_date", request.plan_date)
        return GeneratePlanResponse(
            plan_text=plan_text,
            plan_date=plan_date,
            schedule=_repair_schedule(plan_text, parsed.get("schedule", []), plan_date),
            summary=parsed.get("summary", "Plan generated."),
        )

    return GeneratePlanResponse(
        plan_text=content,
        plan_date=request.plan_date,
        schedule=_repair_schedule(content, [], request.plan_date),
        summary="Plan generated as plain text.",
    )


def adjust_plan(request):
    prompt = build_adjust_plan_prompt(request)
    content, error = _call_llm(prompt, json_mode=True)
    if error:
        return AdjustPlanResponse(
            adjusted_plan_text=error,
            plan_date=request.current_date,
            summary="Plan was not adjusted.",
        )

    parsed = _extract_json(content)
    if parsed:
        return AdjustPlanResponse(
            adjusted_plan_text=parsed.get("adjusted_plan_text", content),
            plan_date=parsed.get("plan_date", request.current_date),
            summary=parsed.get("summary", "Plan adjusted."),
        )

    return AdjustPlanResponse(
        adjusted_plan_text=content,
        plan_date=request.current_date,
        summary="Adjusted plan generated as plain text.",
    )


def generate_daily_review(request):
    prompt = build_daily_review_prompt(request)
    content, error = _call_llm(prompt, json_mode=True)
    if error:
        return DailyReviewResponse(
            review_text=error,
            completion_summary="Review was not generated.",
            tomorrow_suggestions="Add OPENAI_API_KEY to enable AI suggestions.",
        )

    parsed = _extract_json(content)
    if parsed:
        return DailyReviewResponse(
            review_text=parsed.get("review_text", content),
            completion_summary=parsed.get("completion_summary", "Review generated."),
            tomorrow_suggestions=parsed.get("tomorrow_suggestions", ""),
        )

    return DailyReviewResponse(
        review_text=content,
        completion_summary="Review generated as plain text.",
        tomorrow_suggestions="",
    )


def chat_with_secretary(request):
    prompt = build_chat_secretary_prompt(request)
    content, error = _call_llm(prompt, json_mode=True)
    if error:
        current_plan = request.current_plan
        return ChatResponse(
            reply=(
                "I heard you, but I could not reach the AI service right now. "
                f"Here is the technical message: {error}"
            ),
            extracted_items=[],
            plan_text=current_plan.plan_text if current_plan else "",
            plan_date=request.current_date or (current_plan.plan_date if current_plan else None),
            schedule=current_plan.schedule if current_plan else [],
            summary="No new plan was created because the AI request failed.",
            needs_follow_up=True,
            follow_up_question="Please try sending the message again after the AI connection is available.",
        )

    parsed = _extract_json(content)
    if parsed:
        plan_text = parsed.get("plan_text", "")
        plan_date = parsed.get("plan_date", request.current_date)
        return ChatResponse(
            reply=parsed.get("reply", "Got it. I updated your plan."),
            extracted_items=_safe_extracted_items(parsed.get("extracted_items", [])),
            plan_text=plan_text,
            plan_date=plan_date,
            schedule=_repair_schedule(plan_text, parsed.get("schedule", []), plan_date),
            summary=parsed.get("summary", "Plan updated."),
            operations=_safe_plan_operations(parsed.get("operations", [])),
            needs_follow_up=parsed.get("needs_follow_up", False),
            follow_up_question=parsed.get("follow_up_question"),
        )

    return ChatResponse(
        reply=content,
        extracted_items=[],
        plan_text=request.current_plan.plan_text if request.current_plan else "",
        plan_date=request.current_date or (request.current_plan.plan_date if request.current_plan else None),
        schedule=(
            _repair_schedule(
                request.current_plan.plan_text,
                request.current_plan.schedule,
                request.current_date or request.current_plan.plan_date,
            )
            if request.current_plan
            else []
        ),
        summary="The AI replied in plain text, so no structured plan update was available.",
        needs_follow_up=False,
    )


def summarize_old_memory(old_summary, messages):
    if not messages:
        return old_summary or ""

    prompt = build_memory_summary_prompt(old_summary, messages)
    content, error = _call_llm(prompt)
    if not error and content:
        return content.strip()

    fallback_lines = [old_summary.strip()] if old_summary else []
    fallback_lines.append("Older conversation highlights:")
    for message in messages[-8:]:
        role = message.get("role", "unknown")
        content = message.get("content", "")
        if content:
            fallback_lines.append(f"- {role}: {content[:160]}")
    return "\n".join(line for line in fallback_lines if line).strip()
