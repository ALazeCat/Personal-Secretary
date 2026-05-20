import { useEffect, useState } from "react";

import { chatWithSecretary } from "../api.js";
import { formatLocalDate } from "../dateUtils.js";
import ScheduleView from "./ScheduleView.jsx";

function getCurrentDate() {
  return formatLocalDate();
}

function getCurrentTime() {
  return new Date().toTimeString().slice(0, 5);
}

const defaultProfile = {
  wake_up_time: "09:00",
  sleep_time: "23:30",
  energy_level: "normal",
  planning_style: "realistic"
};

export default function ChatSecretary({ language, plan, todayPlan, todayDate, onPlanUpdated, t }) {
  const [messages, setMessages] = useState([{ role: "assistant", content: t.chat.starter }]);
  const [input, setInput] = useState("");
  const [extractedItems, setExtractedItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setMessages((current) => {
      if (current.length === 1 && current[0].role === "assistant") {
        return [{ role: "assistant", content: t.chat.starter }];
      }
      return current;
    });
  }, [language, t.chat.starter]);

  async function handleSubmit(event) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || loading) {
      return;
    }

    const userMessage = { role: "user", content: trimmed };
    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);
    setError("");

    try {
      const result = await chatWithSecretary({
        message: trimmed,
        language,
        current_date: getCurrentDate(),
        current_time: getCurrentTime(),
        user_profile: defaultProfile,
        conversation_history: nextMessages.slice(-8),
        current_plan: plan
      });

      setMessages((current) => [...current, { role: "assistant", content: result.reply }]);
      setExtractedItems(result.extracted_items || []);

      const plansByDate = result.plans_by_date || {};
      const hasSavedPlanUpdate = Object.keys(plansByDate).length > 0;
      const hasDirectPlanUpdate = Boolean(result.plan_text || result.schedule?.length);
      const hasAppliedOperation = (result.operation_results || []).some((operation) => operation.applied);

      if (hasSavedPlanUpdate || hasDirectPlanUpdate || hasAppliedOperation) {
        const visiblePlan = plansByDate[getCurrentDate()] || {
          plan_text: result.plan_text || plan?.plan_text || "",
          plan_date: result.plan_date || plan?.plan_date || getCurrentDate(),
          schedule: result.schedule?.length ? result.schedule : plan?.schedule || [],
          summary: result.summary || plan?.summary || ""
        };
        onPlanUpdated(
          visiblePlan,
          hasSavedPlanUpdate ? plansByDate : null
        );
      }
    } catch (err) {
      setError(err.message);
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: t.chat.error
        }
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="chat-layout">
      <div className="chat-panel">
        <div className="message-list" aria-live="polite">
          {messages.map((message, index) => (
            <div className={`message ${message.role}`} key={`${message.role}-${index}`}>
              <p>{message.content}</p>
            </div>
          ))}
          {loading && (
            <div className="message assistant">
              <p>{t.chat.thinking}</p>
            </div>
          )}
        </div>

        {extractedItems.length > 0 && (
          <div className="extracted-strip">
            {extractedItems.map((item, index) => (
              <span key={`${item.title}-${index}`}>
                {t.chat.extractedTypes?.[item.kind] || item.kind}: {item.title}
              </span>
            ))}
          </div>
        )}

        {error && <p className="error-box">{error}</p>}

        <form className="chat-input-row" onSubmit={handleSubmit}>
          <textarea
            aria-label={t.chat.messageLabel || "Message to AI secretary"}
            placeholder={t.chat.placeholder}
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                handleSubmit(event);
              }
            }}
          />
          <button className="send-button" type="submit" disabled={loading || !input.trim()}>
            {t.chat.send}
          </button>
        </form>
      </div>

      <ScheduleView plan={todayPlan} compactEmpty todayOnly todayDate={todayDate} t={t} />
    </section>
  );
}
