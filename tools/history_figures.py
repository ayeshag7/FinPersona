"""
Every figure of docs/env_v2/history/SYNTHETIC_ENVIRONMENT_HISTORY.md, generated from the files the document cites.

    python -m tools.history_figures               # every figure
    python -m tools.history_figures --only F1,F2  # a subset

Writes docs/env_v2/history/figures/<name>.png and figures/manifest.json, which records for each figure the source
files it was drawn from and the sample sizes shown, so the document can cite them and a reader can regenerate them.
No number is typed into this file: every value is read from a generated file under docs/env_v2/generated/.

Style follows the data-visualisation method used for the deck: one hue for magnitude, a fixed categorical order for
identity (validated for colour-vision deficiency), status colours only for pass / fail, thin marks, hairline solid
gridlines, one axis per plot, a legend whenever two or more series are drawn, and selective direct labels.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                     # noqa: E402
import numpy as np                                  # noqa: E402
import pandas as pd                                 # noqa: E402
from matplotlib.colors import ListedColormap        # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "docs", "env_v2", "generated")
V21 = os.path.join(GEN, "v2_1")
OUT = os.path.join(ROOT, "docs", "env_v2", "history", "figures")

# ---------------------------------------------------------------------------------------------------- palette
SURFACE = "#fcfcfb"
INK, INK2, MUTED, GRID, AXIS = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]   # fixed order
SEQ = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab",
       "#184f95", "#104281", "#0d366b"]
GOOD, CRITICAL, WARNING = "#0ca30c", "#d03b3b", "#fab219"
DEEMPH = "#c3c2b7"
DPI = 300          # the document scales every figure to 17.6 cm, so a lower value visibly softens the narrow ones

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    "mathtext.fontset": "stix", "font.size": 9.5, "axes.titlesize": 10.5, "axes.labelsize": 9.5,
    "axes.edgecolor": AXIS, "axes.linewidth": 0.8, "axes.facecolor": SURFACE, "figure.facecolor": SURFACE,
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-", "axes.grid": False,
    "legend.frameon": False, "legend.fontsize": 8, "text.color": INK, "axes.labelcolor": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 2.0, "lines.markersize": 6,
})

MANIFEST: Dict[str, dict] = {}


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


KEEP_LOWER = ("gpt", "gemini", "claude", "openrouter", "qwen", "deepseek", "glm", "sd(", "sd ", "s_x", "x ", "x,", "h ", "n ",
              "n/a", "k·", "k ", "lam", "log", "df", "mu_", "sigma", "theta", "tau", "band_", "v21_", "mcr", "turnover",
              "return_pct", "mdd_pct", "acf", "hill", "jb_", "lb_", "arch_", "garch", "gjr", "leverage_", "volume_",
              "logvolume", "skew", "worst_", "mdd", "daily_", "abs_", "vol_", "sent_", "div_", "pe_", "p_loss",
              "blowoff", "jump_", "half_life", "analyst_", "sentiment_", "implied_", "news_", "reported_", "dividend_",
              "days_", "trend_", "sbar", "fw_", "ar1", "e3.8", "e6.", "e1.", "e2.", "e4.", "e5.", "e7.", "e8.",
              "e9.", "innov", "α", "β", "γ", "ν", "θ", "σ", "τ", "λ", "χ", "Δ", "|", "(n", "v1", "v2", "p1", "p2", "p3",
              "p4", "p5", "p6", "p10", "p50", "p90", "m3", "m6", "r1", "r2", "r3", "r4", "r5", "l =", "s =", "sma",
              "macd", "rsi", "phi", "rho", "kappa", "b_pred", "iv")


def capitalise(s: str) -> str:
    """Sentence case for figure text: the first letter is capitalised unless the label is an identifier or symbol."""
    if not s:
        return s
    m = re.match(r"^(\([a-z0-9]+\)\s+)(.*)$", s)          # "(a) some title" keeps its panel tag
    head, body = (m.group(1), m.group(2)) if m else ("", s)
    if not body or not body[0].isalpha() or not body[0].islower() or ord(body[0]) > 127:
        return s
    low = body.lower(); first = body.split(" ")[0]
    if any(low.startswith(k) for k in KEEP_LOWER) or "_" in first or any(ch.isdigit() for ch in first) or "/" in first:
        return s                                              # identifiers, model names and symbols keep their case
    return head + body[0].upper() + body[1:]


def _capitalise_axes(fig):
    """Apply sentence case to every title, axis label, legend entry and word-like tick label of a figure."""
    if fig._suptitle is not None:
        fig._suptitle.set_text(capitalise(fig._suptitle.get_text()))
    for ax in fig.get_axes():
        ax.title.set_text(capitalise(ax.get_title()))            # set_text keeps the title's pad and size
        ax.xaxis.label.set_text(capitalise(ax.get_xlabel())); ax.yaxis.label.set_text(capitalise(ax.get_ylabel()))
        leg = ax.get_legend()
        if leg is not None:
            for t in leg.get_texts():
                t.set_text(capitalise(t.get_text()))
        if getattr(ax, "_keep_tick_case", False):
            continue
        for axis in (ax.xaxis, ax.yaxis):
            labels = [t.get_text() for t in axis.get_ticklabels()]
            if labels and any(labels):
                new = []
                for lab in labels:
                    parts = lab.split("\n")
                    new.append("\n".join([capitalise(parts[0])] + parts[1:]) if parts[0] and parts[0][0].isalpha() else lab)
                if new != labels:
                    axis.set_ticks(axis.get_ticklocs()[: len(new)] if len(axis.get_ticklocs()) >= len(new) else axis.get_ticklocs())
                    axis.set_ticklabels(new)
    for leg in fig.legends:
        for t in leg.get_texts():
            t.set_text(capitalise(t.get_text()))


def save(fig, name: str, title: str, sources: List[str], n: str, note: str = ""):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, f"{name}.png")
    _capitalise_axes(fig)
    fig.savefig(p, dpi=DPI, facecolor=SURFACE, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    MANIFEST[name] = {"file": rel(p), "title": title, "sources": [rel(s) if os.path.isabs(s) else s for s in sources],
                      "n": n, "note": note}
    print(f"  {name}: {rel(p)}")


def tidy(ax, ygrid=True, xgrid=False):
    ax.set_axisbelow(True)
    if ygrid:
        ax.yaxis.grid(True)
    if xgrid:
        ax.xaxis.grid(True)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(AXIS)


def bar_ends(ax, bars, fmt="{:.3f}", dx=0.0, dy=0.0, horizontal=False, color=INK2, size=8):
    for b in bars:
        if horizontal:
            x = b.get_width(); y = b.get_y() + b.get_height() / 2
            ax.text(x + dx, y + dy, fmt.format(x), va="center", ha="left", fontsize=size, color=color)
        else:
            x = b.get_x() + b.get_width() / 2; y = b.get_height()
            ax.text(x + dx, y + dy, fmt.format(y), ha="center", va="bottom", fontsize=size, color=color)


def csv(rel_path: str) -> pd.DataFrame:
    return pd.read_csv(os.path.join(GEN, rel_path))


def jsn(rel_path: str) -> dict:
    return json.load(open(os.path.join(GEN, rel_path), encoding="utf-8"))


# ================================================================================================== the versions
CHECKLISTS = [("v1", "checklist_v1.csv"), ("v2", "checklist_v2.csv"),
              ("v2.1 P1 before", "v2_1/e1_6_checklist_before.csv"), ("P1 after", "v2_1/e1_6_checklist_after.csv"),
              ("P2 after", "v2_1/e2_after_checklist.csv"), ("P3 after", "v2_1/e3_after_checklist.csv"),
              ("P4 after", "v2_1/e4_after_checklist.csv"), ("P5 after", "v2_1/e5_after_checklist.csv"),
              ("P6 after", "v2_1/e6_after_checklist.csv")]
AUDITS = [("v1", "leakage_audit_v1"), ("v2", "leakage_audit_v2"),
          ("P1 after", "v2_1/e1_6/audit_after_levelfree"), ("P2 after", "v2_1/e2_6_after/audit_after_levelfree"),
          ("P3 after", "v2_1/e3_after/audit_after_levelfree"), ("P4 after", "v2_1/e4_21/audit_after_levelfree"),
          ("P5 after", "v2_1/e5_after/audit_after_levelfree"), ("P6 after", "v2_1/e6_after/audit_after_derived")]


def F1_checklist_heatmap():
    """The 20-item stylized-facts checklist by version and phase, at the v2 numeric criteria."""
    cols, mats, ns = [], [], []
    props = None
    for label, f in CHECKLISTS:
        t = csv(f).sort_values("item")
        if props is None:
            props = [f"Item {int(i)}" for i in t["item"]]          # the items are named in the text's checklist table
        v = t["pass"].map(lambda x: 1.0 if str(x) == "True" else (0.0 if str(x) == "False" else np.nan)).to_numpy()
        cols.append(label); mats.append(v); ns.append(int(t["n_seeds"].max()))
    M = np.column_stack(mats)
    fig, ax = plt.subplots(figsize=(7.6, 7.4))
    cmap = ListedColormap([CRITICAL, GOOD])
    ax.imshow(np.where(np.isnan(M), np.nan, M), cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax.set_facecolor("#efeeea")                       # blank cells: judged by another audit, or not applicable
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M[i, j]
            ax.text(j, i, "pass" if v == 1 else ("fail" if v == 0 else "n/a"), ha="center", va="center", fontsize=7,
                    color="white" if v in (0, 1) else MUTED)
    ax.set_xticks(range(len(cols))); ax.set_xticklabels([f"{c}\nn ≤ {n:,}" for c, n in zip(cols, ns)], fontsize=6.5)
    ax.set_yticks(range(len(props))); ax.set_yticklabels(props, fontsize=7)
    ax.set_title("Stylized-facts checklist by item and state, judged at the v2 criteria", pad=48, fontsize=10)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    passes = [int(np.nansum(m)) for m in mats]
    fails = [int(np.sum(m == 0)) for m in mats]
    for j, (p, f) in enumerate(zip(passes, fails)):
        ax.text(j, -0.9, f"{p} / {f}", ha="center", va="bottom", fontsize=7, color=INK2)
    ax.text(-0.5, -1.6, "pass / fail counts", fontsize=7, color=INK2)
    save(fig, "F01_checklist_by_version", "Stylized-facts checklist by version",
         [f for _, f in CHECKLISTS], "per item: the n_seeds column of each file (largest shown per column)",
         "Grey cells are items judged by the leakage audit or not applicable in that state.")


def F2_leakage_by_version():
    """The leakage audit across versions: the best value inversion, the calm surrogate, resolvable calm steps."""
    rows = []
    for label, base in AUDITS:
        l1 = csv(f"{base}_L1.csv"); best = l1.sort_values("median_APE").iloc[0]
        l2 = csv(f"{base}_L2.csv")
        sel = l2[(l2.target == "x") & (l2.phase_group == "calm")]          # best of ridge, GBT, MLP, as the audits report
        full = sel[sel.feature_set == "full"].sort_values("R2", ascending=False).iloc[0]
        po = sel[sel.feature_set == "price_only"].sort_values("R2", ascending=False).iloc[0]
        l4 = csv(f"{base}_L4.csv"); fc = l4[(l4.scenario == "flat") & (l4.phase == "calm")].iloc[0]
        rows.append({"version": label, "l1_candidate": str(best["candidate"]), "l1_median_ape": float(best["median_APE"]),
                     "l1_within5": float(best["within_5pct"]) if "within_5pct" in l1 else np.nan,
                     "r2_full": float(full["R2"]), "r2_po": float(po["R2"]),
                     "r2_full_lo": float(full["R2_lo"]) if "R2_lo" in l2 else np.nan, "r2_full_hi": float(full["R2_hi"]) if "R2_hi" in l2 else np.nan,
                     "r2_po_lo": float(po["R2_lo"]) if "R2_lo" in l2 else np.nan, "r2_po_hi": float(po["R2_hi"]) if "R2_hi" in l2 else np.nan,
                     "n_calm_rows": int(full["n"]), "cov_flat_calm": float(fc["coverage_theta_0.05"]), "n_flat_steps": int(fc["n_steps"])})
    t = pd.DataFrame(rows)
    x = np.arange(len(t))
    fig, axes = plt.subplots(3, 1, figsize=(8.4, 9.4), gridspec_kw={"hspace": 0.6})
    # (a) L1
    ax = axes[0]
    b = ax.bar(x, t["l1_median_ape"], width=0.55, color=CAT[0])
    bar_ends(ax, b, fmt="{:.3f}", dy=0.004)
    short = {"k * P / reported_PE": "k·P/PE", "k * analyst_fair_value": "k·analyst value", "k * P (price itself)": "k·price"}
    ax.set_xticks(x); ax.set_xticklabels([f"{v}\n{short.get(c, c)}" for v, c in zip(t["version"], t["l1_candidate"])], fontsize=7)
    ax.set_ylabel("median abs. % error of\nthe best inversion of V")
    ax.set_title("(a) L1: median error of the best formula that rebuilds V from the shown fields (formula under each bar)", fontsize=9)
    ax.set_ylim(0, max(t["l1_median_ape"]) * 1.25)
    tidy(ax)
    # (b) L2 calm ridge
    ax = axes[1]
    w = 0.36
    LOW = -1.0                                                           # v1's price-only surrogate sits far below: shown clipped
    b1 = ax.bar(x - w / 2, np.clip(t["r2_full"], LOW, None), width=w, color=CAT[0], label="all shown fields")
    b2 = ax.bar(x + w / 2, np.clip(t["r2_po"], LOW, None), width=w, color=CAT[1], label="price fields only")
    ax.set_ylim(LOW - 0.22, 1.3)
    for xs, lo, hi in ((x - w / 2, t["r2_full_lo"], t["r2_full_hi"]), (x + w / 2, t["r2_po_lo"], t["r2_po_hi"])):
        m = ~np.isnan(lo)
        ax.errorbar(np.asarray(xs)[m], ((lo + hi) / 2)[m], yerr=((hi - lo) / 2)[m], fmt="none", ecolor=INK2, elinewidth=0.8, capsize=2)
    ax.axhline(0, color=AXIS, lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels(t["version"], fontsize=7)
    ax.set_ylabel("R² of the best surrogate\nfor x, calm rows")
    ax.set_title("(b) L2: predictability of the hidden mispricing from the agent's screen\n(calm days, best of three surrogates; bars below -1 clipped)", fontsize=9)
    ax.legend(loc="upper right", ncol=2)
    # value labels sit clear of the bar and of its interval: above the upper limit, or below the lower one
    for i in range(len(t)):
        for xx, v, lo, hi in ((i - w / 2, t["r2_full"][i], t["r2_full_lo"][i], t["r2_full_hi"][i]),
                              (i + w / 2, t["r2_po"][i], t["r2_po_lo"][i], t["r2_po_hi"][i])):
            if v >= 0:
                top = hi if np.isfinite(hi) else v
                ax.text(xx, top + 0.04, f"{v:.2f}", ha="center", va="bottom", fontsize=6, color=INK2)
            elif v >= LOW:
                bottom = lo if np.isfinite(lo) else v
                ax.text(xx, bottom - 0.04, f"{v:.2f}", ha="center", va="top", fontsize=6, color=INK2)
            else:
                ax.text(xx, LOW - 0.04, f"{v:.0f} (clipped)", ha="center", va="top", fontsize=6, color=INK2)
    tidy(ax)
    # (c) L4
    ax = axes[2]
    ax.plot(x, t["cov_flat_calm"], color=CAT[0], marker="o", markersize=7, markeredgecolor=SURFACE, markeredgewidth=1.5)
    for i, v in enumerate(t["cov_flat_calm"]):
        ax.text(i, v + 0.06, f"{v:.2f}", ha="center", fontsize=7, color=INK2)
    ax.set_ylim(-0.05, 1.0)
    ax.set_xticks(x); ax.set_xticklabels(t["version"], fontsize=7)
    ax.set_ylabel("share of flat calm days\nwith |x| above θ = 0.05")
    ax.set_title("(c) L4: share of flat-market calm days that are resolvable at θ = 0.05", fontsize=9)
    tidy(ax)
    save(fig, "F02_leakage_by_version", "Leakage audit by version",
         [f"{b}_L1.csv" for _, b in AUDITS] + [f"{b}_L2.csv" for _, b in AUDITS] + [f"{b}_L4.csv" for _, b in AUDITS],
         f"calm rows per version (L2): {', '.join(f'{v} {n:,}' for v, n in zip(t.version, t.n_calm_rows))}; "
         f"flat calm steps (L4): {', '.join(f'{v} {n:,}' for v, n in zip(t.version, t.n_flat_steps))}",
         "v1 and v2 audits carry no confidence intervals; the v2.1 audits carry seed-cluster bootstrap 95 % intervals.")
    return t


def F3_v1_gate():
    """Where v1 stood: the day-1 persona separability gate per model and arm on the v1 runs."""
    t = csv("e0_gate_v1_per_model.csv")
    t = t[(t.model != "POOLED") & (t.agent_type.isin(["static", "memory"]))]
    order = t.groupby("model")["auc_ovr_macro"].max().sort_values().index.tolist()
    y = {m: i for i, m in enumerate(order)}
    fig, ax = plt.subplots(figsize=(7.6, 6.4))
    for m in order:
        s = t[t.model == m]
        ax.plot([s["auc_ovr_macro"].min(), s["auc_ovr_macro"].max()], [y[m], y[m]], color=DEEMPH, lw=1.0, zorder=2)
    for arm, col, mk in (("static", CAT[0], "o"), ("memory", CAT[1], "s")):
        s = t[t.agent_type == arm]
        ax.scatter(s["auc_ovr_macro"], [y[m] for m in s["model"]], s=34, color=col, marker=mk, label=f"{arm} arm",
                   zorder=3, edgecolor=SURFACE, linewidth=0.8)
    ax.axvline(0.5, color=INK2, lw=0.9)
    ax.text(0.503, len(order) - 0.6, "chance (AUC 0.5)", fontsize=7, color=INK2, va="top")
    ax.set_yticks(range(len(order))); ax.set_yticklabels(order, fontsize=7)
    ax.set_xlim(0.2, 0.9)
    ax.set_xlabel("macro one-vs-rest AUC of the day-1 cash share against the persona (75 runs per point; 54 for gemma-3-4b-it)",
                  fontsize=8)
    ax.set_title(f"v1 baseline, the day-1 separability gate: {int(t['gate_pass'].sum())} of {len(t)} model and arm cells pass",
                 fontsize=9)
    ax.legend(fontsize=7, loc="lower right")
    tidy(ax, ygrid=False, xgrid=True)
    save(fig, "F03_v1_separability_gate", "v1 day-1 persona separability gate per model and arm",
         ["e0_gate_v1_per_model.csv"],
         f"{int(t['n_runs'].sum()):,} v1 runs across {t.model.nunique()} models and 2 arms (POOLED rows excluded)",
         "gate_pass requires ordering, band, AUC and surrogate criteria together; no model passes on either arm.")

REGISTRY = {"F1": F1_checklist_heatmap, "F2": F2_leakage_by_version, "F3": F3_v1_gate}


# ================================================================================================== helpers (batch 2)
def ci(v, key=None):
    """Coerce an interval to (lo, hi) whether stored as [lo, hi], {"lo":..,"hi":..} or {key: [lo, hi]}."""
    if v is None:
        return (np.nan, np.nan)
    if isinstance(v, dict):
        if key is not None and key in v:
            return ci(v[key])
        if "lo" in v and "hi" in v:
            return (float(v["lo"]), float(v["hi"]))
        vals = list(v.values())
        if len(vals) == 2 and all(isinstance(x, (int, float)) for x in vals):
            return (float(vals[0]), float(vals[1]))
        return (np.nan, np.nan)
    if isinstance(v, (list, tuple)) and len(v) >= 2:
        return (float(v[0]), float(v[1]))
    return (np.nan, np.nan)


def num(v):
    """A number stored bare or inside {"value": ..} / {"median": ..} / {"payout": ..} / {"point": ..}."""
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v)
    if isinstance(v, dict):
        for k in ("value", "median", "payout", "point", "mean"):
            if isinstance(v.get(k), (int, float)):
                return float(v[k])
    return np.nan


def dot_ci(ax, x, y, lo, hi, color, label=None, ms=7, horizontal=False):
    x, y, lo, hi = map(np.asarray, (x, y, lo, hi))
    if horizontal:
        ax.errorbar(y, x, xerr=[np.maximum(y - lo, 0), np.maximum(hi - y, 0)], fmt="o", color=color, ecolor=color,
                    elinewidth=1.2, capsize=2.5, markersize=ms, markeredgecolor=SURFACE, markeredgewidth=1.5, label=label)
    else:
        ax.errorbar(x, y, yerr=[np.maximum(y - lo, 0), np.maximum(hi - y, 0)], fmt="o", color=color, ecolor=color,
                    elinewidth=1.2, capsize=2.5, markersize=ms, markeredgecolor=SURFACE, markeredgewidth=1.5, label=label)


def _wrap(text: str, width: int) -> str:
    """Break a long tick label on spaces so that it does not eat the plotting area."""
    out, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > width:
            out.append(line); line = word
        else:
            line = f"{line} {word}".strip()
    out.append(line)
    return "\n".join(out)


# ================================================================================================== Phase 1
def F4_phase1_estimators():
    """Phase 1: the three estimators of the mispricing half-life and sd, and where the engine fit later put them."""
    d = jsn("v2_1/e1_2/decision.json")
    est = d["estimates"]; use = d["usability"]
    labels, h, hlo, hhi, sx, slo, shi, usable = [], [], [], [], [], [], [], []
    for k in ("A", "B", "C"):
        e = est[k]; labels.append(_wrap(f"{k}: {e['name']}", 44))      # wrapped, not cut: a cut at 38 lost a closing bracket
        h.append(float(e["h"])); lo, hi = ci(e.get("h_ci")); hlo.append(lo); hhi.append(hi)
        sx.append(float(e["s_x"])); lo, hi = ci(e.get("s_x_ci")); slo.append(lo); shi.append(hi)
        u = use.get(k, {}); usable.append(bool(u.get("usable")) if isinstance(u, dict) else bool(u))
    # the engine refits of Phases 2 and 3
    p2 = jsn("v2_1/e2_3/smm_ar1_full.json"); p3 = jsn("v2_1/e2_3/smm_ar1c_full_p3.json")
    for lab, f in (("Phase 2 engine refit (AR(1), SMM)", p2), ("Phase 3 constrained refit (in force)", p3)):
        labels.append(lab); h.append(float(f["params"]["h"]))
        lo, hi = ci(f.get("bootstrap_refits", {}).get("ci95"), "h"); hlo.append(lo); hhi.append(hi)
        sx.append(np.nan); slo.append(np.nan); shi.append(np.nan); usable.append(True)
    y = np.arange(len(labels))
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.6), gridspec_kw={"wspace": 0.55, "width_ratios": [1.3, 1]})
    ax = axes[0]
    for i in range(len(labels)):
        col = CAT[0] if usable[i] else DEEMPH
        dot_ci(ax, [y[i]], [h[i]], [hlo[i]], [hhi[i]], col, horizontal=True)
        ax.text(hhi[i] * 1.15 if np.isfinite(hhi[i]) else h[i] * 1.15, y[i], f"{h[i]:.1f} d", va="center", fontsize=7, color=INK2)
    ax.set_xscale("log"); ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=7); ax.invert_yaxis()
    ax.set_xlabel("mispricing half-life h (days, log scale)"); ax.set_title("(a) half-life from the three panel estimators and the two engine refits", fontsize=9)
    tidy(ax, ygrid=False, xgrid=True)
    ax = axes[1]
    for i in range(3):
        col = CAT[0] if usable[i] else DEEMPH
        dot_ci(ax, [y[i]], [sx[i]], [slo[i]], [shi[i]], col, horizontal=True)
        ax.text(shi[i] + 0.005 if np.isfinite(shi[i]) else sx[i] + 0.005, y[i], f"{sx[i]:.3f}", va="center", fontsize=7, color=INK2)
    # Phase 2 (P2-6) corrected estimator C's s_x: the 0.129 was the calm engine's sd at a 150-day half-life, not the fit's
    vj = json.load(open(os.path.join(ROOT, "envs", "v2", "params", "value.json"), encoding="utf-8"))
    sx_c_corr = float(vj["s_x_fit"]["value"])
    ax.scatter([sx_c_corr], [y[2]], marker="D", s=40, color=CAT[1], edgecolor=SURFACE, linewidth=1.2, zorder=4)
    ax.text(sx_c_corr, y[2] - 0.14, f"corrected in Phase 2: {sx_c_corr:.3f}", ha="left", va="bottom", fontsize=6.5, color=CAT[1])
    ax.set_yticks(y[:3]); ax.set_yticklabels(["A", "B", "C"], fontsize=7); ax.invert_yaxis()
    ax.set_xlabel("stationary sd of the mispricing, s_x"); ax.set_title("(b) stationary sd of the mispricing by estimator (grey: judged unusable)", fontsize=9)
    tidy(ax, ygrid=False, xgrid=True)
    save(fig, "F04_phase1_estimators", "Phase 1: three estimators of h and s_x, and the later engine refits",
         ["v2_1/e1_2/decision.json", "v2_1/e2_3/smm_ar1_full.json", "v2_1/e2_3/smm_ar1c_full_p3.json"],
         "; ".join(f"{k}: n = {est[k].get('n')}" for k in ("A", "B", "C")) + "; refits: 30 bootstrap refits each",
         "Blue = usable by the registered recovery rule; grey = not usable. Intervals are 95 %.")


def F5_vr_curve():
    """Phase 1: the panel's variance-ratio curve and the model fitted to it."""
    d = jsn("v2_1/e1_2/vr_fit.json")["periods"]["full"]
    ks = [5, 10, 20, 60, 120, 250, 500]
    pm = d["pooled_moments"]; cis = d.get("pooled_moments_ci_stock", {}); band = d.get("per_stock_VR_p25_p75", {})
    y = [float(pm[f"VR{k}"]) for k in ks]
    lo = [ci(cis.get(f"VR{k}"))[0] for k in ks]; hi = [ci(cis.get(f"VR{k}"))[1] for k in ks]
    b25 = [ci(band.get(f"VR{k}"))[0] for k in ks]; b75 = [ci(band.get(f"VR{k}"))[1] for k in ks]
    mm = d["fit"].get("model_moments")
    if isinstance(mm, dict):
        fit = [float(mm.get(f"VR{k}", np.nan)) for k in ks]
    elif isinstance(mm, list) and len(mm) >= len(ks) + 1:
        fit = [float(v) for v in mm[1:len(ks) + 1]]
    else:
        fit = [np.nan] * len(ks)
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    ax.fill_between(ks, b25, b75, color=CAT[0], alpha=0.12, label="per-stock interquartile range")
    ax.plot(ks, y, color=CAT[0], marker="o", markeredgecolor=SURFACE, markeredgewidth=1.5, label="pooled panel (417 stocks)")
    ax.errorbar(ks, y, yerr=[np.maximum(np.array(y) - lo, 0), np.maximum(np.array(hi) - y, 0)], fmt="none", ecolor=CAT[0], elinewidth=1, capsize=2)
    if np.isfinite(fit).any():
        ax.plot(ks, fit, color=CAT[1], marker="s", markersize=5, markeredgecolor=SURFACE, markeredgewidth=1.2, label=f"fitted value + AR(1) mispricing model (h = {d['fit']['h_days']:.1f} d)")
    ax.axhline(1.0, color=AXIS, lw=0.8)
    ax.text(ks[-1], 1.005, "random walk = 1", ha="right", va="bottom", fontsize=7, color=INK2)
    ax.set_xscale("log"); ax.set_xticks(ks); ax.set_xticklabels([str(k) for k in ks])
    ax.set_xlabel("horizon k (trading days)"); ax.set_ylabel("variance ratio VR(k)")
    ax.set_title("Variance ratio of returns by horizon: the panel and the fitted model")
    ax.legend(loc="lower left"); tidy(ax)
    save(fig, "F05_variance_ratio_curve", "Phase 1: panel variance-ratio curve and the fitted model",
         ["v2_1/e1_2/vr_fit.json"], f"{d['n_stocks']} stocks, {d.get('T_days')} trading days each, stock-bootstrap intervals",
         "Points are the pooled variance ratios; the shaded band is the interquartile range across stocks.")


