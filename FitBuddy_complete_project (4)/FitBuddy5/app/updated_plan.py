import json
import re

from google import genai
from google.genai import types

from .config import get_settings

settings = get_settings()


def _client() -> genai.Client:
    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. Add it to the .env file."
        )
    return genai.Client(api_key=settings.gemini_api_key)


def _clean_response(text: str) -> str:
    text = text.strip()
    # Remove accidental markdown fences while keeping the actual plan.
    text = re.sub(r"^```(?:text|markdown)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    try:
        parsed = json.loads(text)
        return json.dumps(parsed, indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        return text


def update_workout_plan(original_plan: str, feedback: str) -> str:
    prompt = f"""
You are FitBuddy's workout-plan revision assistant.

Original 7-day workout plan:
---BEGIN PLAN---
{original_plan}
---END PLAN---

User feedback:
---BEGIN FEEDBACK---
{feedback}
---END FEEDBACK---

Revise the plan according to the feedback while preserving a clear 7-day structure.
Return a complete revised plan, not just a list of changes.
Keep the plan practical and general. Do not diagnose or treat medical conditions.
Include warm-up, exercises with sets/reps or duration, and cooldown/recovery guidance where appropriate.
""".strip()

    response = _client().models.generate_content(
        model=settings.update_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.6,
            max_output_tokens=5000,
        ),
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty updated plan.")

    return _clean_response(response.text)
