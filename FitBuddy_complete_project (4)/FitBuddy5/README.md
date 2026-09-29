# FitBuddy – AI Fitness Plan Generator using Gemini Models

FitBuddy is a FastAPI + Jinja2 web application based on the supplied project documentation. It collects a user's name, user ID, age, weight, fitness goal, and workout intensity, then uses Gemini to generate a 7-day workout plan and a nutrition/recovery tip. Users can submit feedback to regenerate their plan, and an admin view can inspect stored users and original/updated plans.

## Implemented project structure

```text
FitBuddy/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── routes.py
│   ├── gemini_generator.py
│   ├── gemini_flash_generator.py
│   └── updated_plan.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── result.html
│   ├── feedback.html
│   ├── all_users.html
│   └── error.html
├── static/
│   ├── css/style.css
│   └── js/app.js
├── tests/
│   ├── __init__.py
│   └── test_app.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.11 or newer recommended
- VS Code
- A Gemini API key from Google AI Studio
- Internet access for Gemini requests

The original documentation mentions `google-generativeai`. This implementation uses Google's current `google-genai` Python SDK and the `from google import genai` client pattern.

## 1. Open in VS Code

Extract the project ZIP, then open the `FitBuddy` folder in VS Code:

**File → Open Folder → FitBuddy**

Open the integrated terminal:

**Terminal → New Terminal**

## 2. Create a virtual environment

### Windows PowerShell

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

```cmd
py -3 -m venv .venv
.venv\Scripts\activate.bat
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Configure Gemini

Copy:

```text
.env.example
```

to:

```text
.env
```

Then edit `.env` and add your API key:

```env
GEMINI_API_KEY=YOUR_REAL_GEMINI_API_KEY
```

You can leave the other defaults unchanged for a first run.

The model settings are configurable:

```env
WORKOUT_MODEL=gemini-3.8-flash
NUTRITION_MODEL=gemini-3.8-flash
UPDATE_MODEL=gemini-3.8-flash
```

If your Gemini account has access to another supported model, these values can be changed without editing Python code.

## 5. Run the application

From the project root:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

FastAPI API documentation:

```text
http://127.0.0.1:8000/docs
```

## 6. Test the application manually

### Generate a plan

On the home page enter, for example:

- Name: Aisha
- User ID: FB001
- Age: 22
- Weight: 60
- Goal: Weight loss
- Intensity: Medium

Click **Generate Plan**.

The application will:
1. Validate the form.
2. Call Gemini for a structured 7-day workout.
3. Call Gemini for a nutrition/recovery tip.
4. Save the user and plan in SQLite.
5. Render the result page.

### Submit feedback

From the result page, enter feedback such as:

```text
Add more cardio and include one additional rest day.
```

The application sends the original plan plus feedback to Gemini and stores the revised plan separately.

### Admin page

The admin page is protected by `ADMIN_TOKEN`.

Default development token in `.env.example`:

```text
change-me
```

Open:

```text
http://127.0.0.1:8000/view-all-users?token=change-me
```

Change this token before using the application outside a local development environment.

## 7. Run automated tests

The test suite does not call Gemini. AI calls are mocked so tests are fast and do not consume API quota.

```bash
pytest -q
```

## API endpoints

### `GET /health`

Health check.

### `POST /api/generate-workout`

JSON example:

```json
{
  "username": "Aisha",
  "user_id": "FB001",
  "age": 22,
  "weight": 60,
  "goal": "weight loss",
  "intensity": "medium"
}
```

### `POST /api/submit-feedback`

JSON example:

```json
{
  "user_id": "FB001",
  "feedback": "Add more cardio and one rest day."
}
```

### `GET /api/users?token=change-me`

Returns stored users and plans when the correct admin token is supplied.

## SQLite database

The application automatically creates:

```text
fitbuddy.db
```

in the project root on first startup.

No manual database setup is required.

## Important safety note

FitBuddy generates general fitness and nutrition suggestions. It is not a medical diagnosis or a substitute for a qualified healthcare or fitness professional. The UI includes this disclaimer.

## Troubleshooting

### `ModuleNotFoundError`

Make sure the virtual environment is activated and run:

```bash
pip install -r requirements.txt
```

### `GEMINI_API_KEY is missing`

Check that `.env` exists in the project root and contains:

```env
GEMINI_API_KEY=...
```

Then restart Uvicorn.

### Gemini request errors

Check:
- API key is valid.
- The selected model is available to your account.
- Internet access is working.
- You have not exceeded API limits.

You can change model names in `.env` without changing application code.

### Port already in use

Run:

```bash
uvicorn app.main:app --reload --port 8001
```

Then visit:

```text
http://127.0.0.1:8001
```
