"""ATS (applicant tracking system) readiness checks and bullet-point analysis."""
from __future__ import annotations

import re

STANDARD_SECTIONS = {
    "Experience": ["experience", "employment", "work history"],
    "Education": ["education", "qualifications"],
    "Skills": ["skills", "technical skills", "core competencies"],
    "Summary": ["summary", "profile", "objective", "about me"],
}
ACTION_VERBS = {
    "achieved", "automated", "built", "championed", "configured", "created", "cut", "delivered", "deployed",
    "designed", "developed", "drove", "engineered", "established", "executed", "expanded", "generated",
    "grew", "implemented", "improved", "increased", "introduced", "launched", "led", "managed", "migrated",
    "optimised", "optimized", "organised", "owned", "pioneered", "planned", "produced", "reduced", "redesigned",
    "refactored", "resolved", "containerised", "containerized", "scaled", "shipped", "spearheaded", "streamlined", "trained", "transformed", "mentored",
    "analysed", "analyzed", "coordinated", "negotiated", "prepared", "wrote", "maintained", "partnered", "ran",
    "taught", "won", "made", "sold", "spoke", "drew", "founded", "chaired", "hosted", "won",
}
# Label-style list lines ("Languages: English, Urdu") are not achievement bullets.
LABEL_LINE = re.compile(r"^[A-Z][A-Za-z0-9 &/()+-]{0,30}:\s")


def is_action_verb(word: str) -> bool:
    w = word.lower()
    return w in ACTION_VERBS or (w.endswith("ed") and len(w) > 4 and w not in WEAK_STARTS)
WEAK_STARTS = {"responsible", "worked", "helped", "assisted", "involved", "tasked", "duties", "did", "was", "handled", "participated"}
VERB_SUGGEST = {
    "responsible": "Owned", "worked": "Developed", "helped": "Contributed to", "assisted": "Supported",
    "involved": "Delivered", "tasked": "Executed", "handled": "Managed", "participated": "Collaborated on",
}


def check_ats(text: str, filename: str = "", raw: bytes | None = None) -> dict:
    """Return an ATS-readiness score (0-100) and a list of issues."""
    issues: list[tuple[str, str, int]] = []  # (severity, message, penalty)
    lower = text.lower()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    heads = " ".join(l.lower() for l in lines if len(l) < 40)
    for sec, keys in STANDARD_SECTIONS.items():
        if not any(k in heads for k in keys):
            pen = 12 if sec in ("Experience", "Education", "Skills") else 5
            issues.append(("High" if pen > 10 else "Low", f"No standard '{sec}' heading found. ATS parsers look for conventional section names.", pen))
    if not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text):
        issues.append(("High", "No email address detected. Add contact details as plain text at the top.", 15))
    if not re.search(r"\+?\d[\d\s()-]{8,}\d", text):
        issues.append(("Medium", "No phone number detected.", 6))
    words = len(text.split())
    if words > 1000:
        issues.append(("Medium", f"CV is long ({words} words). Aim for 400-800 words (one to two pages).", 8))
    elif words < 150:
        issues.append(("Medium", f"CV is very short ({words} words). ATS ranking favours fuller descriptions.", 8))
    if text.count("|") >= 6 or re.search(r"\t.+\t", text):
        issues.append(("Medium", "Table or column layout detected. Many ATS read tables out of order; use a single column.", 8))
    if raw is not None and filename.lower().endswith(".docx"):
        if b"word/media/" in raw:
            issues.append(("Medium", "Embedded images detected. Text inside images cannot be read by ATS.", 8))
        if b"<w:tbl>" in raw or b"<w:tbl " in raw:
            if not any("Table" in i[1] for i in issues):
                issues.append(("Medium", "Table layout detected in DOCX. Use a single-column layout.", 8))
    if raw is not None and filename.lower().endswith(".pdf") and words < 50:
        issues.append(("High", "Very little selectable text in PDF. It may be a scanned image; export as text-based PDF.", 20))
    symbols = len(re.findall(r"[^\w\s.,;:()/&+%'’\-–@#|\"]", text))
    if words and symbols / words > 0.05:
        issues.append(("Low", "Many decorative symbols detected. Replace icons with plain text labels.", 4))
    score = max(0, 100 - sum(p for _, _, p in issues))
    return {"score": score, "issues": [{"severity": s, "issue": m} for s, m, _ in issues], "words": words}


def bullets(text: str) -> list[str]:
    """Bullet points, re-joining lines that PDF extraction wrapped onto the next line."""
    out: list[str] = []
    open_bullet = False
    for line in text.splitlines():
        s = line.strip()
        if re.match(r"^[-*•·▪◦]\s+", s):
            out.append(re.sub(r"^[-*•·▪◦]\s+", "", s))
            open_bullet = True
        elif open_bullet and s and not out[-1].rstrip().endswith((".", "!", "?")) and "|" not in s \
                and not (s.isupper() and not re.search(r"\d", s)):
            out[-1] = out[-1].rstrip() + " " + s
        else:
            open_bullet = False
    return [b for b in out if not LABEL_LINE.match(b)]


def analyse_bullets(text: str) -> list[dict]:
    """Flag weak bullets (no action verb or no quantification) and propose a rewrite template."""
    results = []
    for b in bullets(text):
        words = re.findall(r"[A-Za-z']+", b)
        if not words:
            continue
        first = words[0].lower()
        has_verb = is_action_verb(first)
        has_number = bool(re.search(r"\d", b))
        weak_start = first in WEAK_STARTS
        if has_verb and has_number:
            continue
        problems = []
        if not has_verb:
            problems.append("does not start with a strong action verb")
        if not has_number:
            problems.append("has no measurable result")
        rest = b
        if weak_start:
            rest = re.sub(r"^(responsible for|worked on|worked with|helped (with |to )?|assisted (with|in)|involved in|tasked with|handled|participated in|duties included)\s*", "", b, flags=re.IGNORECASE)
        verb = VERB_SUGGEST.get(first, "Delivered" if not has_verb else words[0].capitalize())
        core = rest[0].lower() + rest[1:] if rest and not rest[:2].isupper() and len(rest.split()) > 1 and rest.split()[1][0].islower() else rest
        if has_verb:
            core = b[len(words[0]):].strip()
        rewrite = f"{verb} {core.rstrip('.')}"
        if not has_number:
            rewrite += ", achieving [measurable result, e.g. 30% faster reporting for 12 users]"
        results.append({"original": b, "problems": "; ".join(problems), "suggested_rewrite": rewrite + "."})
    return results
