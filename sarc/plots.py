"""Matplotlib figures (PT/EN labels, optional grayscale, PNG 300 dpi). No Streamlit imports."""
import io

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

_FONT = "Arial" if any(f.name == "Arial" for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
plt.rcParams.update({"font.family": _FONT, "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 110, "savefig.bbox": "tight"})

COLOR = ["#003366", "#0066CC", "#FF6600", "#28A745", "#8E44AD", "#C0392B", "#16A085", "#7F8C8D", "#D4AC0D"]
GRAY = ["#1a1a1a", "#4d4d4d", "#7a7a7a", "#a6a6a6", "#cccccc", "#e0e0e0", "#333333", "#999999", "#666666"]
HATCH = ["", "///", "...", "xx", "\\\\", "++", "oo", "--", "**"]
LSTYLE = ["-", "--", ":", "-.", (0, (5, 1, 1, 1, 1, 1)), (0, (1, 1))]

L = {
    "pt": dict(psi="Peso do PSI", gmd="Peso do GMD", uni="Peso do vetor uniforme", region="Região",
               area="da área", others="Demais regiões", critical="Nó crítico", center="Centro selecionado",
               position="Posição", weight="Peso", criterion="Critério", removed="Alternativa removida",
               taub="τ-b do LOAO", smin="S_min", smean="S_mean", ref="Referência",
               normalized="Desempenho relativo (mín-máx sobre todas as alternativas)"),
    "en": dict(psi="PSI weight", gmd="GMD weight", uni="Uniform vector weight", region="Region",
               area="of area", others="Other regions", critical="Critical node", center="Selected center",
               position="Position", weight="Weight", criterion="Criterion", removed="Removed alternative",
               taub="LOAO τ-b", smin="S_min", smean="S_mean", ref="Reference",
               normalized="Relative performance (min-max over all alternatives)"),
}


def _pal(gray):
    return GRAY if gray else COLOR


def to_png(fig, dpi=300):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor="white")
    return buf.getvalue()


def _fmt(x, lang, nd=3):
    s = f"{x:.{nd}f}"
    return s.replace(".", ",") if lang == "pt" else s


# (a) ternary map --------------------------------------------------------------------------------
def ternary_regions(theta, region, top_regions, center_theta, K, lang="pt", gray=False):
    lb = L[lang]
    a, b, c = theta[:, 0], theta[:, 1], theta[:, 2]
    x, y = b + c / 2, c * np.sqrt(3) / 2
    fig, ax = plt.subplots(figsize=(5.9, 5.3))
    s = max(0.6, 2800 / K ** 1.35)
    fills = (["#262626", "#595959", "#8c8c8c", "#b3b3b3", "#d9d9d9"] if gray
             else ["#003366", "#0066CC", "#FF6600", "#28A745", "#8E44AD"])
    ax.scatter(x[region == 0], y[region == 0], s=s, c="#f0f0f0" if gray else "#e9ecef", marker="h", lw=0)
    handles = []
    for i in range(1, 6):
        mk = region == i
        if mk.any():
            ax.scatter(x[mk], y[mk], s=s, c=fills[i - 1], marker="h", lw=0)
            pct = _fmt(100 * top_regions[i - 1]["P"], lang, 1)
            handles.append(Patch(color=fills[i - 1], label=f"{lb['region']} {i} ({pct}% {lb['area']})"))
    handles.append(Patch(color="#f0f0f0" if gray else "#e9ecef", label=lb["others"]))
    if (region == -1).any():
        mk = region == -1
        ax.scatter(x[mk], y[mk], s=s * 2, c="red" if not gray else "black", marker="x", lw=0.5)
        handles.append(Line2D([], [], marker="x", ls="", color="black", label=lb["critical"]))
    ca, cb, cc = center_theta
    ax.scatter([cb + cc / 2], [cc * np.sqrt(3) / 2], marker="D", s=70, c="black", edgecolors="white", lw=1.2, zorder=5)
    th = "; ".join(_fmt(v, lang) for v in center_theta)
    handles.append(Line2D([], [], marker="D", ls="", color="black", markeredgecolor="white",
                          label=f"{lb['center']} (θ = {th})"))
    # frame and ternary grid every 0.2
    V = np.array([[0, 0], [1, 0], [0.5, np.sqrt(3) / 2], [0, 0]])
    ax.plot(V[:, 0], V[:, 1], color="black", lw=0.8)
    for t in np.arange(0.2, 1.0, 0.2):
        for p0, p1 in [((t, 0, 1 - t), (t, 1 - t, 0)), ((0, t, 1 - t), (1 - t, t, 0)), ((0, 1 - t, t), (1 - t, 0, t))]:
            P = np.array([p0, p1])
            ax.plot(P[:, 1] + P[:, 2] / 2, P[:, 2] * np.sqrt(3) / 2, color="#888", lw=0.4, ls=":")
        ax.text(1 - t + t / 2 + 0.02, t * np.sqrt(3) / 2, _fmt(t, lang, 1), fontsize=7, va="center")   # c axis
        ax.text(t, -0.035, _fmt(t, lang, 1), fontsize=7, ha="center")                                  # b axis
        ax.text((1 - t) / 2 - 0.05, (1 - t) * np.sqrt(3) / 2, _fmt(t, lang, 1), fontsize=7, ha="right", va="center")  # a
    ax.text(-0.03, -0.06, "PSI", ha="right", fontweight="bold")
    ax.text(1.03, -0.06, "GMD", ha="left", fontweight="bold")
    ax.text(0.5, np.sqrt(3) / 2 + 0.04, "UNI", ha="center", fontweight="bold")
    ax.text(0.5, -0.085, lb["gmd"], ha="center", fontsize=8)
    ax.text(0.86, 0.47, lb["uni"], rotation=-60, ha="center", fontsize=8)
    ax.text(0.14, 0.47, lb["psi"], rotation=60, ha="center", fontsize=8)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.06), fontsize=7, frameon=False, ncol=2)
    return fig


