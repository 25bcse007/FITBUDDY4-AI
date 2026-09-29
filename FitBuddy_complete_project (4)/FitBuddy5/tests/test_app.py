import os
from pathlib import Path

os.environ["GEMINI_API_KEY"] = "test-key"
os.environ["ADMIN_TOKEN"] = "test-admin"

from fastapi.testclient import TestClient

from app.gemini_flash_generator import generate_nutrition_tip_with_flash
from app.gemini_generator import generate_workout_gemini
from app.main import app


def fake_workout(*args, **kwargs):
    return """Day 1
Focus: Full body
Warm-up: 5 minutes walking
- Squats (3 sets, 10 reps, 60 sec rest)
- Push-ups (3 sets, 8 reps, 60 sec rest)
Cooldown: 5 minutes

Day 2
Focus: Cardio
Warm-up: 5 minutes
- Brisk walk (1, 25 minutes)
Cooldown: 5 minutes

Day 3
Focus: Core
Warm-up: 5 minutes
- Plank (3 sets, 30 sec)
Cooldown: 5 minutes

Day 4
Focus: Recovery
- Gentle stretching (15 minutes)

Day 5
Focus: Lower body
- Lunges (3 sets, 10 reps)
- Glute bridge (3 sets, 12 reps)

Day 6
Focus: Upper body
- Wall push-ups (3 sets, 10 reps)
- Rows (3 sets, 10 reps)

Day 7
Focus: Recovery
- Easy walk and stretching (20 minutes)
"""


def fake_tip(*args, **kwargs):
    return "Stay hydrated and include balanced meals with protein and fiber."


def fake_update(*args, **kwargs):
    return "Updated 7-day plan based on the user's feedback."


app.dependency_overrides = {}

import app.routes as routes

routes.generate_workout_gemini = fake_workout
routes.generate_nutrition_tip_with_flash = fake_tip
routes.update_workout_plan = fake_update


client = TestClient(app)


def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "FitBuddy" in response.text


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_generate_plan():
    response = client.post(
        "/api/generate-workout",
        json={
            "username": "Aisha",
            "user_id": "TEST001",
            "age": 22,
            "weight": 60,
            "goal": "weight loss",
            "intensity": "medium",
        },
    )
    assert response.status_code == 200
    assert response.json()["plan"]["nutrition_tip"]


def test_feedback():
    response = client.post(
        "/api/submit-feedback",
        json={
            "user_id": "TEST001",
            "feedback": "Add more cardio.",
        },
    )
    assert response.status_code == 200
    assert "Updated 7-day plan" in response.json()["updated_plan"]


def test_admin():
    response = client.get("/api/users?token=test-admin")
    assert response.status_code == 200
    assert any(row["user_id"] == "TEST001" for row in response.json())


def test_admin_rejected():
    response = client.get("/api/users?token=wrong")
    assert response.status_code == 403
