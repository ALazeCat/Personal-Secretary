import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";

import {
  deletePlan,
  deleteScheduleItem,
  getLatestPlan,
  getPlans,
  updateScheduleItem,
  updateScheduleItemStatus
} from "./api.js";
import AdjustPlan from "./components/AdjustPlan.jsx";
import BottomNav from "./components/BottomNav.jsx";
import ChatSecretary from "./components/ChatSecretary.jsx";
import DailyReview from "./components/DailyReview.jsx";
import SettingsPanel from "./components/SettingsPanel.jsx";
import TaskForm from "./components/TaskForm.jsx";
import TodayView from "./components/TodayView.jsx";
import { formatLocalDate } from "./dateUtils.js";
import { getInitialLanguage, translations } from "./i18n.js";
import { registerServiceWorker } from "./pwa.js";
import "./styles.css";

function App() {
  const [activeTab, setActiveTab] = useState("secretary");
  const [language, setLanguage] = useState(getInitialLanguage);
  const [plan, setPlan] = useState(null);
  const [plansByDate, setPlansByDate] = useState({});
  const [adjustedPlan, setAdjustedPlan] = useState(null);
  const [review, setReview] = useState(null);
  const [planActionError, setPlanActionError] = useState("");
  const t = translations[language];
  const todayDate = formatLocalDate();

  useEffect(() => {
    async function loadRememberedPlan() {
      try {
        const latestPlan = await getLatestPlan();
        if (latestPlan?.plan_text || latestPlan?.schedule?.length) {
          setPlan(latestPlan);
        }
        const plans = await getPlans();
        setPlansByDate(plans.plans_by_date || {});
      } catch {
        // The app can still work without memory, so startup should stay quiet.
      }
    }

    loadRememberedPlan();
  }, []);

  function handleLanguageChange(nextLanguage) {
    setLanguage(nextLanguage);
    localStorage.setItem("secretary-language", nextLanguage);
  }

  function handlePlanUpdated(nextPlan, nextPlansByDate = null) {
    setPlan(nextPlan);
    if (nextPlansByDate) {
      setPlansByDate(nextPlansByDate);
      return;
    }
    if (nextPlan?.plan_date) {
      setPlansByDate((current) => ({
        ...current,
        [nextPlan.plan_date]: {
          ...current[nextPlan.plan_date],
          ...nextPlan,
          status: current[nextPlan.plan_date]?.status || "planned"
        }
      }));
    }
  }

  function handlePlanReviewed(reviewDate) {
    setPlansByDate((current) => {
      if (!current[reviewDate]) {
        return current;
      }
      return {
        ...current,
        [reviewDate]: {
          ...current[reviewDate],
          status: "reviewed"
        }
      };
    });
  }

  async function handleDeletePlan(planDate) {
    setPlanActionError("");
    try {
      await deletePlan(planDate);
      setPlansByDate((current) => {
        const next = { ...current };
        delete next[planDate];
        return next;
      });
      if (plan?.plan_date === planDate) {
        setPlan(null);
      }
    } catch {
      setPlanActionError(t.schedule.deleteFailed);
    }
  }

  async function handleDeleteScheduleItem(planDate, itemIndex) {
    setPlanActionError("");
    try {
      const result = await deleteScheduleItem(planDate, itemIndex);
      setPlansByDate(result.plans_by_date || {});
      setPlan(result.current_plan || null);
    } catch {
      setPlanActionError(t.schedule.deleteItemFailed);
    }
  }

  async function handleUpdateScheduleItemStatus(planDate, itemIndex, status) {
    setPlanActionError("");
    try {
      const completedDate = status === "done" ? todayDate : null;
      const result = await updateScheduleItemStatus(planDate, itemIndex, status, completedDate);
      setPlansByDate(result.plans_by_date || {});
      setPlan(result.current_plan || null);
    } catch {
      setPlanActionError(t.schedule.statusUpdateFailed);
    }
  }

  async function handleUpdateScheduleItem(planDate, itemIndex, payload) {
    setPlanActionError("");
    try {
      const result = await updateScheduleItem(planDate, itemIndex, payload);
      setPlansByDate(result.plans_by_date || {});
      setPlan(result.current_plan || null);
    } catch {
      setPlanActionError(t.schedule.editFailed);
    }
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">{t.appName}</p>
          <h1>{t.tabs[activeTab]}</h1>
        </div>
        <div className="header-actions">
          <div className="language-toggle" aria-label={t.languageSwitchLabel || "Language switch"}>
            <button
              className={language === "en" ? "active" : ""}
              type="button"
              onClick={() => handleLanguageChange("en")}
            >
              {t.english}
            </button>
            <button
              className={language === "zh" ? "active" : ""}
              type="button"
              onClick={() => handleLanguageChange("zh")}
            >
              {t.chinese}
            </button>
          </div>
          <div className="status-pill">
            {activeTab === "today" || activeTab === "secretary" ? todayDate : plan?.plan_date || t.chatMvp}
          </div>
        </div>
      </header>

      <main className="app-main">
        {activeTab === "secretary" && (
          <ChatSecretary
            language={language}
            plan={plan}
            todayPlan={plansByDate[todayDate] || null}
            todayDate={todayDate}
            onPlanUpdated={handlePlanUpdated}
            t={t}
          />
        )}
        {activeTab === "today" && (
          <TodayView
            plansByDate={plansByDate}
            adjustedPlan={adjustedPlan}
            t={t}
            todayDate={todayDate}
            onDeletePlan={handleDeletePlan}
            onDeleteScheduleItem={handleDeleteScheduleItem}
            onUpdateScheduleItem={handleUpdateScheduleItem}
            onUpdateScheduleItemStatus={handleUpdateScheduleItemStatus}
            actionError={planActionError}
          />
        )}
        {activeTab === "review" && (
          <DailyReview
            plan={plan}
            plansByDate={plansByDate}
            todayDate={todayDate}
            t={t}
            review={review}
            onReviewGenerated={setReview}
            onReviewCompleted={handlePlanReviewed}
          />
        )}
        {activeTab === "manual" && (
          <section className="stack">
            <TaskForm t={t} onPlanGenerated={handlePlanUpdated} onGoToday={() => setActiveTab("today")} />
            <AdjustPlan
              plan={plan}
              t={t}
              onPlanAdjusted={setAdjustedPlan}
              onGoToday={() => setActiveTab("today")}
            />
          </section>
        )}
        {activeTab === "settings" && <SettingsPanel t={t} />}
      </main>

      <BottomNav activeTab={activeTab} onChange={setActiveTab} labels={t.tabs} />
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
registerServiceWorker();
