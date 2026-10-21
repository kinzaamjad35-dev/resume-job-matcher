"""Experience, education and seniority extraction from CV and JD text."""
from __future__ import annotations

import re
from datetime import date

EDU_LEVELS = [
    (4, "PhD", [r"\bph\.?d\b", "doctorate"]),
    (3, "Master's", [r"\bmaster'?s?\b", r"\bm\.?sc\b", r"\bmba\b", r"\bm\.?s\.?\b(?= in)"]),
    (2, "Bachelor's", [r"\bbachelor'?s?\b", r"\bb\.?sc\b", r"\bb\.?s\.?\b(?= in)", r"\bb\.?a\.?\b(?= in)", r"\bbeng\b", "undergraduate degree", r"\bdegree\b"]),
    (1, "Diploma / A-levels", [r"\bdiploma\b", "a-levels", "a levels", "high school", "baccalaureate"]),
]
SENIORITY = [(0, "Entry / Junior", 0, 2), (1, "Mid-level", 2, 5), (2, "Senior", 5, 9), (3, "Lead / Principal", 9, 99)]
MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec"
RANGE_RE = re.compile(
    rf"(?:(?:{MONTHS})[a-z]*\.? )?((?:19|20)\d\d)\s*(?:-|–|to)\s*(?:(?:{MONTHS})[a-z]*\.? )?((?:19|20)\d\d|present|current|now)",
    re.IGNORECASE,
)


def education_level(text: str) -> tuple[int, str]:
    t = text.lower()
    for level, name, pats in EDU_LEVELS:
        if any(re.search(p, t) for p in pats):
            return level, name
    return 0, "Not stated"


def required_years(jd: str) -> float | None:
    m = re.findall(r"(\d+)\s*\+?\s*(?:-|to)?\s*\d*\s*\+?\s*years?", jd, re.IGNORECASE)
    vals = [int(x) for x in m if int(x) < 30]
    return float(min(vals)) if vals else None


def cv_years(cv: str, today: int | None = None) -> float:
    """Estimate total experience: explicit 'N years' statement, else merged date ranges."""
    today = today or date.today().year
    explicit = re.findall(r"(\d+)\+?\s*years?(?:'|’)?\s*(?:of\s+)?(?:professional\s+|industry\s+|hands-on\s+)?experience", cv, re.IGNORECASE)
    if explicit:
        return float(max(int(x) for x in explicit))
    # Only use the experience section for date ranges where possible.
    lower = cv.lower()
    start = lower.find("experience")
    end = lower.find("education", start + 1) if start >= 0 else -1
    block = cv[start:end] if start >= 0 and end > start else cv
    spans = []
    for a, b in RANGE_RE.findall(block):
        y1 = int(a)
        y2 = today if not b[0].isdigit() else int(b)
        if y2 >= y1:
            spans.append((y1, max(y2, y1 + 0.5)))
    spans.sort()
    total, cur = 0.0, None
    for s, e in spans:
        if cur and s <= cur[1]:
            cur = (cur[0], max(cur[1], e))
        else:
            if cur:
                total += cur[1] - cur[0]
            cur = (s, e)
    if cur:
        total += cur[1] - cur[0]
    return round(total, 1)


def seniority_from_years(years: float) -> tuple[int, str]:
    for lvl, name, lo, hi in SENIORITY:
        if lo <= years < hi:
            return lvl, name
    return 3, "Lead / Principal"


def jd_seniority(jd: str, req: float | None) -> tuple[int, str]:
    t = jd.lower()
    if re.search(r"\b(lead|principal|head of|staff)\b", t[:300]):
        return 3, "Lead / Principal"
    if re.search(r"\bsenior\b", t[:300]):
        return 2, "Senior"
    if re.search(r"\b(junior|graduate|entry[- ]level|intern)\b", t[:300]):
        return 0, "Entry / Junior"
    if req is not None:
        return seniority_from_years(req)
    return 1, "Mid-level"