def F6_sweep_heatmap():
    """Phase 1: how much the price alone reveals about the mispricing across the sigma_V x s_x design, and the bound."""
    d = jsn("v2_1/e1_3/sweep.json")
    g = pd.DataFrame([{"sigma_V": r["sigma_V"], "df_V": r["df_V"], "s_x": r["s_x"],
                       "R2": (r["surrogate_level_free"].get("calm") or {}).get("R2", np.nan) if isinstance(r["surrogate_level_free"], dict) else np.nan,
                       "bound": (r["kalman"] or {}).get("window_avg", np.nan), "gap": r.get("gap_calm_surrogate_minus_bound_window", np.nan),
                       "n": r.get("n_seeds")} for r in d["grid"]])
    dfs = sorted(g["df_V"].astype(str).unique())
    fig, axes = plt.subplots(1, len(dfs) + 1, figsize=(3.4 * (len(dfs) + 1), 3.6), gridspec_kw={"wspace": 0.35})
    vmax = float(np.nanmax(g["R2"]))
    for ax, dfv in zip(axes[:-1], dfs):
        p = g[g["df_V"].astype(str) == dfv].pivot_table(index="sigma_V", columns="s_x", values="R2")
        im = ax.imshow(p.to_numpy(), cmap=ListedColormap(SEQ), vmin=0, vmax=vmax, aspect="auto", origin="lower")
        ax.set_xticks(range(p.shape[1])); ax.set_xticklabels([f"{c:g}" for c in p.columns], fontsize=7)
        ax.set_yticks(range(p.shape[0])); ax.set_yticklabels([f"{i:g}" for i in p.index], fontsize=7)
        for i in range(p.shape[0]):
            for j in range(p.shape[1]):
                v = p.to_numpy()[i, j]
                if np.isfinite(v):
                    ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6.5, color="white" if v > 0.55 * vmax else INK)
        ax.set_xlabel("s_x (sd of the mispricing)"); ax.set_ylabel("σ_V (daily sd of the value)")
        ax.set_title(f"calm level-free R²(x), value shocks {dfv}", fontsize=9); ax.tick_params(length=0)
    ax = axes[-1]
    p = g[g["df_V"].astype(str) == dfs[0]].pivot_table(index="sigma_V", columns="s_x", values="bound")
    im2 = ax.imshow(p.to_numpy(), cmap=ListedColormap(SEQ), vmin=0, vmax=vmax, aspect="auto", origin="lower")
    for i in range(p.shape[0]):
        for j in range(p.shape[1]):
            v = p.to_numpy()[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6.5, color="white" if v > 0.55 * vmax else INK)
    ax.set_xticks(range(p.shape[1])); ax.set_xticklabels([f"{c:g}" for c in p.columns], fontsize=7)
    ax.set_yticks(range(p.shape[0])); ax.set_yticklabels([f"{i:g}" for i in p.index], fontsize=7)
    ax.set_xlabel("s_x"); ax.set_title("Kalman bound (window average)", fontsize=9); ax.tick_params(length=0)
    fig.colorbar(im2, ax=axes, fraction=0.02, pad=0.02).set_label("R²", color=INK2)
    save(fig, "F06_phase1_sweep_bound", "Phase 1: sigma_V x s_x sweep against the Kalman bound",
         ["v2_1/e1_3/sweep.json"], f"{len(g)} grid points, {int(g['n'].iloc[0])} seeds each",
         "Same colour scale in every panel, so a cell darker than the bound panel's cell is a surrogate above the bound.")


