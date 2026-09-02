import json
from pathlib import Path

from flask import session

TRANSLATIONS_DIR = Path(__file__).resolve().parent.parent / "translations"
_CACHE = {}


def load_catalog(lang: str) -> dict:
    lang = (lang or "en").split("-")[0]
    if lang not in ("en", "hi", "mr"):
        lang = "en"
    if lang in _CACHE:
        return _CACHE[lang]
    path = TRANSLATIONS_DIR / f"{lang}.json"
    with path.open(encoding="utf-8") as fh:
        _CACHE[lang] = json.load(fh)
    return _CACHE[lang]


def get_locale() -> str:
    return session.get("language", "en")


def translate(key: str, **kwargs) -> str:
    catalog = load_catalog(get_locale())
    text = catalog.get(key) or load_catalog("en").get(key) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
