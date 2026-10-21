"""Resume and Job Matcher: single CV analysis."""
import pandas as pd
import streamlit as st

from src import ui
from src.ats import analyse_bullets, check_ats
from src.learning import learning_note
from src.matcher import WEIGHTS, match, where_to_add
from src.report import build_pdf

ui.setup("Match Analysis")
st.title("Resume and Job Matcher")
st.markdown("Score a CV against a job description, see exactly why, and get concrete steps to improve it. "
            "Choose a sample, upload a PDF, DOCX or TXT file, or paste text.")

c1, c2 = st.columns(2)
with c1:
    st.subheader("Candidate CV")
    cv_name, cv = ui.text_input("CV", "cv", "bilal_junior_analyst")
with c2:
    st.subheader("Job description")
    jd_name, jd = ui.text_input("JD", "jd", "data_scientist")

if not cv or not jd:
    st.info("Provide both a CV and a job description to see the analysis.")
    st.stop()


@st.cache_data(show_spinner="Analysing CV against the job description...")
def run(cv_text, jd_text):
    return match(cv_text, jd_text)


r = run(cv, jd)
raw = st.session_state.get("cv_raw") if st.session_state.get("cv_mode") == "Upload file" else None
ats = check_ats(cv, raw[0] if raw else "", raw[1] if raw else None)
weak = analyse_bullets(cv)

st.divider()
k = st.columns(5)
ui.kpi(k[0], f"{r.overall:.0f}", f"Overall match ({r.verdict})")
ui.kpi(k[1], f"{len(r.matched_required)}/{len(r.matched_required) + len(r.missing_required)}", "Required skills matched")
ui.kpi(k[2], f"{ats['score']}", "ATS readiness")
ui.kpi(k[3], f"{r.cv_years:g} yrs", f"Experience (job asks {r.jd_years:g}+)" if r.jd_years else "Experience")
ui.kpi(k[4], f"{len(weak)}", "Bullets to strengthen")

tabs = st.tabs(["Overview", "Skills and learning plan", "Keyword optimisation", "ATS check", "Bullet improver", "Experience fit"])
with tabs[0]:
    a, b = st.columns([1, 1.4])
    a.plotly_chart(ui.gauge(r.overall), width="stretch")
    b.markdown("**Score breakdown** (each component 0-100, combined with fixed weights)")
    b.plotly_chart(ui.breakdown_chart(r.components, WEIGHTS), width="stretch")
    st.markdown("**Improvement suggestions**")
    for s in r.suggestions:
        st.markdown(f"- {s}")
    if r.semantic_method != "embeddings":
        st.caption("Semantic model unavailable; semantic score uses the TF-IDF fallback.")
    pdf = build_pdf(r, ats, weak, cv_name, jd_name)
    st.download_button("Download full PDF report", pdf, file_name="match_report.pdf", mime="application/pdf", type="primary")

with tabs[1]:
    a, b = st.columns(2)
    a.markdown("**Required skills matched**"); a.markdown(ui.chips(r.matched_required, "ok"), unsafe_allow_html=True)
    b.markdown("**Required skills missing**"); b.markdown(ui.chips(r.missing_required, "miss"), unsafe_allow_html=True)
    a.markdown("**Preferred skills matched**"); a.markdown(ui.chips(r.matched_preferred, "ok"), unsafe_allow_html=True)
    b.markdown("**Preferred skills missing**"); b.markdown(ui.chips(r.missing_preferred, "miss"), unsafe_allow_html=True)
    st.markdown("**Other skills on the CV**"); st.markdown(ui.chips(r.extra_skills, "extra"), unsafe_allow_html=True)
    gaps = r.missing_required + r.missing_preferred
    st.markdown("#### Skill-gap learning plan")
    if gaps:
        st.dataframe(pd.DataFrame({"Skill": gaps, "Priority": ["Required"] * len(r.missing_required) + ["Preferred"] * len(r.missing_preferred),
                                   "What to learn": [learning_note(g) for g in gaps]}), hide_index=True, width="stretch")
    else:
        st.success("No skill gaps detected for this role.")

with tabs[2]:
    st.markdown(f"Top job keywords found: **{len(r.keywords_matched)} of {len(r.keywords_matched) + len(r.keywords_missing)}**")
    st.markdown(ui.chips(r.keywords_matched, "ok") + ui.chips(r.keywords_missing, "miss"), unsafe_allow_html=True)
    st.caption("Teal: present in the CV. Amber: missing. Highlighted below where they appear in the CV.")
    a, b = st.columns([1.5, 1])
    a.markdown(ui.highlight(cv, r.keywords_matched + r.matched_required + r.matched_preferred, r.keywords_missing), unsafe_allow_html=True)
    b.markdown("**Where to add missing terms**")
    missing = r.missing_required + [k for k in r.keywords_missing if k.lower() not in {m.lower() for m in r.missing_required}]
    b.dataframe(pd.DataFrame({"Missing term": missing, "Suggested place": [where_to_add(m) for m in missing]}), hide_index=True, width="stretch")
    b.caption("Only add terms that reflect real experience.")

with tabs[3]:
    a, b = st.columns([1, 2])
    a.plotly_chart(ui.gauge(ats["score"], "ATS readiness"), width="stretch")
    a.caption(f"{ats['words']} words")
    b.markdown("**Issues found**")
    if ats["issues"]:
        b.dataframe(pd.DataFrame(ats["issues"]), hide_index=True, width="stretch")
    else:
        b.success("No ATS issues detected: standard headings, contact details and a single-column text layout.")
    b.caption("Checks: standard section headings, email and phone, length, tables or columns, embedded images (DOCX), scanned PDFs and decorative symbols.")

with tabs[4]:
    if weak:
        st.markdown(f"**{len(weak)} bullet points** could be stronger. Replace the bracketed placeholders with your real figures.")
        st.dataframe(pd.DataFrame(weak).rename(columns={"original": "Original", "problems": "Problems", "suggested_rewrite": "Suggested rewrite"}),
                     hide_index=True, width="stretch")
    else:
        st.success("Every bullet point starts with an action verb and includes a measurable result.")

with tabs[5]:
    a, b, c = st.columns(3)
    ui.kpi(a, f"{r.cv_years:g} years", f"Estimated CV experience ({r.cv_seniority})")
    ui.kpi(b, f"{r.jd_years:g}+ years" if r.jd_years else "Not stated", f"Job requirement ({r.jd_seniority})")
    ui.kpi(c, r.seniority_fit.split(" (")[0], "Seniority match")
    st.markdown(f"Education: CV shows **{r.cv_education}**; the job asks for **{r.jd_education}**.")
    st.caption("Experience is taken from an explicit statement such as '4 years of experience', otherwise from merged date ranges in the experience section.")
