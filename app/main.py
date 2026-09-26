"""PocketSmart AI: app entry point. Connects the routes, CORS and static files."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from app import models
from app.config import APP_DIR, settings
from app.deps import NotAuthenticated, get_optional_user, render
from app.routes import auth, pages, planners


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.init_db()
    yield


app = FastAPI(title="PocketSmart AI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")

app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(planners.router)


@app.exception_handler(NotAuthenticated)
async def redirect_to_login(request: Request, exc: NotAuthenticated):
    return RedirectResponse("/login", status_code=303)


@app.exception_handler(HTTPException)
async def http_error_page(request: Request, exc: HTTPException):
    return render(
        request, "error.html", user=get_optional_user(request),
        status_code=exc.status_code, code=exc.status_code, message=exc.detail,
    )


@app.get("/health")
def health():
    return {"status": "ok"}
