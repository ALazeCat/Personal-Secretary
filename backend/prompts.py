import json


def _to_pretty_json(data):
    return json.dumps(data, ensure_ascii=False, indent=2)


def _compact_schedule_item(item):
    if hasattr(item, "model_dump"):
        item = item.model_dump()

    return {
        "date": item.get("date"),
        "start": item.get("start"),
        "end": item.get("end"),
        "activity": item.get("activity"),
        "type": item.get("type", "task"),
        "status": item.get("status", "not_started"),
        "completed_date": item.get("completed_date"),
        "due_date": item.get("due_date"),
    }


def _compact_plan(plan, max_items=12):
    if not plan:
        return None
    if hasattr(plan, "model_dump"):
        plan = plan.model_dump()

    schedule = plan.get("schedule", [])
    return {
        "plan_date": plan.get("plan_date"),
        "summary": plan.get("summary", ""),
        "status": plan.get("status", "planned"),
        "schedule": [
            {"index": index, **_compact_schedule_item(item)}
            for index, item in enumerate(schedule[:max_items])
        ],
    }


def _compact_plans_by_date(plans_by_date, current_date, current_plan_date, max_plans=7):
    if not plans_by_date:
        return {}

    priority_dates = [date for date in [current_date, current_plan_date] if date]
    sorted_dates = sorted(plans_by_date.keys())
    future_dates = [date for date in sorted_dates if not current_date or date >= current_date]
    past_dates = [date for date in sorted_dates if current_date and date < current_date]

    selected_dates = []
    for date in priority_dates + future_dates + list(reversed(past_dates)):
        if date not in selected_dates and date in plans_by_date:
            selected_dates.append(date)
        if len(selected_dates) >= max_plans:
            break

    return {date: _compact_plan(plans_by_date[date], max_items=6) for date in selected_dates}


def _compact_chat_payload(request):
    memory_context = request.memory_context
    current_plan = request.current_plan or (memory_context.current_plan if memory_context else None)
    current_plan_date = current_plan.plan_date if hasattr(current_plan, "plan_date") else None

    recent_messages = []
    if memory_context:
        recent_messages = [message.model_dump() for message in memory_context.recent_messages[-6:]]

    plans_by_date = memory_context.plans_by_date if memory_context else {}

    return {
        "message": request.message,
        "language": request.language,
        "current_date": request.current_date,
        "current_time": request.current_time,
        "user_profile": request.user_profile.model_dump() if request.user_profile else None,
        "memory_summary": memory_context.summary if memory_context else "",
        "recent_messages": recent_messages[-4:],
        "current_plan": _compact_plan(current_plan, max_items=8),
        "saved_plans": _compact_plans_by_date(
            plans_by_date,
            request.current_date,
            current_plan_date,
            max_plans=5,
        ),
    }


def build_generate_plan_prompt(request):
    payload = request.model_dump()
    return f"""
You are a realistic personal AI secretary for a student.

Create a daily plan from the user's profile, fixed events, and tasks.

Rules:
- Use the user's plan_date as the main planning date when it is provided.
- Use YYYY-MM-DD format for all dates.
- Respect wake-up time and sleep time.
- Respect all fixed events for the planning date.
- Prioritize high-priority tasks and tasks with closer due dates.
- Add breaks and buffer time.
- Avoid overpacking the day.
- Prefer difficult tasks during high-energy time.
- If a task is not due today and today is already full, suggest moving it to another day.
- Keep the plan practical for a real student, not perfect or robotic.

Return JSON if possible using exactly this shape:
{{
  "plan_text": "...",
  "plan_date": "2026-05-20",
  "schedule": [
    {{
      "date": "2026-05-20",
      "start": "09:00",
      "end": "10:30",
      "activity": "Study Linux",
      "type": "study",
      "due_date": "2026-05-21"
    }}
  ],
  "summary": "..."
}}

User input:
{_to_pretty_json(payload)}
""".strip()


