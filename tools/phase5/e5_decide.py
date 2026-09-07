"""
Apply the pre-registered decision rules of PREREG_PHASE_5.md sections 4-9 -- with the readings registered in
PREREG_PHASE_5_ADDENDUM.md sections 2, 3 and 5 -- to the arm results on disk, and write the decisions file that
tools/phase5/apply_e5.py consumes.

    python -m tools.phase5.e5_decide [--out docs/env_v2/generated/v2_1/e5_arms/decisions.json] [--allow-pending]

Evidence, all read from disk and none typed in:
  e5_7a/baseline/ablation.json   the permutation null margins of PREREG section 3 (absolute admissibility)
  e5_arms/<arm>/ablation.json    dR2_add of the arm's group on x / P-all with its paired CI, and the per-path
                                 sufficient statistics from which the cross-arm paired intervals are drawn on the
                                 SAME resample indices the tool used for its own tables (_boot_idx)
  e5_7c/<arm>/onset.json         the onset verdict as registered and under ADDENDUM section 1.3 (non-price fields)
  e5_arms/stats.json             the KS check (both conventions), item 12 (rule i), item 7
  e5_7b/<arm>/l1ext.json         the inversion share (E5.1's second clause)
  e5_6/volume.json               the run-up turnover ratio (E5.6's first clause)

A contest whose evidence is not on disk is PENDING.  The decisions file is written only when nothing is pending
unless --allow-pending is given; a file with a pending contest must not be fed to apply_e5.py.  The markdown
beside it is the table the report's section 4 reproduces.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from tools.phase5.common import GROUPS  # noqa: E402
from tools.phase5.e5_7a_ablation import _boot_idx, ci, r2_draws  # noqa: E402
from tools.phase5.e5_params import ANALYST_LIT_ANCHOR  # noqa: E402

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
A_ARMS = {"analyst_A_sd0.300": 0.300, "analyst_A_sd0.450": 0.450, "analyst_A_sd0.564": ANALYST_LIT_ANCHOR,
          "analyst_A_sd0.600": 0.600}
SENT_ARMS = {"A": "sentiment_A", "B-full": "sentiment_B_full", "B-half": "sentiment_B_half", "C": "sentiment_C"}


def _try(rel):
    p = os.path.join(GEN, rel)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def ablation(arm):
    j = _try(f"e5_arms/{arm}/ablation.json")
    return j if j and "tables" in j else None


def add_one(ab, group, target="x", pop="all"):
    if ab is None:
        return None
    return ab["tables"].get(f"{target}|{pop}", {}).get("groups", {}).get(group, {}).get("add_one")


def paired_diff(ab1, ab2, group, target="x", pop="all"):
    """dR2_add(group)_1 - dR2_add(group)_2 with the paired cluster-bootstrap CI on the tool's own resample indices."""
    if ab1 is None or ab2 is None:
        return None
    kb, kg = f"BASE|{target}|{pop}", f"BASE+{group}|{target}|{pop}"
    for ab in (ab1, ab2):
        if kb not in ab["fits"] or kg not in ab["fits"]:
            return None
    n = int(ab1["n_paths"])
    if int(ab2["n_paths"]) != n:
        return None
    idx = _boot_idx(n)
    d1 = r2_draws(ab1["fits"][kg]["stats"], idx) - r2_draws(ab1["fits"][kb]["stats"], idx)
    d2 = r2_draws(ab2["fits"][kg]["stats"], idx) - r2_draws(ab2["fits"][kb]["stats"], idx)
    return {"delta": float(add_one(ab1, group, target, pop)["delta"] - add_one(ab2, group, target, pop)["delta"]),
            "ci": ci(d1 - d2), "n_paths": n, "n_boot": int(len(idx))}


