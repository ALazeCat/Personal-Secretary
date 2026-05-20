from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from llm_client import test_llm_connection
from memory import (
    apply_summary,
    apply_plan_operations,
    delete_plan,
    delete_schedule_item,
    get_memory,
    get_plans_by_date,
    mark_plan_reviewed,
    get_messages_to_summarize,
    save_chat_turn,
    save_current_plan,
    save_profile_preferences,
    should_summarize,
    update_schedule_item,
    update_schedule_item_status,
)
from model_settings import get_public_model_settings, save_model_settings
from planner import (
    adjust_plan,
    chat_with_secretary,
    generate_daily_review,
    generate_plan,
    summarize_old_memory,
)
from schemas import (
    AdjustPlanRequest,
    AdjustPlanResponse,
    ChatRequest,
    ChatResponse,
    DailyReviewRequest,
    DailyReviewResponse,
    GeneratePlanRequest,
    GeneratePlanResponse,
    MemoryContext,
    ModelSettingsRequest,
    ModelSettingsResponse,
    ScheduleItemStatusRequest,
    ScheduleItemUpdateRequest,
)


app = FastAPI(title="Personal AI Secretary")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=(
        r"^http://("
        r"localhost|127\.0\.0\.1|"
        r"192\.168\.\d+\.\d+|"
        r"10\.\d+\.\d+\.\d+|"
        r"172\.(1[6-9]|2\d|3[01])\.\d+\.\d+"
        r"):\d+$"
    ),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _memory_context_from_file(memory_data):
    current_plan = memory_data["working_memory"].get("current_plan")
    plans_by_date = memory_data["working_memory"].get("plans_by_date", {})
    recent_messages = []
    for message in memory_data["working_memory"].get("recent_messages", []):
        role = message.get("role")
        content = message.get("content")
        if role in {"user", "assistant"} and content:
            recent_messages.append({"role": role, "content": content})

    return MemoryContext(
        summary=memory_data["summary_memory"].get("summary", ""),
        recent_messages=recent_messages,
        current_plan=current_plan,
        plans_by_date=plans_by_date,
    )


def _daily_review_succeeded(response: DailyReviewResponse):
    return response.completion_summary != "Review was not generated." and not response.review_text.startswith(
        "AI request failed"
    )


def _append_unique(existing_items, new_items):
    seen = {item.strip().lower() for item in existing_items}
    merged = list(existing_items)
    for item in new_items:
        normalized = item.strip().lower()
        if item and normalized not in seen:
            merged.append(item)
            seen.add(normalized)
    return merged


def _collect_review_progress(review_date):
    plans_by_date = get_plans_by_date()
    completed = []
    partial = []
    missed = []

    for plan_date, plan in plans_by_date.items():
        for item in plan.get("schedule", []):
            title = item.get("activity")
            if not title:
                continue

            status = item.get("status", "not_started")
            completed_date = item.get("completed_date")
            label = title
            if plan_date != review_date:
                label = f"{title} (planned for {plan_date})"

            if status == "done" and (completed_date == review_date or (plan_date == review_date and not completed_date)):
                completed.append(label)
            elif plan_date == review_date and status == "partial":
                partial.append(label)
            elif plan_date == review_date and status == "missed":
                missed.append(label)

    return completed, partial, missed


def _operation_failure_message(results, language):
    failed = [result for result in results or [] if not result.get("applied")]
    if not failed:
        return ""

    if language == "zh":
        return "有些修改我理解了，但没有在已保存计划里找到完全对应的事项，所以没有全部应用。"
    return "I understood the request, but some changes could not be applied because I could not match the saved item."


@app.get("/")
def read_root():
    return {"message": "Personal AI Secretary backend is running."}


@app.post("/api/generate-plan", response_model=GeneratePlanResponse)
def api_generate_plan(request: GeneratePlanRequest):
    response = generate_plan(request)
    save_current_plan(response.model_dump())
    return response


@app.post("/api/adjust-plan", response_model=AdjustPlanResponse)
def api_adjust_plan(request: AdjustPlanRequest):
    response = adjust_plan(request)
    return response


