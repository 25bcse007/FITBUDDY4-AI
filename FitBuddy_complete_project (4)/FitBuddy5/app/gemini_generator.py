import json
import re
from typing import Any

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


def _extract_json(text: str) -> Any:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def _format_plan(data: Any) -> str:
    if not isinstance(data, dict):
        return str(data)

    lines: list[str] = []
    days = data.get("days", data)

    if isinstance(days, dict):
        for day, details in days.items():
            lines.append(str(day))
            if isinstance(details, dict):
                focus = details.get("focus")
                if focus:
                    lines.append(f"Focus: {focus}")

                warmup = details.get("warm_up") or details.get("warmup")
                if warmup:
                    lines.append(f"Warm-up: {warmup}")

                exercises = details.get("exercises", [])
                if isinstance(exercises, list):
                    for exercise in exercises:
                        if isinstance(exercise, dict):
                            name = exercise.get("name", "Exercise")
                            sets = exercise.get("sets")
                            reps = exercise.get("reps")
                            duration = exercise.get("duration")
                            rest = exercise.get("rest")
                            detail = " | ".join(
                                str(x) for x in [
                                    f"sets: {sets}" if sets else "",
                                    f"reps: {reps}" if reps else "",
                                    f"duration: {duration}" if duration else "",
                                    f"rest: {rest}" if rest else "",
                                ] if x
                            )
                            lines.append(f"- {name}" + (f" ({detail})" if detail else ""))
                        else:
                            lines.append(f"- {exercise}")

                cooldown = details.get("cooldown") or details.get("recovery")
                if cooldown:
                    lines.append(f"Cooldown/Recovery: {cooldown}")
            else:
                lines.append(str(details))
            lines.append("")
        return "\n".join(lines).strip()

    return json.dumps(data, indent=2, ensure_ascii=False)


def generate_workout_gemini(
    username: str,
    age: int,
    weight: float,
    goal: str,
    intensity: str,
) -> str:
    prompt = f"""
You are FitBuddy, a fitness-plan generation assistant.

Create a practical, beginner-friendly 7-day general fitness plan for:
Name: {username}
Age: {age}
Weight (kg): {weight}
Goal: {goal}
Preferred intensity: {intensity}

Requirements:
- Exactly 7 days.
- Each day must have a focus.
- Include warm-up, main exercises, and cooldown/recovery guidance.
- Exercises should include sets/repetitions or duration and rest where appropriate.
- Match the requested goal and intensity.
- Avoid claiming medical treatment or diagnosis.
- Include a short safety note telling the user to stop if they experience pain or concerning symptoms.
- Return JSON only in this shape:
{{
  "days": {{
    "Day 1": {{
      "focus": "...",
      "warm_up": "...",
      "exercises": [
        {{"name": "...", "sets": 3, "reps": "8-12", "duration": "", "rest": "60 sec"}}
      ],
      "cooldown": "..."
    }}
  }}
}}
""".strip()

    response = _client().models.generate_content(
        model=settings.workout_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.6,
            max_output_tokens=5000,
            response_mime_type="application/json",
        ),
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty workout plan.")

    try:
        return _format_plan(_extract_json(response.text))
    except (json.JSONDecodeError, ValueError):
        return response.text.strip()
