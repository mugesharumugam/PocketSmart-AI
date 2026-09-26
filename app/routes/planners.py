"""The three planner pages: show the form, call Gemini, save and show the result."""
from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from app import models
from app.deps import get_current_user, render
from app.services.gemini_service import GeminiError, generate_recommendations
from app.services.planners import PLANNERS

router = APIRouter()
MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGES = {"image/jpeg", "image/png", "image/webp"}


def _get_planner(key: str) -> dict:
    if key not in PLANNERS:
        raise HTTPException(status_code=404, detail="Planner not found")
    return PLANNERS[key]


@router.get("/planner/{key}")
def planner_page(request: Request, key: str, user=Depends(get_current_user)):
    planner = _get_planner(key)
    return render(request, "planner.html", user=user, key=key, planner=planner, form={})


@router.post("/planner/{key}")
async def planner_submit(request: Request, key: str, user=Depends(get_current_user)):
    planner = _get_planner(key)
    data = await request.form()
    form = {
        "budget": str(data.get("budget", "")).strip(),
        "requirements": str(data.get("requirements", "")).strip(),
        "preferences": str(data.get("preferences", "")).strip(),
    }
    for field in planner["extra"]:
        form[field["name"]] = str(data.get(field["name"], "")).strip()

    try:
        budget = float(form["budget"].replace(",", ""))
    except ValueError:
        budget = 0.0

    error = None
    image_bytes = image_mime = None
    upload = data.get("image")
    if budget < 500:
        error = "Enter a total budget of at least ₹500."
    elif not form["requirements"]:
        error = "Tell us what you need so we can plan it."
    elif len(form["requirements"]) > 1500 or len(form["preferences"]) > 1000:
        error = "Your text is too long. Shorten the requirements or preferences and try again."
    elif planner["allow_image"] and upload is not None and getattr(upload, "filename", ""):
        if upload.content_type not in ALLOWED_IMAGES:
            error = "Upload a JPG, PNG or WebP image."
        else:
            image_bytes = await upload.read()
            image_mime = upload.content_type
            if len(image_bytes) > MAX_IMAGE_BYTES:
                error = "The image is larger than 5 MB. Upload a smaller one."

    page = dict(user=user, key=key, planner=planner, form=form)
    if error:
        return render(request, "planner.html", status_code=400, error=error, **page)

    try:
        result = await run_in_threadpool(
            generate_recommendations, key, budget, form, image_bytes, image_mime
        )
    except GeminiError as exc:
        return render(request, "planner.html", status_code=502, error=str(exc), **page)

    models.save_history(
        user["id"], key, budget, {**form, "had_image": bool(image_bytes)}, result
    )
    return render(request, "planner.html", result=result, **page)
