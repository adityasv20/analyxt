"""
tools/charts.py — Minimal, readable chart generation.

Design principles:
- Cohesive vibrant palette with high contrast on dark surfaces
- No grid lines on simple charts — let data breathe
- Tight DPI for fast loading, generous figsize for readability
- Dark background matching the refreshed UI theme
- Axis labels only when necessary, no redundant titles inside figure
- Max 6 histograms, 1 heatmap, 3 categorical bars, 1 box, 1 scatter
"""

import os
import uuid
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns

warnings.filterwarnings("ignore")

CHARTS_DIR = "outputs/charts"

# ── Theme constants ───────────────────────────────────────────────────────────
BG      = "#07131b"
SURFACE = "#111b2a"
BORDER  = "#274054"
TEXT    = "#d7e8f7"
ACCENT  = "#22d3ee"
ACCENT2 = "#fb923c"
MUTED   = "#8fb5cf"
RED     = "#fb7185"

def _base_fig(w=8, h=4.2):
    fig, ax = plt.subplots(figsize=(w, h), facecolor=BG)
    ax.set_facecolor(SURFACE)
    ax.tick_params(colors=MUTED, labelsize=9)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    return fig, ax


def _save(fig, prefix: str) -> str:
    name = f"{prefix}_{uuid.uuid4().hex[:6]}.png"
    path = os.path.join(CHARTS_DIR, name)
    fig.savefig(path, dpi=110, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    return f"/outputs/charts/{name}"


def generate_charts(df: pd.DataFrame) -> list:
    os.makedirs(CHARTS_DIR, exist_ok=True)
    paths = []
    numeric = df.select_dtypes(include="number").columns.tolist()
    cats = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # 1 ── Histograms (max 6 numeric columns)
    for col in numeric[:6]:
        data = df[col].dropna()
        if len(data) < 3:
            continue

        fig, ax = _base_fig(7, 3.8)
        n, bins, patches = ax.hist(data, bins=28, color=ACCENT, alpha=0.85, edgecolor=BG, linewidth=0.4)

        # Overlay mean line
        mean_val = data.mean()
        ax.axvline(mean_val, color=ACCENT2, linewidth=1.5, linestyle="--", alpha=0.9, label=f"mean {mean_val:,.2f}")
        ax.legend(fontsize=8, framealpha=0, labelcolor=TEXT)

        ax.set_xlabel(col, color=TEXT, fontsize=9)
        ax.set_ylabel("count", color=TEXT, fontsize=9)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
        ax.grid(axis="y", color=BORDER, linewidth=0.5, alpha=0.6)
        ax.set_axisbelow(True)
        fig.tight_layout(pad=1.2)
        paths.append(_save(fig, "hist"))

    # 2 ── Correlation heatmap (if 2+ numeric)
    if len(numeric) >= 2:
        corr = df[numeric].corr()
        n = len(numeric)
        size = max(5, min(n * 0.9, 10))
        fig, ax = plt.subplots(figsize=(size, size * 0.85), facecolor=BG)
        ax.set_facecolor(BG)

        # Custom diverging colormap
        cmap = sns.diverging_palette(260, 30, l=40, as_cmap=True)
        mask = np.zeros_like(corr, dtype=bool)
        mask[np.triu_indices_from(mask)] = True  # show lower triangle only

        sns.heatmap(
            corr, mask=mask, annot=True, fmt=".2f", cmap=cmap,
            linewidths=0.5, linecolor=BG,
            annot_kws={"size": 8, "color": "#e4e4e7"},
            ax=ax,
            cbar_kws={"shrink": 0.7, "pad": 0.02},
            vmin=-1, vmax=1
        )
        ax.tick_params(colors=TEXT, labelsize=8, rotation=40)
        ax.set_xticklabels(ax.get_xticklabels(), ha="right")

        # Style colorbar
        cbar = ax.collections[0].colorbar
        cbar.ax.tick_params(colors=TEXT, labelsize=7)
        cbar.outline.set_edgecolor(BORDER)

        fig.tight_layout(pad=1.0)
        paths.append(_save(fig, "corr"))

    # 3 ── Categorical bar charts (top 8 values, max 3 columns)
    for col in cats[:3]:
        top = df[col].value_counts().head(8)
        if len(top) < 2:
            continue

        fig, ax = _base_fig(7, 3.8)
        bars = ax.barh(
            top.index.astype(str)[::-1],
            top.values[::-1],
            color=ACCENT, alpha=0.85, edgecolor=BG, linewidth=0.4,
            height=0.6
        )

        # Value labels on bars
        for bar, val in zip(bars, top.values[::-1]):
            ax.text(
                bar.get_width() + top.max() * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{val:,}", va="center", ha="left",
                color=TEXT, fontsize=8
            )

        ax.set_xlabel("count", color=TEXT, fontsize=9)
        ax.set_ylabel(col, color=TEXT, fontsize=9)
        ax.set_xlim(0, top.max() * 1.15)
        ax.spines["left"].set_visible(False)
        ax.tick_params(left=False)
        ax.grid(axis="x", color=BORDER, linewidth=0.5, alpha=0.6)
        ax.set_axisbelow(True)
        fig.tight_layout(pad=1.2)
        paths.append(_save(fig, "cat"))

    # 4 ── Box plots (numeric columns, max 8)
    cols_to_box = numeric[:8]
    if cols_to_box:
        fig, ax = _base_fig(max(7, len(cols_to_box) * 1.1), 4.2)

        data_to_plot = [df[c].dropna().values for c in cols_to_box]
        bp = ax.boxplot(
            data_to_plot,
            labels=cols_to_box,
            patch_artist=True,
            medianprops={"color": ACCENT2, "linewidth": 2},
            flierprops={"marker": "o", "markerfacecolor": RED, "markersize": 3, "alpha": 0.5, "markeredgewidth": 0},
            whiskerprops={"color": MUTED, "linewidth": 1},
            capprops={"color": MUTED, "linewidth": 1},
            boxprops={"linewidth": 0},
            widths=0.55,
        )
        for patch in bp["boxes"]:
            patch.set_facecolor(ACCENT)
            patch.set_alpha(0.35)

        ax.set_ylabel("value", color=TEXT, fontsize=9)
        plt.xticks(rotation=30, ha="right", fontsize=8, color=TEXT)
        ax.grid(axis="y", color=BORDER, linewidth=0.5, alpha=0.5)
        ax.set_axisbelow(True)
        fig.tight_layout(pad=1.2)
        paths.append(_save(fig, "box"))

    # 5 ── Scatter (first two numeric cols)
    if len(numeric) >= 2:
        x_col, y_col = numeric[0], numeric[1]
        fig, ax = _base_fig(7, 4.2)

        sample = df[[x_col, y_col]].dropna()
        if len(sample) > 2000:
            sample = sample.sample(2000, random_state=42)

        ax.scatter(
            sample[x_col], sample[y_col],
            color=ACCENT, alpha=0.35, s=14,
            edgecolors="none", linewidths=0
        )

        # Trend line
        try:
            z = np.polyfit(sample[x_col], sample[y_col], 1)
            p = np.poly1d(z)
            xs = np.linspace(sample[x_col].min(), sample[x_col].max(), 100)
            ax.plot(xs, p(xs), color=ACCENT2, linewidth=1.5, alpha=0.8)
        except Exception:
            pass

        ax.set_xlabel(x_col, color=TEXT, fontsize=9)
        ax.set_ylabel(y_col, color=TEXT, fontsize=9)
        ax.grid(color=BORDER, linewidth=0.4, alpha=0.5)
        ax.set_axisbelow(True)
        fig.tight_layout(pad=1.2)
        paths.append(_save(fig, "scatter"))

    # 6 ── Missing values bar (only if any exist)
    missing = df.isnull().sum()
    missing = missing[missing > 0].sort_values(ascending=True)
    if not missing.empty:
        fig, ax = _base_fig(max(6, len(missing) * 0.8), 3.6)
        ax.barh(
            missing.index.astype(str),
            missing.values,
            color=RED, alpha=0.7, edgecolor=BG, linewidth=0.4, height=0.5
        )
        for i, (col, val) in enumerate(missing.items()):
            pct = val / len(df) * 100
            ax.text(val + missing.max() * 0.01, i, f"{val:,} ({pct:.1f}%)",
                    va="center", color=TEXT, fontsize=8)
        ax.set_xlabel("missing count", color=TEXT, fontsize=9)
        ax.set_xlim(0, missing.max() * 1.2)
        ax.spines["left"].set_visible(False)
        ax.tick_params(left=False)
        ax.grid(axis="x", color=BORDER, linewidth=0.4, alpha=0.5)
        ax.set_axisbelow(True)
        fig.tight_layout(pad=1.2)
        paths.append(_save(fig, "missing"))

    return paths