# ================================================================================================== Phase 2
def F7_phase2_engines():
    """Phase 2: the three candidate mispricing engines against the panel moments and the held-out window."""
    d = jsn("v2_1/e2_4/decision.json")
    acc, held = d["acceptance"], d["heldout"]
    engines = ["ar1", "fw_v2", "fw_plus"]
    names = {"ar1": "AR(1)\n(adopted)", "fw_v2": "Franke-Westerhoff\nv2 form", "fw_plus": "Franke-Westerhoff\nplus (two noises)"}
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.6), gridspec_kw={"wspace": 0.45})
    ax = axes[0]
    J = [float(acc[e]["J"]) for e in engines]; crit = [float(acc[e]["chi2_crit_95"]) for e in engines]
    x = np.arange(3)
    b = ax.bar(x, J, width=0.5, color=[CAT[0] if e == d["decision"]["adopted"] else DEEMPH for e in engines])
    for xi, c in zip(x, crit):
        ax.hlines(c, xi - 0.3, xi + 0.3, color=INK2, lw=1.2)
    ax.text(0.03, 0.97, "black tick on each bar: χ² 95 % critical value", transform=ax.transAxes, fontsize=7, color=INK2, va="top")
    bar_ends(ax, b, fmt="{:.1f}", dy=1.5)
    ax.set_ylim(0, max(J) * 1.28)
    ax.set_xticks(x); ax.set_xticklabels([f"{names[e]}\ndf {acc[e]['df']}" for e in engines], fontsize=7)
    ax.set_ylabel("SMM distance J to 17 panel moments"); ax.set_title("(a) fit to the panel: none accepted (χ² test)", fontsize=9)
    tidy(ax)
    ax = axes[1]
    D = [float(held[e]["D_persistence"]) for e in engines]
    lo = [ci(held[e]["D_persistence_ci95"])[0] for e in engines]; hi = [ci(held[e]["D_persistence_ci95"])[1] for e in engines]
    for i, e in enumerate(engines):
        dot_ci(ax, [x[i]], [D[i]], [lo[i]], [hi[i]], CAT[0] if e == d["decision"]["adopted"] else DEEMPH)
        ax.text(x[i] + 0.12, D[i], f"{D[i]:.2f}", fontsize=7, color=INK2, va="center")
    ax.set_xticks(x); ax.set_xticklabels([names[e] for e in engines], fontsize=7)
    wt = held["ar1"]["window_test"]
    wt = f"{str(wt[0])[:4]} to {str(wt[1])[:4]}" if isinstance(wt, (list, tuple)) and len(wt) == 2 else str(wt)
    ax.set_ylabel("held-out distance on the persistence moments"); ax.set_title(f"(b) held out {wt}: none beats the AR(1)", fontsize=9)
    tidy(ax)
    save(fig, "F07_phase2_engines", "Phase 2: candidate engines, fit and held-out check",
         ["v2_1/e2_4/decision.json"], f"{acc['ar1']['n_paths']} simulated paths per evaluation; panel moments from 417 stocks",
         "Blue = the engine adopted (P2-4); the chi-square line is the acceptance threshold none of them clears.")


# ================================================================================================== Phase 3
def F8_garch_fits():
    """Phase 3: GJR-GARCH-t parameters fitted stock by stock, by sub-period."""
    t = csv("v2_1/e3_1/garch_fits.csv")
    t = t[(t["set"] == "A") & (t["converged"].astype(str) == "True")]
    periods = ["full", "2000-07", "2008-12", "2013-19", "2020-24"]
    params = [("alpha", "α (news)"), ("gamma", "γ (leverage)"), ("beta", "β (memory)"), ("nu", "ν (tail df)"), ("persistence", "α + γ/2 + β")]
    fig, axes = plt.subplots(1, 5, figsize=(11, 3.8), gridspec_kw={"wspace": 0.5})
    # the stock counts go in the title rather than beside each box, where they collided with the whiskers
    ns = [int(t[t.period == per][params[0][0]].notna().sum()) for per in periods]
    nlab = f"{ns[0]} stocks per period" if len(set(ns)) == 1 else f"{max(ns)} stocks per period ({min(ns)} in the last two)"
    for ax, (p, lab) in zip(axes, params):
        data = [t[t.period == per][p].dropna().to_numpy() for per in periods]
        ax.boxplot(data, widths=0.5, showfliers=False, patch_artist=True,
                   medianprops={"color": INK, "lw": 1.2}, whiskerprops={"color": CAT[0], "lw": 1}, capprops={"color": CAT[0], "lw": 1},
                   boxprops={"facecolor": CAT[0], "alpha": 0.25, "edgecolor": CAT[0]})
        ax.set_xticks(range(1, 6)); ax.set_xticklabels(periods, fontsize=7.5, rotation=45, ha="right", rotation_mode="anchor")
        ax.set_title(lab, fontsize=9.5); tidy(ax)
    fig.suptitle(f"GJR-GARCH-t parameters fitted per stock, by period ({nlab}; boxes: quartiles, whiskers: 1.5 IQR)", fontsize=10)
    save(fig, "F08_garch_fits_by_period", "Phase 3: per-stock GJR-GARCH-t fits by sub-period",
         ["v2_1/e3_1/garch_fits.csv"], f"{len(t)} converged fits over {t.ticker.nunique()} stocks",
         "The full-sample medians (α 0.027, γ 0.058, β 0.932) are the parameters in force; ν was set jointly with the jumps.")


def F9_event_multipliers():
    """Phase 3: the panel's variance multipliers per event phase, and what the closed-loop calibration realised."""
    cal = jsn("v2_1/e3_4/calibration.json"); ep = jsn("v2_1/e3_3/episodes.json")["multipliers"]
    phases = ["deterioration", "panic", "stabilisation", "mania", "blow-off", "post-top"]
    tgt = [float(cal["verify"][p]["target"]) for p in phases]
    lo = [ci(cal["verify"][p]["target_ci"])[0] for p in phases]; hi = [ci(cal["verify"][p]["target_ci"])[1] for p in phases]
    real = [float(cal["verify"][p]["realised"]) if cal["verify"][p].get("realised") is not None else np.nan for p in phases]
    inside = [bool(cal["verify"][p].get("inside_ci")) for p in phases]
    n = [cal["verify"][p].get("n") for p in phases]
    neps = [ep[f"m_{p}"].get("n_episodes") for p in phases]
    # one row per phase: the panel's interval as a bar, its median as a dot, the generator's realisation as a diamond
    y = np.arange(len(phases))[::-1]
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    for i in range(len(phases)):
        ax.plot([lo[i], hi[i]], [y[i], y[i]], color=CAT[0], lw=5, alpha=0.32, solid_capstyle="butt", zorder=1)
    ax.scatter(tgt, y, s=46, color=CAT[0], edgecolor=SURFACE, linewidth=1.2, zorder=3,
               label="panel target: median variance ratio, with its 95 % interval")
    ax.scatter(real, y, marker="D", s=52, color=[GOOD if i else CRITICAL for i in inside], edgecolor=SURFACE, linewidth=1.2, zorder=4,
               label="realised by the generator (green inside the interval, red outside)")
    for i in range(len(phases)):
        ax.text(lo[i] * 0.93, y[i], f"{tgt[i]:.2f}", ha="right", va="center", fontsize=8, color=CAT[0])
        if np.isfinite(real[i]):
            col = GOOD if inside[i] else CRITICAL
            if real[i] < lo[i]:                      # each label sits beside its own marker, on the outer side
                ax.text(real[i] * 0.93, y[i] - 0.28, f"{real[i]:.2f}", ha="center", va="center", fontsize=8, color=col)
            else:
                ax.text(max(hi[i], real[i]) * 1.07, y[i], f"{real[i]:.2f}", ha="left", va="center", fontsize=8, color=col)
    ax.axvline(1.0, color=AXIS, lw=0.9, zorder=0)
    ax.set_xscale("log"); ax.set_xlim(0.85, 16)
    ax.set_xticks([1, 1.5, 2, 3, 5, 7.5, 10]); ax.set_xticklabels(["1", "1.5", "2", "3", "5", "7.5", "10"])
    ax.set_yticks(y); ax.set_yticklabels([f"{p.capitalize()}\npanel n {neps[i]:,}; generator n {n[i]}" for i, p in enumerate(phases)], fontsize=8)
    ax.set_ylim(-0.7, len(phases) - 0.3)
    ax.set_xlabel("total-return variance relative to the stock's unconditional level (log scale; 1 = no elevation)")
    ax.set_title("Event-phase variance multipliers: panel target (417 stocks) and generator realisation")
    ax.legend(loc="lower right", fontsize=7.5); tidy(ax, ygrid=False, xgrid=True)
    save(fig, "F09_event_multipliers", "Phase 3: event-phase variance multipliers, target vs realised",
         ["v2_1/e3_4/calibration.json", "v2_1/e3_3/episodes.json"],
         "targets: 1,592 drawdown and 3,125 run-up episodes over 412 / 394 stocks; realised: 200 generator seeds per phase",
         "The blow-off multiplier was found to be dead code and post-top to be drift-dominated (Phase 3 §E3.4); Phase 4 owned both.")


def F10_ladder():
    """Phases 3 and 6: the calm level-free channel decomposed block by block against the Gaussian bound."""
    L = jsn("v2_1/e6_6/bound.json")["ladder"]["rungs"]
    lab = [f"{r['rung']}. {r['label']}" for r in L]
    r2 = [float(r["levelfree_R2"]) for r in L]; lo = [ci(r["ci95"])[0] for r in L]; hi = [ci(r["ci95"])[1] for r in L]
    bnd = [float(r["bound_window_avg"]) for r in L]; n = [r.get("n_paths") for r in L]
    y = np.arange(len(L))
    import textwrap
    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    dot_ci(ax, y, r2, lo, hi, CAT[0], horizontal=True, label="measured calm level-free R²(x), 95 % CI")
    ax.scatter(bnd, y, marker="|", s=260, color=CAT[1], linewidths=2.2, label="Gaussian Kalman bound at that rung's s_x", zorder=3)
    for i in range(len(L)):
        ax.text(max(hi[i], bnd[i]) + 0.012, y[i], f"{r2[i]:.3f}  (n {n[i]})", va="center", fontsize=7, color=INK2)
    ax.set_yticks(y); ax.set_yticklabels([textwrap.fill(s, 46) for s in lab], fontsize=7); ax.invert_yaxis()
    ax.set_xlabel("R² of a level-free surrogate for the mispricing on calm days")
    ax.set_title("Calm level-free channel by generator component, against the Gaussian bound", fontsize=9)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, fontsize=7); tidy(ax, ygrid=False, xgrid=True)
    save(fig, "F10_calm_channel_ladder", "Phases 3 and 6: the calm level-free channel ladder",
         ["v2_1/e6_6/bound.json", "v2_1/e3_8/decomposition.json"], "; ".join(f"rung {r['rung']}: {r.get('n_paths')} paths" for r in L),
         "Rung 1 is the bound's own model; the last rung is the deployed generator on the audit panel's calm rows.")


def F11_calm_trained_by_phase():
    """Phases 3 to 5: the calm-trained surrogate, level-free and with every field, at each hand-over."""
    h = jsn("v2_1/e5_after/calm_trained_phase5.json")["headline"]
    states = [("phase3", "after Phase 3"), ("phase4_postD14", "after Phase 4"), ("phase5", "after Phase 5")]
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.6), gridspec_kw={"wspace": 0.4})
    x = np.arange(len(states))
    for j, (key, lab, col) in enumerate((("calm_trained_levelfree", "level-free (price shape only)", CAT[0]), ("calm_trained_full", "every shown field", CAT[1]))):
        r2 = [float(h[s][key]["R2"]) for s, _ in states]; lo = [float(h[s][key]["R2_lo"]) for s, _ in states]; hi = [float(h[s][key]["R2_hi"]) for s, _ in states]
        sa = [float(h[s][key]["sign_acc_resolvable"]) for s, _ in states]; slo = [float(h[s][key]["sign_lo"]) for s, _ in states]; shi = [float(h[s][key]["sign_hi"]) for s, _ in states]
        dot_ci(axes[0], x + (j - 0.5) * 0.16, r2, lo, hi, col, label=lab)
        dot_ci(axes[1], x + (j - 0.5) * 0.16, sa, slo, shi, col, label=lab)
        for i in range(len(states)):
            axes[0].text(x[i] + (j - 0.5) * 0.16, hi[i] + 0.012, f"{r2[i]:.2f}", ha="center", fontsize=7, color=INK2)
            axes[1].text(x[i] + (j - 0.5) * 0.16, shi[i] + 0.006, f"{sa[i]:.2f}", ha="center", fontsize=7, color=INK2)
    for ax, ylab, ttl in zip(axes, ("R² for x, calm rows, calm-trained", "sign accuracy on resolvable steps"), ("(a) R² for x on calm rows, calm-trained", "(b) sign accuracy on resolvable steps")):
        ax.set_xticks(x); ax.set_xticklabels([l for _, l in states], fontsize=8); ax.set_ylabel(ylab); ax.set_title(ttl); tidy(ax)
    axes[1].axhline(0.5, color=AXIS, lw=0.8); axes[1].text(x[-1] + 0.25, 0.502, "chance", fontsize=7, color=INK2, va="bottom", ha="right")
    axes[0].legend(loc="upper right")
    n = h["phase5"]["calm_trained_levelfree"]
    save(fig, "F11_calm_trained_by_phase", "Phases 3 to 5: the calm-trained surrogate at each hand-over",
         ["v2_1/e5_after/calm_trained_phase5.json"], f"{n['n_paths']} paths, {n['n_rows']:,} calm rows, {n['n_resolvable']:,} resolvable steps (Phase 5 state)",
         "Calm-trained means the surrogate is fitted on calm rows only, the reading the Phase 3 review required.")


