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


def generate_nutrition_tip_with_flash(goal: str, intensity: str) -> str:
    prompt = f"""
You are FitBuddy's nutrition and recovery assistant.

Give one concise, practical general wellness tip for a person whose:
- Fitness goal: {goal}
- Workout intensity: {intensity}

Keep it to 2-4 sentences. Mention hydration, balanced food, protein/fiber, or recovery when relevant.
Do not prescribe medication, diagnose illness, or give extreme dieting advice.
""".strip()

    response = _client().models.generate_content(
        model=settings.nutrition_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.5,
            max_output_tokens=250,
        ),
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty nutrition tip.")

    return response.text.strip()
