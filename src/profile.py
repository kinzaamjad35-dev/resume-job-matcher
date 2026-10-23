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
_MON = rf"(?:({MONTHS})[a-z]*\.?,?\s+)?"
_DASHES = re.compile(r"[\u2010-\u2015\u2212]")  # hyphen, en dash, em dash, minus, ...
_OPEN_END = r"present|current|currently|now|today|date|ongoing"
RANGE_RE = re.compile(
    rf"{_MON}((?:19|20)\d\d)\s*(?:-|to|until|till)\s*(?:{_MON}((?:19|20)\d\d)|({_OPEN_END})\b)",
    re.IGNORECASE,
)
SINGLE_RE = re.compile(rf"(?<![\d-]){_MON}((?:19|20)\d\d)(?![\d-])", re.IGNORECASE)
DURATION_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(week|wk|month|mo|year|yr)s?\b", re.IGNORECASE)
EXP_HEADING = re.compile(
    r"^\s*(?:(?:work|professional|relevant|employment|career)\s+)?(?:experience|employment(?:\s+history)?|work\s+history)\s*:?\s*$",
    re.IGNORECASE,
)
OTHER_HEADING = re.compile(
    r"^\s*(?:education|projects?|personal projects|skills|technical skills|certifications?.*|awards?.*|leadership.*|"
    r"languages|interests|references|volunteering|publications|summary|professional summary|profile)\s*:?\s*$",
    re.IGNORECASE,
)
_MIDX = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}
DEFAULT_SINGLE_MONTHS = 6  # a role dated by a single year with no stated duration


def _month(tok: str | None) -> int | None:
    return _MIDX.get(tok.lower()[:3]) if tok else None


def experience_section(cv: str) -> str | None:
    """Text under an experience heading line, up to the next section heading (None if no heading)."""
    lines = _DASHES.sub("-", cv).splitlines()
    for i, line in enumerate(lines):
        if EXP_HEADING.match(line):
            out = []
            for nxt in lines[i + 1:]:
                s = nxt.strip()
                if EXP_HEADING.match(s):
                    continue
                if OTHER_HEADING.match(s) or (s.isupper() and 0 < len(s.split()) <= 6 and not re.search(r"\d", s)):
                    break
                out.append(nxt)
            return "\n".join(out)
    return None


def date_spans(text: str, today: tuple[int, int]) -> list[tuple[int, int]]:
    """Date ranges as half-open (start, end) month indices (year*12 + month)."""
    now = today[0] * 12 + today[1]  # "Present" = start of the current month
    spans = []
    for line in _DASHES.sub("-", text).splitlines():
        used = []
        for m in RANGE_RE.finditer(line):
            used.append(m.span())
            m1, y1, m2, y2, open_end = m.groups()
            s = int(y1) * 12 + (_month(m1) or 0)
            if open_end:
                e = now
            elif _month(m2) is not None:
                e = int(y2) * 12 + _month(m2) + 1
            else:
                e = int(y2) * 12 + (_month(m1) or 0)  # year-only: 2020 - 2022 counts as 2 years
            e = min(e, now)
            if e > s:
                spans.append((s, e))
        for m in SINGLE_RE.finditer(line):
            if any(a <= m.start() < b for a, b in used):
                continue
            mon, yr = m.groups()
            s = int(yr) * 12 + (_month(mon) or 0)
            d = DURATION_RE.search(line)
            if d:
                n, unit = float(d.group(1)), d.group(2).lower()
                months = n / 4.345 if unit.startswith("w") else n * 12 if unit.startswith("y") else n
            else:
                months = 1 if mon else DEFAULT_SINGLE_MONTHS
            e = min(s + max(1, round(months)), now)
            if e > s:
                spans.append((s, e))
    return spans


def merged_months(spans: list[tuple[int, int]]) -> int:
    total, cur = 0, None
    for s, e in sorted(spans):
        if cur and s <= cur[1]:
            cur = (cur[0], max(cur[1], e))
        else:
            if cur:
                total += cur[1] - cur[0]
            cur = (s, e)
    if cur:
        total += cur[1] - cur[0]
    return total


def education_level(text: str) -> tuple[int, str]:
    t = text.lower()
    for level, name, pats in EDU_LEVELS:
        if any(re.search(p, t) for p in pats):
            return level, name
    return 0, "Not stated"


def required_years(jd: str) -> float | None:
    """Minimum years asked for; for a range such as '0-1 years' or '3 to 5 years' the lower bound."""
    m = re.findall(r"(\d+)\s*\+?\s*(?:(?:-|to)\s*\d+\s*\+?\s*)?years?", _DASHES.sub("-", jd), re.IGNORECASE)
    vals = [int(x) for x in m if int(x) < 30]
    return float(min(vals)) if vals else None


def cv_years(cv: str, today: int | None = None, today_month: int | None = None) -> float:
    """Estimate total experience: explicit 'N years' statement, else merged date ranges.

    Ranges come from the experience section (a heading line such as 'EXPERIENCE' or 'Work experience'),
    falling back to the whole CV. Handles en/em dashes, month names, year-only ranges, 'Present/Current/Now'
    and single-year roles (using a stated duration like '5 months' or '3 weeks' when present).
    Overlapping roles are merged, never double counted. Projects/education are not employment.
    """
    t = date.today()
    year = today or t.year
    month = (today_month if today_month is not None else (t.month if year == t.year else 12)) - 1
    explicit = re.findall(r"(\d+)\+?\s*years?(?:'|’)?\s*(?:of\s+)?(?:professional\s+|industry\s+|hands-on\s+)?experience", cv, re.IGNORECASE)
    if explicit:
        return float(max(int(x) for x in explicit))
    block = experience_section(cv)
    if block is None:
        block = cv
    return round(merged_months(date_spans(block, (year, month))) / 12, 1)


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