def F12_discrimination_by_handover():
    """Phases 2 to 5: does the benchmark still separate an informed policy from a trivial one, at each hand-over."""
    d = jsn("v2_1/e5_l5/discrimination.json")["states"]
    states = [("phase2_after", "P2"), ("phase3_after", "P3"), ("phase4_after", "P4"), ("phase5_after", "P5")]
    scenarios = ["flat", "bull_trap", "crash", "sustained_bull"]
    policies = [("mandate_conditional_oracle", "oracle (knows V)", CAT[0]), ("L5_full", "L5 surrogate, every field", CAT[1]),
                ("L5_price_only", "L5 surrogate, price only", CAT[2]), ("constant_mix", "constant mix (trivial)", CAT[3]), ("always_hold", "always hold (trivial)", CAT[4])]
    fig, axes = plt.subplots(2, 2, figsize=(9.2, 6.4), gridspec_kw={"wspace": 0.3, "hspace": 0.45})
    x = np.arange(len(states))
    for ax, sc in zip(axes.ravel(), scenarios):
        for j, (pk, lab, col) in enumerate(policies):
            m, lo, hi = [], [], []
            for sk, _ in states:
                pp = d[sk]["scenarios"][sc]["per_policy"].get(pk, {})
                m.append(float(pp.get("mean", np.nan))); l_, h_ = ci(pp.get("ci95")); lo.append(l_); hi.append(h_)
            off = (j - 2) * 0.13
            dot_ci(ax, x + off, m, lo, hi, col, ms=5, label=lab if sc == "flat" else None)
        ax.set_xticks(x); ax.set_xticklabels([l for _, l in states]); ax.set_title(f"{sc.replace('_', ' ')}  (n = {d['phase5_after']['scenarios'][sc]['n_cells']} cells per state)", fontsize=9)
        ax.set_ylabel("mandate-conditional regret at θ = 0.05"); tidy(ax)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=5, fontsize=7, bbox_to_anchor=(0.5, -0.01))
    fig.suptitle("Policy spread at each hand-over: regret of the oracle, the surrogates and the trivial policies", fontsize=10)
    save(fig, "F12_discrimination_by_handover", "Phases 2 to 5: policy spread by hand-over", ["v2_1/e5_l5/discrimination.json"],
         f"{d['phase5_after']['n_seeds']} seeds x 3 personas per scenario and state", "Lower regret is better; intervals are seed-cluster bootstrap 95 %.")


# ================================================================================================== Phase 4
def F13_crash_depth_duration():
    """Phase 4: crash depth against duration, the real panel beside the v2 and v2.1 generator schedules."""
    dd = csv("v2_1/e4_1/dd30.csv"); v2 = csv("v2_1/e4_2/paths_v2.csv"); v21 = csv("v2_1/e4_2/paths_v21_empirical.csv")
    box = jsn("v2_1/e4_19/criteria.json")["panel_box"]
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    ax.scatter(dd["duration"], dd["depth"], s=9, color=CAT[0], alpha=0.35, linewidths=0, label=f"real drawdown episodes (n {len(dd):,})")
    for t, lab, col, mk in ((v2, f"generator, v2 schedule (n {v2['depth'].notna().sum()})", CAT[1], "s"), (v21, f"generator, v2.1 empirical schedule (n {v21['depth'].notna().sum()})", CAT[2], "^")):
        t = t.dropna(subset=["depth", "duration"])
        ax.scatter(t["duration"], t["depth"], s=14, color=col, alpha=0.6, marker=mk, linewidths=0, label=lab)
    dlo, dhi = ci(box["depth"]); ulo, uhi = ci(box["duration"])
    ax.add_patch(plt.Rectangle((ulo, dlo), uhi - ulo, dhi - dlo, fill=False, edgecolor=INK, lw=1.2))
    ax.text(uhi, dhi, " Panel box: P10 to P90 on both axes", fontsize=8.5, color=INK, va="bottom", fontweight="bold")
    ax.set_xscale("log"); ax.set_xlabel("peak-to-trough duration (trading days, log)"); ax.set_ylabel("depth (trough / peak minus 1)")
    ax.set_title("Crash depth against duration: 417 stocks and the generator")
    ax.legend(loc="lower left", fontsize=7); tidy(ax, xgrid=True)
    save(fig, "F13_crash_depth_duration", "Phase 4: crash depth vs duration, panel and generator",
         ["v2_1/e4_1/dd30.csv", "v2_1/e4_2/paths_v2.csv", "v2_1/e4_2/paths_v21_empirical.csv", "v2_1/e4_19/criteria.json"],
         f"panel {len(dd):,} episodes; generator 500 seeds per schedule", "The box is the panel's P10 to P90 in depth and duration, the target the schedules were judged against.")


def F14_dynamics_stop():
    """Phase 4: every event-dynamics formulation against the coverage rule; the D5 stop."""
    c = jsn("v2_1/e4_19/criteria.json")["arms"]; dyn = jsn("v2_1/e4_6/dynamics.json")["decision"]
    arms = list(c.keys())
    cov = [float(c[a]["coverage"]) for a in arms]; clo = [ci(c[a]["coverage_ci95"])[0] for a in arms]; chi = [ci(c[a]["coverage_ci95"])[1] for a in arms]
    ss = [float(c[a]["script_share_median"]) for a in arms]; slo = [ci(c[a].get("script_share_ci95"))[0] for a in arms]; shi = [ci(c[a].get("script_share_ci95"))[1] for a in arms]
    x = np.arange(len(arms))
    nice = {"A_lam0.02": "A\ngain 0.02", "A_lam0.05": "A\ngain 0.05", "A_lam0.1": "A\ngain 0.10", "A_lam0.25": "A\ngain 0.25",
            "B_shifted_pstar": "B\nshifted\ntarget", "C_scripted_no_feedback": "C\nfully\nscripted", "D_unscripted_regime": "D\nunscripted\nswitch"}
    labs = [nice.get(a, a.replace("_", "\n")) for a in arms]
    cols = [CAT[0] if a.startswith("A_") else CAT[3] for a in arms]      # the incumbent family apart from the three alternatives
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.2), gridspec_kw={"wspace": 0.3})
    ax = axes[0]
    for i in range(len(arms)):
        dot_ci(ax, [x[i]], [cov[i]], [clo[i]], [chi[i]], cols[i])
    ceil = dyn.get("ceiling", {})
    reg = 0.70                                                          # the registered coverage threshold
    ax.axhline(reg, color=CRITICAL, lw=1.2, ls=(0, (5, 3)))
    ax.text(x[0] - 0.4, reg + 0.006, f"registered rule: at least {reg:.2f}", fontsize=7.5, color=CRITICAL, va="bottom", ha="left")
    if "panel_self_coverage" in ceil:
        psc = float(ceil["panel_self_coverage"])
        ax.axhline(psc, color=CAT[1], lw=1.2)
        ax.text(x[0] - 0.4, psc + 0.006, f"what the panel scores on itself: {psc:.2f}", fontsize=7.5, color=CAT[1], va="bottom", ha="left")
    ax.set_ylim(min(clo) - 0.04, reg + 0.055)
    ax.set_xlim(-0.75, len(arms) - 0.25)
    ax.set_xticks(x); ax.set_xticklabels(labs, fontsize=7.5)
    ax.set_ylabel("share of generator crashes inside the panel box")
    ax.set_title("(a) coverage of the panel's depth and duration box", fontsize=9.5); tidy(ax)
    ax = axes[1]
    for i in range(len(arms)):
        dot_ci(ax, [x[i]], [ss[i]], [slo[i]], [shi[i]], cols[i])
    ax.set_xlim(-0.75, len(arms) - 0.25)
    ax.set_xticks(x); ax.set_xticklabels(labs, fontsize=7.5)
    ax.set_ylabel("median share of the event's move that is scripted")
    ax.set_title("(b) how much of the move the script writes directly", fontsize=9.5); tidy(ax)
    hs = [plt.Line2D([], [], color=CAT[0], marker="o", ls="", markersize=6), plt.Line2D([], [], color=CAT[3], marker="o", ls="", markersize=6)]
    fig.legend(hs, ["Formulation A, the incumbent, at four gains", "Formulations B, C and D"],
               loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=2, fontsize=8)
    save(fig, "F14_event_dynamics_stop", "Phase 4: event-dynamics formulations against the coverage rule (the D5 stop)",
         ["v2_1/e4_19/criteria.json", "v2_1/e4_6/dynamics.json"], "1,000 generator seeds per formulation",
         f"Decision status recorded in the file: {dyn.get('status', '')}. Eligible formulations: {dyn.get('eligible', [])}.")


# ================================================================================================== Phase 5
def F15_observables_fits():
    """Phase 5: the observable processes fitted to data, beside the values v2 had assumed."""
    mult = jsn("v2_1/e5_1/multiple.json"); div = jsn("v2_1/e5_3/dividends.json"); vol = jsn("v2_1/e5_6/volume.json"); eps = jsn("v2_1/e5_2/eps.json")
    fig, axes = plt.subplots(1, 4, figsize=(11.5, 3.8), gridspec_kw={"wspace": 0.62})
    # (a) P/E cross-section
    ax = axes[0]
    qs = ["p10", "p25", "p50", "p75", "p90"]
    v = [num(mult["cross_section_pooled"][q]) for q in qs]; lo = [ci(mult["cross_section_pooled"][q].get("ci95"))[0] for q in qs]; hi = [ci(mult["cross_section_pooled"][q].get("ci95"))[1] for q in qs]
    dot_ci(ax, range(5), v, lo, hi, CAT[0], label="panel percentiles (95 % CI)")
    kr = ci(mult["v2_incumbent"]["k_range"])
    ax.axhspan(kr[0], kr[1], color=CAT[1], alpha=0.18, label=f"v2 design range [{kr[0]:g}, {kr[1]:g}]")
    ax.set_xticks(range(5)); ax.set_xticklabels([q.upper() for q in qs], fontsize=7.5); ax.set_ylabel("trailing P/E")
    ax.set_title("(a) the earnings multiple", fontsize=9.5); ax.set_ylim(0, max(hi) * 1.18); tidy(ax)
    # (b) payout ratio
    ax = axes[1]
    pm = num(div["payout"]["median"]); piqr = ci(div["payout"].get("iqr")); inc = num(div["payout"].get("v2_incumbent"))
    dot_ci(ax, [0], [pm], [piqr[0]], [piqr[1]], CAT[0], label="panel median (IQR)")
    if np.isfinite(inc):
        ax.scatter([0.35], [inc], marker="D", color=CAT[1], s=40, zorder=3, label="v2 assumed")
        ax.text(0.42, inc, f"{inc:.2f}", fontsize=7, color=INK2, va="center")
    ax.text(0.07, pm, f"{pm:.3f}", fontsize=7, color=INK2, va="center")
    ax.set_xlim(-0.5, 0.9); ax.set_xticks([]); ax.set_ylabel("dividend payout ratio")
    ax.set_title(f"(b) payout ({int(div['payout'].get('n_stock_years', 0)):,} stock-years)", fontsize=9.5); tidy(ax)
    # (c) volume
    ax = axes[2]
    keys = [("rho_v", "rho"), ("beta_absr_per_sd_z", "b_absr"), ("sd_e", "sd_e")]
    v = [num(vol["design_A"][k]) for k, _ in keys]; lo = [ci(vol["design_A"][k].get("ci95"))[0] for k, _ in keys]; hi = [ci(vol["design_A"][k].get("ci95"))[1] for k, _ in keys]
    inc = [num(vol["v2_incumbent"].get(i2)) for _, i2 in keys]
    dot_ci(ax, range(3), v, lo, hi, CAT[0], label="panel (95 % CI)")
    ax.scatter(np.arange(3) + 0.25, inc, marker="D", color=CAT[1], s=40, zorder=3, label="v2 assumed")
    ax.set_xticks(range(3)); ax.set_xticklabels(["AR(1) ρ", "β on |return|", "innovation sd"], fontsize=7.5,
                                                rotation=20, ha="right", rotation_mode="anchor")
    ax.set_title(f"(c) Log-volume process ({vol['design_A']['rho_v'].get('n')} stocks)", fontsize=9.5)
    ax.set_xlim(-0.5, 2.75); ax.set_ylim(min(lo) - 0.04, max(max(hi), max(inc)) + 0.06); tidy(ax)
    # (d) announcement lag
    ax = axes[3]
    a8 = eps["announcement_lags"]["announcement_8k"]
    v = [num(a8["p10_td"]), num(a8["p50_td"]), num(a8["p90_td"])]
    ax.plot([0, 1, 2], v, color=CAT[0], marker="o", markeredgecolor=SURFACE, markeredgewidth=1.5, label="8-K announcement lag, panel")
    oj = json.load(open(os.path.join(ROOT, "envs", "v2", "params", "observables.json"), encoding="utf-8"))
    lag_v2 = oj.get("eps", {}).get("v2_before", {}).get("lag")           # the v2 design value the fit replaced
    if isinstance(lag_v2, (list, tuple)) and len(lag_v2) == 2:
        ax.axhspan(float(lag_v2[0]), float(lag_v2[1]), color=CAT[1], alpha=0.18, label=f"v2 assumed uniform [{lag_v2[0]:g}, {lag_v2[1]:g}]")
        ax.set_ylim(8, max(38, float(lag_v2[1]) + 3))
    for i, vv in enumerate(v):
        ax.text(i, vv + 0.6, f"{vv:g}", ha="center", fontsize=7, color=INK2)
    ax.set_xticks([0, 1, 2]); ax.set_xticklabels(["P10", "P50", "P90"], fontsize=7.5); ax.set_ylabel("trading days after quarter end")
    ax.set_title(f"(d) earnings announcement lag ({int(a8.get('n_filings', 0)):,} filings)", fontsize=9.5)
    ax.set_xlim(-0.35, 2.35); tidy(ax)
    # one legend for the four panels: what the data give against what v2 had assumed
    hs = [plt.Line2D([], [], color=CAT[0], marker="o", ls="-", markersize=6, markeredgecolor=SURFACE, markeredgewidth=1.2),
          plt.Line2D([], [], color=CAT[1], marker="D", ls="", markersize=6),
          plt.Rectangle((0, 0), 1, 1, color=CAT[1], alpha=0.18)]
    fig.legend(hs, ["What the data give: the fitted value with its 95 % interval or IQR",
                    "What v2 assumed: a single value", "What v2 assumed: a range"],
               loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=3, fontsize=8)
    save(fig, "F15_observables_fits", "Phase 5: observable processes fitted to data vs the v2 assumptions",
         ["v2_1/e5_1/multiple.json", "v2_1/e5_3/dividends.json", "v2_1/e5_6/volume.json", "v2_1/e5_2/eps.json"],
         "P/E: 411 tickers monthly 2009 to 2024; payout: EDGAR stock-years; volume: 417 stocks; lags: 8-K filings",
         "Orange marks and bands are what v2 had assumed (DESIGN); blue is what the data give (FIT).")


def F16_onset_heatmap():
    """Phase 5: does any shown field announce a phase change before the price does (the onset audit)."""
    d = jsn("v2_1/e5_7c/final/onset.json")["transitions"]
    trans = list(d.keys()); fields = sorted({f for t in trans for f in d[t]["fields"]})
    M = np.full((len(fields), len(trans)), np.nan); fail = np.zeros_like(M, dtype=bool)
    for j, t in enumerate(trans):
        for i, f in enumerate(fields):
            r = d[t]["fields"].get(f)
            if r:
                M[i, j] = float(r.get("delta_auc", np.nan)); fail[i, j] = (r.get("pass") is False)
    vmax = float(np.nanmax(np.abs(M)))
    fig, ax = plt.subplots(figsize=(7.4, 6.0))
    cmap = ListedColormap(["#0d366b", "#256abf", "#6da7ec", "#b7d3f6", "#f0efec", "#f3b7b6", "#e66767", "#d03b3b", "#8f1f1f"])
    im = ax.imshow(M, cmap=cmap, vmin=-vmax, vmax=vmax, aspect="auto")
    for i in range(len(fields)):
        for j in range(len(trans)):
            if np.isfinite(M[i, j]):
                ax.text(j, i, f"{M[i, j]:+.3f}" + (" †" if fail[i, j] else ""), ha="center", va="center", fontsize=6.5, color="white" if abs(M[i, j]) > 0.55 * vmax else INK)
    ax.set_xticks(range(len(trans))); ax.set_xticklabels([t.replace(":", "\n").replace("->", "\nto ") for t in trans], fontsize=6.5)
    ax.set_yticks(range(len(fields))); ax.set_yticklabels(fields, fontsize=7); ax.tick_params(length=0); ax._keep_tick_case = True
    ax.set_title("Onset audit: a field's AUC for the next five days minus the best price-based reference\n(negative: the field announces nothing the price did not; †: fails the registered null)", fontsize=9)
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02).set_label("ΔAUC", color=INK2)
    n = d[trans[0]].get("n_paths_with_transition")
    save(fig, "F16_onset_audit", "Phase 5: onset-detection audit by field and transition", ["v2_1/e5_7c/final/onset.json"],
         f"paths with the transition: {', '.join(str(d[t].get('n_paths_with_transition')) for t in trans)}; permutation null of 500 shifts",
         "Diverging scale: blue below zero, red above, grey at zero.")


