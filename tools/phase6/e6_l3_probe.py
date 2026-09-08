"""
v2.1 Phase 6 -- the L3 LLM probe (plan 10.2 E6.6; PREREG_PHASE_6.md section 9).  Built now; the paid arm runs only
after D2 (the roster and the ~$12 are the team's).

    python -m tools.phase6.e6_l3_probe --out docs/env_v2/generated/v2_1/e6_l3 --dry-run          # probes + baselines, no calls
    python -m tools.phase6.e6_l3_probe --out ... --models gemini-2.5-flash,gpt-5-mini,claude-sonnet-5,claude-haiku-4-5-20251001,claude-opus-5

Design (registered).  200 probes stratified by scenario (4) x macro phase (calm / event / resolution) x seed, drawn from
the stored SEP panel's RESOLVABLE rows (|x| >= theta = 0.05) with a fixed seed; each probe is one benchmark day rendered
exactly as the v2 harness renders it (`agent.render.render_v2_input` on `env.get_observation()` at that day, the
persona-free market block), followed by one question: is the stock over-valued, under-valued or fairly valued relative
to its fundamental value?  One-word answer.  Scored as sign accuracy against sign(x).

Two arms.  `normal`: the probe as rendered.  `shuffled-V`: the same probe with the observation of ANOTHER probe's day
(the whole rendered block swapped across probes by a fixed permutation) scored against THIS probe's x -- the audit's
shuffled-V construction; the answer's link to this path's x is broken, so the arm sits at chance if the model reads
the fields and not something else.  A call-free null is also computed: the normal arm's answers scored against 500
permutations of the probes' x signs (the exact null of the accuracy statistic).

The entitled reader.  A level-free GBT (the audit's estimator on the audit's level-free control columns, 5 lags,
fitted on every panel path whose seed is not among the probes') predicts x on the 200 probe rows; its sign accuracy
on the same probes, with a Wilson interval, is the ceiling a model may reach without reading anything the price
path does not carry.  Rule: a model's normal-arm accuracy <= the surrogate's + the Wilson half-width at n = 200;
the shuffled-V arm inside its own Wilson interval of chance (the null's p95).

Cost: 2 arms x 200 probes x |models| short calls; the prompts are ~1.5k tokens.  Temperature 0.
Output: <out>/probes.csv (the 200 probes with prompts, x, phase), <out>/answers_<model>.csv, <out>/l3.{json,md}
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

from tools.phase5.common import GEN, PANELS, encode_nm, pin_state, shown_fields_of  # noqa: E402

THETA = 0.05
N_PROBES = 200
SEED = 630001
QUESTION = ("\n\nQUESTION: Relative to its fundamental (intrinsic) value, is this stock currently OVERVALUED, UNDERVALUED, "
            "or FAIRLY VALUED? Answer with exactly one word: OVERVALUED, UNDERVALUED or FAIR.")
ANSWER_RE = re.compile(r"\b(OVERVALUED|UNDERVALUED|FAIR(?:LY)?(?: VALUED)?)\b", re.I)


def wilson(k: int, n: int, z: float = 1.959963985):
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    hw = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, c - hw), min(1.0, c + hw))


# ------------------------------------------------------------------------------------------ probes
def draw_probes(panel: pd.DataFrame, n: int, rng: np.random.Generator) -> pd.DataFrame:
    """Stratified: scenario x macro group x seed; resolvable rows only; one row per (scenario, group, seed) cell at most."""
    d = panel[np.abs(panel["x"]) >= THETA].copy()
    d["group"] = d["macro"].replace({"down-event": "event", "up-event": "event"})
    cells = d.groupby(["scenario", "group"]).size()
    per_cell = max(1, n // len(cells))
    picks = []
    for (sc, g), sub in d.groupby(["scenario", "group"]):
        seeds = sub["seed"].unique(); rng.shuffle(seeds)
        for s in seeds[:per_cell]:
            rows = sub[sub["seed"] == s]
            picks.append(rows.iloc[rng.integers(0, len(rows))])
    out = pd.DataFrame(picks)
    if len(out) > n:
        out = out.sample(n=n, random_state=int(rng.integers(0, 2**31 - 1)))
    return out.reset_index(drop=True)


def render_probe(scenario: str, seed: int, day: int) -> str:
    """The v2 harness's market block for that day (the observation dict as the env renders it, incl. 'n/m')."""
    from envs.synthetic_market import SyntheticMarketEnv
    from agent.render import render_v2_input
    kw = {}
    if scenario == "crash" and seed >= 100000:              # the SEP crash seed encoding: seed*100 + delta*100
        kw["crash_discount"] = (seed % 100) / 100.0; seed = seed // 100
    env = SyntheticMarketEnv(scenario, 200, seed, **kw)
    env.reset()
    for _ in range(day - 1):
        env.step()
    o = env.get_observation()
    port = {"cash": 5000.0, "holdings_value": 5000.0, "cash_share": 0.5}
    return render_v2_input(o, port)


