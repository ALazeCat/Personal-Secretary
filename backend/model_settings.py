import json
from pathlib import Path

from config import OPENAI_API_KEY, OPENAI_MODEL


DATA_DIR = Path(__file__).parent / "data"
SETTINGS_FILE = DATA_DIR / "settings.json"


PROVIDER_OPTIONS = {
    "openai": {
        "id": "openai",
        "name": "OpenAI / ChatGPT",
        "default_model": "gpt-4o-mini",
        "default_base_url": None,
        "openai_compatible": True,
    },
    "deepseek": {
        "id": "deepseek",
        "name": "DeepSeek",
        "default_model": "deepseek-chat",
        "default_base_url": "https://api.deepseek.com",
        "openai_compatible": True,
    },
    "gemini": {
        "id": "gemini",
        "name": "Gemini",
        "default_model": "gemini-2.0-flash",
        "default_base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "openai_compatible": True,
    },
    "kimi": {
        "id": "kimi",
        "name": "Kimi / Moonshot",
        "default_model": "moonshot-v1-8k",
        "default_base_url": "https://api.moonshot.cn/v1",
        "openai_compatible": True,
    },
    "qwen": {
        "id": "qwen",
        "name": "Qwen / Tongyi Qianwen",
        "default_model": "qwen3.6-plus",
        "default_base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        "openai_compatible": True,
    },
    "custom": {
        "id": "custom",
        "name": "Custom OpenAI-compatible",
        "default_model": "",
        "default_base_url": "",
        "openai_compatible": True,
    },
}


def _default_settings():
    return {
        "provider": "openai",
        "model": OPENAI_MODEL or PROVIDER_OPTIONS["openai"]["default_model"],
        "api_key": "",
        "base_url": None,
    }


def _ensure_settings_file():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SETTINGS_FILE.exists():
        _write_settings(_default_settings())


def _write_settings(settings):
    SETTINGS_FILE.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")


def _mask_api_key(api_key):
    if not api_key:
        return None
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return f"{api_key[:4]}...{api_key[-4:]}"


def get_available_providers():
    return list(PROVIDER_OPTIONS.values())


def get_model_settings():
    _ensure_settings_file()
    try:
        settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        settings = _default_settings()

    defaults = _default_settings()
    for key, value in defaults.items():
        settings.setdefault(key, value)

    provider = settings.get("provider")
    if provider not in PROVIDER_OPTIONS:
        settings["provider"] = "openai"
    return settings


def get_effective_model_settings():
    settings = get_model_settings()
    provider = settings["provider"]
    provider_config = PROVIDER_OPTIONS[provider]
    api_key = settings.get("api_key") or (OPENAI_API_KEY if provider == "openai" else "")
    model = settings.get("model") or provider_config["default_model"]
    base_url = settings.get("base_url")
    if base_url is None:
        base_url = provider_config["default_base_url"]

    return {
        "provider": provider,
        "model": model,
        "api_key": api_key,
        "base_url": base_url,
        "using_env_fallback": bool(provider == "openai" and not settings.get("api_key") and OPENAI_API_KEY),
    }


def get_public_model_settings():
    settings = get_model_settings()
    effective = get_effective_model_settings()
    stored_key = settings.get("api_key", "")
    return {
        "provider": effective["provider"],
        "model": effective["model"],
        "base_url": effective["base_url"],
        "api_key_set": bool(stored_key or effective["using_env_fallback"]),
        "masked_api_key": _mask_api_key(stored_key) or ("from .env" if effective["using_env_fallback"] else None),
        "using_env_fallback": effective["using_env_fallback"],
        "available_providers": get_available_providers(),
    }


def save_model_settings(payload):
    current = get_model_settings()
    provider = payload.provider if payload.provider in PROVIDER_OPTIONS else "custom"
    provider_config = PROVIDER_OPTIONS[provider]
    api_key = payload.api_key if payload.api_key is not None else current.get("api_key", "")

    settings = {
        "provider": provider,
        "model": payload.model or provider_config["default_model"],
        "api_key": api_key.strip(),
        "base_url": payload.base_url if payload.base_url is not None else provider_config["default_base_url"],
    }
    _write_settings(settings)
    return get_public_model_settings()
