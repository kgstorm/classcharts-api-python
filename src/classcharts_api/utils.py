from urllib.parse import unquote
from typing import Any


def parse_cookies(raw: str) -> dict[str, str]:
    """Parse a raw Set-Cookie header string into a key/value dict.

    Mirrors parseCookies() in utils.ts.
    """
    output: dict[str, str] = {}
    cookies = raw.split(",")
    for cookie in cookies:
        parts = cookie.split(";")[0].split("=", 1)
        if len(parts) == 2:
            key = unquote(parts[0]).strip()
            value = unquote(parts[1])
            output[key] = value
    return output


def is_homework_ticked(homework: dict[str, Any]) -> bool:
    """Return True when the pupil has ticked the homework as done.

    This reflects only pupil action (`status.ticked`) and intentionally does
    not infer app UI labels like "to-do", "completed", or "submitted".
    """
    status = homework.get("status")
    if not isinstance(status, dict):
        return False
    ticked = str(status.get("ticked") or "").strip().lower()
    return ticked == "yes"


def is_homework_unticked(homework: dict[str, Any]) -> bool:
    """Return True when the pupil has not ticked homework as done."""
    return not is_homework_ticked(homework)
