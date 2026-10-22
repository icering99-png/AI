"""Slug generator module."""
import re


def make_slug(title: str, max_len: int = 15) -> str:
    """Generate normalized slug bounded by max length."""
    if not title:
        return ""
    txt: str = title.lower()
    txt = re.sub(r"[^\w\s-]", "", txt)
    txt = re.sub(r"[\s_-]+", "-", txt).strip("-")
    if len(txt) > max_len:
        txt = txt[:max_len].rstrip("-")
    return txt