def build_adjust_plan_prompt(request):
    payload = request.model_dump()
    return f"""
You are a practical personal AI secretary.

Adjust the remaining day plan based on what changed.

Rules:
- Start from the current date and current time.
- Consider the original plan and what was completed or delayed.
- Consider task due dates.
- Keep high-priority and urgent tasks first when possible.
- Preserve breaks and buffer time.
- Do not overpack the rest of the day.
- Give the user a calm and realistic adjusted plan.

Return JSON if possible using exactly this shape:
{{
  "adjusted_plan_text": "...",
  "plan_date": "2026-05-20",
  "summary": "..."
}}

User input:
{_to_pretty_json(payload)}
""".strip()


def build_daily_review_prompt(request):
    payload = request.model_dump()
    return f"""
You are a supportive personal AI secretary helping a student review the day.

Create a short daily review.

Rules:
- Use the review_date when it is provided.
- Summarize completed, partially completed, and missed tasks.
- Identify what went well.
- Identify likely causes of delays without blaming the user.
- Suggest realistic improvements for tomorrow.
- Keep the tone calm, specific, and useful.

Return JSON if possible using exactly this shape:
{{
  "review_text": "...",
  "completion_summary": "...",
  "tomorrow_suggestions": "..."
}}

User input:
{_to_pretty_json(payload)}
""".strip()


def build_chat_secretary_prompt(request):
    payload = _compact_chat_payload(request)
    reply_language = "Simplified Chinese" if request.language == "zh" else "English"
    return f"""
You are a fast, realistic AI secretary. Use {reply_language} in reply.

Task: convert the user's message into plan operations. Return JSON only.

Rules:
- Understand typos, informal wording, and compound requests.
- Do not ignore any part of the message.
- Prefer operations over long explanations.
- Use saved schedule item index when you can identify the target.
- If index is uncertain, use item_match plus target_type and time_hint.
- target_type should be language-neutral when possible: task, study, project, exam, meeting, meal, appointment, exercise, buffer, break.
- Use target_type="buffer" for free-time or flexible placeholder blocks in any language.
- Use time_hint.part_of_day as morning, afternoon, or evening when the user gives a vague time period.
- Resolve relative dates from current_date according to the user's language and message.
- Default duration if missing: meal 90m, meeting 90m, appointment/date 120m, study 90m.
- Ask a follow-up only if a required date or target item is truly impossible to infer.
- Keep reply short.

Operation shapes:
- add_item: include item {{date,start,end,activity,type,status:"not_started"}}.
- delete_item: include plan_date and item_index if known; otherwise include item_match, target_type, and time_hint.
- update_item: include plan_date, target, and changes.
- set_status: include status; for done use current_date as completed_date.

Return exactly this JSON shape:
{{
  "reply": "...",
  "extracted_items": [],
  "plan_text": "",
  "plan_date": null,
  "schedule": [],
  "summary": "...",
  "operations": [
    {{
      "action": "update_item",
      "plan_date": "2026-05-19",
      "item_match": "Exam",
      "item_index": null,
      "target_type": "exam",
      "time_hint": {{"part_of_day": "afternoon", "start": null, "end": null}},
      "changes": {{"start": "13:30", "end": "15:30"}},
      "item": {{}},
      "status": null,
      "completed_date": null
    }}
  ],
  "needs_follow_up": false,
  "follow_up_question": null
}}

Compact state:
{_to_pretty_json(payload)}
""".strip()


def build_memory_summary_prompt(old_summary, messages):
    return f"""
You are maintaining memory for a personal AI secretary.

Create a compact memory summary from older chat messages.

Keep:
- Stable user preferences.
- Current commitments and fixed events.
- Unfinished tasks.
- Task progress statuses, especially items marked done, partial, missed, or completed early.
- Planning habits, such as overestimating time or needing breaks.
- Important personal context for future planning.

Remove:
- Small talk.
- Repeated wording.
- Details that are no longer useful.

Return plain text only. Keep it concise but useful.

Previous memory summary:
{old_summary or "(empty)"}

Older messages to compress:
{_to_pretty_json(messages)}
""".strip()
