"""Landing page, dashboard and history."""
from fastapi import APIRouter, Depends, HTTPException, Request

from app import models
from app.deps import get_current_user, get_optional_user, render
from app.services.planners import PLANNERS

router = APIRouter()


@router.get("/")
def index(request: Request):
    return render(request, "index.html", user=get_optional_user(request), planners=PLANNERS)


@router.get("/dashboard")
def dashboard(request: Request, user=Depends(get_current_user)):
    recent = models.list_history(user["id"], limit=3)
    return render(request, "dashboard.html", user=user, planners=PLANNERS, recent=recent)


@router.get("/history")
def history(request: Request, user=Depends(get_current_user)):
    return render(request, "history.html", user=user, planners=PLANNERS,
                  entries=models.list_history(user["id"]))


@router.get("/history/{history_id}")
def history_detail(request: Request, history_id: int, user=Depends(get_current_user)):
    entry = models.get_history(user["id"], history_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return render(request, "history_detail.html", user=user, entry=entry,
                  planner=PLANNERS.get(entry["planner"]))