REGISTRY.update({"F4": F4_phase1_estimators, "F5": F5_vr_curve, "F6": F6_sweep_heatmap, "F7": F7_phase2_engines,
                 "F8": F8_garch_fits, "F9": F9_event_multipliers, "F10": F10_ladder, "F11": F11_calm_trained_by_phase,
                 "F12": F12_discrimination_by_handover, "F13": F13_crash_depth_duration, "F14": F14_dynamics_stop,
                 "F15": F15_observables_fits, "F16": F16_onset_heatmap})


# ================================================================================================== Phase 6
def _interval_str(v):
    """[lo, hi] stored as a JSON string, a list, or two columns."""
    if isinstance(v, str):
        try:
            return ci(json.loads(v))
        except Exception:  # noqa: BLE001
            return (np.nan, np.nan)
    return ci(v)


def F17_reference_ranges():
    """Phase 6: the generator's P10 to P90 range of every statistic against the real panel's, standardised per row."""
    t = csv("v2_1/e6_after_checklist_reference.csv")
    t = t[(t["population"].astype(str) == "all") & (t["reference"].astype(str) == "all")].copy()
    if "is_main" in t and t["is_main"].astype(str).eq("True").any():
        t = t[t["is_main"].astype(str) == "True"]
    t = t.sort_values(["item", "statistic"]).reset_index(drop=True)
    w = (t["ref_p90"] - t["ref_p10"]).replace(0, np.nan)
    z = lambda col: (t[col] - t["ref_p50"]) / w  # noqa: E731
    y = np.arange(len(t))
    fig, ax = plt.subplots(figsize=(8.6, 0.32 * len(t) + 1.6))
    for i in range(len(t)):
        ax.plot([z("ref_p10")[i], z("ref_p90")[i]], [y[i] + 0.18, y[i] + 0.18], color=DEEMPH, lw=5, solid_capstyle="butt")
        ax.plot([z("gen_p10")[i], z("gen_p90")[i]], [y[i] - 0.18, y[i] - 0.18], color=CAT[0], lw=5, solid_capstyle="butt")
        ax.scatter([z("gen_p50")[i]], [y[i] - 0.18], color=INK, s=14, zorder=3)
        verdict = f"B {'pass' if str(t['B_pass'][i]) == 'True' else 'fail'}   C {'pass' if str(t['C_pass'][i]) == 'True' else 'fail'}"
        ax.text(2.55, y[i], verdict, va="center", fontsize=6.5, color=INK2)
    ax.axvline(0, color=AXIS, lw=0.8)
    ax.set_yticks(y); ax.set_yticklabels([f"{int(a)}. {b}" for a, b in zip(t['item'], t['statistic'])], fontsize=7); ax.invert_yaxis()
    ax.set_xlim(-2.5, 3.6); ax.set_xlabel("position relative to the real panel: (value minus panel median) / (panel P90 minus P10)")
    ax.set_title(f"Generator P10 to P90 (blue, median dot) against the real panel's P10 to P90 (grey), per statistic\n"
                 f"generator n = {int(t['n_gen'].iloc[0]):,} paths; panel n = {int(t['n_ref'].iloc[0]):,} 200-day windows of 417 stocks", fontsize=9)
    ax.plot([], [], color=DEEMPH, lw=5, label="real panel P10 to P90"); ax.plot([], [], color=CAT[0], lw=5, label="generator P10 to P90 (dot = median)")
    ax.text(2.55, -1.0, "verdicts: B (KS distance), C (share in band)", fontsize=6.5, color=INK2, va="center")
    ax.legend(loc="upper left", fontsize=7); tidy(ax, ygrid=False, xgrid=True)
    save(fig, "F17_reference_distributions", "Phase 6: generator vs real-panel reference distributions", ["v2_1/e6_after_checklist_reference.csv"],
         f"generator {int(t['n_gen'].iloc[0]):,} paths (500 seeds per scenario); reference {int(t['n_ref'].iloc[0]):,} windows",
         "B is the distributional criterion (KS distance against D0 = 0.10), C the band criterion (share inside P10 to P90 at least 0.80).")


def F18_gate_16a():
    """Phase 6 checkpoint 16A, restated under the Phase 7 metrics: mandate-conditional regret per policy and scenario."""
    t = csv("v2_1/e7_16a/restate.csv")
    t = t[(t["metric"] == "mcr") & (np.isclose(t["theta"].astype(float), 0.05))]
    want = [("oracle", "oracle (knows V)", CAT[0]), ("L5_full", "L5 surrogate, every field", CAT[1]), ("L5_level_free", "L5 surrogate, level-free", CAT[1]),
            ("L5_price", "L5 surrogate, price only", CAT[1]), ("p_sma50", "rule: price vs 50-day average", CAT[2]), ("band_hi", "constant: band high", DEEMPH),
            ("band_lo", "constant: band low", DEEMPH), ("constant_mix", "constant mix", DEEMPH), ("always_hold", "always hold", DEEMPH), ("random", "random", DEEMPH)]
    scenarios = ["flat", "bull_trap", "crash", "sustained_bull"]
    fig, axes = plt.subplots(1, 4, figsize=(12.5, 4.2), sharey=True, gridspec_kw={"wspace": 0.12})
    rows_used = []
    for ax, sc in zip(axes, scenarios):
        sub = t[t["scenario"] == sc]
        labels, vals, los, his, cols = [], [], [], [], []
        for key, lab, col in want:
            m = sub[sub["policy"].astype(str).str.contains(key, regex=False)]
            if len(m) == 0:
                continue
            m = m.sort_values("policy").iloc[0]
            labels.append(lab); vals.append(float(m["mean"])); los.append(float(m["lo"])); his.append(float(m["hi"])); cols.append(col); rows_used.append(str(m["policy"]))
        y = np.arange(len(labels))
        for i in range(len(labels)):
            dot_ci(ax, [y[i]], [vals[i]], [los[i]], [his[i]], cols[i], horizontal=True, ms=6)
        ax.set_yticks(y); ax.set_yticklabels(labels); ax.invert_yaxis()
        ax.set_title(sc.replace("_", " ")); tidy(ax, ygrid=False, xgrid=True)
    n = int(t["n_runs"].max())
    fig.suptitle("Checkpoint 16A, gate G1: mandate-conditional regret by policy and scenario", y=1.04)
    fig.supxlabel("Mandate-conditional regret at θ = 0.05")      # one shared axis label instead of four overlapping ones
    save(fig, "F18_checkpoint_16A", "Phase 6 checkpoint 16A restated under Phase 7 metrics", ["v2_1/e7_16a/restate.csv"],
         f"up to {n} runs per policy and scenario (100 scored seeds x 3 personas)", f"policies matched: {sorted(set(rows_used))}")


# ================================================================================================== Phase 7
def F19_theta():
    """Phase 7: how the surrogate's sign accuracy and the share of resolvable days move with the resolvability threshold theta."""
    t = csv("v2_1/e7_1/theta_info.csv")
    scope = "pooled" if (t["scope"] == "pooled").any() else str(t["scope"].iloc[0])
    sub = t[(t["scope"] == scope) & (t["population"].astype(str) == "all")]
    tv = jsn("v2_1/e7_1/theta_cost_var.json")
    th_cost = num(tv.get("theta_cost", {})) if isinstance(tv.get("theta_cost"), dict) else num(tv.get("theta_cost"))
    th_var = num(tv.get("theta_var", {})) if isinstance(tv.get("theta_var"), dict) else num(tv.get("theta_var"))
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), gridspec_kw={"wspace": 0.35})
    for j, (fs, lab, col) in enumerate((("full", "every shown field", CAT[0]), ("price_only", "price fields only", CAT[1]))):
        s = sub[sub["feature_set"] == fs].sort_values("theta")
        if len(s) == 0:
            continue
        axes[0].plot(s["theta"], s["sign_acc"], color=col, marker="o", markersize=4, markeredgecolor=SURFACE, label=lab)
        axes[0].fill_between(s["theta"], s["sign_lo"], s["sign_hi"], color=col, alpha=0.12)
        if j == 0:
            axes[1].plot(s["theta"], s["coverage"], color=CAT[0], marker="o", markersize=4, markeredgecolor=SURFACE)
    for ax in axes:
        ax.set_xscale("log"); ax.set_xlabel("threshold θ on |x| for a day to count as resolvable (log)")
        for v, lab in ((th_cost, "θ_cost"), (th_var, "θ_var")):
            if np.isfinite(v):
                ax.axvline(v, color=INK2, lw=0.9); ax.text(v, ax.get_ylim()[1] if ax.get_ylim()[1] < 1.2 else 1.0, f" {lab} = {v:.3g}", fontsize=7, color=INK2, va="top")
        tidy(ax)
    axes[0].axhline(0.5, color=AXIS, lw=0.8); axes[0].set_ylabel("sign accuracy of the level-free surrogate"); axes[0].set_title("(a) sign accuracy of the surrogate against θ", fontsize=9); axes[0].legend(loc="lower right")
    axes[1].set_ylabel("share of days that are resolvable"); axes[1].set_title("(b) share of resolvable days against θ", fontsize=9)
    save(fig, "F19_theta_tradeoff", "Phase 7: sign accuracy and coverage against theta", ["v2_1/e7_1/theta_info.csv", "v2_1/e7_1/theta_cost_var.json"],
         f"scope {scope}: {int(sub['n_paths'].max()):,} paths, {int(sub['n_rows'].max()):,} rows", "The two vertical lines are the derived thresholds; θ = 0.05 is the value in force.")


def F20_metric_matrix_sweeps():
    """Phase 7: are the metrics measuring different things (the correlation matrix), and do they move as intended (the scripted sweeps)."""
    m = csv("v2_1/e7_8/matrix.csv"); sw = csv("v2_1/e7_8/sweeps.csv")
    scoring = "A_decomposition" if (m["scoring"] == "A_decomposition").any() else str(m["scoring"].iloc[0])
    mm = m[m["scoring"] == scoring]
    names = sorted(set(mm["a"]) | set(mm["b"]))
    shown = {"band_mas": "band-MAS", "mcr": "MCR", "mcr_B": "B (band violation)", "mcr_D": "D (direction)",
             "mdd_pct": "Drawdown", "return_pct": "Return", "turnover": "Turnover"}   # the document's names for the metrics
    P = pd.DataFrame(np.nan, index=names, columns=names)
    for _, r in mm.iterrows():
        P.loc[r["a"], r["b"]] = float(r["abs_r"]); P.loc[r["b"], r["a"]] = float(r["abs_r"])
    fig = plt.figure(figsize=(12, 4.6)); gs = fig.add_gridspec(1, 3, width_ratios=[1.25, 1, 1], wspace=0.45)
    ax = fig.add_subplot(gs[0, 0])
    im = ax.imshow(P.to_numpy(dtype=float), cmap=ListedColormap(SEQ), vmin=0, vmax=1, aspect="auto")
    for i in range(len(names)):
        for j in range(len(names)):
            v = P.to_numpy(dtype=float)[i, j]
            if np.isfinite(v):
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", color="white" if v > 0.55 else INK)
    disp = [shown.get(x, x) for x in names]
    ax.set_xticks(range(len(names))); ax.set_xticklabels(disp, rotation=40, ha="right", rotation_mode="anchor")
    ax.set_yticks(range(len(names))); ax.set_yticklabels(disp)
    ax.tick_params(length=0); ax.set_title(f"(a) |r| between metrics across {int(mm['n_cells'].max())} cells")
    fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    s = sw[(sw["scoring"] == scoring) & (np.isclose(sw["theta"].astype(float), 0.05))]
    fams = sorted(s["family"].unique())[:2]
    for k, fam in enumerate(fams):
        ax = fig.add_subplot(gs[0, 1 + k]); ss = s[s["family"] == fam]
        mets = [x for x in ["band_mas", "mcr", "mcr_B", "mcr_D"] if x in set(ss["metric"])][:3] or sorted(ss["metric"].unique())[:3]
        for j, met in enumerate(mets):
            q = ss[ss["metric"] == met].sort_values("swept")
            ax.plot(q["swept"], q["mean"], color=CAT[j], marker="o", markersize=4, markeredgecolor=SURFACE, label=shown.get(met, met))
            ax.fill_between(q["swept"], q["lo"], q["hi"], color=CAT[j], alpha=0.12)
        ax.set_title(f"(b{k + 1}) scripted sweep: {fam}"); ax.set_xlabel("swept parameter of the scripted policy"); ax.legend(); tidy(ax)
    fig.suptitle("Construct validity of the scores")
    save(fig, "F20_metric_matrix_and_sweeps", "Phase 7: metric correlation matrix and scripted sweeps", ["v2_1/e7_8/matrix.csv", "v2_1/e7_8/sweeps.csv"],
         f"{int(mm['n_cells'].max())} cells for the matrix; sweeps: n_cells {int(s['n_cells'].max())}, n_seeds {int(s['n_seeds'].max())}", f"scoring {scoring}")


# ================================================================================================== Phase 8
def F21_variance_components():
    """Phase 8 variance pilot: the seed-level spread of the memory minus static difference per model and metric."""
    t = csv("v2_1/e8_5/components.csv")
    mets = [m for m in ["band_mas", "v21_mcr_0.05", "v21_mcr_B_0.05", "v21_mcr_D_0.05", "v21_mcr_0.002"] if m in set(t["metric"])]
    models = list(dict.fromkeys(t["Model"]))
    x = np.arange(len(mets)); w = 0.8 / max(len(models), 1)
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.8), gridspec_kw={"wspace": 0.35})
    for j, mod in enumerate(models):
        s = t[t["Model"] == mod].set_index("metric").reindex(mets)
        b = axes[0].bar(x + (j - (len(models) - 1) / 2) * w, s["sigma_d_R1"], width=w * 0.9, color=CAT[j], label=f"{mod} (n pairs {int(s['n_pairs'].max())})")
        axes[0].scatter(x + (j - (len(models) - 1) / 2) * w, s["sigma_d_R1_mls90"], marker="_", s=180, color=INK, linewidths=1.6, zorder=3)
        axes[1].bar(x + (j - (len(models) - 1) / 2) * w, s["share_int_R1"], width=w * 0.9, color=CAT[j])
    axes[0].scatter([], [], marker="_", s=180, color=INK, label="one-sided 90 % upper limit")
    shown = {"band_mas": "band-MAS", "v21_mcr_0.05": "MCR\nat θ = 0.05", "v21_mcr_B_0.05": "B term\nat θ = 0.05",
             "v21_mcr_D_0.05": "D term\nat θ = 0.05", "v21_mcr_0.002": "MCR\nat θ = 0.002"}    # the document's metric names
    tick = [shown.get(m, m) for m in mets]
    axes[0].set_xticks(x); axes[0].set_xticklabels(tick, fontsize=7.5); axes[0].set_ylabel("σ_d at R = 1 (sd of the paired difference)")
    axes[0].set_ylim(0, float(t[t["metric"].isin(mets)]["sigma_d_R1_mls90"].max()) * 1.55)
    axes[0].set_title("(a) sd of the seed-level memory minus static difference", fontsize=9)
    axes[0].legend(fontsize=7, loc="upper center", ncol=2); tidy(axes[0])
    axes[1].set_xticks(x); axes[1].set_xticklabels(tick, fontsize=7.5); axes[1].set_ylabel("share of that variance from seed x arm"); axes[1].set_ylim(0, 1)
    axes[1].set_title("(b) share of that variance from seed by arm interaction", fontsize=9); tidy(axes[1])
    save(fig, "F21_variance_components", "Phase 8: variance components per model and metric", ["v2_1/e8_5/components.csv"],
         "; ".join(f"{m}: {int(t[t.Model == m]['n_pairs'].max())} pairs" for m in models), "Flash ran thinking off; GPT-5 mini at temperature 1 on one scenario.")