@app.post("/api/daily-review", response_model=DailyReviewResponse)
def api_daily_review(request: DailyReviewRequest):
    enriched_request = request
    if request.review_date:
        completed, partial, missed = _collect_review_progress(request.review_date)
        enriched_request = request.model_copy(
            update={
                "completed_tasks": _append_unique(request.completed_tasks, completed),
                "partially_completed_tasks": _append_unique(request.partially_completed_tasks, partial),
                "failed_tasks": _append_unique(request.failed_tasks, missed),
            }
        )

    response = generate_daily_review(enriched_request)
    if enriched_request.review_date and _daily_review_succeeded(response):
        mark_plan_reviewed(enriched_request.review_date)
    return response


@app.post("/api/chat", response_model=ChatResponse)
def api_chat(request: ChatRequest):
    memory_data = get_memory()
    memory_context = _memory_context_from_file(memory_data)
    remembered_plan = memory_context.current_plan
    enriched_request = request.model_copy(
        update={
            "memory_context": memory_context,
            "current_plan": request.current_plan or remembered_plan,
        }
    )

    response = chat_with_secretary(enriched_request)

    save_profile_preferences(language=request.language, user_profile=request.user_profile)
    updated_memory = save_chat_turn(
        user_message=request.message,
        assistant_reply=response.reply,
        language=request.language,
        response_data=response.model_dump(),
    )
    operation_result = None
    if response.operations:
        operation_result = apply_plan_operations([operation.model_dump() for operation in response.operations])
        updated_memory = get_memory()

        latest_plan = operation_result.get("current_plan") or updated_memory["working_memory"].get("current_plan")
        failure_message = _operation_failure_message(operation_result.get("operation_results", []), request.language)
        response = ChatResponse.model_validate(
            {
                **response.model_dump(),
                "reply": f"{response.reply}\n{failure_message}" if failure_message else response.reply,
                "operation_results": operation_result.get("operation_results", []),
                "plans_by_date": operation_result.get("plans_by_date", {})
                or updated_memory["working_memory"].get("plans_by_date", {}),
                "plan_text": latest_plan.get("plan_text", response.plan_text) if latest_plan else response.plan_text,
                "plan_date": latest_plan.get("plan_date", response.plan_date) if latest_plan else response.plan_date,
                "schedule": latest_plan.get("schedule", response.schedule) if latest_plan else response.schedule,
                "summary": latest_plan.get("summary", response.summary) if latest_plan else response.summary,
            }
        )

    if should_summarize(updated_memory):
        messages_to_summarize = get_messages_to_summarize(updated_memory)
        summary = summarize_old_memory(
            updated_memory["summary_memory"].get("summary", ""),
            messages_to_summarize,
        )
        updated_memory = apply_summary(summary)

    return response


@app.get("/api/latest-plan")
def api_latest_plan():
    memory_data = get_memory()
    return memory_data["working_memory"].get("current_plan")


@app.get("/api/plans")
def api_plans():
    return {"plans_by_date": get_plans_by_date()}


@app.delete("/api/plans/{plan_date}")
def api_delete_plan(plan_date: str):
    result = delete_plan(plan_date)
    return result


@app.delete("/api/plans/{plan_date}/items/{item_index}")
def api_delete_schedule_item(plan_date: str, item_index: int):
    result = delete_schedule_item(plan_date, item_index)
    if not result["deleted"]:
        raise HTTPException(status_code=404, detail="Schedule item was not found.")
    return result


@app.patch("/api/plans/{plan_date}/items/{item_index}")
def api_update_schedule_item(plan_date: str, item_index: int, request: ScheduleItemUpdateRequest):
    updates = request.model_dump(exclude_unset=True)
    result = update_schedule_item(plan_date, item_index, updates)
    if not result["updated"]:
        status_code = 400 if result.get("reason") == "invalid_item" else 404
        raise HTTPException(status_code=status_code, detail="Schedule item could not be updated.")
    return result


@app.patch("/api/plans/{plan_date}/items/{item_index}/status")
def api_update_schedule_item_status(plan_date: str, item_index: int, request: ScheduleItemStatusRequest):
    result = update_schedule_item_status(plan_date, item_index, request.status, request.completed_date)
    if not result["updated"]:
        raise HTTPException(status_code=404, detail="Schedule item was not found.")
    return result


@app.get("/api/settings", response_model=ModelSettingsResponse)
def api_get_settings():
    return get_public_model_settings()


@app.post("/api/settings", response_model=ModelSettingsResponse)
def api_save_settings(request: ModelSettingsRequest):
    return save_model_settings(request)


@app.post("/api/settings/test")
def api_test_settings():
    return test_llm_connection()
