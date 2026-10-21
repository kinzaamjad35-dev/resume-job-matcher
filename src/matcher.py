"""Transparent weighted CV-to-JD matching.

overall = sum(weight_i * component_i), each component scored 0-100:
  skills     required and preferred skills from the taxonomy found in the CV
  semantic   sentence-transformer similarity between JD requirement lines and CV lines
  keywords   coverage of the JD's top TF-IDF terms
  experience estimated CV years vs JD minimum years
  education  CV education level vs level the JD asks for
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from . import profile
from .skills import SKILL_CATEGORY, extract_skills

WEIGHTS = {"skills": 0.35, "semantic": 0.25, "keywords": 0.15, "experience": 0.15, "education": 0.10}
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
PREFERRED_RE = re.compile(r"(nice to have|preferred|desirable|bonus|plus points|good to have)", re.IGNORECASE)


@lru_cache(maxsize=1)
def get_encoder():
    """Load the sentence-transformer model; return None if unavailable (TF-IDF fallback)."""
    try:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(MODEL_NAME, device="cpu")
    except Exception:  # pragma: no cover - offline or missing package
        return None


def split_jd(jd: str) -> tuple[str, str]:
    m = PREFERRED_RE.search(jd)
    return (jd[: m.start()], jd[m.start():]) if m else (jd, "")


def _lines(text: str, min_words: int = 4) -> list[str]:
    parts = re.split(r"\n|(?<=[.;])\s+", text)
    return [p.strip(" -*") for p in parts if len(p.split()) >= min_words]


def _scale(x: float, lo: float, hi: float) -> float:
    return float(np.clip((x - lo) / (hi - lo), 0, 1) * 100)


def semantic_score(cv: str, jd: str, use_embeddings: bool = True) -> tuple[float, str]:
    jd_lines, cv_lines = _lines(jd), _lines(cv)
    if not jd_lines or not cv_lines:
        return 0.0, "none"
    enc = get_encoder() if use_embeddings else None
    if enc is not None:
        a = enc.encode(jd_lines, normalize_embeddings=True, batch_size=64)
        b = enc.encode(cv_lines, normalize_embeddings=True, batch_size=64)
        sims = a @ b.T
        line_sim = float(sims.max(axis=1).mean())
        return _scale(line_sim, 0.20, 0.70), "embeddings"
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2)).fit(jd_lines + cv_lines)
    sims = (vec.transform(jd_lines) @ vec.transform(cv_lines).T).toarray()
    return _scale(float(sims.max(axis=1).mean()), 0.05, 0.45), "tfidf"


STOP_EXTRA = {"experience", "work", "team", "role", "years", "strong", "ability", "including", "using", "join",
              "looking", "candidate", "responsibilities", "requirements", "skills", "knowledge", "good", "excellent",
              "plus", "nice", "preferred", "will", "able", "new", "required", "working", "understanding", "related",
              "field", "company", "hands", "proven", "etc", "years experience", "similar", "high", "day", "great", "clear", "build", "looking", "data", "team", "use", "make", "help"}


def jd_keywords(jd: str, cv: str = "", top_n: int = 20) -> list[str]:
    """Key phrases of the JD using a RAKE-style scorer (split on stop words and punctuation)."""
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

    lines = [l for l in jd.splitlines()[1:] if "sample data" not in l.lower()]
    stop = ENGLISH_STOP_WORDS | STOP_EXTRA | {"or", "and", "with", "such", "need", "perform", "solid", "expert", "basic", "guide", "runs", "deep", "own", "lead", "grow", "operate", "implement", "improve", "maintain", "write", "integrate", "plan", "run", "manage", "develop", "design", "builds", "build"}
    phrases: list[list[str]] = []
    for chunk in re.split(r"[,.;:()!?\n]|\s-\s|^- ", "\n".join(lines), flags=re.M):
        cur: list[str] = []
        for w in re.findall(r"[A-Za-z][A-Za-z+#/.-]*[A-Za-z+#]|[A-Za-z]", chunk):
            if w.lower() in stop or len(w) < 2:
                if cur:
                    phrases.append(cur)
                cur = []
            else:
                cur.append(w.lower())
        if cur:
            phrases.append(cur)
    phrases = [p for p in phrases if len(p) <= 2]
    freq: dict[str, int] = {}
    deg: dict[str, int] = {}
    for p in phrases:
        for w in p:
            freq[w] = freq.get(w, 0) + 1
            deg[w] = deg.get(w, 0) + len(p)
    scored: dict[str, float] = {}
    for p in phrases:
        key = " ".join(p)
        scored[key] = sum(deg[w] / freq[w] for w in p) + 0.5 * sum(freq[w] for w in p)
    out: list[str] = []
    for k in sorted(scored, key=lambda k: -scored[k]):
        if len(k) < 3 or any(k == o or k in o.split() for o in out):
            continue
        out.append(k)
        if len(out) >= top_n:
            break
    return out


def keyword_in(text: str, kw: str) -> bool:
    """True if every word of the phrase appears in the text (prefix match tolerates plurals and tense)."""
    low = text.lower().replace("-", " ")
    return all(re.search(rf"(?<![a-z]){re.escape(w[:max(4, len(w) - 2)])}", low) for w in kw.lower().replace("-", " ").split())


@dataclass
class MatchResult:
    overall: float
    components: dict[str, float]
    matched_required: list[str]
    missing_required: list[str]
    matched_preferred: list[str]
    missing_preferred: list[str]
    extra_skills: list[str]
    keywords_matched: list[str]
    keywords_missing: list[str]
    cv_years: float
    jd_years: float | None
    cv_seniority: str
    jd_seniority: str
    seniority_fit: str
    cv_education: str
    jd_education: str
    semantic_method: str
    suggestions: list[str] = field(default_factory=list)

    @property
    def verdict(self) -> str:
        return "Strong fit" if self.overall >= 70 else "Partial fit" if self.overall >= 50 else "Weak fit"


def match(cv: str, jd: str, use_embeddings: bool = True) -> MatchResult:
    req_text, pref_text = split_jd(jd)
    cv_sk = extract_skills(cv)
    req = set(extract_skills(req_text))
    pref = set(extract_skills(pref_text)) - req
    m_req, x_req = sorted(req & cv_sk.keys()), sorted(req - cv_sk.keys())
    m_pref, x_pref = sorted(pref & cv_sk.keys()), sorted(pref - cv_sk.keys())
    denom = len(req) + 0.5 * len(pref)
    skills = 100 * (len(m_req) + 0.5 * len(m_pref)) / denom if denom else 50.0

    sem, method = semantic_score(cv, jd, use_embeddings)

    kws = jd_keywords(jd, cv)
    k_hit = [k for k in kws if keyword_in(cv, k)]
    k_miss = [k for k in kws if k not in k_hit]
    keywords = 100 * len(k_hit) / len(kws) if kws else 50.0

    yrs = profile.cv_years(cv)
    need = profile.required_years(jd)
    experience = 100.0 if need is None or need == 0 else float(min(1.0, yrs / need) * 100)
    cv_sen = profile.seniority_from_years(yrs)
    jd_sen = profile.jd_seniority(jd, need)
    gap = cv_sen[0] - jd_sen[0]
    sen_fit = "Matches" if gap == 0 else ("Above requirement (possibly over-qualified)" if gap > 0 else "Below requirement")
    if need is None and gap < 0:
        experience = max(0.0, 100 - 35 * -gap)

    cv_edu = profile.education_level(cv)
    jd_edu = profile.education_level(jd)
    education = 100.0 if cv_edu[0] >= jd_edu[0] else 100.0 * cv_edu[0] / max(jd_edu[0], 1)

    comps = {"skills": skills, "semantic": sem, "keywords": keywords, "experience": experience, "education": education}
    overall = sum(WEIGHTS[k] * v for k, v in comps.items())
    res = MatchResult(
        overall=round(overall, 1), components={k: round(v, 1) for k, v in comps.items()},
        matched_required=m_req, missing_required=x_req, matched_preferred=m_pref, missing_preferred=x_pref,
        extra_skills=sorted(set(cv_sk) - req - pref), keywords_matched=k_hit, keywords_missing=k_miss,
        cv_years=yrs, jd_years=need, cv_seniority=cv_sen[1], jd_seniority=jd_sen[1], seniority_fit=sen_fit,
        cv_education=cv_edu[1], jd_education=jd_edu[1] if jd_edu[0] else "Not specified", semantic_method=method,
    )
    res.suggestions = suggestions(res)
    return res


SECTION_HINT = {
    "Programming": "Skills section and in the project or role where you used it",
    "Libraries": "Skills section and in a project bullet describing what you built with it",
    "Data and ML": "Summary and an experience bullet with a measurable result",
    "Data platforms": "Skills section and in an experience bullet about data work",
    "Cloud and DevOps": "Skills section and in an experience bullet about deployment or infrastructure",
    "Design and product": "Experience bullets describing how you worked",
    "Business": "Summary and relevant experience bullets",
}


def where_to_add(skill_or_kw: str) -> str:
    cat = SKILL_CATEGORY.get(skill_or_kw)
    return SECTION_HINT.get(cat, "Summary or the most relevant experience bullet") if cat else "Summary or the most relevant experience bullet"


def suggestions(r: MatchResult) -> list[str]:
    s = []
    if r.missing_required:
        s.append("Address missing required skills: " + ", ".join(r.missing_required[:8]) +
                 ". If you have this experience, state it explicitly; otherwise see the learning plan.")
    if r.missing_preferred:
        s.append("Preferred skills not found: " + ", ".join(r.missing_preferred[:6]) + ". Adding any you genuinely have will raise your rank.")
    if r.components["keywords"] < 60 and r.keywords_missing:
        s.append("Mirror the job's language. Key terms missing from your CV: " + ", ".join(r.keywords_missing[:8]) + ".")
    if r.jd_years and r.cv_years < r.jd_years:
        s.append(f"The role asks for {r.jd_years:g}+ years; about {r.cv_years:g} were detected. Include dates for every role and count relevant projects, internships and freelance work.")
    if r.seniority_fit.startswith("Above"):
        s.append("Your experience exceeds the level advertised. Emphasise motivation for the role to avoid an over-qualification concern.")
    if r.components["education"] < 100:
        s.append(f"The job mentions {r.jd_education}; your CV shows {r.cv_education}. List equivalent qualifications or certifications if you have them.")
    if r.components["semantic"] < 55:
        s.append("Your experience descriptions read differently from the job's responsibilities. Rewrite two or three bullets to describe comparable outcomes in the job's terms.")
    if not s:
        s.append("Strong alignment. Tailor the summary to the company and quantify your two most relevant achievements.")
    return s
