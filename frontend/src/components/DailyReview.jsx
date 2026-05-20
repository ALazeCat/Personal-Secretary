import { useEffect, useMemo, useState } from "react";

import { generateDailyReview } from "../api.js";
import { formatLocalDate } from "../dateUtils.js";

const today = formatLocalDate();

function splitList(text) {
  return text
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function reviewSucceeded(result) {
  return result?.completion_summary !== "Review was not generated." && !result?.review_text?.startsWith("AI request failed");
}

function collectReviewItems(plansByDate, reviewDate) {
  const completed = [];
  const partial = [];
  const missed = [];
  const todo = [];

  Object.values(plansByDate || {}).forEach((plan) => {
    const planDate = plan.plan_date;
    (plan.schedule || []).forEach((item) => {
      const label = planDate === reviewDate ? item.activity : `${item.activity} (${planDate})`;

      if (item.status === "done" && (item.completed_date === reviewDate || (planDate === reviewDate && !item.completed_date))) {
        completed.push(label);
      } else if (planDate === reviewDate && item.status === "partial") {
        partial.push(label);
      } else if (planDate === reviewDate && item.status === "missed") {
        missed.push(label);
      } else if (planDate === reviewDate && (!item.status || item.status === "not_started")) {
        todo.push(label);
      }
    });
  });

  return { completed, partial, missed, todo };
}

function ReviewList({ title, items, emptyText }) {
  return (
    <div className="review-group">
      <h3>{title}</h3>
      {items.length > 0 ? (
        <ul>
          {items.map((item, index) => (
            <li key={`${item}-${index}`}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="muted-note">{emptyText}</p>
      )}
    </div>
  );
}

export default function DailyReview({
  plan,
  plansByDate = {},
  todayDate = today,
  t,
  review,
  onReviewGenerated,
  onReviewCompleted
}) {
  const [reviewDate, setReviewDate] = useState(plan?.plan_date || todayDate);
  const [extraCompleted, setExtraCompleted] = useState("");
  const [extraPartial, setExtraPartial] = useState("");
  const [extraFailed, setExtraFailed] = useState("");
  const [mood, setMood] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!reviewDate && todayDate) {
      setReviewDate(todayDate);
    }
  }, [reviewDate, todayDate]);

  const reviewPlan = plansByDate?.[reviewDate] || (plan?.plan_date === reviewDate ? plan : null);
  const autoItems = useMemo(() => collectReviewItems(plansByDate, reviewDate), [plansByDate, reviewDate]);
  const completedTasks = [...autoItems.completed, ...splitList(extraCompleted)];
  const partialTasks = [...autoItems.partial, ...splitList(extraPartial)];
  const failedTasks = [...autoItems.missed, ...splitList(extraFailed)];

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const result = await generateDailyReview({
        review_date: reviewDate,
        today_plan: reviewPlan?.plan_text || "",
        completed_tasks: completedTasks,
        partially_completed_tasks: partialTasks,
        failed_tasks: failedTasks,
        mood
      });
      onReviewGenerated(result);
      if (reviewSucceeded(result)) {
        onReviewCompleted?.(reviewDate);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="stack">
      <form className="card form-card" onSubmit={handleSubmit}>
        <h2>{t?.review?.title || "Daily Review"}</h2>
        <label>
          {t?.review?.reviewDate || "Review date"}
          <input type="date" value={reviewDate} onChange={(event) => setReviewDate(event.target.value)} />
        </label>

        <section className="review-preview">
          <ReviewList
            title={t?.review?.autoCompleted || "Auto Completed"}
            items={autoItems.completed}
            emptyText={t?.review?.noneCompleted || "No completed items marked yet."}
          />
          <ReviewList
            title={t?.review?.autoPartial || "Auto Partial"}
            items={autoItems.partial}
            emptyText={t?.review?.nonePartial || "No partial items marked yet."}
          />
          <ReviewList
            title={t?.review?.autoMissed || "Auto Missed"}
            items={autoItems.missed}
            emptyText={t?.review?.noneMissed || "No missed items marked yet."}
          />
          {autoItems.todo.length > 0 && (
            <ReviewList
              title={t?.review?.stillTodo || "Still Todo"}
              items={autoItems.todo}
              emptyText=""
            />
          )}
        </section>

        <label>
          {t?.review?.extraCompleted || "Extra completed tasks"}
          <textarea
            placeholder={t?.review?.extraCompletedPlaceholder || "Optional, comma-separated"}
            value={extraCompleted}
            onChange={(event) => setExtraCompleted(event.target.value)}
          />
        </label>
        <label>
          {t?.review?.extraPartial || "Extra partially completed tasks"}
          <textarea value={extraPartial} onChange={(event) => setExtraPartial(event.target.value)} />
        </label>
        <label>
          {t?.review?.extraMissed || "Extra missed tasks"}
          <textarea value={extraFailed} onChange={(event) => setExtraFailed(event.target.value)} />
        </label>
        <label>
          {t?.review?.mood || "Mood / notes"}
          <input
            placeholder={t?.review?.moodPlaceholder || "a little tired, but focused"}
            value={mood}
            onChange={(event) => setMood(event.target.value)}
          />
        </label>

        {error && <p className="error-box">{error}</p>}
        <button className="primary-button" type="submit" disabled={loading}>
          {loading ? t?.review?.reviewing || "Reviewing..." : t?.review?.generate || "Generate Daily Review"}
        </button>
      </form>

      {review && (
        <article className="card accent-card">
          <h2>{t?.review?.resultTitle || "Review Result"}</h2>
          <p className="pre-line">{review.review_text}</p>
          <p className="summary">{review.completion_summary}</p>
          {review.tomorrow_suggestions && <p>{review.tomorrow_suggestions}</p>}
        </article>
      )}
    </section>
  );
}
