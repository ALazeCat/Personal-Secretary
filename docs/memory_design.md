# Memory Mechanism Design

## Goal

The AI secretary should not feel like a blank chatbot every time.

It should remember:

- The latest conversation.
- The current plan.
- Older important context in a shorter summary.

## Two-layer memory

The project uses two memory layers.

## 1. Short-term memory

Short-term memory stores recent messages in full.

Example:

```json
{
  "role": "user",
  "content": "I have an exam at 13:00 today."
}
```

This helps the AI understand the current conversation.

## 2. Summary memory

When recent messages become too many, older messages are compressed into a summary.

Example:

```text
The user is preparing for graduate school. They often study Linux and IELTS.
They prefer realistic plans with breaks. Today they have an exam from 13:00 to 15:00.
```

This helps the AI keep useful long-term context without sending every old message again.

## Memory file

Memory is stored in:

```text
backend/data/memory.json
```

It has three sections:

```json
{
  "profile_memory": {},
  "working_memory": {},
  "summary_memory": {}
}
```

## profile_memory

Stores stable preferences:

- preferred language
- wake-up time
- sleep time
- planning style

## working_memory

Stores active state:

- current plan
- plans grouped by date
- recent full messages

`current_plan` is kept for compatibility, but the better long-term structure is:

```json
{
  "plans_by_date": {
    "2026-05-20": {
      "status": "planned",
      "plan_text": "...",
      "schedule": []
    }
  }
}
```

This lets the app distinguish:

- today's plan
- future plans
- past plans that need review
- reviewed plans

For the MVP, the main statuses are:

```text
planned
reviewed
```

Future plans stay `planned`. After the user creates a daily review for a date, that date becomes `reviewed`.

## Deleting a plan

The user can delete a plan by date.

Backend endpoint:

```text
DELETE /api/plans/{plan_date}
```

Example:

```text
DELETE /api/plans/2026-05-20
```

This removes the plan from `plans_by_date`.

If the deleted plan is also `current_plan`, the backend chooses the most recently updated remaining plan as the new `current_plan`. If no plans remain, `current_plan` becomes `null`.

## summary_memory

Stores compressed older conversation:

- summary
- updated_at

## Chat flow

```text
User sends message
  -> backend loads memory
  -> memory is passed into the AI prompt
  -> AI returns reply and updated plan
  -> backend saves user message, assistant reply, and latest plan
  -> if recent messages are too many, older messages are summarized
```

## Why JSON keys stay English

Even when the user chooses Chinese, the code still needs stable field names:

```json
{
  "reply": "好的，我已经记录你的考试。",
  "schedule": []
}
```

The visible text can change language, but the code keys should stay stable.
