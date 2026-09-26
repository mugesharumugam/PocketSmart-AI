# PocketSmart AI

A GenAI budget and recommendation assistant. Users enter a budget and requirements, and Gemini suggests
items that fit. It has three planners: Home Interior, Party and Jewellery (with optional reference image).

**Stack:** FastAPI, Jinja2 templates, HTML/CSS/JS, SQLite, JWT login (HttpOnly cookie), Google Gemini API.

## Run it

1. Create a Gemini API key in Google AI Studio.
2. In the project folder, copy `.env.example` to `.env` and paste your key after `GEMINI_API_KEY=`.
   Save the file. Never upload `.env` to GitHub.
3. Create and activate a virtual environment, then install the libraries:

   ```
   python -m venv venv
   venv\Scripts\activate          (Windows)
   source venv/bin/activate       (Mac / Linux)
   pip install -r requirements.txt
   ```
4. Start the app: `python run.py`
5. Open http://127.0.0.1:8000, create an account, sign in and try a planner.

The Gemini model is set in `.env` (`GEMINI_MODEL`). If Google retires a model, change this value to a current one.

## Project structure

```
run.py                     starts the server
app/main.py                creates the FastAPI app, CORS, static files, routes
app/config.py              reads settings from .env
app/models.py              SQLite tables (users, history) and queries
app/deps.py                templates, current-user check, rupee formatting
app/routes/auth.py         register, login, logout (JWT cookie)
app/routes/pages.py        landing page, dashboard, history
app/routes/planners.py     the three planner forms and results
app/services/gemini_service.py   prompt, Gemini call, result clean-up
app/services/planners.py   fields and focus for each planner
app/services/security.py   password hashing and JWT
app/templates/             HTML pages (Jinja2)
app/static/                CSS and JavaScript
```

## How a request flows

User → form in the browser → FastAPI route (checks login and input) → Gemini service (builds the prompt,
calls Gemini) → totals recalculated and saved to history → page shown with the plan.
