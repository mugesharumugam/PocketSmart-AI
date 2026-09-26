"""Shared helpers: templates, the logged-in user, and page rendering."""
from fastapi import Request
from fastapi.templating import Jinja2Templates

from app import models
from app.config import APP_DIR
from app.services.security import decode_access_token

templates = Jinja2Templates(directory=str(APP_DIR / "templates"))


def format_inr(value) -> str:
    """Format a number the Indian way: 150000 -> ₹1,50,000."""
    try:
        n = int(round(float(value)))
    except (TypeError, ValueError):
        return "₹0"
    digits = str(abs(n))
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        digits = ",".join(groups + [tail])
    return ("-" if n < 0 else "") + "₹" + digits


templates.env.filters["inr"] = format_inr


class NotAuthenticated(Exception):
    """Raised when a page needs a logged-in user."""


def get_optional_user(request: Request):
    token = request.cookies.get("access_token")
    payload = decode_access_token(token) if token else None
    if not payload:
        return None
    try:
        return models.get_user_by_id(int(payload["sub"]))
    except (KeyError, ValueError):
        return None


def get_current_user(request: Request):
    user = get_optional_user(request)
    if user is None:
        raise NotAuthenticated()
    return user


def render(request: Request, name: str, user=None, status_code: int = 200, **context):
    context["user"] = user
    return templates.TemplateResponse(request, name, context, status_code=status_code)
