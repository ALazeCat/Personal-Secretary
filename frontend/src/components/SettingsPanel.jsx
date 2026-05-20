import { useEffect, useState } from "react";

import { getApiBase, getSettings, saveSettings, testSettings } from "../api.js";

const fallbackProviderOptions = [
  {
    id: "openai",
    name: "OpenAI / ChatGPT",
    default_model: "gpt-4o-mini",
    default_base_url: ""
  },
  {
    id: "deepseek",
    name: "DeepSeek",
    default_model: "deepseek-chat",
    default_base_url: "https://api.deepseek.com"
  },
  {
    id: "gemini",
    name: "Gemini",
    default_model: "gemini-2.0-flash",
    default_base_url: "https://generativelanguage.googleapis.com/v1beta/openai/"
  },
  {
    id: "kimi",
    name: "Kimi / Moonshot",
    default_model: "moonshot-v1-8k",
    default_base_url: "https://api.moonshot.cn/v1"
  },
  {
    id: "qwen",
    name: "Qwen / Tongyi Qianwen",
    default_model: "qwen3.6-plus",
    default_base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  },
  {
    id: "custom",
    name: "Custom OpenAI-compatible",
    default_model: "",
    default_base_url: ""
  }
];

export default function SettingsPanel({ t }) {
  const [settings, setSettings] = useState(null);
  const [provider, setProvider] = useState("openai");
  const [model, setModel] = useState("gpt-4o-mini");
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState("");
  const [testMessage, setTestMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadSettings() {
      try {
        const result = await getSettings();
        setSettings(result);
        setProvider(result.provider);
        setModel(result.model || "");
        setBaseUrl(result.base_url || "");
      } catch (err) {
        setError(err.message);
      }
    }

    loadSettings();
  }, []);

  const providerOptions = settings?.available_providers?.length
    ? settings.available_providers
    : fallbackProviderOptions;

  function handleProviderChange(nextProvider) {
    setProvider(nextProvider);
    const option = providerOptions.find((item) => item.id === nextProvider);
    if (option) {
      setModel(option.default_model || "");
      setBaseUrl(option.default_base_url || "");
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setMessage("");
    setTestMessage("");
    setError("");

    try {
      const result = await saveSettings({
        provider,
        model,
        api_key: apiKey || null,
        base_url: baseUrl || null
      });
      setSettings(result);
      setApiKey("");
      setMessage(t.settings.saved);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveAndTest() {
    setLoading(true);
    setTesting(true);
    setMessage("");
    setTestMessage("");
    setError("");

    try {
      const saved = await saveSettings({
        provider,
        model,
        api_key: apiKey || null,
        base_url: baseUrl || null
      });
      setSettings(saved);
      setApiKey("");

      const test = await testSettings();
      if (test.ok) {
        setTestMessage(`${t.settings.connected}: ${test.provider} / ${test.model}`);
      } else {
        setError(test.message || t.settings.testFailed);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setTesting(false);
    }
  }

  return (
    <form className="card form-card" onSubmit={handleSubmit}>
      <h2>{t.settings.title}</h2>
      <p className="helper-text">{t.settings.backend}: {getApiBase()}</p>

      <div className="field-group">
        <span className="field-label">{t.settings.provider}</span>
        <div className="provider-grid" role="radiogroup" aria-label={t.settings.provider}>
          {providerOptions.map((option) => {
            const providerName = option.id === "custom" ? t.settings.customProviderName : option.name;
            return (
              <button
                className={provider === option.id ? "provider-option active" : "provider-option"}
                key={option.id}
                type="button"
                role="radio"
                aria-checked={provider === option.id}
                onClick={() => handleProviderChange(option.id)}
              >
                <span>{providerName}</span>
                <small>{option.default_model || t.settings.customModel}</small>
              </button>
            );
          })}
        </div>
      </div>

      <label>
        {t.settings.model}
        <input value={model} onChange={(event) => setModel(event.target.value)} placeholder="gpt-4o-mini" />
      </label>

      <label>
        {t.settings.apiKey}
        <input
          autoComplete="off"
          type="password"
          value={apiKey}
          onChange={(event) => setApiKey(event.target.value)}
          placeholder={settings?.masked_api_key || "sk-..."}
        />
      </label>
      <p className="helper-text">
        {t.settings.keyHelp}
        {settings?.api_key_set && (
          <>
            {" "}
            {t.settings.keyStatus}: {settings.masked_api_key}
          </>
        )}
      </p>

      <label>
        {t.settings.baseUrl}
        <input
          value={baseUrl}
          onChange={(event) => setBaseUrl(event.target.value)}
          placeholder="https://api.example.com/v1"
        />
      </label>
      <p className="helper-text">{t.settings.baseUrlHelp}</p>

      {message && <p className="success-box">{message}</p>}
      {testMessage && <p className="success-box">{testMessage}</p>}
      {error && <p className="error-box">{error}</p>}

      <button className="primary-button" type="button" disabled={loading} onClick={handleSaveAndTest}>
        {testing ? t.settings.testing : t.settings.saveAndTest}
      </button>
      <button className="ghost-button full-width-button" type="submit" disabled={loading}>
        {loading ? t.settings.saving : t.settings.save}
      </button>
    </form>
  );
}