def surrogate_on_probes(panel: pd.DataFrame, probes: pd.DataFrame) -> np.ndarray:
    """The level-free GBT of the audit, trained on every path whose seed is not a probe's, predicting the probe rows."""
    from evaluation.leakage_audit import _prepare, _models
    shown = shown_fields_of(panel)
    dfl, cols, ctrl = _prepare(encode_nm(panel), shown, "level_free")
    key = dfl["scenario"].astype(str) + "-" + dfl["seed"].astype(str) + "-" + dfl["day"].astype(str)
    pkeys = set(probes["scenario"].astype(str) + "-" + probes["seed"].astype(str) + "-" + probes["day"].astype(str))
    pseeds = set(zip(probes["scenario"].astype(str), probes["seed"]))
    train = ~pd.Series(list(zip(dfl["scenario"].astype(str), dfl["seed"]))).isin(pseeds).to_numpy()
    X = dfl[ctrl].to_numpy(float); y = dfl["x"].to_numpy(float)
    m = _models()["gbt"].fit(X[train], y[train])
    idx = key.isin(pkeys).to_numpy()
    pred = pd.Series(m.predict(X[idx]), index=key[idx].to_numpy())
    want = probes["scenario"].astype(str) + "-" + probes["seed"].astype(str) + "-" + probes["day"].astype(str)
    return pred.reindex(want.to_numpy()).to_numpy(float)


# ------------------------------------------------------------------------------------------ calls
def ask(model_name: str, prompts: List[str], out_csv: str, sleep: float = 0.0) -> pd.DataFrame:
    from agent.llm_factory import make_llm
    llm = make_llm(model_name, temperature=0.0)
    done = pd.read_csv(out_csv) if os.path.exists(out_csv) else pd.DataFrame(columns=["i", "raw"])
    have = set(done["i"].tolist())
    rows = done.to_dict("records")
    for i, p in enumerate(prompts):
        if i in have:
            continue
        try:
            r = llm.invoke(p)
            raw = r.content if hasattr(r, "content") else str(r)
            if isinstance(raw, list):
                raw = " ".join(str(x.get("text", x)) if isinstance(x, dict) else str(x) for x in raw)
        except Exception as e:
            raw = f"ERROR: {type(e).__name__}: {e}"
        rows.append({"i": i, "raw": str(raw)[:500]})
        pd.DataFrame(rows).to_csv(out_csv, index=False)
        if sleep:
            time.sleep(sleep)
    return pd.DataFrame(rows).sort_values("i").reset_index(drop=True)


def parse(raw: str) -> int:
    m = ANSWER_RE.search(str(raw))
    if not m:
        return 0
    w = m.group(1).upper()
    return 1 if w.startswith("OVER") else (-1 if w.startswith("UNDER") else 0)


