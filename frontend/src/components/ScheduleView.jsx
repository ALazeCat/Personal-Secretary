import { useState } from "react";

function EmptySchedule({ compactEmpty, t, todayOnly, todayDate, otherPlanDate }) {
  return (
    <section className={compactEmpty ? "empty-state compact-empty" : "empty-state"}>
      <h2>
        {todayOnly
          ? t?.schedule.noPlanForTodayTitle || "No plan for today"
          : t?.schedule.noPlanTitle || "No plan yet"}
      </h2>
      <p>
        {todayOnly
          ? t?.schedule.noPlanForTodayBody || "There is no saved schedule for today."
          : t?.schedule.noPlanBody || "Talk to your secretary first. Your schedule will appear here automatically."}
      </p>
      {todayOnly && otherPlanDate && (
        <p className="muted-note">
          {(t?.schedule.otherPlanDate || "Latest remembered plan:").replace("{date}", otherPlanDate)}
        </p>
      )}
      {todayOnly && todayDate && <span className="small-pill">{todayDate}</span>}
    </section>
  );
}

export function ScheduleStatusControl({ item, t, onStatusChange }) {
  return (
    <div className="status-control" aria-label={t?.schedule.itemStatus || "Item status"}>
      {["not_started", "done", "partial", "missed"].map((status) => (
        <button
          className={item.status === status || (!item.status && status === "not_started") ? "active" : ""}
          type="button"
          key={status}
          onClick={() => onStatusChange(status)}
        >
          {t?.schedule.itemStatuses?.[status] || status}
        </button>
      ))}
    </div>
  );
}

export function CompletedDateNote({ item, planDate, t }) {
  if (item.status !== "done" || !item.completed_date) {
    return null;
  }

  const label =
    item.completed_date === planDate
      ? t?.schedule.completedOn || "Done on {date}"
      : t?.schedule.completedEarly || "Done early on {date}";

  return <p className="completion-note">{label.replace("{date}", item.completed_date)}</p>;
}

export function ScheduleItemEditForm({ item, planDate, t, onCancel, onSave }) {
  const [form, setForm] = useState({
    date: item.date || planDate || "",
    start: item.start || "",
    end: item.end || "",
    activity: item.activity || "",
    type: item.type || "task",
    due_date: item.due_date || ""
  });

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function handleSubmit(event) {
    event.preventDefault();
    onSave({
      ...form,
      due_date: form.due_date || null
    });
  }

  return (
    <form className="inline-edit-form" onSubmit={handleSubmit}>
      <div className="two-column">
        <label>
          {t?.schedule.editDate || "Date"}
          <input type="date" value={form.date} onChange={(event) => updateField("date", event.target.value)} />
        </label>
        <label>
          {t?.schedule.editType || "Type"}
          <input value={form.type} onChange={(event) => updateField("type", event.target.value)} />
        </label>
      </div>
      <div className="two-column">
        <label>
          {t?.schedule.editStart || "Start"}
          <input type="time" value={form.start} onChange={(event) => updateField("start", event.target.value)} />
        </label>
        <label>
          {t?.schedule.editEnd || "End"}
          <input type="time" value={form.end} onChange={(event) => updateField("end", event.target.value)} />
        </label>
      </div>
      <label>
        {t?.schedule.editActivity || "Activity"}
        <input
          required
          value={form.activity}
          onChange={(event) => updateField("activity", event.target.value)}
        />
      </label>
      <label>
        {t?.schedule.editDueDate || "Due date"}
        <input type="date" value={form.due_date} onChange={(event) => updateField("due_date", event.target.value)} />
      </label>
      <div className="inline-edit-actions">
        <button className="ghost-button" type="button" onClick={onCancel}>
          {t?.schedule.cancelEdit || "Cancel"}
        </button>
        <button className="primary-button compact-button" type="submit">
          {t?.schedule.saveEdit || "Save"}
        </button>
      </div>
    </form>
  );
}

function scheduleIdentity(item, fallbackDate = "") {
  return [
    item.date || fallbackDate,
    item.start || "",
    item.end || "",
    (item.activity || "").trim().toLowerCase(),
    (item.type || "task").trim().toLowerCase()
  ].join("|");
}

export function getDisplaySchedule(plan) {
  const seen = new Set();
  return (plan.schedule || [])
    .map((item, originalIndex) => ({ item, originalIndex }))
    .filter(({ item }) => {
      const key = scheduleIdentity(item, plan.plan_date);
      if (seen.has(key)) {
        return false;
      }
      seen.add(key);
      return true;
    });
}

export function getItemTypeLabel(type, t) {
  const normalized = String(type || "task").trim().toLowerCase();
  return t?.schedule?.itemTypes?.[normalized] || type || t?.schedule?.itemTypes?.task || "task";
}

