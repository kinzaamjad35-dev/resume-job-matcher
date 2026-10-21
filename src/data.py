"""Access to the bundled synthetic sample CVs and job descriptions."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "data"


def _load(folder: str) -> dict[str, str]:
    return {p.stem: p.read_text(encoding="utf-8") for p in sorted((ROOT / folder).glob("*.txt"))}


def sample_cvs() -> dict[str, str]:
    return _load("sample_cvs")


def sample_jds() -> dict[str, str]:
    return _load("sample_jds")


def pretty(key: str) -> str:
    return key.replace("_", " ").title()