# (b) slopegraph -------------------------------------------------------------------------------
def slopegraph(rank_df, columns, label_col="alternative", n_highlight=5, lang="pt", gray=False, labels=None):
    """rank_df: positions per column; highlights the n largest shifts between the first two columns."""
    lb = L[lang]
    labels = labels or columns
    m = len(rank_df)
    fig, ax = plt.subplots(figsize=(1.9 * len(columns) + 2.6, max(4.0, 0.2 * m + 1.2)))
    xs = np.arange(len(columns))
    shift = (rank_df[columns[0]] - rank_df[columns[1]]).abs().values
    # largest shifts; ties broken by position in the first column
    hi = list(np.lexsort((rank_df[columns[0]].values, -shift))[:n_highlight]) if len(columns) > 1 else []
    for i in range(m):
        ys = rank_df[columns].iloc[i].values.astype(float)
        if i in hi:
            continue
        ax.plot(xs, ys, color="#bfbfbf", lw=0.7, marker="o", ms=2)
    pal = _pal(gray)
    for k, i in enumerate(hi):
        ys = rank_df[columns].iloc[i].values.astype(float)
        col = "black" if gray else pal[k % len(pal)]
        ax.plot(xs, ys, color=col, lw=1.8, ls=LSTYLE[k % len(LSTYLE)], marker="o", ms=4)
        name = str(rank_df[label_col].iloc[i])[:28]
        ax.text(xs[0] - 0.06, ys[0], f"{name}  {ys[0]:g}", ha="right", va="center", fontsize=7, color=col)
        ax.text(xs[-1] + 0.06, ys[-1], f"{ys[-1]:g}  {name}", ha="left", va="center", fontsize=7, color=col)
        for xx, yy in zip(xs[1:-1], ys[1:-1]):
            ax.text(xx + 0.05, yy, f"{yy:g}", fontsize=6.5, color=col, va="bottom")
    ax.set_xticks(xs)
    ax.set_xticklabels(labels, fontweight="bold")
    ax.set_ylim(m + 0.8, 0.2)
    ax.set_xlim(-1.45, len(columns) + 0.45)
    ax.set_ylabel(lb["position"])
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="x", length=0)
    return fig


