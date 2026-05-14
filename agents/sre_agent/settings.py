import os
from urllib.parse import urlsplit, urlunsplit

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "srebot")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")

DB_URL = os.environ.get(
    "SESSION_SERVICE_URI",
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
)


def get_db_url() -> str:
    """Single source of truth for the session service DB URL."""
    return DB_URL


def redact_db_url(url: str) -> str:
    """
    Redact password from a DB URL for safe logging.
    Example: postgresql://user:***@host:5432/db
    """
    try:
        parts = urlsplit(url)
        if "@" not in parts.netloc:
            return url
        creds, host = parts.netloc.split("@", 1)
        if ":" in creds:
            user, _pw = creds.split(":", 1)
            safe_netloc = f"{user}:***@{host}"
        else:
            safe_netloc = f"{creds}:***@{host}"
        return urlunsplit((parts.scheme, safe_netloc, parts.path, parts.query, parts.fragment))
    except Exception:
        # Fallback: best-effort string replace
        if DB_PASSWORD and DB_PASSWORD in url:
            return url.replace(DB_PASSWORD, "***")
        return url
