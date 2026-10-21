"""Evaluation results on the labelled sample set."""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src import ui

ui.setup("Evaluation")
st.title("Evaluation")
root = Path(__file__).resolve().parent.parent
res = json.loads((root / "docs/eval_results.json").read_text())
st.markdown(f"Measured on **{res['n_pairs']} hand-labelled CV and job pairs** (8 synthetic CVs x 4 synthetic job descriptions, "
            "labelled good, partial or poor fit before scoring). Produced by `tools/evaluate.py`.")
methods = [k for k in res if isinstance(res[k], dict) and "spearman" in res[k]]
st.dataframe(pd.DataFrame([{"Method": m, "Spearman": res[m]["spearman"], "Pairwise accuracy": res[m]["pairwise_accuracy"],
                            "Top-1 per job": res[m]["top1_accuracy"], "Good vs rest AUC": res[m]["good_vs_rest_auc"]} for m in methods]),
             hide_index=True, width="stretch")
st.image(str(root / "docs/method_comparison.png"))
st.image(str(root / "docs/score_by_label.png"))
st.markdown("**Mean overall score by label:** " + ", ".join(f"{k} {v}" for k, v in res["mean_score_by_label"].items()))
if res["misordered_pairs"]:
    st.markdown("**Mis-ordered pairs:**")
    for m in res["misordered_pairs"]:
        st.markdown(f"- {m}")
st.caption("The test set is small and synthetic; treat these figures as a sanity check, not a benchmark.")
