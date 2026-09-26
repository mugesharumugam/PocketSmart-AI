"""Talks to Gemini and turns its answer into clean data for the templates."""
import json
import logging
import time

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.config import settings
from app.services.planners import PLANNERS

log = logging.getLogger(__name__)
_client = None

SYSTEM_PROMPT = (
    "You are PocketSmart AI, a careful budget and shopping assistant for shoppers in India. "
    "You reply with valid JSON only."
)

JSON_SHAPE = """{
  "summary": "2-3 sentences on how the plan uses the budget",
  "items": [
    {"name": "product name", "category": "short category", "quantity": 1,
     "estimated_price": 0, "why": "one sentence on why it fits", "buy_from": "store or platform"}
  ],
  "tips": ["short money-saving tip"]
}"""


class GeminiError(Exception):
    """Raised with a message that is safe to show to the user."""


def _get_client():
    global _client
    key = settings.GEMINI_API_KEY
    if not key or key.startswith("your_"):
        raise GeminiError(
            "The Gemini API key is missing. Add GEMINI_API_KEY to your .env file and restart the app."
        )
    if _client is None:
        _client = genai.Client(api_key=key)
    return _client


def build_prompt(planner_key: str, budget: float, form: dict, has_image: bool) -> str:
    planner = PLANNERS[planner_key]
    extras = "\n".join(
        f"- {f['label']}: {form.get(f['name'])}" for f in planner["extra"] if form.get(f["name"])
    )
    image_line = (
        "An image is attached. Use it as a style reference and match its look where the budget allows.\n"
        if has_image
        else ""
    )
    return f"""Planner: {planner['title']}
Focus: {planner['focus']}
Total budget: {int(budget)} INR
Requirements: {form['requirements']}
Preferences: {form.get('preferences') or 'None given'}
{extras}
{image_line}
Rules:
- Use Indian Rupees (INR) and realistic market prices in India. These are estimates, not live prices.
- "estimated_price" is the total for that line (unit price multiplied by quantity).
- The estimated_price values added together must stay within the total budget. If the request cannot fit,
  pick the closest fit and say so in the summary.
- Cover every requirement the user listed. Use 3 to 8 items and 2 to 4 tips.
- "buy_from" is a well-known store or platform in India (for example Amazon India, Flipkart, IKEA India,
  Pepperfry, Tanishq, CaratLane). Never invent web links.

Return JSON in exactly this shape and nothing else:
{JSON_SHAPE}"""


def _number(value) -> float:
    try:
        return max(float(str(value).replace(",", "").replace("₹", "")), 0.0)
    except ValueError:
        return 0.0


def normalise_result(raw, budget: float) -> dict:
    """Recalculate totals ourselves so the numbers on screen always add up."""
    if not isinstance(raw, dict) or not isinstance(raw.get("items"), list) or not raw["items"]:
        raise GeminiError("Gemini returned an answer we could not read. Please try again.")
    items = []
    for it in raw["items"][:10]:
        if not isinstance(it, dict):
            continue
        items.append(
            {
                "name": str(it.get("name", "Item")).strip()[:120],
                "category": str(it.get("category", "")).strip()[:60],
                "quantity": max(int(_number(it.get("quantity")) or 1), 1),
                "estimated_price": _number(it.get("estimated_price")),
                "why": str(it.get("why", "")).strip()[:300],
                "buy_from": str(it.get("buy_from", "")).strip()[:80],
            }
        )
    if not items:
        raise GeminiError("Gemini returned an answer we could not read. Please try again.")
    total = sum(i["estimated_price"] for i in items)
    scale = max(budget, total) or 1
    for i in items:
        i["pct"] = round(i["estimated_price"] / scale * 100, 1)
    remaining = budget - total
    tips = [str(t).strip() for t in raw.get("tips", []) if str(t).strip()][:4]
    return {
        "summary": str(raw.get("summary", "")).strip(),
        "items": items,
        "total": total,
        "budget": budget,
        "remaining": remaining,
        "remaining_pct": max(round(remaining / scale * 100, 1), 0),
        "tips": tips,
    }


def generate_recommendations(
    planner_key: str, budget: float, form: dict, image_bytes: bytes | None = None, image_mime: str | None = None
) -> dict:
    client = _get_client()
    contents = [build_prompt(planner_key, budget, form, bool(image_bytes))]
    if image_bytes:
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime))
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        response_mime_type="application/json",
        temperature=0.5,
    )

    attempts = 3
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL, contents=contents, config=config
            )
            text = (response.text or "").strip()
            break
        except genai_errors.ServerError as exc:
            # 503 "high demand" / 500s are usually temporary on Google's side.
            last_exc = exc
            log.warning("Gemini server error on attempt %s/%s: %s", attempt, attempts, exc)
            if attempt < attempts:
                time.sleep(2 * attempt)  # 2s, then 4s
                continue
            raise GeminiError(
                "Gemini is temporarily overloaded (high demand on Google's side). "
                "Please wait a moment and click Get Recommendations again."
            ) from exc
        except genai_errors.ClientError as exc:
            log.exception("Gemini rejected the request")
            raise GeminiError(
                f"Gemini rejected the request: {exc}. "
                "Check GEMINI_MODEL and GEMINI_API_KEY in your .env file."
            ) from exc
        except Exception as exc:  # network problems, unexpected errors
            log.exception("Gemini request failed")
            raise GeminiError(
                f"Gemini could not complete the request ({type(exc).__name__}). "
                "Check your internet connection and try again."
            ) from exc
    else:  # pragma: no cover - defensive, loop always breaks or raises
        raise GeminiError("Gemini did not respond. Please try again.") from last_exc
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise GeminiError("Gemini returned an answer we could not read. Please try again.") from exc
    return normalise_result(raw, budget)
