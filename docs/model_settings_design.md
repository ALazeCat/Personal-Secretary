# Model Settings and Bring Your Own Key

## Goal

The app should be shareable with parents and friends.

That means they should not use the developer's API key. Each user should be able to use their own provider, model, and key.

## Current MVP design

The app now supports a simple "Bring Your Own Key" flow:

```text
Frontend Settings tab
  -> user chooses provider, model, base URL, and API key
  -> backend saves settings locally
  -> planner uses those settings for AI calls
```

## Files

```text
backend/model_settings.py
backend/llm_client.py
backend/data/settings.example.json
frontend/src/components/SettingsPanel.jsx
```

## backend/model_settings.py

This file is responsible for:

- listing supported providers
- reading settings
- saving settings
- masking API keys before sending data back to the frontend

The real saved settings file is:

```text
backend/data/settings.json
```

This file is ignored by Git because it can contain a real API key.

## backend/llm_client.py

This file has one important function:

```python
call_llm(prompt)
```

The rest of the backend does not need to know whether the user chose OpenAI, DeepSeek, Gemini, Qwen, Kimi, or a custom provider.

That keeps the planner code simple.

## Supported providers

The MVP treats these providers as OpenAI-compatible:

- OpenAI / ChatGPT
- DeepSeek
- Gemini
- Qwen / Tongyi Qianwen
- Kimi / Moonshot
- Custom OpenAI-compatible provider

If a provider changes its official endpoint later, the user can edit the Base URL in Settings.

## Security note

This MVP stores keys locally in:

```text
backend/data/settings.json
```

This is acceptable for a local MVP, but it is not enough for a public cloud app.

For a real hosted product, API keys should be encrypted or stored in a secure secret manager.

## Why keys are masked

The backend never sends the full saved key back to the frontend.

It returns a masked value like:

```text
sk-t...3456
```

This helps avoid accidentally showing a full secret on screen.
