import { useState } from "react";

import ScheduleView, {
  CompletedDateNote,
  ScheduleItemEditForm,
  ScheduleStatusControl,
  getDisplaySchedule,
  shouldShowSummary
} from "./ScheduleView.jsx";

function PlanPreview({
  plan,
  label,
  t,
  onDeletePlan,
  onDeleteScheduleItem,
  onUpdateScheduleItem,
  onUpdateScheduleItemStatus
}) {
  const [editingIndex, setEditingIndex] = useState(null);
  const displaySchedule = getDisplaySchedule(plan);

  return (
    <article className="schedule-card">
      <div className="card-title-row">
        <h3>{plan.plan_date}</h3>
        <div className="card-actions">
          <span className={`status-badge ${plan.status || "planned"}`}>{label}</span>
          <button className="tiny-danger-button" type="button" onClick={() => onDeletePlan(plan.plan_date)}>
            {t?.schedule.deletePlan || "Delete"}
          </button>
        </div>
      </div>
      {shouldShowSummary(plan.summary, t) && <p className="summary">{plan.summary}</p>}
      {displaySchedule.map(({ item, originalIndex }) => (
        <div className="mini-schedule-line" key={`${item.start}-${item.end}-${originalIndex}`}>
          <span>{item.start} - {item.end}</span>
          <div>
            <strong>{item.activity}</strong>
            <CompletedDateNote item={item} planDate={plan.plan_date} t={t} />
          </div>
          {onDeleteScheduleItem && (
            <button
              className="tiny-danger-button"
              type="button"
              onClick={() => onDeleteScheduleItem(plan.plan_date, originalIndex)}
            >
              {t?.schedule.deleteItem || "Remove"}
            </button>
          )}
          {onUpdateScheduleItem && (
            <button className="tiny-ghost-button" type="button" onClick={() => setEditingIndex(originalIndex)}>
              {t?.schedule.editItem || "Edit"}
            </button>
          )}
          {editingIndex === originalIndex && (
            <div className="mini-edit-row">
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
            </div>
          )}
          {onUpdateScheduleItemStatus && (
            <div className="mini-status-row">
              <ScheduleStatusControl
                item={item}
                t={t}
                onStatusChange={(status) => onUpdateScheduleItemStatus(plan.plan_date, originalIndex, status)}
              />
            </div>
          )}
        </div>
      ))}
    </article>
  );
}

function PlanSection({
  title,
  emptyText,
  plans,
  label,
  t,
  onDeletePlan,
  onDeleteScheduleItem,
  onUpdateScheduleItem,
  onUpdateScheduleItemStatus
}) {
  return (
    <section className="stack compact">
      <h2 className="section-heading">{title}</h2>
      {plans.length === 0 ? (
        <p className="muted-note">{emptyText}</p>
      ) : (
        plans.map((plan) => (
          <PlanPreview
            key={plan.plan_date}
            plan={plan}
            label={label(plan)}
            t={t}
            onDeletePlan={onDeletePlan}
            onDeleteScheduleItem={onDeleteScheduleItem}
            onUpdateScheduleItem={onUpdateScheduleItem}
            onUpdateScheduleItemStatus={onUpdateScheduleItemStatus}
          />
        ))
      )}
    </section>
  );
}

export default function TodayView({
  plansByDate,
  todayDate,
  adjustedPlan,
  t,
  onDeletePlan,
  onDeleteScheduleItem,
  onUpdateScheduleItem,
  onUpdateScheduleItemStatus,
  actionError
}) {
  const plans = Object.values(plansByDate || {}).sort((a, b) => a.plan_date.localeCompare(b.plan_date));
  const todayPlan = plansByDate?.[todayDate];
  const upcomingPlans = plans.filter((plan) => plan.plan_date > todayDate && plan.status !== "reviewed");
  const needsReviewPlans = plans.filter((plan) => plan.plan_date < todayDate && plan.status !== "reviewed");
  const reviewedPlans = plans
    .filter((plan) => plan.plan_date < todayDate && plan.status === "reviewed")
    .slice(-3)
    .reverse();

  return (
    <section className="stack">
      {actionError && <p className="error-box">{actionError}</p>}

      <ScheduleView
        plan={todayPlan}
        adjustedPlan={adjustedPlan}
        t={t}
        todayOnly
        todayDate={todayDate}
        onDeletePlan={onDeletePlan}
        onDeleteScheduleItem={onDeleteScheduleItem}
        onUpdateScheduleItem={onUpdateScheduleItem}
        onUpdateScheduleItemStatus={onUpdateScheduleItemStatus}
      />

      <PlanSection
        title={t?.schedule.upcomingTitle || "Upcoming"}
        emptyText={t?.schedule.noUpcoming || "No future plans saved yet."}
        plans={upcomingPlans}
        label={() => t?.schedule.statusPlanned || "planned"}
        t={t}
        onDeletePlan={onDeletePlan}
        onDeleteScheduleItem={onDeleteScheduleItem}
        onUpdateScheduleItem={onUpdateScheduleItem}
        onUpdateScheduleItemStatus={onUpdateScheduleItemStatus}
      />

      <PlanSection
        title={t?.schedule.needsReviewTitle || "Needs Review"}
        emptyText={t?.schedule.noNeedsReview || "No past plans need review."}
        plans={needsReviewPlans}
        label={() => t?.schedule.statusNeedsReview || "needs review"}
        t={t}
        onDeletePlan={onDeletePlan}
        onDeleteScheduleItem={onDeleteScheduleItem}
        onUpdateScheduleItem={onUpdateScheduleItem}
        onUpdateScheduleItemStatus={onUpdateScheduleItemStatus}
      />

      {reviewedPlans.length > 0 && (
        <PlanSection
          title={t?.schedule.reviewedTitle || "Reviewed"}
          emptyText=""
          plans={reviewedPlans}
          label={() => t?.schedule.statusReviewed || "reviewed"}
          t={t}
          onDeletePlan={onDeletePlan}
          onDeleteScheduleItem={onDeleteScheduleItem}
          onUpdateScheduleItem={onUpdateScheduleItem}
          onUpdateScheduleItemStatus={onUpdateScheduleItemStatus}
        />
      )}
    </section>
  );
}
