from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    wake_up_time: str
    sleep_time: str
    energy_level: str
    planning_style: str = "realistic"


class FixedEvent(BaseModel):
    title: str
    date: Optional[str] = None
    start: str
    end: str


class Task(BaseModel):
    title: str
    estimated_minutes: int
    priority: str
    category: str
    due_date: Optional[str] = None


class GeneratePlanRequest(BaseModel):
    plan_date: Optional[str] = None
    user_profile: UserProfile
    fixed_events: List[FixedEvent] = Field(default_factory=list)
    tasks: List[Task] = Field(default_factory=list)


class ScheduleItem(BaseModel):
    date: Optional[str] = None
    start: str
    end: str
    activity: str
    type: str = "task"
    due_date: Optional[str] = None
    status: Literal["not_started", "done", "partial", "missed"] = "not_started"
    completed_date: Optional[str] = None


class GeneratePlanResponse(BaseModel):
    plan_text: str
    plan_date: Optional[str] = None
    schedule: List[ScheduleItem] = Field(default_factory=list)
    summary: str


class AdjustPlanRequest(BaseModel):
    original_plan: str
    current_date: Optional[str] = None
    current_time: str
    change_description: str
    remaining_tasks: List[Task] = Field(default_factory=list)


class AdjustPlanResponse(BaseModel):
    adjusted_plan_text: str
    plan_date: Optional[str] = None
    summary: str


class DailyReviewRequest(BaseModel):
    review_date: Optional[str] = None
    today_plan: str
    completed_tasks: List[str] = Field(default_factory=list)
    partially_completed_tasks: List[str] = Field(default_factory=list)
    failed_tasks: List[str] = Field(default_factory=list)
    mood: str


class DailyReviewResponse(BaseModel):
    review_text: str
    completion_summary: str
    tomorrow_suggestions: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ExtractedItem(BaseModel):
    kind: Literal["task", "fixed_event", "note"]
    title: str
    date: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    estimated_minutes: Optional[int] = None
    priority: str = "medium"
    category: str = "general"
    due_date: Optional[str] = None
    notes: Optional[str] = None


class MemoryContext(BaseModel):
    summary: str = ""
    recent_messages: List[ChatMessage] = Field(default_factory=list)
    current_plan: Optional[GeneratePlanResponse] = None
    plans_by_date: Dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    message: str
    language: Literal["en", "zh"] = "en"
    current_date: Optional[str] = None
    current_time: Optional[str] = None
    user_profile: Optional[UserProfile] = None
    conversation_history: List[ChatMessage] = Field(default_factory=list)
    current_plan: Optional[GeneratePlanResponse] = None
    memory_context: Optional[MemoryContext] = None


class PlanOperation(BaseModel):
    action: Literal["update_item", "delete_item", "set_status", "add_item"]
    plan_date: str
    item_match: Optional[str] = None
    item_index: Optional[int] = None
    target_type: Optional[str] = None
    time_hint: Dict[str, Any] = Field(default_factory=dict)
    changes: Dict[str, Any] = Field(default_factory=dict)
    item: Dict[str, Any] = Field(default_factory=dict)
    status: Optional[Literal["not_started", "done", "partial", "missed"]] = None
    completed_date: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    extracted_items: List[ExtractedItem] = Field(default_factory=list)
    plan_text: str
    plan_date: Optional[str] = None
    schedule: List[ScheduleItem] = Field(default_factory=list)
    summary: str
    operations: List[PlanOperation] = Field(default_factory=list)
    operation_results: List[Dict[str, Any]] = Field(default_factory=list)
    plans_by_date: Dict[str, Any] = Field(default_factory=dict)
    needs_follow_up: bool = False
    follow_up_question: Optional[str] = None


class MemoryResponse(BaseModel):
    profile_memory: Dict[str, Any] = Field(default_factory=dict)
    working_memory: Dict[str, Any] = Field(default_factory=dict)
    summary_memory: Dict[str, Any] = Field(default_factory=dict)


class ProviderOption(BaseModel):
    id: str
    name: str
    default_model: str
    default_base_url: Optional[str] = None
    openai_compatible: bool = True


class ModelSettingsRequest(BaseModel):
    provider: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class ModelSettingsResponse(BaseModel):
    provider: str
    model: str
    base_url: Optional[str] = None
    api_key_set: bool = False
    masked_api_key: Optional[str] = None
    using_env_fallback: bool = False
    available_providers: List[ProviderOption] = Field(default_factory=list)


class ScheduleItemStatusRequest(BaseModel):
    status: Literal["not_started", "done", "partial", "missed"]
    completed_date: Optional[str] = None


class ScheduleItemUpdateRequest(BaseModel):
    date: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    activity: Optional[str] = None
    type: Optional[str] = None
    due_date: Optional[str] = None
