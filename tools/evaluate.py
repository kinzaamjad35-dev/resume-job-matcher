"""Evaluate the matcher on the labelled sample set (32 CV/JD pairs).

Labels in data/labels.csv were assigned by hand (good=2, partial=1, poor=0)
before the scorer was run. Writes docs/eval_results.json and charts.
Run:  python tools/evaluate.py
"""
import json
import os
import sys
from itertools import combinations

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.getcwd())

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import roc_auc_score

from src.data import sample_cvs, sample_jds
from src.matcher import get_encoder, match

NAVY, TEAL, AMBER = "#0F2C4C", "#0D9488", "#F59E0B"
LAB = {"good": 2, "partial": 1, "poor": 0}
cvs, jds = sample_cvs(), sample_jds()
df = pd.read_csv("data/labels.csv")
df["y"] = df["label"].map(LAB)

enc = get_encoder()
tf = TfidfVectorizer(stop_words="english").fit(list(cvs.values()) + list(jds.values()))
rows = []
for _, r in df.iterrows():
    cv, jd = cvs[r.cv], jds[r.jd]
    res = match(cv, jd)
    a, b = enc.encode([cv, jd], normalize_embeddings=True)
    rows.append({"weighted": res.overall, "tfidf_cosine": float((tf.transform([cv]) @ tf.transform([jd]).T)[0, 0]),
                 "embedding_cosine": float(a @ b), "skills_only": res.components["skills"]})
df = pd.concat([df, pd.DataFrame(rows)], axis=1)
df.to_csv("docs/eval_scores.csv", index=False)


def metrics(col):
    rho = spearmanr(df["y"], df[col]).statistic
    corr = tot = top1 = 0
    for _, g in df.groupby("jd"):
        for (_, x), (_, y) in combinations(g.iterrows(), 2):
            if x.y != y.y:
                tot += 1
                corr += (x[col] > y[col]) == (x.y > y.y)
        top1 += g.loc[g[col].idxmax(), "y"] == 2
    auc = roc_auc_score(df["y"] == 2, df[col])
    return {"spearman": round(float(rho), 3), "pairwise_accuracy": round(corr / tot, 3),
            "top1_accuracy": f"{top1}/{df.jd.nunique()}", "good_vs_rest_auc": round(float(auc), 3), "pairs": int(tot)}


methods = {"Weighted matcher (this project)": "weighted", "Skills taxonomy only": "skills_only",
           "Embedding cosine only": "embedding_cosine", "TF-IDF cosine only": "tfidf_cosine"}
out = {name: metrics(col) for name, col in methods.items()}
out["mean_score_by_label"] = df.groupby("label")["weighted"].mean().round(1).to_dict()
out["n_pairs"] = len(df)
mis = []
for jd, g in df.groupby("jd"):
    for (_, x), (_, y) in combinations(g.iterrows(), 2):
        if x.y > y.y and x.weighted <= y.weighted or y.y > x.y and y.weighted <= x.weighted:
            mis.append(f"{jd}: {x.cv} ({x.label}, {x.weighted}) vs {y.cv} ({y.label}, {y.weighted})")
out["misordered_pairs"] = mis
json.dump(out, open("docs/eval_results.json", "w"), indent=2)
print(json.dumps(out, indent=2))

# Chart 1: method comparison
fig, ax = plt.subplots(figsize=(9, 4.2))
names = list(methods)
pa = [out[n]["pairwise_accuracy"] for n in names]
sp = [out[n]["spearman"] for n in names]
x = np.arange(len(names))
ax.bar(x - 0.2, pa, 0.4, color=NAVY, label="Pairwise ranking accuracy")
ax.bar(x + 0.2, sp, 0.4, color=TEAL, label="Spearman correlation")
for i, (p, s) in enumerate(zip(pa, sp)):
    ax.text(i - 0.2, p + 0.01, f"{p:.2f}", ha="center", fontsize=9)
    ax.text(i + 0.2, s + 0.01, f"{s:.2f}", ha="center", fontsize=9)
ax.set_xticks(x, [n.replace(" (this project)", "\n(this project)") for n in names], fontsize=9)
ax.set_ylim(0, 1.22); ax.legend(frameon=False, loc="upper center", ncol=2); ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Ranking quality on 32 labelled CV/JD pairs (higher is better)", color=NAVY)
fig.tight_layout(); fig.savefig("docs/method_comparison.png", dpi=150); plt.close(fig)

# Chart 2: score distribution by label
fig, ax = plt.subplots(figsize=(9, 3.8))
colors = {"good": TEAL, "partial": AMBER, "poor": NAVY}
for i, lab in enumerate(["poor", "partial", "good"]):
    v = df[df.label == lab]["weighted"]
    ax.scatter(v, np.full(len(v), i) + np.random.default_rng(0).uniform(-0.12, 0.12, len(v)), s=70, color=colors[lab], alpha=0.85)
ax.set_yticks([0, 1, 2], ["Poor fit", "Partial fit", "Good fit"]); ax.set_xlabel("Overall match score (0-100)")
ax.set_xlim(0, 100); ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Match scores by human label", color=NAVY)
fig.tight_layout(); fig.savefig("docs/score_by_label.png", dpi=150); plt.close(fig)
