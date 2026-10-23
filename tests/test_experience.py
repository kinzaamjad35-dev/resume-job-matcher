"""Regression tests for experience extraction, keyword extraction and bullet parsing (Oct 2026 bug)."""
from pathlib import Path

import pytest

from src.ats import analyse_bullets, bullets
from src.matcher import jd_keywords, keyword_in, match
from src.profile import cv_years, experience_section, required_years

FIX = Path(__file__).parent / "fixtures"
KINZA_CV = (FIX / "kinza_cv.txt").read_text()
JD = (FIX / "ai_ml_intern_jd.md").read_text()


def yrs(body: str) -> float:
    return cv_years("EXPERIENCE\n" + body + "\nEDUCATION\nBSc 2010 – 2014", today=2026, today_month=10)


@pytest.mark.parametrize("body,expected", [
    ("Founder | Digital Inqalab Oct 2024 – Present", 2.0),        # en dash + Present
    ("Analyst Oct 2024 — Current", 2.0),                          # em dash + Current
    ("Analyst Oct 2024 - now", 2.0),
    ("Analyst Oct 2024 to Present", 2.0),
    ("Assistant 2023 – 2025", 2.0),                               # year-only, en dash
    ("Analyst Jan 2020 – Dec 2020", 1.0),                         # month names, inclusive
    ("Analyst March 2021 – June 2021", 0.3),
    ("Advisor (Part-Time, 5 months) 2025", 0.4),                  # single year + duration
    ("Legal Intern (3 weeks) 2025", 0.1),                         # short internship counts
    ("A 2020 – 2023\nB 2021 – 2022", 3.0),                        # overlap not double-counted
    ("A Oct 2024 – Present\nB 2023 – 2025", 3.8),                 # partial overlap merged
])
def test_date_formats(body, expected):
    assert yrs(body) == expected


def test_education_and_projects_dates_not_counted():
    cv = "PROJECTS\nForecaster Oct 2026\nEXPERIENCE\nIntern Jun 2025 – Aug 2025\nEDUCATION\nIB 2024 – 2026"
    assert cv_years(cv, today=2026, today_month=10) == 0.2


def test_word_experience_in_summary_does_not_pick_wrong_section():
    sec = experience_section(KINZA_CV)
    assert sec is not None and "Digital Inqalab" in sec and "IB Diploma, 40/45" not in sec


def test_kinza_cv_experience_detected():
    assert cv_years(KINZA_CV, today=2026, today_month=10) == pytest.approx(3.8)


def test_required_years_ranges_and_dashes():
    assert required_years("0–1 years of experience") == 0
    assert required_years("3-5 years of experience") == 3
    assert required_years("2 to 4 years") == 2
    assert required_years("Requirements: 3+ years of experience") == 3


def test_kinza_match_experience_component_full():
    r = match(KINZA_CV, JD, use_embeddings=False)
    assert r.cv_years > 0 and r.components["experience"] == 100.0


def test_jd_metadata_lines_not_keywords():
    kws = jd_keywords(JD)
    assert not any(k in kws for k in ("dha phase", "paid internship"))


def test_keyword_suffix_tolerance_is_bounded():
    assert keyword_in("built dashboards", "dashboard")
    assert keyword_in("analysed datasets", "analyse datasets")
    assert not keyword_in("international relations", "internal")


def test_pdf_wrapped_bullets_rejoined_and_labels_skipped():
    text = ("- Compared 5 models; LightGBM achieved 29% lower error (MAE\n5.90, MAPE 12.93%).\n"
            "- Languages: English (fluent), Urdu (native)\nNext Role | Company 2025")
    b = bullets(text)
    assert b == ["Compared 5 models; LightGBM achieved 29% lower error (MAE 5.90, MAPE 12.93%)."]


def test_kinza_bullet_count_reasonable():
    weak = analyse_bullets(KINZA_CV)
    assert len(weak) <= 6
    assert not any(w["original"].startswith(("Compared", "Guided", "Taught", "Languages:")) for w in weak)
