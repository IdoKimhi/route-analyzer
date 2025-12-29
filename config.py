import os

def getenv_required(name: str) -> str:
    v = os.getenv(name)
    if not v or not v.strip():
        raise RuntimeError(f"Missing required env var: {name}")
    return v.strip()

class Settings:
    # Flask
    SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")
    APP_TIMEZONE: str = os.getenv("APP_TIMEZONE", "Asia/Jerusalem")

    # DB
    DATABASE_URL: str = getenv_required("DATABASE_URL")

    # Polling cadence
    POLL_MINUTES: int = int(os.getenv("POLL_MINUTES", "30"))

    # Providers
    WAZE_REGION: str = os.getenv("WAZE_REGION", "IL")
