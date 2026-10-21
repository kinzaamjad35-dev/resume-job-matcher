"""Compare one CV against up to three job descriptions."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import ui
from src.data import pretty, sample_jds
from src.matcher import match
from src.parsing import extract_text

ui.setup("Compare Jobs")
st.title("Compare jobs")
st.markdown("Score one CV against up to three job descriptions to see which role fits best.")
cv_name, cv = ui.text_input("CV", "ccv", "chen_ml_engineer")
jds = sample_jds()
st.subheader("Job descriptions")
chosen = st.multiselect("Sample job descriptions (up to 3)", list(jds), default=list(jds)[:3], max_selections=3, format_func=pretty)
ups = st.file_uploader("Or upload your own (PDF, DOCX or TXT)", type=["pdf", "docx", "txt"], accept_multiple_files=True, key="cmp_up")
items = [(pretty(k), jds[k]) for k in chosen] + [(f.name, extract_text(f.getvalue(), f.name)) for f in (ups or [])]
items = items[:3]
if not cv or not items:
    st.info("Provide a CV and at least one job description.")
    st.stop()

results = [(n, match(cv, t)) for n, t in items]
best = max(results, key=lambda x: x[1].overall)
st.success(f"Best fit: {best[0]} with {best[1].overall:.0f}/100 ({best[1].verdict}).")
cols = st.columns(len(results))
for col, (n, r) in zip(cols, results):
    with col:
        st.plotly_chart(ui.gauge(r.overall, n), width="stretch")
        st.markdown("**Missing required**"); st.markdown(ui.chips(r.missing_required, "miss"), unsafe_allow_html=True)
comps = list(results[0][1].components)
fig = go.Figure()
for (n, r), color in zip(results, [ui.TEAL, ui.NAVY, ui.AMBER]):
    fig.add_trace(go.Scatterpolar(r=[r.components[c] for c in comps] + [r.components[comps[0]]], theta=[c.title() for c in comps] + [comps[0].title()],
                                  name=n, line_color=color, fill="toself", opacity=0.55))
fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])), height=420, margin=dict(t=30, b=30))
st.plotly_chart(fig, width="stretch")
st.dataframe(pd.DataFrame([{"Job": n, "Overall": r.overall, **{c.title(): r.components[c] for c in comps},
                            "Seniority fit": r.seniority_fit} for n, r in results]), hide_index=True, width="stretch")