def F26_estimator_size():
    """Phase 8: size of the four contrast estimators on simulated data with a known answer."""
    t = csv("v2_1/e8_3/mixed.csv")
    t = t[(t["R"] == 1) & (np.isclose(t["rho"].astype(float), 0.0))]
    size = t[np.isclose(t["beta"].astype(float), 0.0)].copy(); power = t[t["beta"].astype(float) > 0].copy()
    ests = [("e0", "E0 nested (v2)", DEEMPH), ("e1", "E1 crossed mixed model", CAT[0]), ("e2", "E2 two-way cluster bootstrap", CAT[1]), ("e3", "E3 run bootstrap", CAT[2])]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.9), gridspec_kw={"wspace": 0.3})
    for ax, sub, ttl, ref in ((axes[0], size, "(a) false-positive rate when there is no arm effect (nominal 0.05)", 0.05), (axes[1], power, "(b) power at a true effect of 0.05", None)):
        sub = sub.sort_values(["s_ma", "M", "S"]); labels = [f"M{int(r.M)} S{int(r.S)}\nsd {r.s_ma:g}" for r in sub.itertuples()]
        x = np.arange(len(sub))
        for j, (e, lab, col) in enumerate(ests):
            dot_ci(ax, x + (j - 1.5) * 0.17, sub[f"{e}_reject"], sub[f"{e}_reject_lo"], sub[f"{e}_reject_hi"], col, ms=5, label=lab if ax is axes[0] else None)
        if ref is not None:
            ax.axhline(ref, color=INK2, lw=0.9)
        ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=6.5); ax.set_title(ttl, fontsize=9); ax.set_ylabel("rejection rate"); tidy(ax)
    axes[0].legend(fontsize=6.5, loc="upper left")
    save(fig, "F26_estimator_size_power", "Phase 8: size and power of the contrast estimators on simulated data", ["v2_1/e8_3/mixed.csv"],
         f"{int(t['n_datasets'].max())} simulated datasets per condition; Wilson 95 % intervals", "M models, S seeds; sd = planted between-model spread of the arm effect. E0 is the v2 estimator.")


# ================================================================================================== Phase 9
def F22_throughput():
    """Phase 9: seconds per run for every roster configuration, from the pilots."""
    t = csv("v2_1/e9_0/throughput.csv"); t = t[t["kind"] == "pilot"].sort_values("mean_s_per_run")
    y = np.arange(len(t))
    fig, ax = plt.subplots(figsize=(8.4, 0.34 * len(t) + 1.4))
    b = ax.barh(y, t["mean_s_per_run"] / 60, height=0.6, color=CAT[0])
    for yi, r in zip(y, t.itertuples()):
        ax.text(r.mean_s_per_run / 60 + 0.4, yi, f"{r.mean_s_per_run / 60:.1f} min  (n {int(r.n_runs)}; reasoning {int(round(r.reasoning_tokens_per_call)):,} tok/call)", va="center", fontsize=7, color=INK2)
    ax.set_yticks(y); ax.set_yticklabels([f"{m} · {c}" for m, c in zip(t["model"], t["config_tag"])], fontsize=7)
    ax.set_xlabel("mean minutes per 200-call run"); ax.set_xlim(0, t["mean_s_per_run"].max() / 60 * 1.75)
    ax.set_title("Mean run time per configuration (one run is 200 sequential LLM calls)")
    tidy(ax, ygrid=False, xgrid=True)
    save(fig, "F22_throughput_per_model", "Phase 9: seconds per run by configuration", ["v2_1/e9_0/throughput.csv"],
         "; ".join(f"{m}: {int(n)} runs" for m, n in zip(t["model"], t["n_runs"])), "Provider defaults except Gemini 2.5 Flash with thinking off; the roster's clock is set by its slowest member.")


def F23_sigma_d_and_pilots():
    """Phase 9: band-MAS sigma_d per configuration with its upper limit, and how far each pilot got."""
    s = csv("v2_1/e9_2/sigma.csv"); z = jsn("v2_1/e9_2/sizing.json")
    roster = z["roster"]; bm = s[(s["metric"] == "band_mas") & (s["Model"].isin(roster))].sort_values("sigma_d_R1_limit90")
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 0.36 * len(roster) + 1.6), gridspec_kw={"wspace": 0.55, "width_ratios": [1.15, 1]})
    ax = axes[0]; y = np.arange(len(bm))
    cols = [CAT[1] if m == z["plugin_model"] else CAT[0] for m in bm["Model"]]
    ax.barh(y, bm["sigma_d_R1"], height=0.6, color=cols)
    ax.scatter(bm["sigma_d_R1_limit90"], y, marker="|", s=220, color=INK, linewidths=1.8, zorder=3)
    for yi, r in zip(y, bm.itertuples()):
        ax.text(r.sigma_d_R1_limit90 + 0.002, yi, f"limit {r.sigma_d_R1_limit90:.4f}  ({int(r.n_pairs)} pairs, {int(r.df_d)} df)", va="center", fontsize=6.5, color=INK2)
    ax.set_yticks(y); ax.set_yticklabels([m.replace("openrouter/", "") for m in bm["Model"]], fontsize=7)
    ax.set_xlabel("σ_d of band-MAS at R = 1 (bar) and its one-sided 90 % upper limit (tick)"); ax.set_xlim(0, bm["sigma_d_R1_limit90"].max() * 1.9)
    ax.set_title(f"(a) σ_d per configuration; the largest limit ({z['plugin_sigma_d_band_mas']:.4f}) gives {z['stage1_seeds_appA']} seeds per cell", fontsize=9); tidy(ax, ygrid=False, xgrid=True)
    ax = axes[1]
    done = z["runs_done_vs_planned"]; keys = list(done.keys()); y2 = np.arange(len(keys))
    trunc = set(z.get("truncated_by_the_clock", [])); dropped = set(z.get("dropped_and_unfinished", [])); short = set(z.get("truncated_seed_lists_addendum_10", []))
    for yi, k in zip(y2, keys):
        d, p = done[k]
        col = DEEMPH if k in dropped else (CAT[3] if k in trunc else CAT[0])
        ax.barh(yi, p, height=0.6, color="#efeeea"); ax.barh(yi, d, height=0.6, color=col)
        ax.text(p + 5, yi, f"{d} / {p}", va="center", fontsize=6.5, color=INK2)
    ax.set_yticks(y2); ax.set_yticklabels([k.replace("openrouter/", "").replace("|default", "") for k in keys], fontsize=7); ax.invert_yaxis()
    ax.set_xlabel("pilot runs completed / planned"); ax.set_title("(b) pilot completion: blue complete, yellow stopped on the clock, grey dropped for cost", fontsize=9)
    tidy(ax, ygrid=False, xgrid=True)
    save(fig, "F23_sigma_d_and_pilot_completion", "Phase 9: sigma_d per configuration and pilot completion", ["v2_1/e9_2/sigma.csv", "v2_1/e9_2/sizing.json"],
         "; ".join(f"{m.replace('openrouter/', '')}: {int(n)} pairs" for m, n in zip(bm["Model"], bm["n_pairs"])),
         f"Plug-in taken over {z['plugin_over_n_of_roster'][0]} of {z['plugin_over_n_of_roster'][1]} configurations; not piloted: {z.get('not_piloted_registered')}.")


def F24_parameter_ranking():
    """Phase 9: the effect of each generator parameter on the level-free oracle and the scripted policies."""
    t = csv("v2_1/e9_1/effects.csv"); rk = jsn("v2_1/e9_1/ranking.json")["decision"]
    t = t[t["ranked"].astype(str) == "True"].copy() if "ranked" in t else t
    t = t.sort_values("rank_sum").reset_index(drop=True)
    y = np.arange(len(t))
    fig, ax = plt.subplots(figsize=(9, 0.36 * len(t) + 1.6))
    for i, r in t.iterrows():
        lo1, hi1 = _interval_str(r["E_oracle_ci95"]); lo2, hi2 = _interval_str(r["E_scripted_ci95"])
        six = r["candidate"] in set(rk["data_driven_six"])
        dot_ci(ax, [y[i] - 0.17], [r["E_oracle"]], [lo1], [hi1], CAT[0] if six else DEEMPH, horizontal=True, ms=6)
        dot_ci(ax, [y[i] + 0.17], [r["E_scripted"]], [lo2], [hi2], CAT[1] if six else "#dedcd4", horizontal=True, ms=6)
        ax.text(max(hi1, hi2, r["E_oracle"], r["E_scripted"]) * 1.06 + 0.001, y[i], f"share in top six {r['top_six_share_boot']:.2f}", va="center", fontsize=6.5, color=INK2)
    ax.plot([], [], "o", color=CAT[0], label="effect on the level-free oracle's regret"); ax.plot([], [], "o", color=CAT[1], label="effect on the scripted policies' band-MAS")
    ax.plot([], [], "o", color=DEEMPH, label="not in the data-driven six (greyed)")
    ax.set_yticks(y); ax.set_yticklabels([f"{c}{'  (plan)' if str(p) == 'True' else ''}" for c, p in zip(t["candidate"], t["plan_six"])], fontsize=7); ax.invert_yaxis()
    ax.set_xlabel("standardised effect against the default, the larger of the two registered levels (95 % bootstrap interval)")
    ax.set_title(f"Effect of each generator parameter on the benchmark's outcomes; the six swept: {', '.join(rk['data_driven_six'])}", fontsize=9)
    ax.legend(fontsize=7, loc="lower right"); tidy(ax, ygrid=False, xgrid=True)
    save(fig, "F24_parameter_ranking", "Phase 9: the parameter ranking", ["v2_1/e9_1/effects.csv", "v2_1/e9_1/ranking.json"],
         "100 seeds per panel; 1,000 bootstrap resamples for the top-six share", f"shared with the plan's six: {rk['shared_with_plan']}")


def F25_criteria():
    """Phase 9: the reference distribution's size and power, and the three robustness criteria, against the roster size M."""
    rf = csv("v2_1/e9_3/refdist_fresh.csv"); cr = csv("v2_1/e9_3/criteria.csv")
    base = rf[(rf["S"] == 93) & (rf["shared"].astype(str) == "True") & (rf["hetero"].astype(str) == "False") & (rf["tau_label"].astype(str) == "half_limit")]
    size = base[np.isclose(base["beta"].astype(float), 0.0)].sort_values("M"); power = base[base["beta"].astype(float) > 0].sort_values("M")
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.9), gridspec_kw={"wspace": 0.35})
    cands = [("R1", "R1 normal", DEEMPH), ("R2", "R2 t on per-model means", CAT[1]), ("R4", "R4 two-way ANOVA, Satterthwaite df", CAT[2]), ("R5", "R5 two-way variance, t(M minus 1)  (adopted)", CAT[0])]
    for c, lab, col in cands:
        if f"{c}_reject" in size:
            axes[0].plot(size["M"], size[f"{c}_reject"], color=col, marker="o", markersize=4, markeredgecolor=SURFACE, label=lab)
            axes[1].plot(power["M"], power[f"{c}_reject_prime"], color=col, marker="o", markersize=4, markeredgecolor=SURFACE)
    axes[0].axhline(0.05, color=INK2, lw=0.9); axes[0].text(size["M"].max(), 0.052, "nominal 0.05", ha="right", va="bottom", color=INK2)
    axes[0].set_title("(a) false-positive rate at α = 0.05"); axes[0].set_ylabel("rejection rate when the true effect is 0")
    axes[1].set_title("(b) power at α′ = 0.05/36, true effect Δ"); axes[1].set_ylabel("rejection rate")
    h0, l0 = axes[0].get_legend_handles_labels()
    fig.legend(h0, l0, loc="upper center", bbox_to_anchor=(0.5, -0.04), ncol=4,
               title="Panels (a) and (b): the candidate reference distributions")   # under the figure, above the criteria legend
    ax = axes[2]
    c1 = cr[(cr["L"] == 12) & (cr["S"] == 93) & (cr["tau_lam_label"].astype(str) == "half_limit") & (cr["beta_label"] == "half_delta") & (cr["int_label"].astype(str) == "0")].sort_values("M")
    c2 = cr[(cr["L"] == 12) & (cr["S"] == 93) & (cr["tau_lam_label"].astype(str) == "0") & (cr["beta_label"] == "delta") & (cr["int_label"].astype(str) == "0")].sort_values("M")
    c3 = cr[(cr["L"] == 12) & (cr["S"] == 93) & (cr["tau_lam_label"].astype(str) == "half_limit") & (cr["beta_label"] == "delta") & (cr["int_label"].astype(str) == "0")].sort_values("M")
    for q, col, lab, colname in ((c1, CRITICAL, "(i) sign criterion, plain reading: false level-dependent rate", "level_dependent_plain"),
                                 (c1, CAT[2], "(i) sign criterion, significant-only reading: false rate", "level_dependent_significant_only"),
                                 (c2, CAT[0], "(ii) every level clears α′ (power)", "ii_holds_alpha_prime"),
                                 (c3, CAT[1], "(iii) equivalence declared when the true interaction is 0 (power)", "equivalence_declared")):
        ax.plot(q["M"], q[colname], color=col, marker="o", markersize=4, markeredgecolor=SURFACE, label=lab)
        ax.fill_between(q["M"], q[f"{colname}_lo"], q[f"{colname}_hi"], color=col, alpha=0.12)
    ax.set_title("(c) the three robustness criteria (L = 12, S = 93)"); ax.set_ylabel("rate")
    hs, ls = ax.get_legend_handles_labels()
    fig.legend(hs, ls, loc="upper center", bbox_to_anchor=(0.5, -0.19), ncol=2, title="Panel (c): the three robustness criteria")
    for a in axes:
        a.set_xlabel("number of models M"); tidy(a)
    save(fig, "F25_reference_distribution_and_criteria", "Phase 9: reference distribution and robustness criteria vs M", ["v2_1/e9_3/refdist_fresh.csv", "v2_1/e9_3/criteria.csv"],
         f"reference distribution: {int(rf['n_datasets'].max()):,} datasets per condition; criteria: {int(cr['n_datasets'].max()):,}",
         "Panel (c): the plain sign criterion's false rate falls with M but never reaches 0.05 at these shapes; (ii) and (iii) are governed by M.")


REGISTRY.update({"F17": F17_reference_ranges, "F18": F18_gate_16a, "F19": F19_theta, "F20": F20_metric_matrix_sweeps,
                 "F21": F21_variance_components, "F26": F26_estimator_size, "F22": F22_throughput, "F23": F23_sigma_d_and_pilots,
                 "F24": F24_parameter_ranking, "F25": F25_criteria})


