import { useState } from "react";

import { generatePlan } from "../api.js";

const today = new Date().toISOString().slice(0, 10);

function emptyEvent() {
  return { title: "", date: today, start: "12:00", end: "13:00" };
}

function emptyTask() {
  return {
    title: "",
    estimated_minutes: 60,
    priority: "medium",
    category: "study",
    due_date: today
  };
}

export default function TaskForm({ t, onPlanGenerated, onGoToday }) {
  const labels = t?.manual || {};
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [profile, setProfile] = useState({
    wake_up_time: "09:00",
    sleep_time: "24:00",
    energy_level: "normal",
    planning_style: "realistic"
  });
  const [planDate, setPlanDate] = useState(today);
  const [fixedEvents, setFixedEvents] = useState([emptyEvent()]);
  const [tasks, setTasks] = useState([emptyTask()]);

  function updateProfile(field, value) {
    setProfile((current) => ({ ...current, [field]: value }));
  }

  function updateEvent(index, field, value) {
    setFixedEvents((current) =>
      current.map((event, eventIndex) => (eventIndex === index ? { ...event, [field]: value } : event))
    );
  }

  function updateTask(index, field, value) {
    setTasks((current) =>
      current.map((task, taskIndex) =>
        taskIndex === index
          ? { ...task, [field]: field === "estimated_minutes" ? Number(value) : value }
          : task
      )
    );
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    const payload = {
      plan_date: planDate,
      user_profile: profile,
      fixed_events: fixedEvents.filter((item) => item.title.trim()),
      tasks: tasks.filter((item) => item.title.trim())
    };

    try {
      const result = await generatePlan(payload);
      onPlanGenerated(result);
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
        <h2>{labels.daySetup || "Day Setup"}</h2>
        <label>
          {labels.planDate || "Plan date"}
          <input type="date" value={planDate} onChange={(event) => setPlanDate(event.target.value)} />
        </label>
        <div className="two-column">
          <label>
            {labels.wakeUp || "Wake up"}
            <input
              type="time"
              value={profile.wake_up_time}
              onChange={(event) => updateProfile("wake_up_time", event.target.value)}
            />
          </label>
          <label>
            {labels.sleep || "Sleep"}
            <input
              type="time"
              value={profile.sleep_time === "24:00" ? "23:59" : profile.sleep_time}
              onChange={(event) => updateProfile("sleep_time", event.target.value)}
            />
          </label>
        </div>
        <label>
          {labels.energy || "Energy"}
          <select value={profile.energy_level} onChange={(event) => updateProfile("energy_level", event.target.value)}>
            <option value="low">{labels.energyLow || "Low"}</option>
            <option value="normal">{labels.energyNormal || "Normal"}</option>
            <option value="high">{labels.energyHigh || "High"}</option>
          </select>
        </label>
        <label>
          {labels.planningStyle || "Planning style"}
          <select
            value={profile.planning_style}
            onChange={(event) => updateProfile("planning_style", event.target.value)}
          >
            <option value="realistic">{labels.styleRealistic || "Realistic"}</option>
            <option value="light">{labels.styleLight || "Light"}</option>
            <option value="focused">{labels.styleFocused || "Focused"}</option>
          </select>
        </label>
      </section>

      <section className="card form-card">
        <div className="card-title-row">
          <h2>{labels.fixedEvents || "Fixed Events"}</h2>
          <button className="ghost-button" type="button" onClick={() => setFixedEvents([...fixedEvents, emptyEvent()])}>
            {labels.add || "Add"}
          </button>
        </div>
        {fixedEvents.map((item, index) => (
          <div className="mini-form" key={index}>
            <input
              aria-label={labels.eventTitle || "Event title"}
              placeholder={labels.eventPlaceholder || "Lunch, class, meeting..."}
              value={item.title}
              onChange={(event) => updateEvent(index, "title", event.target.value)}
            />
            <input type="date" value={item.date} onChange={(event) => updateEvent(index, "date", event.target.value)} />
            <div className="two-column">
              <input type="time" value={item.start} onChange={(event) => updateEvent(index, "start", event.target.value)} />
              <input type="time" value={item.end} onChange={(event) => updateEvent(index, "end", event.target.value)} />
            </div>
          </div>
        ))}
      </section>

      <section className="card form-card">
        <div className="card-title-row">
          <h2>{labels.tasks || "Tasks"}</h2>
          <button className="ghost-button" type="button" onClick={() => setTasks([...tasks, emptyTask()])}>
            {labels.add || "Add"}
          </button>
        </div>
        {tasks.map((item, index) => (
          <div className="mini-form" key={index}>
            <input
              aria-label={labels.taskTitle || "Task title"}
              placeholder={labels.taskPlaceholder || "Study Linux"}
              value={item.title}
              onChange={(event) => updateTask(index, "title", event.target.value)}
            />
            <div className="two-column">
              <input
                aria-label={labels.estimatedMinutes || "Estimated minutes"}
                min="10"
                step="5"
                type="number"
                value={item.estimated_minutes}
                onChange={(event) => updateTask(index, "estimated_minutes", event.target.value)}
              />
              <select value={item.priority} onChange={(event) => updateTask(index, "priority", event.target.value)}>
                <option value="high">{labels.priorityHigh || "High"}</option>
                <option value="medium">{labels.priorityMedium || "Medium"}</option>
                <option value="low">{labels.priorityLow || "Low"}</option>
              </select>
            </div>
            <div className="two-column">
              <input
                aria-label={labels.category || "Category"}
                placeholder={labels.categoryPlaceholder || "study"}
                value={item.category}
                onChange={(event) => updateTask(index, "category", event.target.value)}
              />
              <input
                aria-label={labels.dueDate || "Due date"}
                type="date"
                value={item.due_date}
                onChange={(event) => updateTask(index, "due_date", event.target.value)}
              />
            </div>
          </div>
        ))}
      </section>

      {error && <p className="error-box">{error}</p>}
      <button className="primary-button" type="submit" disabled={loading}>
        {loading ? labels.generating || "Generating..." : labels.generate || "Generate Daily Plan"}
      </button>
    </form>
  );
}
