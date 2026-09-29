from pathlib import Path

required = [
    "app/main.py", "app/routes.py", "app/database.py", "app/models.py",
    "app/schemas.py", "app/gemini_generator.py",
    "app/gemini_flash_generator.py", "app/updated_plan.py",
    "templates/index.html", "templates/result.html",
    "templates/feedback.html", "templates/all_users.html",
    "static/css/style.css", "requirements.txt", ".env.example",
    "tests/test_app.py", "README.md",
]

missing = [p for p in required if not Path(p).exists()]
if missing:
    raise SystemExit("Missing files:\n" + "\n".join(missing))

print(f"FitBuddy project structure OK: {len(required)} required files found.")