# ================================================================================================== additions (batch 4)
SCEN4 = [("flat", "flat"), ("crash", "crash"), ("bull_trap", "bull trap"), ("sustained_bull", "sustained bull")]


def F27_start_price():
    """Phase 1: the four start-price mechanisms against the attacker test and the rule-100 test."""
    d = jsn("v2_1/e1_1/start_price.json")["mechanisms"]
    mech = [("fixed", "fixed at 100 (v2)"), ("A", "A: randomised level"), ("B", "B: normalised level"), ("C", "C: both (in force)")]
    scen = SCEN4[:3]
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0), gridspec_kw={"wspace": 0.32, "width_ratios": [1, 1.3]})
    ax = axes[0]
    for j, (mk, ml) in enumerate(mech):
        xs, ys, lo, hi = [], [], [], []
        for i, (sk, sl) in enumerate(scen):
            a = d[mk]["attacker"][f"{sk}|all"]
            xs.append(i + (j - 1.5) * 0.18); ys.append(float(a["delta_level_minus_levelfree"]))
            c = ci(a["delta_ci95"]); lo.append(c[0]); hi.append(c[1])
        dot_ci(ax, xs, ys, lo, hi, CAT[j], label=ml, ms=6)
    ax.axhline(0, color=INK2, lw=0.9)
    ax.set_xticks(range(len(scen))); ax.set_xticklabels([s[1] for s in scen])
    ax.set_ylabel("R² advantage of the price level over level-free features")
    ax.set_title("(a) attacker test: the level may add nothing (interval touching zero)", fontsize=9)
    ax.legend(fontsize=7, loc="upper right"); tidy(ax)
    ax = axes[1]
    for j, (mk, ml) in enumerate(mech):
        for i, (sk, sl) in enumerate(SCEN4):
            r = d[mk]["rule100"].get(sk)
            if not isinstance(r, dict) or "rule100" not in r:
                continue
            x = i + (j - 1.5) * 0.18
            e = sorted([num(r["edge_lo"]), num(r["edge_hi"])])
            ax.plot([x, x], e, color=DEEMPH, lw=3.5, solid_capstyle="butt", zorder=2)
            m = num(r["rule100"]); c = ci(r["rule100"].get("ci95"))
            ax.errorbar([x], [m], yerr=[[max(m - c[0], 0)], [max(c[1] - m, 0)]], fmt="o", color=CAT[j], ecolor=CAT[j],
                        markersize=5.5, markeredgecolor=SURFACE, markeredgewidth=1.2, capsize=2, zorder=3)
            o = num(r["mandate_conditional_oracle"])
            ax.plot([x - 0.07, x + 0.07], [o, o], color=INK, lw=1.3, zorder=4)
    ax.plot([], [], color=DEEMPH, lw=3.5, label="range of the two constant band-edge policies")
    ax.plot([], [], color=INK, lw=1.3, label="true-value oracle")
    ax.scatter([], [], color=INK2, s=22, label="the two-line rule (colour as in panel a)")
    ax.set_xticks(range(len(SCEN4))); ax.set_xticklabels([s[1] for s in SCEN4])
    ax.set_ylabel("mandate-conditional regret at θ = 0.05"); ax.set_ylim(0, 0.215)
    ax.set_title("(b) Rule-100 test: the rule must sit with the band-edge policies, not the oracle", fontsize=9)
    ax.legend(fontsize=7, loc="upper left"); tidy(ax)
    save(fig, "F27_start_price_mechanisms", "Phase 1: start-price mechanisms against the attacker and rule-100 tests",
         ["v2_1/e1_1/start_price.json"], "500 seeds per scenario per mechanism (2,000 paths each); 500-resample cluster bootstrap",
         "Mechanism B was the team's provisional choice and failed both tests; C is in force.")


def F28_persistence_sweep():
    """Phase 2: what the mispricing half-life does to the oracle's decisions and to coverage (matched sd of x)."""
    s = jsn("v2_1/e2_6/sweep.json")["cells"]
    hs = sorted({float(k.split("|h")[1]) for k in s if k.startswith("sd|")})
    key = lambda h: f"sd|h{int(h) if float(h).is_integer() else h}"  # noqa: E731
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.9), gridspec_kw={"wspace": 0.3})
    for i, (sk, sl) in enumerate(SCEN4):
        share, lo, hi, cov = [], [], [], []
        for h in hs:
            sw = s[key(h)]["switch"][sk]
            share.append(float(sw["share_ge2"])); w = ci(sw.get("share_ge2_wilson")); lo.append(w[0]); hi.append(w[1])
            cov.append(float(sw["mean_coverage"]))
        axes[0].plot(hs, share, marker="o", color=CAT[i], label=sl, markeredgecolor=SURFACE, markeredgewidth=1.2)
        axes[0].fill_between(hs, lo, hi, color=CAT[i], alpha=0.14, linewidth=0)
        axes[1].plot(hs, cov, marker="o", color=CAT[i], label=sl, markeredgecolor=SURFACE, markeredgewidth=1.2)
    for ax in axes:
        ax.set_xscale("log"); ax.set_xlabel("mispricing half-life h (days, log scale)")
        ax.axvline(7.5, color=INK2, lw=0.9); ax.axvline(150, color=DEEMPH, lw=1.2)
        tidy(ax)
    axes[0].text(7.5 * 1.1, 0.985, "fitted at Phase 2 (7.5 d)", fontsize=7, color=INK2, va="top")
    axes[0].text(150 * 1.1, 0.6, "v2 (150 d)", fontsize=7, color=INK2, va="bottom")
    axes[0].axhline(0.5, color=AXIS, lw=0.9)
    axes[0].text(hs[-1], 0.515, "G3 requires 0.5", fontsize=7, color=INK2, va="bottom", ha="right")
    axes[0].set_ylim(0, 1.0); axes[0].set_ylabel("share of runs with at least two oracle target switches")
    axes[0].set_title("(a) decisions per run against the half-life", fontsize=9)
    axes[0].legend(fontsize=7, loc="upper right")
    axes[1].set_ylim(0, 0.9); axes[1].set_ylabel("share of days resolvable at θ = 0.05")
    axes[1].set_title("(b) coverage against the half-life", fontsize=9)
    save(fig, "F28_persistence_sweep", "Phase 2: oracle switches and coverage against the mispricing half-life",
         ["v2_1/e2_6/sweep.json"], "200 seeds per scenario and level; matched stationary sd of x; Wilson 95 % bands",
         "The fitted half-life gives two to three decisions per run where v2's 150 days gave at most one.")


def F29_half_life_bias():
    """Phase 2: the bias of the naive half-life estimator on a pure AR(1) at the benchmark's horizons."""
    d = jsn("v2_1/e2_5/hl_table.json"); c = d["cells"]; hs = [float(h) for h in d["design"]["hs"]]; Ts = [int(t) for t in d["design"]["Ts"]]
    cols = [SEQ[3], SEQ[6], SEQ[9], SEQ[12]]
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.9), gridspec_kw={"wspace": 0.3})
    ax = axes[0]
    ax.plot([min(hs), max(hs)], [min(hs), max(hs)], color=DEEMPH, lw=1.4, label="no bias (estimate equals truth)")
    for j, T in enumerate(Ts):
        cells = [c[f"h{int(h)}|T{T}"]["naive"] for h in hs]
        med = [float(k["median"]) for k in cells]; p25 = [float(k["p25"]) for k in cells]; p75 = [float(k["p75"]) for k in cells]
        ax.plot(hs, med, marker="o", color=cols[j], label=f"T = {T:,} days", markeredgecolor=SURFACE, markeredgewidth=1.2)
        ax.fill_between(hs, p25, p75, color=cols[j], alpha=0.14, linewidth=0)
    ax.set_xscale("log"); ax.set_yscale("log")
    from matplotlib.ticker import FixedLocator, FixedFormatter, NullFormatter, NullLocator
    tick_hs = [h for h in hs if int(h) not in (150, 600)]           # 150 and 600 sit too close to their neighbours to label
    ax.xaxis.set_major_locator(FixedLocator(tick_hs)); ax.xaxis.set_major_formatter(FixedFormatter([f"{int(h)}" for h in tick_hs]))
    ax.xaxis.set_minor_locator(NullLocator())
    yt = [20, 30, 50, 100, 200, 300, 600]
    ax.yaxis.set_major_locator(FixedLocator(yt)); ax.yaxis.set_major_formatter(FixedFormatter([str(v) for v in yt])); ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel("true half-life (days, log scale)"); ax.set_ylabel("naive ACF(1) half-life estimate, median and IQR (days, log)")
    ax.set_title("(a) the naive estimate against the truth, by window length", fontsize=9)
    ax.legend(fontsize=7, loc="upper left"); tidy(ax, ygrid=True, xgrid=True)
    ax = axes[1]
    for j, T in enumerate(Ts):
        sh = [float(c[f"h{int(h)}|T{T}"]["naive"]["share_ge_60d"]) for h in hs]
        ax.plot(hs, sh, marker="o", color=cols[j], label=f"T = {T:,} days", markeredgecolor=SURFACE, markeredgewidth=1.2)
    ax.set_xscale("log"); ax.set_ylim(0, 1.02)
    ax.xaxis.set_major_locator(FixedLocator(tick_hs)); ax.xaxis.set_major_formatter(FixedFormatter([f"{int(h)}" for h in tick_hs]))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xlabel("true half-life (days, log scale)"); ax.set_ylabel("share of paths whose estimate clears 60 days")
    ax.set_title("(b) the v2 item-9 criterion (at least 60 days) against the truth", fontsize=9)
    ax.legend(fontsize=7, loc="lower right"); tidy(ax)
    save(fig, "F29_half_life_estimator_bias", "Phase 2: bias of the naive half-life estimator",
         ["v2_1/e2_5/hl_table.json"], "pure Gaussian AR(1); 200 seeds per cell; 7 true half-lives x 4 window lengths",
         "At T = 200 the naive estimate reads 18 to 30 days whatever the truth between 30 and 600 days.")


def F30_jumps_and_iv():
    """Phase 3: (a) the jump detection on the panel; (b) the implied-volatility step at phase transitions, v2 against v2.1."""
    det = jsn("v2_1/e3_2/detection.json"); au = jsn("v2_1/e3_5/audit.json")
    rows = jsn("v2_1/findings/R16_iv_step.json")["rows"]
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.9), gridspec_kw={"wspace": 0.35})
    ax = axes[0]
    th = [float(t) for t in det["design"]["thresholds"]]
    obs = [float(det["observed_share"][str(t)]) for t in th]; exp = [float(det["expected_t_tail_share"][str(t)]) for t in th]
    ax.plot(th, obs, marker="o", color=CAT[0], label="observed share of days", markeredgecolor=SURFACE, markeredgewidth=1.2)
    ax.plot(th, exp, marker="s", color=CAT[1], label="each stock's fitted t tail", markeredgecolor=SURFACE, markeredgewidth=1.2)
    ax.set_yscale("log"); ax.set_xlabel("threshold on the absolute standardised residual"); ax.set_ylabel("share of stock-days above the threshold (log)")
    ex = det["excess_share"]["4.0"]; exc = ci(det["excess_ci95"]["4.0"])
    ax.annotate(f"excess at 4: {ex:+.5f} [{exc[0]:+.5f}, {exc[1]:+.5f}]", xy=(4.0, obs[th.index(4.0)]), xytext=(4.15, obs[th.index(4.0)] * 3.0),
                fontsize=7, color=INK2, arrowprops=dict(arrowstyle="-", color=INK2, lw=0.7))
    ax.set_title("(a) jump detection: 2.6 million stock-days against the fitted t tail", fontsize=9)
    ax.legend(fontsize=7, loc="upper right"); tidy(ax)
    ax = axes[1]
    trans = [("calm->deterioration", "calm to\ndeterioration", "calm → deterioration"),
             ("deterioration->panic", "deterioration\nto panic", "deterioration → panic"),
             ("panic->stabilisation", "panic to\nstabilisation", "panic → stabilisation")]
    z_v2 = []
    for _, _, needle in trans:
        row = next((r for r in rows if needle in str(r.get("statistic", ""))), None)
        m = re.search(r"z = ([+-]?[0-9.]+)", str(row.get("note", ""))) if row else None
        z_v2.append(float(m.group(1)) if m else np.nan)
    z_v21 = [float(au["transitions"][k]["z_iv_mean"]) for k, _, _ in trans]
    tz = [float(au["transitions"][k]["T_z"]) for k, _, _ in trans]
    x = np.arange(len(trans)); w = 0.34
    b1 = ax.bar(x - w / 2, z_v2, width=w * 0.92, color=CAT[1], label="v2 construction (label-driven multiplier)")
    b2 = ax.bar(x + w / 2, z_v21, width=w * 0.92, color=CAT[0], label="v2.1 construction (past-only filter)")
    for xi, t in zip(x, tz):
        ax.plot([xi - 0.45, xi + 0.45], [t, t], color=INK, lw=1.2); ax.plot([xi - 0.45, xi + 0.45], [-t, -t], color=INK, lw=1.2)
    ax.plot([], [], color=INK, lw=1.2, label="derived tolerance ± T_z (95th percentile of the reference)")
    bar_ends(ax, b1, fmt="{:+.2f}", dy=0.15, size=7); bar_ends(ax, b2, fmt="{:+.2f}", dy=0.15, size=7)
    ax.axhline(0, color=AXIS, lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels([t[1] for t in trans], fontsize=8)
    ax.set_ylabel("mean z-score of the one-day change in log IV")
    ax.set_title("(b) implied volatility at the crash transitions: the phase step removed", fontsize=9)
    ax.set_ylim(-9.8, 14.5); ax.legend(fontsize=7, loc="upper left")      # headroom above the bars for the legend
    tidy(ax)
    save(fig, "F30_jumps_and_iv_transitions", "Phase 3: jump detection and the implied-volatility transition step",
         ["v2_1/e3_2/detection.json", "v2_1/e3_5/audit.json", "v2_1/findings/R16_iv_step.json"],
         "(a) 417 stocks, 2,622,096 stock-days, 1,000-resample stock bootstrap; (b) v2: 50 crash seeds (Phase 0); v2.1: 200 crash seeds",
         "The v2 IV construction jumped by z = 7.7 at the panic onset; the v2.1 construction reads z = 0.12.")


def F31_field_group_ablation():
    """Phase 5: what each field group adds to a level-free reader of the mispricing, before and after the redesign."""
    b = jsn("v2_1/e5_7a/baseline/ablation.json")["tables"]; f = jsn("v2_1/e5_7a/final/ablation.json")["tables"]
    groups = [("VOL", "volume"), ("VAL", "valuation (P/E, yield, days since announcement)"), ("SENT", "sentiment"),
              ("ANALYST", "analyst estimate"), ("LEVELS", "price levels (price, averages, MACD)"), ("IV", "implied volatility")]
    # the group names are long, so they are written once on the left and the two panels share them
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0), sharey=True, gridspec_kw={"wspace": 0.09})
    for ax, pop, title in ((axes[0], "x|all", "(a) all rows"), (axes[1], "x|calm", "(b) calm rows, calm-trained")):
        y = np.arange(len(groups)); w = 0.36
        for j, (src, lab, col) in enumerate(((b, "fields as inherited (v2 constructions)", CAT[1]), (f, "fields after Phase 5", CAT[0]))):
            vals = np.array([float(src[pop]["groups"][g]["add_one"]["delta"]) for g, _ in groups])
            los = np.array([ci(src[pop]["groups"][g]["add_one"]["ci"])[0] for g, _ in groups])
            his = np.array([ci(src[pop]["groups"][g]["add_one"]["ci"])[1] for g, _ in groups])
            ax.barh(y + (j - 0.5) * w, vals, height=w * 0.92, color=col, label=lab)
            ax.errorbar(vals, y + (j - 0.5) * w, xerr=[np.maximum(vals - los, 0), np.maximum(his - vals, 0)], fmt="none", ecolor=INK2, elinewidth=0.8, capsize=2)
        ax.set_yticks(y); ax.set_yticklabels([g[1] for g in groups], fontsize=8)
        ax.axvline(0, color=AXIS, lw=0.8); ax.set_xlabel("R² for x added by the group to the level-free base (add-one)")
        ax.set_title(title, fontsize=9.5); tidy(ax, ygrid=False, xgrid=True)
    axes[0].invert_yaxis()                                   # shared axis: invert once, or the two calls cancel
    hs, ls = axes[0].get_legend_handles_labels()
    fig.legend(hs, ls, loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=2, fontsize=8.5)
    save(fig, "F31_field_group_ablation", "Phase 5: the field-group ablation before and after the redesign",
         ["v2_1/e5_7a/baseline/ablation.json", "v2_1/e5_7a/final/ablation.json"],
         "1,600 paths, 288,000 modelled rows; 500-resample paired cluster bootstrap by path",
         "All shown fields together added +0.39 of R² over the level-free base as inherited and +0.026 after Phase 5.")


