from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db
from .gemini_flash_generator import generate_nutrition_tip_with_flash
from .gemini_generator import generate_workout_gemini
from .models import Plan, User, utc_now
from .schemas import FeedbackRequest, UserInput
from .updated_plan import update_workout_plan

settings = get_settings()
router = APIRouter()
templates = Jinja2Templates(directory="templates")


def _get_user(db: Session, user_id: str) -> User | None:
    return db.scalar(select(User).where(User.user_id == user_id))


def _get_latest_plan(db: Session, user_id: str) -> Plan | None:
    return db.scalars(
        select(Plan)
        .where(Plan.user_id == user_id)
        .order_by(Plan.id.desc())
    ).first()


def _verify_admin(token: str) -> None:
    if token != settings.admin_token:
        raise HTTPException(status_code=403, detail="Invalid admin token.")


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "FitBuddy – AI Fitness Plan Generator",
            "min_age": settings.min_age,
            "max_age": settings.max_age,
            "min_weight": settings.min_weight_kg,
            "max_weight": settings.max_weight_kg,
        },
    )


@router.post("/generate-workout", response_class=HTMLResponse)
def generate_workout(
    request: Request,
    username: str = Form(...),
    user_id: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        user_input = UserInput(
            username=username,
            user_id=user_id,
            age=age,
            weight=weight,
            goal=goal,
            intensity=intensity.lower(),
        )

        workout_plan = generate_workout_gemini(
            user_input.username,
            user_input.age,
            user_input.weight,
            user_input.goal,
            user_input.intensity,
        )
        nutrition_tip = generate_nutrition_tip_with_flash(
            user_input.goal,
            user_input.intensity,
        )

        user = _get_user(db, user_input.user_id)
        if user is None:
            user = User(
                user_id=user_input.user_id,
                username=user_input.username,
                age=user_input.age,
                weight=user_input.weight,
                goal=user_input.goal,
                intensity=user_input.intensity,
            )
            db.add(user)
        else:
            user.username = user_input.username
            user.age = user_input.age
            user.weight = user_input.weight
            user.goal = user_input.goal
            user.intensity = user_input.intensity

        plan = _get_latest_plan(db, user_input.user_id)
        if plan is None:
            plan = Plan(
                user_id=user_input.user_id,
                original_plan=workout_plan,
                nutrition_tip=nutrition_tip,
            )
            db.add(plan)
        else:
            # A fresh generation replaces the current original baseline.
            plan.original_plan = workout_plan
            plan.updated_plan = None
            plan.feedback = None
            plan.nutrition_tip = nutrition_tip
            plan.updated_at = utc_now()

        db.commit()

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "title": "Your FitBuddy Plan",
                "user": user,
                "plan": plan,
                "display_plan": plan.updated_plan or plan.original_plan,
                "error": None,
            },
        )
    except ValueError as exc:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"title": "Validation Error", "message": str(exc)},
            status_code=422,
        )
    except Exception as exc:
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={
                "title": "Could not generate plan",
                "message": str(exc),
            },
            status_code=500,
        )


@router.get("/feedback", response_class=HTMLResponse)
def feedback_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="feedback.html",
        context={"title": "Update Your Plan"},
    )


@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback(
    request: Request,
    user_id: str = Form(...),
    feedback: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        data = FeedbackRequest(user_id=user_id, feedback=feedback)
        user = _get_user(db, data.user_id)
        plan = _get_latest_plan(db, data.user_id)

        if user is None or plan is None:
            raise HTTPException(
                status_code=404,
                detail="No stored plan was found for this User ID.",
            )

        revised_plan = update_workout_plan(plan.original_plan, data.feedback)
        plan.updated_plan = revised_plan
        plan.feedback = data.feedback
        plan.updated_at = utc_now()
        db.commit()

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "title": "Updated FitBuddy Plan",
                "user": user,
                "plan": plan,
                "display_plan": plan.updated_plan,
                "error": None,
                "updated": True,
            },
        )
    except HTTPException as exc:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"title": "Feedback Error", "message": exc.detail},
            status_code=exc.status_code,
        )
    except Exception as exc:
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"title": "Could not update plan", "message": str(exc)},
            status_code=500,
        )


