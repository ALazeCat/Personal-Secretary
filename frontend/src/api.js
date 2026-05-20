const API_BASE =
  import.meta.env.VITE_API_BASE ||
  `${window.location.protocol}//${window.location.hostname}:8000`;

export function getApiBase() {
  return API_BASE;
}

function getLanguage() {
  return localStorage.getItem("secretary-language") === "zh" ? "zh" : "en";
}

function apiErrorText(kind, detail = "") {
  const language = getLanguage();
  const messages = {
    en: {
      timeout: `Request timed out. Open ${API_BASE}/ on this phone to check whether the backend is reachable.`,
      unreachable: `Cannot reach backend at ${API_BASE}. Make sure the backend is running and Windows Firewall allows port 8000.`,
      server: "The server returned an error."
    },
    zh: {
      timeout: `请求超时。请在手机浏览器打开 ${API_BASE}/，确认后端是否能访问。`,
      unreachable: `无法连接后端 ${API_BASE}。请确认电脑上的后端服务已启动，并且 Windows 防火墙允许 8000 端口。`,
      server: "服务器返回了错误。"
    }
  };

  const text = messages[language][kind] || messages.en[kind] || detail;
  return detail ? `${text} ${detail}` : text;
}

async function request(path, options = {}) {
  const controller = new AbortController();
  const timeoutMs = options.timeoutMs || 30000;
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options,
    signal: controller.signal
  }).catch((error) => {
    if (error.name === "AbortError") {
      throw new Error(apiErrorText("timeout"));
    }
    throw new Error(apiErrorText("unreachable"));
  }).finally(() => {
    window.clearTimeout(timeoutId);
  });

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    const detail = data?.detail || apiErrorText("server");
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  return data;
}

export function generatePlan(payload) {
  return request("/api/generate-plan", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function adjustPlan(payload) {
  return request("/api/adjust-plan", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function generateDailyReview(payload) {
  return request("/api/daily-review", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function chatWithSecretary(payload) {
  return request("/api/chat", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getLatestPlan() {
  return request("/api/latest-plan");
}

export function getPlans() {
  return request("/api/plans");
}

export function deletePlan(planDate) {
  return request(`/api/plans/${encodeURIComponent(planDate)}`, {
    method: "DELETE"
  });
}

export function deleteScheduleItem(planDate, itemIndex) {
  return request(`/api/plans/${encodeURIComponent(planDate)}/items/${itemIndex}`, {
    method: "DELETE"
  });
}

export function updateScheduleItem(planDate, itemIndex, payload) {
  return request(`/api/plans/${encodeURIComponent(planDate)}/items/${itemIndex}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function updateScheduleItemStatus(planDate, itemIndex, status, completedDate = null) {
  return request(`/api/plans/${encodeURIComponent(planDate)}/items/${itemIndex}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status, completed_date: completedDate })
  });
}

export function getSettings() {
  return request("/api/settings");
}

export function saveSettings(payload) {
  return request("/api/settings", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function testSettings() {
  return request("/api/settings/test", {
    method: "POST"
  });
}