# ------------------------------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(GEN, "e6_l3"))
    ap.add_argument("--panel", default=os.path.join(PANELS, "sep_phase5_after.pkl"))
    ap.add_argument("--models", default="", help="comma list of model names for agent.llm_factory.make_llm; empty = no calls")
    ap.add_argument("--arms", default="normal,shuffled")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--n-null", type=int, default=500)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    state = pin_state()
    rng = np.random.default_rng(SEED)
    pp = os.path.join(a.out, "probes.csv")
    panel = pd.read_pickle(a.panel)
    if os.path.exists(pp):
        probes = pd.read_csv(pp)
    else:
        probes = draw_probes(panel, N_PROBES, rng)[["scenario", "seed", "day", "phase", "macro", "x", "P", "V"]].copy()
        probes["prompt"] = [render_probe(sc, int(s), int(d)) + QUESTION for sc, s, d in zip(probes["scenario"], probes["seed"], probes["day"])]
        perm = rng.permutation(len(probes))
        while np.any(perm == np.arange(len(probes))):
            perm = rng.permutation(len(probes))
        probes["shuffled_from"] = perm
        probes["prompt_shuffled"] = [probes["prompt"].iloc[j] for j in perm]
        probes["surrogate_xhat"] = surrogate_on_probes(panel, probes)
        probes.to_csv(pp, index=False)
    y = np.sign(probes["x"].to_numpy(float)).astype(int)
    sur = np.sign(probes["surrogate_xhat"].to_numpy(float)).astype(int)
    k_sur = int(np.sum(sur == y)); n = len(y)
    p_sur, lo_sur, hi_sur = wilson(k_sur, n)
    res = {"state": state, "n_probes": n, "theta": THETA, "seed": SEED,
           "strata": {f"{sc}|{mc}": int(v) for (sc, mc), v in probes.groupby(["scenario", "macro"]).size().items()},
           "surrogate_levelfree_gbt": {"sign_acc": p_sur, "wilson95": [lo_sur, hi_sur], "n": n},
           "rule": "model normal-arm accuracy <= surrogate accuracy + Wilson half-width at n; shuffled arm within the null's p95",
           "ceiling": p_sur + (hi_sur - lo_sur) / 2, "models": {}}
    # the call-free null of the accuracy statistic
    null = []
    for _ in range(a.n_null):
        null.append(float(np.mean(sur == rng.permutation(y))))
    res["null_of_accuracy_sign_perm"] = {"median": float(np.median(null)), "p95": float(np.percentile(null, 95)), "n": a.n_null,
                                         "note": "the surrogate's answers scored against permuted x signs; the same null applies to a model's answers"}
    print(f"probes {n}; surrogate sign accuracy {p_sur:.3f} [{lo_sur:.3f}, {hi_sur:.3f}]; ceiling {res['ceiling']:.3f}; null p95 {res['null_of_accuracy_sign_perm']['p95']:.3f}", flush=True)
    models = [m.strip() for m in a.models.split(",") if m.strip()]
    if a.dry_run or not models:
        json.dump(res, open(os.path.join(a.out, "l3.json"), "w", encoding="utf-8"), indent=1, default=str)
        print("dry run: no calls made ->", a.out); return
    arms = [x.strip() for x in a.arms.split(",")]
    for m in models:
        res["models"][m] = {}
        for arm in arms:
            col = "prompt" if arm == "normal" else "prompt_shuffled"
            ans = ask(m, probes[col].tolist(), os.path.join(a.out, f"answers_{re.sub(r'[^A-Za-z0-9_.-]', '_', m)}_{arm}.csv"))
            pred = np.array([parse(r) for r in ans["raw"]])
            k = int(np.sum(pred == y)); p, lo, hi = wilson(k, n)
            fair = float(np.mean(pred == 0)); err = int(sum(str(r).startswith("ERROR") for r in ans["raw"]))
            blk = {"sign_acc": p, "wilson95": [lo, hi], "n": n, "share_fair_or_unparsed": fair, "n_errors": err}
            if arm == "normal":
                blk["pass_vs_surrogate_ceiling"] = bool(p <= res["ceiling"])
            else:
                blk["within_null"] = bool(p <= res["null_of_accuracy_sign_perm"]["p95"])
            res["models"][m][arm] = blk
            print(f"{m} {arm}: sign accuracy {p:.3f} [{lo:.3f}, {hi:.3f}], fair/unparsed {fair:.2f}, errors {err}", flush=True)
        json.dump(res, open(os.path.join(a.out, "l3.json"), "w", encoding="utf-8"), indent=1, default=str)
    L = ["# L3 — the LLM probe (Phase 6)", "", f"{n} probes; surrogate (level-free GBT, the entitled reader) sign accuracy {p_sur:.3f} "
         f"[{lo_sur:.3f}, {hi_sur:.3f}]; ceiling for a model {res['ceiling']:.3f}; null p95 {res['null_of_accuracy_sign_perm']['p95']:.3f}.", "",
         "| model | arm | sign accuracy [Wilson 95 %] | fair / unparsed | errors | verdict |", "|---|---|---|---|---|---|"]
    for m, arms_ in res["models"].items():
        for arm, b in arms_.items():
            v = b.get("pass_vs_surrogate_ceiling", b.get("within_null"))
            L.append(f"| {m} | {arm} | {b['sign_acc']:.3f} [{b['wilson95'][0]:.3f}, {b['wilson95'][1]:.3f}] | {b['share_fair_or_unparsed']:.2f} | {b['n_errors']} | {'PASS' if v else 'FAIL'} |")
    with open(os.path.join(a.out, "l3.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("->", a.out)


if __name__ == "__main__":
    main()
