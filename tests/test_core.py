import io

import docx
from reportlab.pdfgen import canvas

from src.ats import analyse_bullets, check_ats
from src.data import sample_cvs, sample_jds
from src.learning import learning_note
from src.matcher import WEIGHTS, match
from src.parsing import extract_text
from src.profile import cv_years, education_level, required_years
from src.report import build_pdf
from src.skills import extract_skills

CVS, JDS = sample_cvs(), sample_jds()


def test_weights_sum_to_one():
    assert abs(sum(WEIGHTS.values()) - 1) < 1e-9


def test_skill_extraction_word_boundaries():
    s = extract_skills("Built apps in React and JavaScript; strong Python and SQL.")
    assert {"React", "JavaScript", "Python", "SQL"} <= set(s)
    assert "R" not in s and "Java" not in s


def test_years_and_education():
    assert required_years("Requirements: 3+ years of experience") == 3
    assert cv_years("Experience\nAnalyst (2020 - 2022)\nEngineer (2022 - 2025)\nEducation", today=2026) == 5
    assert education_level("MSc in Computer Science")[1] == "Master's"


def test_good_fit_ranks_first_for_every_sample_job():
    best = {"data_scientist": "ayesha_data_scientist", "frontend_developer": "sara_frontend",
            "devops_engineer": "james_devops", "marketing_manager": "hannah_marketing"}
    for jd, cv in best.items():
        scores = {c: match(t, JDS[jd]).overall for c, t in CVS.items()}
        assert max(scores, key=scores.get) == cv


def test_match_result_fields_and_tfidf_fallback():
    r = match(CVS["bilal_junior_analyst"], JDS["data_scientist"], use_embeddings=False)
    assert r.semantic_method == "tfidf"
    assert 0 <= r.overall <= 100 and r.missing_required and r.suggestions
    assert r.seniority_fit == "Below requirement"


def test_ats_flags_missing_contact_and_headings():
    ats = check_ats("Just some text without structure " * 10)
    msgs = " ".join(i["issue"] for i in ats["issues"])
    assert "email" in msgs and "Experience" in msgs and ats["score"] < 60
    assert check_ats(CVS["ayesha_data_scientist"])["score"] >= 90


def test_bullet_improver():
    out = analyse_bullets("- Responsible for cleaning spreadsheets in Excel\n- Reduced costs by 20% through automation")
    assert len(out) == 1 and out[0]["suggested_rewrite"].startswith("Owned cleaning")


def test_parsing_pdf_docx_txt():
    d = docx.Document(); d.add_paragraph("Python developer with SQL"); b = io.BytesIO(); d.save(b)
    assert "SQL" in extract_text(b.getvalue(), "cv.docx")
    p = io.BytesIO(); c = canvas.Canvas(p); c.drawString(72, 720, "Kubernetes engineer"); c.save()
    assert "Kubernetes" in extract_text(p.getvalue(), "cv.pdf")
    assert extract_text(b"hello", "cv.txt") == "hello"


def test_pdf_report_and_learning_notes():
    cv, jd = CVS["omar_fullstack"], JDS["frontend_developer"]
    r = match(cv, jd)
    pdf = build_pdf(r, check_ats(cv), analyse_bullets(cv))
    assert pdf[:4] == b"%PDF" and len(pdf) > 2000
    assert all(learning_note(s) for s in r.missing_required)
