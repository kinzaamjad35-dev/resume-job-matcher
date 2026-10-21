"""Render docs/banner.png. Run: python tools/make_banner.py"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
fig = plt.figure(figsize=(12, 3.2), dpi=150)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 12); ax.set_ylim(0, 3.2); ax.axis("off")
ax.add_patch(FancyBboxPatch((0, 0), 12, 3.2, boxstyle="square", fc="#0F2C4C", ec="none"))
ax.add_patch(FancyBboxPatch((0, 0), 12, 0.06, boxstyle="square", fc="#0D9488", ec="none"))
ax.text(0.6, 2.05, "Resume and Job Matcher", color="white", fontsize=30, fontweight="bold")
ax.text(0.6, 1.4, "Semantic CV-to-job matching, ATS checks and skill-gap planning", color="#CBD5E1", fontsize=14)
ax.text(0.6, 0.75, "Python  |  Sentence-Transformers  |  scikit-learn  |  Streamlit", color="#F59E0B", fontsize=11.5)
for i, (lab, val, col) in enumerate([("Skills", 0.86, "#0D9488"), ("Semantic", 0.74, "#38BDF8"), ("Keywords", 0.55, "#F59E0B"), ("Experience", 0.95, "#94A3B8")]):
    y = 2.35 - i * 0.5
    ax.text(8.3, y + 0.05, lab, color="white", fontsize=10, ha="right", va="center")
    ax.add_patch(FancyBboxPatch((8.45, y - 0.1), 3.0, 0.22, boxstyle="round,pad=0,rounding_size=0.1", fc="#1E3A5F", ec="none"))
    ax.add_patch(FancyBboxPatch((8.45, y - 0.1), 3.0 * val, 0.22, boxstyle="round,pad=0,rounding_size=0.1", fc=col, ec="none"))
ax.text(9.95, 0.5, "Illustrative score bars", color="#64748B", fontsize=8, ha="center")
fig.savefig("docs/banner.png"); print("ok")