function planTextFromSchedule(plan, displaySchedule) {
  const lines = displaySchedule
    .map(({ item }) => item)
    .filter((item) => item.start && item.end && item.activity)
    .map((item) => `${item.start}-${item.end} ${item.activity}`);
  return lines.length > 0 ? lines.join("\n") : plan.plan_text || "";
}

function hasChineseText(value) {
  return /[\u3400-\u9fff]/.test(value || "");
}

export function shouldShowSummary(summary, t) {
  if (!summary) {
    return false;
  }
  const isChineseUi = t?.tabs?.today === "今日";
  const looksLikeOldEnglishSummary = /[A-Za-z]/.test(summary) && !hasChineseText(summary);
  return !(isChineseUi && looksLikeOldEnglishSummary);
}

export default function ScheduleView({
  plan,
  adjustedPlan,
  compactEmpty = false,
  t,
  todayOnly = false,
  todayDate,
  onDeletePlan,
  onDeleteScheduleItem,
  onUpdateScheduleItem,
  onUpdateScheduleItemStatus
}) {
  const [editingIndex, setEditingIndex] = useState(null);

  if (!plan) {
    return (
      <EmptySchedule compactEmpty={compactEmpty} t={t} todayOnly={todayOnly} todayDate={todayDate} />
    );
  }

  if (todayOnly && plan.plan_date && todayDate && plan.plan_date !== todayDate) {
    return (
      <EmptySchedule
        compactEmpty={compactEmpty}
        t={t}
        todayOnly={todayOnly}
        todayDate={todayDate}
        otherPlanDate={plan.plan_date}
      />
    );
  }

  const displaySchedule = getDisplaySchedule(plan);

  return (
    <section className="stack">
      <article className="card">
        <div className="card-title-row">
          <h2>{t?.schedule.dailyPlan || "Daily Plan"}</h2>
          <div className="card-actions">
            {plan.plan_date && <span className="small-pill">{plan.plan_date}</span>}
            {onDeletePlan && plan.plan_date && (
              <button className="tiny-danger-button" type="button" onClick={() => onDeletePlan(plan.plan_date)}>
                {t?.schedule.deletePlan || "Delete"}
              </button>
            )}
          </div>
        </div>
        <p className="pre-line">{planTextFromSchedule(plan, displaySchedule)}</p>
        {shouldShowSummary(plan.summary, t) && <p className="summary">{plan.summary}</p>}
      </article>

      {displaySchedule.length > 0 && (
        <div className="stack compact">
          {displaySchedule.map(({ item, originalIndex }) => (
            <article className="schedule-card" key={`${item.start}-${item.end}-${originalIndex}`}>
              <div className="schedule-card-header">
                <div>
                  <div className="time-range">
                    {item.start} - {item.end}
                  </div>
                  <h3>{item.activity}</h3>
                </div>
                <div className="item-action-row">
                  {onUpdateScheduleItem && plan.plan_date && (
                    <button className="tiny-ghost-button" type="button" onClick={() => setEditingIndex(originalIndex)}>
                      {t?.schedule.editItem || "Edit"}
                    </button>
                  )}
                  {onDeleteScheduleItem && plan.plan_date && (
                    <button
                      className="tiny-danger-button"
                      type="button"
                      onClick={() => onDeleteScheduleItem(plan.plan_date, originalIndex)}
                    >
                      {t?.schedule.deleteItem || "Remove"}
                    </button>
                  )}
                </div>
              </div>
              {editingIndex === originalIndex ? (
                <ScheduleItemEditForm
                  item={item}
                  planDate={plan.plan_date}
                  t={t}
                  onCancel={() => setEditingIndex(null)}
                  onSave={(payload) => {
                    onUpdateScheduleItem(plan.plan_date, originalIndex, payload);
                    setEditingIndex(null);
                  }}
                />
              ) : (
                <>
                  <div className="meta-row">
                    <span>{getItemTypeLabel(item.type, t)}</span>
                    {item.due_date && <span>{t?.schedule.due || "Due"} {item.due_date}</span>}
                  </div>
                  <CompletedDateNote item={item} planDate={plan.plan_date} t={t} />
                  {onUpdateScheduleItemStatus && plan.plan_date && (
                    <ScheduleStatusControl
                      item={item}
                      t={t}
                      onStatusChange={(status) => onUpdateScheduleItemStatus(plan.plan_date, originalIndex, status)}
                    />
                  )}
                </>
              )}
            </article>
          ))}
        </div>
      )}

      {adjustedPlan && (
        <article className="card accent-card">
          <div className="card-title-row">
            <h2>{t?.schedule.adjustedPlan || "Adjusted Plan"}</h2>
            {adjustedPlan.plan_date && <span className="small-pill">{adjustedPlan.plan_date}</span>}
          </div>
          <p className="pre-line">{adjustedPlan.adjusted_plan_text}</p>
          {shouldShowSummary(adjustedPlan.summary, t) && <p className="summary">{adjustedPlan.summary}</p>}
        </article>
      )}
    </section>
  );
}
