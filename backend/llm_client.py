from openai import OpenAI

from model_settings import get_effective_model_settings


def call_llm(prompt: str, json_mode: bool = False):
    settings = get_effective_model_settings()
    api_key = settings["api_key"]
    if not api_key:
        return (
            None,
            "API key is missing. Open Settings and add your own key, or configure backend/.env for OpenAI.",
        )

    try:
        client_kwargs = {"api_key": api_key}
        if settings.get("base_url"):
            client_kwargs["base_url"] = settings["base_url"]

        client = OpenAI(**client_kwargs)
        request_kwargs = {
            "model": settings["model"],
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful AI secretary. Prefer valid JSON when the prompt asks for it.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        }
        if json_mode:
            request_kwargs["response_format"] = {"type": "json_object"}

        try:
            response = client.chat.completions.create(**request_kwargs)
        except Exception:
            if not json_mode:
                raise
            request_kwargs.pop("response_format", None)
            response = client.chat.completions.create(**request_kwargs)
        return response.choices[0].message.content or "", None
    except Exception as exc:
        return None, f"AI request failed with {settings['provider']} / {settings['model']}: {exc}"


def test_llm_connection():
    settings = get_effective_model_settings()
    content, error = call_llm('Return exactly this JSON: {"ok": true}', json_mode=True)
    return {
        "ok": error is None and bool(content),
        "provider": settings["provider"],
        "model": settings["model"],
        "message": "Connection test succeeded." if error is None else error,
    }