def F32_null_and_floor():
    """Phase 6: (a) the target-permutation null for the derived L2 and L2b gates; (b) the derived L1 ceiling."""
    n = jsn("v2_1/e6_6/null/null.json")["summary"]; fl = jsn("v2_1/e6_5/floor.json")
    names = {"x|all": "L2, all rows", "x|calm": "L2, calm-trained", "macro|all": "L2b, macro-phase clock"}
    keys = [k for k in n if isinstance(n[k], dict) and "null" in n[k]]
    fig, axes = plt.subplots(1, 2, figsize=(9.8, 4.6), gridspec_kw={"wspace": 0.55, "width_ratios": [1, 1.25]})
    ax = axes[0]
    for i, k in enumerate(keys):
        s = n[k]; draws = np.asarray(s["null"]["draws"], dtype=float)
        ax.scatter(draws, np.full(len(draws), i) + np.random.default_rng(3).uniform(-0.12, 0.12, len(draws)), s=9, color=DEEMPH, zorder=2)
        p95 = float(s["null"]["p95"]); hw = float(s["sampling_halfwidth"])
        ax.plot([p95, p95], [i - 0.25, i + 0.25], color=INK2, lw=1.2, zorder=3)
        ax.plot([p95 + hw, p95 + hw], [i - 0.25, i + 0.25], color=INK, lw=1.6, zorder=3)
        m = float(s["measured_selectivity"]); c = ci(s.get("selectivity_ci95_paired"))
        ax.errorbar([m], [i], xerr=[[max(m - c[0], 0)], [max(c[1] - m, 0)]], fmt="o", color=CAT[0], ecolor=CAT[0], markersize=6, markeredgecolor=SURFACE, markeredgewidth=1.3, capsize=2.5, zorder=4)
    ax.scatter([], [], s=9, color=DEEMPH, label="null draws (target permuted across paths)")
    ax.plot([], [], color=INK2, lw=1.2, label="null 95th percentile")
    ax.plot([], [], color=INK, lw=1.6, label="registered margin (p95 plus half-width)")
    ax.errorbar([], [], fmt="o", color=CAT[0], label="measured selectivity (95 % interval)")
    ax.axvline(0, color=AXIS, lw=0.8)
    ax.set_yticks(range(len(keys))); ax.set_yticklabels([names.get(k, k) for k in keys], fontsize=8); ax.invert_yaxis()
    ax.set_xlabel("selectivity: full field set minus level-free base (R² or accuracy)")
    ax.set_title("(a) the derived L2 and L2b gates: the null sits below zero", fontsize=9)
    ax.set_xlim(-0.12, 0.16); ax.legend(fontsize=6.5, loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=2); tidy(ax, ygrid=False, xgrid=True)
    ax = axes[1]
    v, seen = [], set()
    for r in sorted(fl["verdicts_5pct"], key=lambda r: -float(r["within_5pct"])):
        key = round(float(r["within_5pct"]), 4)                     # the same candidate appears under two audit runs
        if key in seen:
            continue
        seen.add(key); v.append(r)
    labs = [str(r["candidate"]).replace("k * ", "k·").replace(" (price itself)", " (price itself)") for r in v]
    vals = [float(r["within_5pct"]) for r in v]
    y = np.arange(len(v))
    ax.barh(y, vals, height=0.62, color=[CAT[0] if "price itself" in labs[i] else DEEMPH for i in range(len(v))])
    ceil = float(fl["rule"]["margin_5pct"]); triv = float(fl["empirical_trivial"]["tau_0.05"]["share"])
    ax.axvline(ceil, color=CRITICAL, lw=1.2); ax.text(ceil + 0.01, len(v) - 0.5, f"derived ceiling {ceil:.3f}", fontsize=7, color=CRITICAL, va="bottom")
    ax.set_yticks(y); ax.set_yticklabels(labs, fontsize=6.2); ax.invert_yaxis()
    ax.set_xlim(0, max(0.75, ceil + 0.12)); ax.set_xlabel("share of steps where the candidate lands within 5 % of V")
    ax.set_title(f"(b) the derived L1 rule: every candidate below the ceiling (price itself at {triv:.3f})", fontsize=9)
    tidy(ax, ygrid=False, xgrid=True)
    save(fig, "F32_derived_gates", "Phase 6: the derived L2 and L2b null margins and the derived L1 ceiling",
         ["v2_1/e6_6/null/null.json", "v2_1/e6_5/floor.json"],
         "L2 null: 40 draws (all rows), 20 (calm-trained and clock) on 1,600 paths; L1: 27 candidates on 1,600 paths, 320,000 steps",
         "Every null draw is negative because a larger feature set overfits a random target more; the registered margin is therefore negative.")


def F33_merton_and_g3():
    """Phase 7: (a) the Merton cash share against the persona bands; (b, c) the oracle's decisions and coverage against theta."""
    m = csv("v2_1/e7_3/merton.csv"); tt = csv("v2_1/e7_rescore/theta_table.csv")
    fig, axes = plt.subplots(1, 3, figsize=(11.4, 3.8), gridspec_kw={"wspace": 0.4})
    ax = axes[0]
    for lab, (lo, hi), col in (("ISFJ conservative band", (0.70, 0.90), CAT[0]), ("INTJ balanced band", (0.40, 0.60), CAT[1]), ("ENTJ aggressive band", (0.00, 0.20), CAT[2])):
        ax.axhspan(lo, hi, color=col, alpha=0.13, linewidth=0, label=lab)
    dot_ci(ax, m["gamma"], m["cash_share"], m["cash_share_ci95_lo"], m["cash_share_ci95_hi"], INK, label="Merton cash share, 95 % interval")
    ax.set_xlabel("risk aversion γ"); ax.set_ylabel("cash share"); ax.set_ylim(0, 1)
    ax.set_title("(a) the Merton cash share against the bands", fontsize=9); ax.legend(fontsize=6.5, loc="lower right"); tidy(ax)
    o = tt[tt["policy"] == "mandate_conditional_oracle"]
    for i, (sk, sl) in enumerate(SCEN4):
        s = o[o["scenario"] == sk].sort_values("theta")
        axes[1].plot(s["theta"], s["oracle_switches"], marker="o", color=CAT[i], label=sl, markeredgecolor=SURFACE, markeredgewidth=1.2)
        axes[1].fill_between(s["theta"], s["oracle_switches_lo"], s["oracle_switches_hi"], color=CAT[i], alpha=0.14, linewidth=0)
        axes[2].plot(s["theta"], s["coverage"], marker="o", color=CAT[i], label=sl, markeredgecolor=SURFACE, markeredgewidth=1.2)
    for ax in axes[1:]:
        ax.set_xscale("log"); ax.set_xlabel("resolvability threshold θ (log scale)")
        for th, lab in ((0.002, "θ_cost"), (0.05, "θ_info")):
            ax.axvline(th, color=INK2, lw=0.9)
        tidy(ax)
    axes[1].axhline(2, color=AXIS, lw=0.9); axes[1].text(0.0022, 2.2, "G3: at least 2", fontsize=7, color=INK2, va="bottom")
    for ax_, yy in ((axes[1], 0.4), (axes[2], 0.04)):
        ax_.text(0.0022, yy, "θ_cost", fontsize=7, color=INK2, va="bottom"); ax_.text(0.054, yy, "θ_info", fontsize=7, color=INK2, va="bottom")
    axes[1].set_ylabel("oracle target switches per run (mean, 95 % interval)"); axes[1].set_title("(b) decisions per run against θ", fontsize=9)
    axes[1].legend(fontsize=7, loc="upper right")
    axes[2].set_ylim(0, 1.02); axes[2].set_ylabel("share of days resolvable"); axes[2].set_title("(c) coverage against θ", fontsize=9)
    save(fig, "F33_merton_and_g3_profile", "Phase 7: the Merton reading of the bands, and the G3 profile against theta",
         ["v2_1/e7_3/merton.csv", "v2_1/e7_rescore/theta_table.csv"],
         "(a) 500 flat seeds; (b, c) 100 seeds x 3 personas per scenario, 500-resample cluster bootstrap over seeds",
         "Three values of γ land in the conservative band and none in the balanced or aggressive bands.")


def F34_multiplicity_and_null():
    """Phase 8: (a) the false-discovery rate of three multiplicity procedures; (b) the size of four temporal nulls."""
    mu = csv("v2_1/e8_3/multiplicity.csv"); nu = csv("v2_1/e8_3/null.csv")
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.2), gridspec_kw={"wspace": 0.3})
    ax = axes[0]
    procs = [("v2", "v2 procedure (BH across the metrics of one contrast)"), ("bh_within", "BH within each family"), ("by_across", "BY across families (adopted)")]
    cases = [("e8_5", 0.0, "36 tests\none family\nno true effects"), ("e8_5", 0.1, "36 tests\none family\n10 % true effects"),
             ("reviewer", 0.0, "360 tests\nfour families\nno true effects"), ("reviewer", 0.1, "360 tests\nfour families\n10 % true effects")]
    x = np.arange(len(cases)); w = 0.26
    for j, (pk, pl) in enumerate(procs):
        vals, hw = [], []
        for g, p, _ in cases:
            r = mu[(mu["grid"] == g) & (np.isclose(mu["pi1"], p)) & (mu["procedure"] == pk)].iloc[0]
            vals.append(float(r["fdr"])); hw.append(float(r["fdr_mc_halfwidth"]))
        ax.bar(x + (j - 1) * w, vals, width=w * 0.92, color=CAT[j], label=pl)
        ax.errorbar(x + (j - 1) * w, vals, yerr=hw, fmt="none", ecolor=INK2, elinewidth=0.8, capsize=2)
    ax.axhline(0.05, color=INK2, lw=0.9); ax.set_xlim(-0.6, 3.75); ax.text(3.7, 0.065, "q = 0.05", fontsize=7, color=INK2, ha="right")
    ax.set_xticks(x); ax.set_xticklabels([c[2] for c in cases], fontsize=7)
    ax.set_ylabel("false-discovery rate"); ax.set_title("(a) multiplicity: false-discovery rate of three procedures", fontsize=9)
    ax.legend(fontsize=7, loc="upper right"); tidy(ax)
    ax = axes[1]
    nulls = [("N0", "N0 circular shift (v2)"), ("N1", "N1 window permutation"), ("N2", "N2 day-block permutation (registered)"), ("N3", "N3 path-level sign flip (adopted)")]
    sub = nu[nu["n_runs"] == 36]
    phis = sorted(sub["phi"].unique()); x = np.arange(len(phis)); w = 0.2
    for j, (nk, nl) in enumerate(nulls):
        s = sub[sub["null"] == nk].sort_values("phi")
        ax.bar(x + (j - 1.5) * w, s["size"].to_numpy(), width=w * 0.92, color=CAT[j], label=nl)
        ax.errorbar(x + (j - 1.5) * w, s["size"].to_numpy(), yerr=[np.maximum(s["size"] - s["size_lo"], 0), np.maximum(s["size_hi"] - s["size"], 0)],
                    fmt="none", ecolor=INK2, elinewidth=0.8, capsize=2)
    ax.axhline(0.05, color=INK2, lw=0.9); ax.set_xlim(-0.6, 3.95); ax.text(3.9, 0.062, "nominal 0.05", fontsize=7, color=INK2, ha="right")
    ax.set_xticks(x); ax.set_xticklabels([f"φ = {p:g}" + (" (pilot)" if bool(sub[sub["phi"] == p]["phi_is_pilot"].iloc[0]) else "") for p in phis], fontsize=7.5)
    ax.set_xlabel("persistence of the daily cash-share series"); ax.set_ylabel("false-positive rate for a within-run trend (no trend present)")
    ax.set_title("(b) temporal nulls at 36 runs: only the sign flip holds its size", fontsize=9)
    ax.legend(fontsize=7, loc="upper left"); tidy(ax)
    save(fig, "F34_multiplicity_and_temporal_null", "Phase 8: multiplicity procedures and temporal nulls on simulated data",
         ["v2_1/e8_3/multiplicity.csv", "v2_1/e8_3/null.csv"],
         "(a) 5,000 replications per cell; (b) 1,000 replications with 999 null draws each",
         "The v2 procedure's false-discovery rate under the global null is 0.43 on one family and 0.996 on four.")


REGISTRY.update({"F27": F27_start_price, "F28": F28_persistence_sweep, "F29": F29_half_life_bias, "F30": F30_jumps_and_iv,
                 "F31": F31_field_group_ablation, "F32": F32_null_and_floor, "F33": F33_merton_and_g3, "F34": F34_multiplicity_and_null})


# The document scales every figure to its text width (17.6 cm). Figures wider than about 9.5 inches would land with
# text under 7 pt on the page, so their fonts are enlarged at generation time to compensate.
WIDE_FONT_SCALE = {"F15": 1.16, "F18": 1.3, "F20": 1.16, "F23": 1.3, "F25": 1.3, "F31": 1.16}


def _scaled_fonts(s: float) -> dict:
    keys = ["font.size", "axes.titlesize", "axes.labelsize", "xtick.labelsize", "ytick.labelsize", "legend.fontsize",
            "figure.titlesize"]
    return {k: plt.rcParams[k] * s for k in keys if isinstance(plt.rcParams[k], (int, float))}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    a = ap.parse_args(argv)
    names = [x.strip() for x in a.only.split(",") if x.strip()] or list(REGISTRY)
    os.makedirs(OUT, exist_ok=True)
    mp = os.path.join(OUT, "manifest.json")
    if os.path.exists(mp):
        MANIFEST.update(json.load(open(mp, encoding="utf-8")))
    failed = []
    for n in names:
        print(f"[{n}]")
        try:
            with plt.rc_context(_scaled_fonts(WIDE_FONT_SCALE.get(n, 1.0))):
                REGISTRY[n]()
        except Exception:  # noqa: BLE001 -- one figure's failure must not hide the others
            import traceback
            traceback.print_exc()
            failed.append(n)
    json.dump(dict(sorted(MANIFEST.items())), open(mp, "w", encoding="utf-8"), indent=1)
    print(f"manifest: {rel(mp)} ({len(MANIFEST)} figures)" + (f"; FAILED: {failed}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