# (c) weight bars --------------------------------------------------------------------------------
def weight_bars(weights_df, columns, lang="pt", gray=False, labels=None):
    lb = L[lang]
    labels = labels or columns
    crit = weights_df["criterion"].astype(str).tolist()
    n, k = len(crit), len(columns)
    fig, ax = plt.subplots(figsize=(max(5.5, 0.9 * n * k / 3 + 2), 3.6))
    wbar = 0.8 / k
    pal = _pal(gray)
    for j, (c, lab) in enumerate(zip(columns, labels)):
        ax.bar(np.arange(n) + (j - (k - 1) / 2) * wbar, weights_df[c].values, wbar, label=lab,
               color=pal[j % len(pal)], edgecolor="black", lw=0.4, hatch=HATCH[j % len(HATCH)] if gray else "")
    ax.set_xticks(np.arange(n))
    ax.set_xticklabels(crit)
    ax.set_xlabel(lb["criterion"])
    ax.set_ylabel(lb["weight"])
    ax.legend(fontsize=7, ncol=min(k, 6), frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.15))
    return fig


# (d) LOAO tau-b ---------------------------------------------------------------------------------
def loao_bars(names, taus, smin, smean, lang="pt", gray=False, max_labels=40):
    lb = L[lang]
    taus = np.nan_to_num(np.asarray(taus, float), nan=0.0)
    o = np.argsort(taus, kind="stable")
    m = len(taus)
    fig, ax = plt.subplots(figsize=(6.3, max(3.2, min(0.17 * m, 14) + 0.8)))
    col = "#7a7a7a" if gray else "#0066CC"
    ax.barh(np.arange(m), taus[o], color=col, edgecolor="black" if m <= 60 else col, lw=0.3)
    if m <= max_labels:
        ax.set_yticks(np.arange(m))
        ax.set_yticklabels([str(names[i])[:34] for i in o], fontsize=6.5)
    else:
        sel = np.arange(min(15, m))
        ax.set_yticks(sel)
        ax.set_yticklabels([str(names[o[i]])[:34] for i in sel], fontsize=6.5)
    ax.axvline(smin, color="black", ls="--", lw=0.9, label=f"{lb['smin']} = {_fmt(smin, lang, 4)}")
    ax.axvline(smean, color="black", ls=":", lw=0.9, label=f"{lb['smean']} = {_fmt(smean, lang, 4)}")
    lo = max(0.0, min(taus.min(), smin) - 0.01)
    ax.set_xlim(lo, 1.0)
    ax.set_xlabel(lb["taub"])
    ax.set_ylabel(lb["removed"])
    ax.legend(fontsize=7, frameon=False, loc="lower right")
    return fig


# heatmap (criteria or method correlation) -------------------------------------------------------
def heatmap(C, labels, lang="pt", gray=False, vmin=-1, vmax=1):
    C = np.asarray(C, float)
    n = len(labels)
    fig, ax = plt.subplots(figsize=(max(4.0, 0.62 * n + 1.6), max(3.4, 0.55 * n + 1.0)))
    cmap = "Greys" if gray else "RdBu_r"
    im = ax.imshow(C, cmap=cmap, vmin=0 if gray else vmin, vmax=vmax)
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticklabels(labels)
    for i in range(n):
        for j in range(n):
            v = C[i, j]
            dark = (abs(v) > 0.6) if not gray else (v > 0.55)
            ax.text(j, i, _fmt(v, lang, 2), ha="center", va="center", fontsize=7,
                    color="white" if dark else "black")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    for s in ax.spines.values():
        s.set_visible(False)
    return fig


# radar (web) of normalized profiles ---------------------------------------------------------------
def radar(R, criteria, names, idx, lang="pt", gray=False):
    lb = L[lang]
    R = np.asarray(R, float)
    span = R.max(0) - R.min(0)
    Z = (R - R.min(0)) / np.where(span > 0, span, 1.0)   # min-max over all alternatives
    n = len(criteria)
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    ang += ang[:1]
    fig, ax = plt.subplots(figsize=(5.4, 4.8), subplot_kw=dict(polar=True))
    pal = _pal(gray)
    for k, i in enumerate(idx):
        v = Z[i].tolist() + [Z[i][0]]
        col = pal[k % len(pal)]
        ax.plot(ang, v, color=col, lw=1.4, ls=LSTYLE[k % len(LSTYLE)] if gray else "-", label=str(names[i])[:30])
        ax.fill(ang, v, color=col, alpha=0.06)
    ax.set_xticks(ang[:-1])
    ax.set_xticklabels(criteria)
    ax.set_ylim(0, 1.0)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.tick_params(axis="y", labelsize=6)
    ax.set_title(lb["normalized"], fontsize=8, pad=14)
    ax.legend(fontsize=7, frameon=False, loc="upper left", bbox_to_anchor=(1.05, 1.05))
    return fig
