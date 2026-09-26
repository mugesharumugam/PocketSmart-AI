"""Register, log in and log out."""
import re

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app import models
from app.config import settings
from app.deps import get_optional_user, render
from app.services.security import create_access_token, hash_password, verify_password

router = APIRouter()
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _logged_in_redirect(user) -> RedirectResponse:
    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie(
        "access_token",
        create_access_token(user["id"], user["username"]),
        httponly=True,
        samesite="lax",
        max_age=settings.TOKEN_EXPIRE_MINUTES * 60,
    )
    return response


@router.get("/register")
def register_page(request: Request):
    if get_optional_user(request):
        return RedirectResponse("/dashboard", status_code=303)
    return render(request, "register.html", form={})


@router.post("/register")
def register_submit(
    request: Request,
    username: str = Form(""),
    email: str = Form(""),
    password: str = Form(""),
    confirm: str = Form(""),
):
    username, email = username.strip(), email.strip().lower()
    error = None
    if not USERNAME_RE.match(username):
        error = "Username must be 3 to 30 characters: letters, numbers or underscores."
    elif not EMAIL_RE.match(email):
        error = "Enter a valid email address."
    elif len(password) < 6:
        error = "Password must be at least 6 characters."
    elif password != confirm:
        error = "The two passwords do not match."
    else:
        error = models.username_or_email_taken(username, email)
    if error:
        return render(
            request, "register.html", status_code=400, error=error,
            form={"username": username, "email": email},
        )
    user_id = models.create_user(username, email, hash_password(password))
    return _logged_in_redirect(models.get_user_by_id(user_id))


@router.get("/login")
def login_page(request: Request):
    if get_optional_user(request):
        return RedirectResponse("/dashboard", status_code=303)
    return render(request, "login.html", form={})


@router.post("/login")
def login_submit(request: Request, login: str = Form(""), password: str = Form("")):
    login = login.strip()
    user = models.get_user_by_login(login) if login else None
    if not user or not verify_password(password, user["password_hash"]):
        return render(
            request, "login.html", status_code=400,
            error="Username or password is incorrect.", form={"login": login},
        )
    return _logged_in_redirect(user)


@router.post("/logout")
def logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("access_token")
    return response
