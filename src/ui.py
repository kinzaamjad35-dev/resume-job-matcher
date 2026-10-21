"""Shared Streamlit helpers."""
from __future__ import annotations

import html
import re

import plotly.graph_objects as go
import streamlit as st

from .data import pretty, sample_cvs, sample_jds
from .parsing import clean_text, extract_text

NAVY, TEAL, AMBER, SLATE = "#0F2C4C", "#0D9488", "#F59E0B", "#64748B"
CSS = """
<style>
.block-container {padding-top: 2rem;}
h1, h2, h3 {color: #0F2C4C;}
.kpi {border:1px solid #E2E8F0; border-radius:10px; padding:14px 16px; background:#F8FAFC;}
.kpi .v {font-size:1.9rem; font-weight:700; color:#0F2C4C;} .kpi .l {color:#64748B; font-size:0.85rem;}
.chip {display:inline-block; padding:3px 10px; margin:3px; border-radius:14px; font-size:0.85rem;}
.ok {background:#CCFBF1; color:#115E59;} .miss {background:#FEF3C7; color:#92400E;} .extra {background:#E2E8F0; color:#0F2C4C;}
mark.hit {background:#99F6E4; padding:0 2px; border-radius:3px;}
.cvbox {border:1px solid #E2E8F0; border-radius:8px; padding:14px; white-space:pre-wrap; font-size:0.88rem; max-height:520px; overflow:auto;}
</style>
"""


def setup(title: str):
    st.set_page_config(page_title=f"{title} | Resume and Job Matcher", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    st.sidebar.markdown("**Resume and Job Matcher**  \nBuilt by Kinza Amjad")
    st.sidebar.caption("Sample CVs and job descriptions are synthetic and fictional. Uploaded files are processed in memory and never stored.")


def kpi(col, value: str, label: str):
    col.markdown(f'<div class="kpi"><div class="v">{value}</div><div class="l">{label}</div></div>', unsafe_allow_html=True)


def chips(items, cls) -> str:
    return "".join(f'<span class="chip {cls}">{html.escape(i)}</span>' for i in items) or '<span class="chip extra">None</span>'


def text_input(kind: str, key: str, default_sample: str | None = None) -> tuple[str, str]:
    """Return (name, text) for a CV or JD from sample / upload / paste."""
    samples = sample_cvs() if kind == "CV" else sample_jds()
    mode = st.radio(f"{kind} source", ["Sample", "Upload file", "Paste text"], horizontal=True, key=f"{key}_mode")
    if mode == "Sample":
        keys = list(samples)
        idx = keys.index(default_sample) if default_sample in keys else 0
        k = st.selectbox(f"Sample {kind}", keys, index=idx, format_func=pretty, key=f"{key}_sample")
        return pretty(k), samples[k]
    if mode == "Upload file":
        f = st.file_uploader(f"Upload {kind} (PDF, DOCX or TXT)", type=["pdf", "docx", "txt"], key=f"{key}_file")
        if f is None:
            return "", ""
        data = f.getvalue()
        st.session_state[f"{key}_raw"] = (f.name, data)
        try:
            return f.name, extract_text(data, f.name)
        except Exception as e:  # noqa: BLE001
            st.error(f"Could not read {f.name}: {e}")
            return "", ""
    t = st.text_area(f"Paste {kind} text", height=220, key=f"{key}_text")
    return (f"Pasted {kind}", clean_text(t)) if t.strip() else ("", "")


def gauge(score: float, title: str = "Overall match"):
    color = TEAL if score >= 70 else AMBER if score >= 50 else NAVY
    fig = go.Figure(go.Indicator(mode="gauge+number", value=score, number={"suffix": "/100"},
                                 title={"text": title, "font": {"color": NAVY}},
                                 gauge={"axis": {"range": [0, 100]}, "bar": {"color": color},
                                        "steps": [{"range": [0, 50], "color": "#F1F5F9"}, {"range": [50, 70], "color": "#FEF3C7"},
                                                  {"range": [70, 100], "color": "#CCFBF1"}]}))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=10))
    return fig


def breakdown_chart(components: dict, weights: dict):
    names = [k.title() for k in components]
    fig = go.Figure(go.Bar(x=list(components.values()), y=names, orientation="h", marker_color=[TEAL, NAVY, AMBER, SLATE, "#38BDF8"],
                           text=[f"{v:.0f}  (weight {weights[k]:.0%})" for k, v in components.items()], textposition="auto"))
    fig.update_layout(height=260, xaxis_range=[0, 100], margin=dict(l=10, r=10, t=10, b=10), yaxis_autorange="reversed")
    return fig


def highlight(cv: str, matched: list[str], missing: list[str]) -> str:
    """HTML of the CV with matched keywords highlighted."""
    out = html.escape(cv)
    for kw in sorted(matched, key=len, reverse=True):
        out = re.sub(rf"(?<![\w>]){re.escape(html.escape(kw))}(?![\w<])", lambda m: f'<mark class="hit">{m.group(0)}</mark>', out, flags=re.IGNORECASE)
    return f'<div class="cvbox">{out}</div>'
