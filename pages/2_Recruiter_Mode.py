"""Rank several CVs against one job description."""
import pandas as pd
import streamlit as st

from src import ui
from src.data import pretty, sample_cvs
from src.matcher import match
from src.parsing import extract_text
from src.skills import extract_skills

ui.setup("Recruiter Mode")
st.title("Recruiter mode")
st.markdown("Rank a pool of candidates against one job description, filter by must-have skills and export a shortlist.")
jd_name, jd = ui.text_input("JD", "rjd", "data_scientist")
cvs = sample_cvs()
use_samples = st.checkbox("Include all sample CVs", value=True)
ups = st.file_uploader("Upload candidate CVs (PDF, DOCX or TXT)", type=["pdf", "docx", "txt"], accept_multiple_files=True, key="rec_up")
pool = ([(pretty(k), v) for k, v in cvs.items()] if use_samples else []) + [(f.name, extract_text(f.getvalue(), f.name)) for f in (ups or [])]
if not jd or not pool:
    st.info("Provide a job description and at least one CV.")
    st.stop()


@st.cache_data(show_spinner="Scoring candidates...")
def score(pool, jd):
    return [(n, match(t, jd)) for n, t in pool]


results = score(tuple(pool), jd)
jd_sk = sorted(extract_skills(jd))
a, b = st.columns([2, 1])
must = a.multiselect("Must-have skills (candidates without all of these are hidden)", jd_sk)
min_score = b.slider("Minimum overall score", 0, 100, 0)
rows = []
for n, r in results:
    have = set(r.matched_required + r.matched_preferred + r.extra_skills)
    rows.append({"Candidate": n, "Overall": r.overall, "Verdict": r.verdict, "Skills": r.components["skills"],
                 "Semantic": r.components["semantic"], "Experience (yrs)": r.cv_years, "Seniority fit": r.seniority_fit,
                 "Missing required": ", ".join(r.missing_required), "_ok": all(m in have for m in must)})
df = pd.DataFrame(rows).sort_values("Overall", ascending=False)
df.insert(0, "Rank", range(1, len(df) + 1))
short = df[df["_ok"] & (df["Overall"] >= min_score)].drop(columns="_ok")
st.markdown(f"**{len(short)} of {len(df)} candidates** meet the filters.")
st.dataframe(short, hide_index=True, width="stretch",
             column_config={"Overall": st.column_config.ProgressColumn("Overall", min_value=0, max_value=100, format="%.0f")})
st.download_button("Export shortlist as CSV", short.to_csv(index=False).encode(), "shortlist.csv", "text/csv", type="primary")
st.caption("Scores support screening decisions; they should not replace a human review.")
