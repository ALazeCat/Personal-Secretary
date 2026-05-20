import { useState } from "react";

import { adjustPlan } from "../api.js";

const today = new Date().toISOString().slice(0, 10);

function parseTasks(text) {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((title) => ({
      title,
      estimated_minutes: 45,
      priority: "medium",
      category: "task",
      due_date: today
    }));
}

export default function AdjustPlan({ plan, t, onPlanAdjusted, onGoToday }) {
  const labels = t?.adjust || {};
  const [currentDate, setCurrentDate] = useState(plan?.plan_date || today);
  const [currentTime, setCurrentTime] = useState("14:00");
  const [changeDescription, setChangeDescription] = useState("");
  const [remainingText, setRemainingText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const result = await adjustPlan({
        original_plan: plan?.plan_text || "",
        current_date: currentDate,
        current_time: currentTime,
        change_description: changeDescription,
        remaining_tasks: parseTasks(remainingText)
      });
      onPlanAdjusted(result);
      onGoToday();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="stack" onSubmit={handleSubmit}>
      <section className="card form-card">
        <h2>{labels.title || "Adjust Plan"}</h2>
        <div className="two-column">
          <label>
            {labels.date || "Date"}
            <input type="date" value={currentDate} onChange={(event) => setCurrentDate(event.target.value)} />
          </label>
          <label>
            {labels.time || "Time"}
            <input type="time" value={currentTime} onChange={(event) => setCurrentTime(event.target.value)} />
          </label>
        </div>
        <label>
          {labels.whatChanged || "What changed?"}
          <textarea
            placeholder={labels.changePlaceholder || "I only finished 30 minutes of Linux study this morning."}
            value={changeDescription}
            onChange={(event) => setChangeDescription(event.target.value)}
          />
        </label>
        <label>
          {labels.remainingTasks || "Remaining tasks"}
          <textarea
            placeholder={labels.remainingPlaceholder || "Study Linux\nPractice IELTS speaking"}
            value={remainingText}
            onChange={(event) => setRemainingText(event.target.value)}
          />
        </label>
      </section>

      {error && <p className="error-box">{error}</p>}
      <button className="primary-button" type="submit" disabled={loading}>
        {loading ? labels.adjusting || "Adjusting..." : labels.submit || "Adjust Plan"}
      </button>
    </form>
  );
}