@router.get("/view-all-users", response_class=HTMLResponse)
def view_all_users(
    request: Request,
    token: str = Query(default=""),
    db: Session = Depends(get_db),
):
    _verify_admin(token)
    users = db.scalars(select(User).order_by(User.id.desc())).all()
    plans = db.scalars(select(Plan).order_by(Plan.id.desc())).all()
    plans_by_user: dict[str, Plan] = {}
    for plan in plans:
        plans_by_user.setdefault(plan.user_id, plan)

    return templates.TemplateResponse(
        request=request,
        name="all_users.html",
        context={
            "title": "FitBuddy Admin Dashboard",
            "users": users,
            "plans_by_user": plans_by_user,
        },
    )


@router.get("/health")
def health():
    return {"status": "ok", "service": "FitBuddy"}


@router.post("/api/generate-workout")
def api_generate_workout(
    payload: UserInput,
    db: Session = Depends(get_db),
):
    workout_plan = generate_workout_gemini(
        payload.username,
        payload.age,
        payload.weight,
        payload.goal,
        payload.intensity,
    )
    nutrition_tip = generate_nutrition_tip_with_flash(
        payload.goal,
        payload.intensity,
    )

    user = _get_user(db, payload.user_id)
    if user is None:
        user = User(
            user_id=payload.user_id,
            username=payload.username,
            age=payload.age,
            weight=payload.weight,
            goal=payload.goal,
            intensity=payload.intensity,
        )
        db.add(user)
    else:
        user.username = payload.username
        user.age = payload.age
        user.weight = payload.weight
        user.goal = payload.goal
        user.intensity = payload.intensity

    plan = _get_latest_plan(db, payload.user_id)
    if plan is None:
        plan = Plan(
            user_id=payload.user_id,
            original_plan=workout_plan,
            nutrition_tip=nutrition_tip,
        )
        db.add(plan)
    else:
        plan.original_plan = workout_plan
        plan.updated_plan = None
        plan.feedback = None
        plan.nutrition_tip = nutrition_tip
        plan.updated_at = utc_now()

    db.commit()
    db.refresh(plan)

    return {
        "user": payload.model_dump(),
        "plan": {
            "id": plan.id,
            "original_plan": plan.original_plan,
            "updated_plan": plan.updated_plan,
            "nutrition_tip": plan.nutrition_tip,
        },
    }


@router.post("/api/submit-feedback")
def api_submit_feedback(
    payload: FeedbackRequest,
    db: Session = Depends(get_db),
):
    user = _get_user(db, payload.user_id)
    plan = _get_latest_plan(db, payload.user_id)

    if user is None or plan is None:
        raise HTTPException(status_code=404, detail="User or plan not found.")

    revised_plan = update_workout_plan(plan.original_plan, payload.feedback)
    plan.updated_plan = revised_plan
    plan.feedback = payload.feedback
    plan.updated_at = utc_now()
    db.commit()
    db.refresh(plan)

    return {
        "user_id": payload.user_id,
        "feedback": payload.feedback,
        "updated_plan": plan.updated_plan,
        "nutrition_tip": plan.nutrition_tip,
    }


@router.get("/api/users")
def api_users(
    token: str = Query(default=""),
    db: Session = Depends(get_db),
):
    _verify_admin(token)
    users = db.scalars(select(User).order_by(User.id.desc())).all()
    result = []

    for user in users:
        plan = _get_latest_plan(db, user.user_id)
        result.append(
            {
                "user_id": user.user_id,
                "username": user.username,
                "age": user.age,
                "weight": user.weight,
                "goal": user.goal,
                "intensity": user.intensity,
                "original_plan": plan.original_plan if plan else None,
                "updated_plan": plan.updated_plan if plan else None,
                "feedback": plan.feedback if plan else None,
                "nutrition_tip": plan.nutrition_tip if plan else None,
            }
        )

    return JSONResponse(result)
