#!/usr/bin/env python3
"""
Hero figure for the oral paper
==============================

A single high-contrast figure that lands the entire central claim of the
paper in 5 seconds when projected at the back of a 300-seat conference room.

Design rationale:
  - One row of 3 small-multiples (one panel per market scenario)
  - X = simulation day (1..100), Y = linguistic adherence P(intended persona)
  - TWO lines per panel: static (red, decaying) vs memory (green, flat)
  - 95% CI bands shaded behind each line
  - Cliff's δ + Hedges' g annotated in-panel, top-right
  - Large fonts (≥14pt), thick lines, no chartjunk

Inputs:
  analysis/outputs/persona_classifier/drift_scores.csv
  analysis/outputs/effect_sizes/effect_size_table.csv

Output:
  analysis/outputs/figures/hero_figure.png   (poster/talk)
  analysis/outputs/figures/hero_figure.pdf   (camera-ready)

Usage:
    python analysis/make_hero_figure.py
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


SCENARIO_ORDER  = ["flat", "bull_trap", "crash"]
SCENARIO_TITLES = {
    "flat":      "Flat market",
    "bull_trap": "Bull-trap bubble",
    "crash":     "Market crash",
}

# Scenario-phase boundaries (fraction of horizon).  Matches envs/synthetic_market.py.
SCENARIO_PHASES = {
    "bull_trap": [
        (0.0, 0.4, "legitimate\nrise",  None),
        (0.4, 0.7, "mania",             "#FDE68A"),   # warm yellow
        (0.7, 1.0, "blow-off",          "#FCA5A5"),   # warm red
    ],
    "crash": [
        (0.0, 0.4, "deterioration", "#FED7AA"),
        (0.4, 0.7, "panic",         "#FCA5A5"),
        (0.7, 1.0, "stabilization", "#A7F3D0"),
    ],
}

# 3-class classifier random baseline (chance ≈ 0.333)
RANDOM_BASELINE = 1.0 / 3

# Refined palette tuned for projection
C_STATIC = "#DC2626"   # vivid red — decaying line
C_MEMORY = "#059669"   # vivid emerald — stable line
C_BAND_S = "#FECACA"
C_BAND_M = "#A7F3D0"
C_GRID   = "#E5E7EB"
C_TEXT   = "#111827"
C_MUTED  = "#6B7280"
C_BASELN = "#9CA3AF"


def load_inputs(drift_path: Path, effects_path: Path):
    if not drift_path.exists():
        print(f"ERROR: {drift_path} not found. Run persona_classifier.py score first.")
        sys.exit(2)
    drift = pd.read_csv(drift_path)
    # Normalize column name
    if "Persona" not in drift.columns and "MBTI" in drift.columns:
        drift = drift.rename(columns={"MBTI": "Persona"})

    eff = None
    if effects_path.exists():
        eff = pd.read_csv(effects_path)
    return drift, eff


def aggregate_per_day(drift_df: pd.DataFrame, scenario: str, window: int):
    """Per-day mean P(intended) ± 95% CI, smoothed by `window` rolling mean."""
    sub = drift_df[drift_df["Scenario"] == scenario]
    rows = []
    for atype in ["static", "memory"]:
        cond = sub[sub["Agent_Type"] == atype]
        if cond.empty:
            continue
        by_day = (cond.groupby("Day")["p_intended"]
                       .agg(["mean", "std", "count"])
                       .reset_index())
        by_day["se"]  = by_day["std"] / np.sqrt(by_day["count"].clip(lower=1))
        # Rolling smooth
        by_day["mean_smooth"] = by_day["mean"].rolling(window, min_periods=1).mean()
        by_day["ci_lo"]       = (by_day["mean"] - 1.96 * by_day["se"]).rolling(window, min_periods=1).mean()
        by_day["ci_hi"]       = (by_day["mean"] + 1.96 * by_day["se"]).rolling(window, min_periods=1).mean()
        by_day["Agent_Type"]  = atype
        rows.append(by_day)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def fetch_effect_size(eff_df: pd.DataFrame, scenario: str):
    """Return (cliffs_delta, hedges_g) for the linguistic-drift row of `scenario`."""
    if eff_df is None:
        return (None, None)
    row = eff_df[(eff_df["Scenario"] == scenario) &
                  (eff_df["Metric"] == "p_intended_persona")]
    if row.empty:
        return (None, None)
    return (float(row["Cliffs_delta"].iloc[0]),
            float(row["Hedges_g"].iloc[0]))


def _draw_phase_shading(ax, scenario, y_top=1.02):
    """Faint coloured background bands marking scenario phases (bull_trap / crash)."""
    phases = SCENARIO_PHASES.get(scenario)
    if not phases:
        return
    for frac_lo, frac_hi, label, color in phases:
        x_lo, x_hi = 100 * frac_lo, 100 * frac_hi
        if color:
            ax.axvspan(x_lo, x_hi, color=color, alpha=0.18, zorder=0)
        # Phase label just below top, centred
        ax.text((x_lo + x_hi) / 2, y_top - 0.015, label,
                ha="center", va="top", fontsize=9, color=C_MUTED,
                linespacing=0.9, zorder=2)


def _annotate_endpoint(ax, x, y, color, label, ha_offset=2):
    """Big bold dot + value label at end of line."""
    ax.scatter([x], [y], s=110, color=color, zorder=6,
                edgecolors="white", linewidths=1.6)
    ax.annotate(f"{y:.2f}", xy=(x, y), xytext=(x + ha_offset, y),
                ha="left", va="center", fontsize=12,
                fontweight="bold", color=color, zorder=6)


def _annotate_gap(ax, x, y_top, y_bot, label):
    """Vertical bracket annotation showing the drift gap."""
    # Bracket
    arrow = dict(arrowstyle="<->", color=C_TEXT, lw=1.8, mutation_scale=14)
    ax.annotate("", xy=(x, y_top), xytext=(x, y_bot), arrowprops=arrow, zorder=5)
    # Centre label, just to the left of the bracket
    y_mid = (y_top + y_bot) / 2
    ax.annotate(label, xy=(x, y_mid), xytext=(x - 4, y_mid),
                ha="right", va="center", fontsize=11.5, fontweight="bold",
                color=C_TEXT,
                bbox=dict(boxstyle="round,pad=0.25",
                           facecolor="white", edgecolor=C_GRID, linewidth=0.8),
                zorder=6)


def make_figure(drift_df: pd.DataFrame, eff_df: pd.DataFrame,
                 out_png: Path, out_pdf: Path,
                 rolling_window: int = 5,
                 exclude_training_days: int = 5):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.family":     "DejaVu Sans",
        "font.size":       13,
        "axes.titlesize":  17,
        "axes.labelsize":  15,
        "xtick.labelsize": 12,
        "ytick.labelsize": 12,
        "legend.fontsize": 13,
        "axes.spines.top":   False,
        "axes.spines.right": False,
    })

    # Drop training days (days 1..exclude_training_days) — they were in the
    # classifier's training set and inflate the early-day score.
    if exclude_training_days > 0:
        drift_df = drift_df[drift_df["Day"] > exclude_training_days]

    fig, axes = plt.subplots(1, 3, figsize=(15.5, 5.2), sharey=True)

    Y_LO, Y_HI = 0.30, 1.04

    for i, (ax, scenario) in enumerate(zip(axes, SCENARIO_ORDER)):
        agg = aggregate_per_day(drift_df, scenario, window=rolling_window)
        if agg.empty:
            ax.set_title(SCENARIO_TITLES[scenario] + " (no data)")
            continue

        # Phase shading goes underneath
        _draw_phase_shading(ax, scenario, y_top=Y_HI)

        # Random-baseline reference line
        ax.axhline(RANDOM_BASELINE, color=C_BASELN, linestyle=(0, (1, 3)),
                    linewidth=1.4, zorder=1)
        if i == 0:
            ax.text(2, RANDOM_BASELINE + 0.018, "chance (1/3)",
                    fontsize=10.5, color=C_BASELN, zorder=2)

        # Pull static/memory series
        endpoints = {}
        for atype, line_color, band_color in [
            ("static", C_STATIC, C_BAND_S),
            ("memory", C_MEMORY, C_BAND_M),
        ]:
            sub = agg[agg["Agent_Type"] == atype].sort_values("Day")
            if sub.empty:
                continue
            ax.fill_between(sub["Day"], sub["ci_lo"], sub["ci_hi"],
                             color=band_color, alpha=0.55, zorder=1)
            ax.plot(sub["Day"], sub["mean_smooth"],
                     color=line_color, linewidth=3.4, zorder=3,
                     label="Static" if atype == "static" else "Memory")
            # Record endpoint for annotation
            last = sub.dropna(subset=["mean_smooth"]).iloc[-1]
            endpoints[atype] = (float(last["Day"]), float(last["mean_smooth"]))

        # Endpoint markers + value labels (drawn after both lines so they stack on top)
        for atype, color in [("static", C_STATIC), ("memory", C_MEMORY)]:
            if atype in endpoints:
                x, y = endpoints[atype]
                _annotate_endpoint(ax, x, y, color,
                                    f"{y:.2f}" + (" (memory)" if atype == "memory" else " (static)"))

        # Vertical drift-gap annotation around day 80 (or near both endpoints)
        if "static" in endpoints and "memory" in endpoints:
            x_gap = 78
            agg_d = agg[agg["Day"] == x_gap]
            if not agg_d.empty:
                y_s_row = agg_d[agg_d["Agent_Type"] == "static"]
                y_m_row = agg_d[agg_d["Agent_Type"] == "memory"]
                if not y_s_row.empty and not y_m_row.empty:
                    y_s = float(y_s_row["mean_smooth"].iloc[0])
                    y_m = float(y_m_row["mean_smooth"].iloc[0])
                    gap_pp = abs(y_m - y_s) * 100
                    _annotate_gap(ax, x_gap, max(y_m, y_s), min(y_m, y_s),
                                   f"{gap_pp:.0f} pp")

        ax.set_title(SCENARIO_TITLES[scenario], fontweight="bold", color=C_TEXT, pad=10)
        ax.set_xlabel("Simulation day", color=C_TEXT)
        ax.set_ylim(Y_LO, Y_HI)
        ax.set_xlim(-2, 112)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.set_yticks([0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
        ax.grid(axis="y", color=C_GRID, linewidth=0.9, zorder=0)
        ax.set_axisbelow(True)
        ax.tick_params(colors=C_MUTED)
        ax.spines["left"].set_color(C_GRID)
        ax.spines["bottom"].set_color(C_GRID)
        for sp_name in ("left", "bottom"):
            ax.spines[sp_name].set_linewidth(1.4)

        # Effect-size annotation, bottom-left
        cliffs, hedges = fetch_effect_size(eff_df, scenario)
        if cliffs is not None:
            txt = (rf"$\delta$ = $+{cliffs:.2f}$, "
                   rf"$g$ = $+{hedges:.2f}$")
            ax.text(0.02, 0.035, txt, transform=ax.transAxes,
                     ha="left", va="bottom", fontsize=13, fontweight="bold",
                     color=C_TEXT,
                     bbox=dict(boxstyle="round,pad=0.45",
                                facecolor="white", edgecolor=C_GRID, linewidth=1))

    # Y-label on leftmost panel only
    axes[0].set_ylabel("$P(\\mathrm{intended\\ persona})$", color=C_TEXT)

    # Single shared legend, prominent
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels,
                loc="upper center", bbox_to_anchor=(0.5, 1.01),
                ncol=2, fontsize=14, frameon=True,
                edgecolor=C_GRID,
                handlelength=2.5, columnspacing=2.2)

    # Suptitle (one short sentence — the entire claim)
    fig.suptitle(
        "Mandate refresh eliminates linguistic persona drift across all market scenarios",
        fontsize=16, fontweight="bold", color=C_TEXT, y=1.11,
    )

    plt.tight_layout(rect=[0, 0, 1, 1.0])
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=220, bbox_inches="tight", facecolor="white")
    fig.savefig(out_pdf,           bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"[Figure] Saved → {out_png}")
    print(f"[Figure] Saved → {out_pdf}")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--drift-scores",
                   default="analysis/outputs/persona_classifier/drift_scores.csv")
    p.add_argument("--effects",
                   default="analysis/outputs/effect_sizes/effect_size_table.csv")
    p.add_argument("--output-dir", default="analysis/outputs/figures")
    p.add_argument("--rolling-window", type=int, default=5,
                   help="Rolling-mean smoothing window in days (default 5)")
    p.add_argument("--exclude-training-days", type=int, default=5,
                   help="Exclude these early days from the plot — they overlap "
                        "the classifier training set (default 5)")
    args = p.parse_args()

    drift, eff = load_inputs(Path(args.drift_scores), Path(args.effects))
    out_dir = Path(args.output_dir)
    make_figure(drift, eff,
                out_png=out_dir / "hero_figure.png",
                out_pdf=out_dir / "hero_figure.pdf",
                rolling_window=args.rolling_window,
                exclude_training_days=args.exclude_training_days)


if __name__ == "__main__":
    sys.exit(main() or 0)