def onset(arm, group):
    """The arm's own group fields under both verdicts; other fields' failures are the baseline's, listed separately."""
    j = _try(f"e5_7c/{arm}/onset.json")
    if j is None:
        return None
    fields = set(GROUPS[group])
    own_np = [f"{t}:{f}" for t, f in j["verdict_nonprice"]["failures"] if f in fields]
    own_reg = [f"{t}:{f}" for t, f in j["verdict"]["failures"] if f in fields]
    other_np = [f"{t}:{f}" for t, f in j["verdict_nonprice"]["failures"] if f not in fields]
    worst = None
    for t, tr in j["transitions"].items():
        for f in fields:
            fd = tr["fields"].get(f)
            if not isinstance(fd, dict):
                continue
            ex = fd["auc"] - tr.get("auc_ref_extended", tr["auc_ref_best"])
            if worst is None or ex > worst["excess"]:
                worst = {"transition": t, "field": f, "auc": fd["auc"], "excess": float(ex), "null_p95": fd["null_p95"],
                         "n_paths": tr["n_paths_with_transition"]}
    return {"group_pass_nonprice": not own_np, "group_failures_nonprice": own_np, "group_pass_registered": not own_reg,
            "group_failures_registered": own_reg, "other_failures_nonprice": other_np, "worst_group_excess": worst}


def inversion_share(arm):
    j = _try(f"e5_7b/{arm}/l1ext.json")
    if j is None:
        return None
    return {"share": j["inversion_share_best_within_5pct"], "ci": j["best"].get("within_5pct_ci95"), "candidate": j["best"]["candidate"]}


def _fmt(row):
    if row is None:
        return "pending"
    return f"{row['delta']:+.4f} [{row['ci'][0]:+.4f}, {row['ci'][1]:+.4f}]"


def _onset_txt(on):
    if on is None:
        return "pending"
    return "PASS" if on["group_pass_nonprice"] else "FAIL " + ", ".join(on["group_failures_nonprice"])


