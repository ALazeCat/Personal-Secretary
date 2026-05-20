# Chat-First AI Secretary Design

## Why this change exists

The first version used forms. That is useful for testing, but it does not feel like a real secretary.

The new direction is chat-first:

1. The user speaks naturally.
2. The backend asks the AI to extract tasks, events, dates, and times.
3. The AI returns both a friendly reply and structured JSON.
4. The frontend shows the conversation and updates the schedule automatically.

## Important idea

The app now separates two things:

- Human experience: a normal conversation.
- Machine data: structured tasks, events, and schedule items.

This is why `/api/chat` returns both `reply` and `schedule`.

## Backend flow

```text
React chat UI
  -> POST /api/chat
  -> ChatRequest schema validates input
  -> build_chat_secretary_prompt creates AI instructions
  -> OpenAI API returns JSON
  -> planner.py parses and cleans JSON
  -> ChatResponse returns reply + extracted items + schedule
  -> memory.py saves the current plan and recent conversation
```

## Frontend flow

```text
User types one natural message
  -> ChatSecretary sends it to /api/chat
  -> assistant reply is added to the chat
  -> extracted items are shown as small labels
  -> current plan state is updated
  -> ScheduleView displays the new plan
```

## Example

User:

```text
I have an exam at 13:00 today. It may take two hours. I also need to study Linux for one hour.
```

AI should extract:

```json
[
  {
    "kind": "fixed_event",
    "title": "Exam",
    "date": "2026-05-19",
    "start": "13:00",
    "end": "15:00"
  },
  {
    "kind": "task",
    "title": "Study Linux",
    "estimated_minutes": 60
  }
]
```

Then it should return a schedule that includes every planned block.

## Schedule repair

LLM output is useful, but it is not always perfectly structured.

Sometimes the AI may write this in `plan_text`:

```text
09:00-10:00 Study Linux
10:00-10:15 Break
13:00-15:00 Exam
```

But only return this in `schedule`:

```json
[
  {
    "start": "13:00",
    "end": "15:00",
    "activity": "Exam"
  }
]
```

The backend now repairs this by parsing clear time-block lines from `plan_text`.

Only simple lines like these are repaired:

```text
09:00-10:00 Study Linux
09:00 - 10:00 Study Linux
09:00 to 10:00 Study Linux
```

This keeps the repair conservative. The app should improve obvious missing structure, but it should not invent schedule items from vague text.
