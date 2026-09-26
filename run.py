import uvicorn

if __name__ == "__main__":
    # reload_dirs limits the auto-reloader to our own code, so it doesn't
    # watch venv/ and flood the terminal with "Reloading..." on every pip install.
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["app"],
    )
