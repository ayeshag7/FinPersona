"""
E1.4 panel side (PREREG_PHASE_1.md section 5.1): where do the large standardised residuals of the panel fall --
inside earnings-announcement windows or on other days?

Residuals: E3.1's z (set A, full-sample GJR-GARCH-t fits), 2009-01-01 .. 2024-12-31 (EDGAR coverage). Announcement
window = the 10 trading days ending on a 10-Q or 10-K filing date inclusive (the release precedes the filing by 0-14
calendar days; no 8-K Item 2.02 dates exist in the panel). Statistics with a 1,000-resample bootstrap over stocks:
q = share of |z| > 4 days inside windows, window share of days, enrichment q / share, |z| > 4 rates inside/outside,
excess kurtosis inside/outside, size of r on jump days inside/outside (mean, sd, negative share).

    python -m tools.phase1.e1_4_panel
Outputs: docs/env_v2/generated/v2_1/e1_4/panel_split.json, panel_split.md, panel_residuals_split.parquet (ticker, z, r, in_window)
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from tools.phase1.panel import DEFAULT, analysis_sets, load_prices, log_returns, filing_dates, OUT_DIR  # noqa: E402

OUT = os.path.join(OUT_DIR, "e1_4")
START, END = "2009-01-01", "2024-12-31"
WINDOW = 10
Z_JUMP = 4.0
N_BOOT = 1000
LIT = {"ABD 2007 (REStat; S&P 500 futures 1990-2002; read by the third pass, LOG 4.2)": "jump variation 14.4 % of realised variance; 27.9 % of days with a significant jump (index level)",
       "Boudoukh, Feldman, Kogan & Richardson 2019 (RFS; read)": "identified news explains 49.6 % of overnight idiosyncratic volatility (firm level)"}


def window_mask(dates: pd.DatetimeIndex, filings: pd.DatetimeIndex, window: int = WINDOW) -> np.ndarray:
    m = np.zeros(len(dates), bool)
    pos = dates.searchsorted(filings, side="right") - 1        # last trading day <= filing date
    for p in pos:
        if p >= 0:
            m[max(0, p - window + 1):p + 1] = True
    return m


def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    sets = analysis_sets(write=False)
    A = sets["A"]
    z = pd.read_parquet(os.path.join(OUT_DIR, "e3_1", "residuals.parquet"))
    z["date"] = pd.to_datetime(z["date"])
    z = z[(z["date"] >= START) & (z["date"] <= END)]
    prices = load_prices(A).ffill()
    rets = log_returns(prices)
    per_stock, frames = [], []
    for t in A:
        zt = z[z["ticker"] == t].sort_values("date")
        if zt.empty:
            continue
        f = filing_dates(t)
        if f is None or len(f) == 0:
            continue
        dates = pd.DatetimeIndex(zt["date"])
        m = window_mask(dates, f[(f >= pd.Timestamp(START) - pd.Timedelta(days=30)) & (f <= END)])
        r = rets[t].reindex(dates).to_numpy()
        zz = zt["z"].to_numpy().astype(float)
        jump = np.abs(zz) > Z_JUMP
        per_stock.append({"ticker": t, "n_days": int(len(zz)), "n_window": int(m.sum()), "n_jump": int(jump.sum()),
                          "n_jump_in": int((jump & m).sum()), "n_filings": int(len(f)),
                          "sum_z2_in": float((zz[m] ** 2).sum()), "sum_z4_in": float((zz[m] ** 4).sum()),
                          "sum_z2_out": float((zz[~m] ** 2).sum()), "sum_z4_out": float((zz[~m] ** 4).sum()),
                          "r_jump_in": r[jump & m].tolist(), "r_jump_out": r[jump & ~m].tolist()})
        frames.append(pd.DataFrame({"ticker": t, "z": zz.astype(np.float32), "r": r.astype(np.float32), "in_window": m}))
    ps = pd.DataFrame(per_stock)
    split = pd.concat(frames, ignore_index=True)
    split.to_parquet(os.path.join(OUT, "panel_residuals_split.parquet"), index=False, compression="zstd")

    def pooled(idx):
        g = ps.iloc[idx]
        n_win, n_days = g["n_window"].sum(), g["n_days"].sum()
        n_j, n_ji = g["n_jump"].sum(), g["n_jump_in"].sum()
        win_share = n_win / n_days
        q = n_ji / max(n_j, 1)
        rate_in = n_ji / max(n_win, 1); rate_out = (n_j - n_ji) / max(n_days - n_win, 1)
        k_in = g["sum_z4_in"].sum() / n_win / (g["sum_z2_in"].sum() / n_win) ** 2 - 3
        k_out = g["sum_z4_out"].sum() / (n_days - n_win) / (g["sum_z2_out"].sum() / (n_days - n_win)) ** 2 - 3
        rin = np.concatenate([np.asarray(v, float) for v in g["r_jump_in"]]) if n_ji else np.array([])
        rout = np.concatenate([np.asarray(v, float) for v in g["r_jump_out"]]) if (n_j - n_ji) else np.array([])
        return {"window_share_of_days": win_share, "q_share_of_jumps_in_window": q, "enrichment": q / win_share if win_share else np.nan,
                "jump_rate_in_window": rate_in, "jump_rate_outside": rate_out, "rate_ratio": rate_in / rate_out if rate_out else np.nan,
                "excess_kurtosis_in": k_in, "excess_kurtosis_out": k_out,
                "r_jump_in_mean": float(rin.mean()) if len(rin) else np.nan, "r_jump_in_sd": float(rin.std()) if len(rin) > 1 else np.nan,
                "r_jump_in_neg_share": float((rin < 0).mean()) if len(rin) else np.nan,
                "r_jump_out_mean": float(rout.mean()) if len(rout) else np.nan, "r_jump_out_sd": float(rout.std()) if len(rout) > 1 else np.nan,
                "r_jump_out_neg_share": float((rout < 0).mean()) if len(rout) else np.nan,
                "n_jumps": int(n_j), "n_jumps_in": int(n_ji), "n_days": int(n_days), "n_window_days": int(n_win)}
    point = pooled(np.arange(len(ps)))
    rng = np.random.default_rng(0)
    boots = [pooled(rng.integers(0, len(ps), len(ps))) for _ in range(N_BOOT)]
    ci = {k: [float(np.nanpercentile([b[k] for b in boots], 2.5)), float(np.nanpercentile([b[k] for b in boots], 97.5))]
          for k in point if not k.startswith("n_")}
    out = {"spec": DEFAULT.to_dict(), "set": "A", "n_stocks": int(len(ps)), "window": [START, END], "window_days": WINDOW, "z_threshold": Z_JUMP,
           "n_boot_over_stocks": N_BOOT, "point": point, "ci95": ci, "literature_beside": LIT,
           "caveats": ["filing dates, not 8-K release dates: the window is 10 trading days ending on the 10-Q/10-K filing",
                       "set A survivors only (REG-15): crash-related jumps of delisted names are absent",
                       "EDGAR coverage starts 2009, so 2000-2008 residuals are not split"],
           "seconds": round(time.time() - t0)}
    with open(os.path.join(OUT, "panel_split.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    p = point
    L = ["# E1.4 panel side: announcement windows vs other days (PREREG_PHASE_1.md section 5.1)", "",
         f"Set A ({len(ps)} names with EDGAR filings), residuals of the full-sample GJR-GARCH-t fits (E3.1), {START} .. {END}; window = the "
         f"{WINDOW} trading days ending on a 10-Q/10-K filing date; jump day = |z| > {Z_JUMP:.0f}. Intervals: {N_BOOT}-resample bootstrap over stocks.", "",
         "| statistic | value | 95 % CI |", "|---|---|---|"]
    for k in ("window_share_of_days", "q_share_of_jumps_in_window", "enrichment", "jump_rate_in_window", "jump_rate_outside", "rate_ratio",
              "excess_kurtosis_in", "excess_kurtosis_out", "r_jump_in_mean", "r_jump_in_sd", "r_jump_in_neg_share", "r_jump_out_mean",
              "r_jump_out_sd", "r_jump_out_neg_share"):
        L.append(f"| {k} | {p[k]:.4f} | [{ci[k][0]:.4f}, {ci[k][1]:.4f}] |")
    L += ["", f"n = {p['n_days']:,} stock-days, {p['n_window_days']:,} in windows; {p['n_jumps']:,} jump days, {p['n_jumps_in']:,} inside windows.", "",
          "Literature beside (not tolerances): " + "; ".join(f"{k}: {v}" for k, v in LIT.items()) + ".", "",
          "Caveats: " + "; ".join(out["caveats"]) + "."]
    with open(os.path.join(OUT, "panel_split.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print(json.dumps({"point": point, "ci95": ci}, indent=1))


if __name__ == "__main__":
    main()