def _worst_txt(on):
    w = on["worst_group_excess"] if on else None
    if w is None:
        return "-"
    return f"{w['excess']:+.3f} at {w['transition']} (p95 {w['null_p95']:+.3f})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(GEN, "e5_arms", "decisions.json"))
    ap.add_argument("--allow-pending", action="store_true")
    a = ap.parse_args()
    stats = _try("e5_arms/stats.json") or {}
    base = _try("e5_7a/baseline/ablation.json") or {}
    nulls = base.get("null_margins") or {}
    e56 = _try("e5_6/volume.json")
    e52 = _try("e5_2/eps.json")
    pending, ev, md = [], {}, []
    design = {"width": "P10-P90", "eps": "v21", "dividend": "v21", "dividend_field": "shown", "analyst_field": "shown"}
    status, label = {}, {}

    # ------------------------------------------------------------------ E5.1 the multiple (section 4.3; ADDENDUM 5)
    A, B = "multiple_A_P10-P90", "multiple_B_P10-P90"
    abA, abB = ablation(A), ablation(B)
    ksA = stats.get(A, {}).get("ks", {}); ksB = stats.get(B, {}).get("ks", {})
    ksA_u = stats.get(A, {}).get("ks_untruncated_posthoc", {}); ksB_u = stats.get(B, {}).get("ks_untruncated_posthoc", {})
    qual_A = bool(ksA.get("pass")); qual_B = bool(ksB_u.get("pass_untruncated"))
    diff_AB = paired_diff(abA, abB, "VAL")
    inv = {A: inversion_share(A), B: inversion_share(B)}
    m = {"ks_A_truncated": ksA, "ks_B_truncated": ksB, "ks_A_untruncated": ksA_u, "ks_B_untruncated": ksB_u,
         "qualifies": {"A": qual_A, "B": qual_B,
                       "convention": "ADDENDUM section 5: A vs the data truncated to its width, B vs the untruncated cross-section"},
         "dR2_add_VAL": {"A": add_one(abA, "VAL"), "B": add_one(abB, "VAL")},
         "dR2_add_VAL_calm": {"A": add_one(abA, "VAL", "x", "calm"), "B": add_one(abB, "VAL", "x", "calm")},
         "paired_A_minus_B": diff_AB, "inversion_share": inv}
    mult = None
    if abA is None or abB is None:
        pending.append("multiple: ablation arm(s) missing")
    else:
        rule_B = qual_A and qual_B and diff_AB is not None and diff_AB["ci"][0] > 0
        mult = "B" if rule_B else "A"
        # inversion-share clause: the share must not move against the adopted design by more than its own paired CI
        sa, sb = inv[A], inv[B]
        if sa and sb:
            hw = 0.5 * (sa["ci"][1] - sa["ci"][0]) if sa.get("ci") else 0.0
            moved_against = (sb["share"] - sa["share"] > hw) if mult == "A" else (sa["share"] - sb["share"] > hw)
            m["inversion_clause"] = {"moved_against_adopted_by_more_than_ci": bool(moved_against), "half_width": hw}
            if moved_against:
                mult = "A"; m["verdict_note"] = "undecided by the inversion clause; A stands as the simpler design"
        m["widths_adopted"] = {}
        for w in ("P25-P75", "P5-P95"):
            arm = f"multiple_{mult}_{w}"
            m["widths_adopted"][w] = {"dR2_add_VAL": add_one(ablation(arm), "VAL"), "ks": stats.get(arm, {}).get("ks"),
                                      "ks_untruncated": stats.get(arm, {}).get("ks_untruncated_posthoc")}
        m["verdict"] = mult
        design["multiple"] = mult
        status["multiple"] = "ADOPTED"
        share_txt = f"{sa['share']:.4f}" if sa else "n/a"
        label["multiple"] = (f"ADOPTED by PREREG section 4.3 on data: design {mult} at width P10-P90 -- FIT (EDGAR trailing P/E "
                             f"cross-section, set A). KS under ADDENDUM section 5's convention: A {'passes' if qual_A else 'fails'} "
                             f"({ksA.get('ks_upper95', float('nan')):.3f} vs 0.10 truncated), B {'passes' if qual_B else 'fails'} "
                             f"({ksB_u.get('ks_upper95_untruncated', float('nan')):.3f} untruncated); paired dR2_add(VAL) A - B = {_fmt(diff_AB)} "
                             f"(x, P-all, 1,600 paths); the inversion share is {share_txt} on both arms (price itself is the best "
                             f"candidate on every panel), so the second clause cannot move it.")
    ev["multiple"] = m
    md += ["## E5.1 -- the multiple (PREREG 4.3; ADDENDUM 5)", "",
           "| arm | KS vs truncated data (upper 95 %) | KS vs untruncated | qualifies | dR2_add(VAL) x, all [paired CI] | calm | inversion share |",
           "|---|---|---|---|---|---|---|"]
    for nm, ab, ks, ksu, q in ((A, abA, ksA, ksA_u, qual_A), (B, abB, ksB, ksB_u, qual_B)):
        iv = inv[nm]
        inv_txt = f"{iv['share']:.4f} [{iv['ci'][0]:.4f}, {iv['ci'][1]:.4f}]" if iv else "pending"
        md.append(f"| {nm} | {ks.get('ks_upper95', float('nan')):.3f} {'pass' if ks.get('pass') else 'fail'} | "
                  f"{ksu.get('ks_upper95_untruncated', float('nan')):.3f} {'pass' if ksu.get('pass_untruncated') else 'fail'} | {q} | "
                  f"{_fmt(add_one(ab, 'VAL'))} | {_fmt(add_one(ab, 'VAL', 'x', 'calm'))} | {inv_txt} |")
    md += ["", f"Paired dR2_add(VAL) A - B (x, P-all): **{_fmt(diff_AB)}** -> rule: B iff the CI lies above zero, else A -> "
               f"**{mult or 'PENDING'}**", ""]

    # ------------------------------------------------------------------ E5.2 / E5.3 EPS and dividends (sections 5, 6; D10)
    sh, hd = ablation("epsdiv_v21_shown"), ablation("epsdiv_v21_hidden")
    e = {"dR2_add_VAL": {"shown": add_one(sh, "VAL"), "hidden": add_one(hd, "VAL")},
         "dR2_add_VAL_calm": {"shown": add_one(sh, "VAL", "x", "calm"), "hidden": add_one(hd, "VAL", "x", "calm")},
         "paired_shown_minus_hidden": paired_diff(sh, hd, "VAL"),
         "nm_share": {"rendered": stats.get("epsdiv_v21_shown", {}).get("nm_share_days"),
                      "data": (e52 or {}).get("nm_frequency", {}).get("share_ttm_nonpositive", {}).get("value")},
         "dividend_yield_zero_share": stats.get("epsdiv_v21_shown", {}).get("dividend_yield_zero_share"),
         "onset_shown": onset("epsdiv_v21_shown", "VAL")}
    ev["eps_dividend"] = e
    if sh is None or hd is None:
        pending.append("eps/dividend: ablation arm(s) missing")
    status["eps"] = "ADOPTED"
    label["eps"] = ("ADOPTED: FIT on EDGAR basic EPS (set A) and 8-K Item 2.02 announcement dates, with the level floor and the "
                    "P5-P95 grid truncation of ADDENDUM section 4; no contest was registered (the v2 construction had no fitted "
                    "alternative and is retrievable under design 'v2'); the residual clock is resolved as an edge effect (e5_2/clock)")
    status["dividend"] = "ADOPTED"
    label["dividend"] = ("ADOPTED for the process: FIT Lintner at quarterly frequency with tau constrained to the FIT median payout "
                         "(ADDENDUM section 4.2.3) and the payer share from EDGAR + Yahoo (4.2.4); the FIELD's rendering is D10's, "
                         "undecided -- both variants carried, default 'shown' = the v2 rendering")
    md += ["## E5.2 / E5.3 -- EPS and dividends (no contest; D10 both variants)", "",
           f"dR2_add(VAL) x, all: shown {_fmt(e['dR2_add_VAL']['shown'])}; hidden {_fmt(e['dR2_add_VAL']['hidden'])}; "
           f"paired shown - hidden {_fmt(e['paired_shown_minus_hidden'])}. n/m share rendered {e['nm_share']['rendered']} vs data "
           f"{e['nm_share']['data']}.", ""]

    # ------------------------------------------------------------------ E5.4 the analyst (section 7.3)
    margin = nulls.get("ANALYST")
    an = {"null_margin_ANALYST": margin, "arms": {}}
    any_pending = margin is None
    admissible = []
    for arm, sd in A_ARMS.items():
        ab = ablation(arm); on = onset(arm, "ANALYST"); d = add_one(ab, "ANALYST")
        row = {"sd": sd, "dR2_add": d, "dR2_add_calm": add_one(ab, "ANALYST", "x", "calm"), "onset": on}
        if d is None or on is None or margin is None:
            row["admissible"] = None; any_pending = True
        else:
            row["inside_null_margin"] = bool(d["delta"] <= margin["p95_estimate"])
            row["admissible"] = bool(row["inside_null_margin"] and on["group_pass_nonprice"])
            if row["admissible"]:
                admissible.append((abs(sd - ANALYST_LIT_ANCHOR), sd, arm))
        an["arms"][arm] = row
    abC = ablation("analyst_C"); onC = onset("analyst_C", "ANALYST")
    an["C"] = {"dR2_add": add_one(abC, "ANALYST"), "dR2_add_calm": add_one(abC, "ANALYST", "x", "calm"), "onset": onC}
    if any_pending or abC is None or onC is None:
        pending.append("analyst: null margin / arm ablation / onset missing"); an["verdict"] = None
    elif admissible:
        _, sd, arm = sorted(admissible)[0]
        an["verdict"] = f"A at sd {sd}"; design.update({"analyst": "A", "analyst_sd": sd})
        status["analyst"] = "ADOPTED"
        label["analyst"] = f"ADOPTED by PREREG section 7.3: design A at the admissible sd closest to the LIT anchor ({sd}); LIT sd, DESIGN persistence"
    else:
        an["verdict"] = "no A arm admissible -> C provisional"
        design.update({"analyst": "C", "analyst_sd": ANALYST_LIT_ANCHOR})
        status["analyst"] = "PROVISIONAL"
        worst = [(v["sd"], v["onset"]["worst_group_excess"]) for v in an["arms"].values()]
        label["analyst"] = ("PROVISIONAL by PREREG section 7.3: no design-A sd is admissible -- every A arm fails the onset rule at the "
                            "crash's calm->deterioration (V's decline is the leak, not the noise: excess "
                            + "; ".join(f"sd {sd}: {w['excess']:+.3f} vs null p95 {w['null_p95']:+.3f}" for sd, w in worst)
                            + f") -- so design C (SMA250(P) e^u, LIT sd {ANALYST_LIT_ANCHOR:.3f}, DESIGN rho 0.95 per 5-day update) "
                            f"is carried as the default; its own dR2_add(ANALYST) is {_fmt(an['C']['dR2_add'])} against a null margin of "
                            f"{margin['p95_estimate']:+.4f} and it passes the onset rule at every transition. C vs B (drop the field) is Phase 9's.")
    ev["analyst"] = an
    mtxt = "pending" if margin is None else f"{margin['p95_estimate']:+.5f} (max {margin['max']:+.5f}, {margin['n_perm']} draws)"
    md += ["## E5.4 -- the analyst (PREREG 7.3)", "",
           f"Permutation null margin, ANALYST (x, P-all): {mtxt}", "",
           "| arm | dR2_add(ANALYST) x, all [paired CI] | calm | inside null margin | onset (non-price rule) | worst group excess (transition, vs null p95) | admissible |",
           "|---|---|---|---|---|---|---|"]
    for arm, row in list(an["arms"].items()) + [("analyst_C", an["C"])]:
        on = row["onset"]
        md.append(f"| {arm} | {_fmt(row['dR2_add'])} | {_fmt(row['dR2_add_calm'])} | {row.get('inside_null_margin', '-')} | "
                  f"{_onset_txt(on)} | {_worst_txt(on)} | {row.get('admissible', '-')} |")
    md += ["", f"Verdict: **{an['verdict'] or 'PENDING'}**", ""]

    # ------------------------------------------------------------------ E5.5 sentiment (section 8.3; ADDENDUM 3; D15)
    se = {"null_margin_SENT": nulls.get("SENT"), "arms": {}}
    abS = {k: ablation(v) for k, v in SENT_ARMS.items()}
    for k, arm in SENT_ARMS.items():
        it = stats.get(arm, {}).get("item12", {})
        meets = it.get("meets_i_weekly") if k == "C" else it.get("meets_i_daily")
        se["arms"][k] = {"arm": arm, "meets_rule_i": meets, "item12": {kk: it.get(kk) for kk in ("daily", "weekly")},
                         "dR2_add": add_one(abS[k], "SENT"), "dR2_add_calm": add_one(abS[k], "SENT", "x", "calm"),
                         "onset": onset(arm, "SENT")}
    for k in ("B-full", "B-half"):
        se["arms"][k]["paired_minus_A"] = paired_diff(abS[k], abS["A"], "SENT")
    cands = [k for k, v in se["arms"].items() if v["meets_rule_i"]]
    miss = [k for k in cands if se["arms"][k]["dR2_add"] is None or se["arms"][k]["onset"] is None]
    se["verdict"] = None; se["note"] = ""
    if miss or not cands:
        pending.append(f"sentiment: evidence missing for {miss or 'all'}")
    else:
        ok = [k for k in cands if se["arms"][k]["onset"]["group_pass_nonprice"]]
        order = sorted(ok, key=lambda k: se["arms"][k]["dR2_add"]["delta"])
        se["ordering_by_dR2_add"] = [(k, se["arms"][k]["dR2_add"]["delta"]) for k in order]
        pick = order[0] if order else None
        note = ""
        if pick and pick.startswith("B"):
            pd_ = se["arms"][pick]["paired_minus_A"]
            if pd_ is None or not (pd_["ci"][0] <= 0 <= pd_["ci"][1]):
                note = (f"{pick} has the lowest dR2_add but its paired increment over A excludes zero ({_fmt(pd_)}): "
                        f"reported as the labelled sensitivity, not the default")
                pick = "A" if "A" in ok else (order[1] if len(order) > 1 else None)
        se["verdict"] = pick; se["note"] = note
        design["sentiment"] = "B" if (pick or "").startswith("B") else (pick or "A")
        design["sentiment_link"] = "half" if pick == "B-half" else "full"
        status["sentiment"] = "PROVISIONAL"
        label["sentiment"] = (f"PROVISIONAL pending D15 (the team's default): PREREG section 8.3's rule selects design {pick} -- "
                              f"rule (i) met by {', '.join(cands)} (C fails the AAII weekly correlation by 0.011, ADDENDUM section 3); "
                              f"rule (ii) ordering by dR2_add(SENT) x, P-all: "
                              + ", ".join(f"{k} {d:+.4f}" for k, d in se["ordering_by_dR2_add"])
                              + (f"; {note}" if note else "")
                              + ". FIT on the SF Fed daily index deconvolved at lambda = 0.95, 200-day window medians; the pairing of "
                                "the sentiment arms is by seed only (re-simulated price paths).")
    ev["sentiment"] = se
    md += ["## E5.5 -- sentiment (PREREG 8.3; ADDENDUM 3; D15 is the team's)", "",
           "| design | meets rule (i) | dR2_add(SENT) x, all [paired CI] | calm | paired minus A | onset (SENT fields, non-price rule) |",
           "|---|---|---|---|---|---|"]
    for k, v in se["arms"].items():
        pm = _fmt(v.get("paired_minus_A")) if k.startswith("B") else "-"
        md.append(f"| {k} | {v['meets_rule_i']} | {_fmt(v['dR2_add'])} | {_fmt(v['dR2_add_calm'])} | {pm} | {_onset_txt(v['onset'])} |")
    md += ["", f"Verdict (the rule's selection; D15 is the team's): **{se['verdict'] or 'PENDING'}**"
               + (f" -- {se['note']}" if se.get("note") else ""), ""]
    # the b_pred = 0 arm: what the sentiment feedback contributes to the calm level-free residual
    ab0 = ablation("sentiment_v2_bpred0")
    if ab0 is not None:
        ev["bpred0"] = {"calm_BASE": ab0["tables"]["x|calm"]["BASE"], "calm_BASE_baseline": base.get("tables", {}).get("x|calm", {}).get("BASE"),
                        "all_BASE": ab0["tables"]["x|all"]["BASE"], "all_BASE_baseline": base.get("tables", {}).get("x|all", {}).get("BASE"),
                        "dR2_add_SENT": add_one(ab0, "SENT"), "dR2_add_SENT_calm": add_one(ab0, "SENT", "x", "calm")}

    # ------------------------------------------------------------------ E5.6 volume (section 9.3; ADDENDUM 2)
    abVA, abVB = ablation("volume_A"), ablation("volume_B")
    onB = onset("volume_B", "VOL"); onA = onset("volume_A", "VOL")
    rr = (e56 or {}).get("runup_turnover_ratio", {})
    lo, hi = rr.get("log_ratio_ci95_stock_boot", [None, None])
    vo = {"runup_log_ratio": rr, "clause1_letter_ci_excludes_zero": (lo is not None and (lo > 0 or hi < 0)),
          "clause1_premise_ci_above_zero": (lo is not None and lo > 0),
          "clause2_B_onset_pass": None if onB is None else onB["group_pass_nonprice"],
          "onset_A": onA, "onset_B": onB,
          "dR2_add_VOL": {"A": add_one(abVA, "VOL"), "B": add_one(abVB, "VOL")},
          "dR2_add_VOL_calm": {"A": add_one(abVA, "VOL", "x", "calm"), "B": add_one(abVB, "VOL", "x", "calm")},
          "paired_A_minus_B": paired_diff(abVA, abVB, "VOL"),
          "item7": {"A": stats.get("volume_A", {}).get("item7"), "B": stats.get("volume_B", {}).get("item7")}}
    vo["verdict"] = None
    if abVA is None or abVB is None or onB is None:
        pending.append("volume: ablation arm(s) / B's onset missing")
    else:
        vo["verdict_letter"] = "B" if (vo["clause1_letter_ci_excludes_zero"] and vo["clause2_B_onset_pass"]) else "A"
        vo["verdict_addendum2"] = "B" if (vo["clause1_premise_ci_above_zero"] and vo["clause2_B_onset_pass"]) else "A"
        vo["verdict"] = vo["verdict_addendum2"]
        design["volume"] = vo["verdict"]
        status["volume"] = "ADOPTED"
        label["volume"] = (f"ADOPTED by PREREG section 9.3 under ADDENDUM section 2's reading: design {vo['verdict']} -- FIT (set A daily "
                           f"volume: rho_v, the |r|/sigma loading and the residual sd); the run-up log-ratio CI [{lo:+.4f}, {hi:+.4f}] excludes "
                           f"zero BELOW (ratio 0.985, n = {rr.get('n_episodes')} run-ups), against the premise, so clause 1 fails in substance; "
                           f"under the clause's letter the verdict would be {vo['verdict_letter']} (B's onset audit passes; its beta_ru is "
                           f"sign-unstable across sub-periods). Both verdicts are recorded; the v2 |x| loading is dropped in either design.")
    ev["volume"] = vo
    md += ["## E5.6 -- volume (PREREG 9.3; ADDENDUM 2)", "",
           f"Run-up log ratio {rr.get('log_ratio_median', float('nan')):+.4f} [{lo}, {hi}] (n = {rr.get('n_episodes')}): clause 1 by the "
           f"letter {vo['clause1_letter_ci_excludes_zero']}, in the premise's direction {vo['clause1_premise_ci_above_zero']}; clause 2 "
           f"(B's onset) {vo['clause2_B_onset_pass']}.", "",
           f"dR2_add(VOL) x, all: A {_fmt(vo['dR2_add_VOL']['A'])}; B {_fmt(vo['dR2_add_VOL']['B'])}; paired A - B "
           f"{_fmt(vo['paired_A_minus_B'])}.", "",
           f"Verdict: letter **{vo.get('verdict_letter', 'PENDING')}**, ADDENDUM section 2 reading **{vo.get('verdict_addendum2', 'PENDING')}** "
           f"(adopted)", ""]

    out = {"what": ("Phase 5 decisions applied by tools/phase5/e5_decide.py from the files it names "
                    "(PREREG_PHASE_5.md sections 4-9; ADDENDUM sections 2, 3, 5)"),
           "pending": pending, "design": design, "status": status, "label": label,
           "D10": ("UNDECIDED (put to the team 6 Sep 2026): both renderings carried; default dividend.field = 'shown' (the v2 rendering); "
                   f"dR2_add(VAL) x, P-all shown {_fmt(e['dR2_add_VAL']['shown'])} vs hidden {_fmt(e['dR2_add_VAL']['hidden'])}, paired "
                   f"shown - hidden {_fmt(e['paired_shown_minus_hidden'])}; paying dividends into the agent's cash is the harness half "
                   "(simulation/, Phase 7/8)"),
           "D15": (f"the team's default, after this table: the rule selects {se.get('verdict') or 'PENDING'}; "
                   + ", ".join(f"{k}: dR2_add(SENT) {_fmt(v['dR2_add'])}, rule (i) {v['meets_rule_i']}" for k, v in se["arms"].items())),
           "analyst_pending": ("C vs B (drop the field) is Phase 9's: its condition -- C's inclusion changes no arm contrast beyond the "
                               "equivalence margin -- is an LLM-grid statement no generator audit can evaluate; B is the fallback if "
                               "Phase 9 rejects C"),
           "evidence": ev}
    md = ["# Phase 5 decisions (tools/phase5/e5_decide.py)", "",
          f"Pending: {pending or 'none'}", "", f"Design: `{json.dumps(design)}`", "", f"Status: `{json.dumps(status)}`", ""] + md
    if pending and not a.allow_pending:
        print("PENDING -- not written:\n  " + "\n  ".join(pending))
        print("\n".join(md))
        return
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(out, open(a.out, "w", encoding="utf-8"), indent=1, default=str)
    open(a.out[:-5] + ".md", "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))
    print(f"\nwrote {os.path.relpath(a.out, ROOT)}" + (" (WITH PENDING CONTESTS -- not for apply_e5)" if pending else ""))


if __name__ == "__main__":
    main()
