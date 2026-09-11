"""
v2.1 Phase 8 -- write the parameter files from the result files (PREREG_PHASE_8.md 6; the Phase-7 pattern of
`tools/phase7/e7_write_scoring_params.py`).  Every measured value is read from a file under
`docs/env_v2/generated/v2_1/e8_*`, never typed; every code constant is read from the code it describes.

    python -u -m tools.phase8.e8_write_params --files harness            # agent/params/harness.json
    python -u -m tools.phase8.e8_write_params --files inference          # experiments/params/inference.json (after E8.3, E8.5)

Each file is re-read through its loud loader immediately after writing (P6-12).
"""
from __future__ import annotations

import argparse
import inspect
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
TODAY = "2026-09-10"

STATUS_KEY = {
    "MEASURED": "measured in this phase on a named file, with its n",
    "DERIVED": "computed in this phase from measured or fitted inputs named by file",
    "REGISTERED": "a rule fixed in PREREG_PHASE_8.md before any number under it was read",
    "DESIGN": "a design choice with no data source; carried with a stated sensitivity",
    "TEAM": "a decision the team recorded in DECISION_LOG.md",
    "READ": "taken from a source that was read and is cited in PHASE_8_REPORT.md section 1",
}


def _j(rel):
    with open(os.path.join(GEN, rel), "r", encoding="utf-8") as fh:
        return json.load(fh)


def build_harness() -> dict:
    from agent.stateful_agent import FALLBACK_HISTORY_TEXT, StatefulV2Agent, TOKENIZER_NAME
    from experiments.arms_v2 import CONTEXT_LEVELS, FACTOR_DEFAULTS
    sig = inspect.signature(StatefulV2Agent.__init__).parameters
    pm = _j("e8_1/placebo_matching.json")
    po = _j("e8_1/pilot_offsets.json")
    cc = _j("e8_2/context_cost.json")
    src_summary = inspect.getsource(StatefulV2Agent.maybe_summarise)
    assert "[:1200]" in src_summary and "[:160]" in src_summary, "the summariser's truncations moved"
    assert "at most 120 words" in StatefulV2Agent.SUMMARY_PROMPT
    return {
        "_note": ("v2.1 Phase 8 harness constants (weakness 34). Written by tools/phase8/e8_write_params.py from the code "
                  "and the e8_* result files; read by the loud loader agent/harness_params.py. The constructor defaults "
                  "are unchanged; test_harness_params_match_code keeps the file and the code in agreement."),
        "_status_key": STATUS_KEY,
        "default_harness_version": {
            "value": "v2", "status": "REGISTERED",
            "label": "the switch default is the code every published stateful run used; 'v2_1' applies E8.1(a)-(d)",
            "source": "PREREG_PHASE_8.md 1.1, 7; simulation/runner_v2.py RunConfig.harness_version",
            "date": TODAY, "interval": "not applicable (a switch)", "n": "not applicable"},
        "context_window_default": {
            "value": sig["window"].default, "status": "DESIGN",
            "label": "rolling window of the stateful arm; its sensitivity is the pre-registered context-length factor",
            "source": "agent/stateful_agent.py StatefulV2Agent(window=); experiments/arms_v2.py",
            "date": TODAY, "interval": "sensitivity: the factor levels in context_window_levels", "n": "not applicable"},
        "context_window_levels": {
            "value": [k for k in CONTEXT_LEVELS], "status": "REGISTERED",
            "label": "E8.2: rolling 5 / 20 / 50 and full, a factor of the decay thesis; 50 added in Phase 8",
            "source": "PREREG_PHASE_8.md 2; experiments/arms_v2.py CONTEXT_LEVELS",
            "date": TODAY, "interval": "not applicable (levels)", "n": len(CONTEXT_LEVELS)},
        "token_budget": {
            "value": sig["token_budget"].default, "status": "DESIGN",
            "label": (f"the full level's history budget. MEASURED consequence: it holds {cc['full_budget_turns']['v2']} "
                      f"retained turns under v2 (chars/4) and {cc['full_budget_turns']['v2_1']} under v2_1 (o200k), so "
                      f"'full' is an ~80-turn window, not an unbounded one"),
            "source": "agent/stateful_agent.py StatefulV2Agent(token_budget=); docs/env_v2/generated/v2_1/e8_2/context_cost.json",
            "date": TODAY, "interval": "sensitivity: the 50-turn level beside it", "n": cc["n_pilot_runs"]},
        "summary_every": {
            "value": sig["summary_every"].default, "status": "DESIGN",
            "label": "the summariser rewrites the running summary every this many steps (one extra call each time)",
            "source": "agent/stateful_agent.py StatefulV2Agent(summary_every=)", "date": TODAY,
            "interval": "sensitivity: the matched rolling-5 control (stateful_r5_*)", "n": "not applicable"},
        "summary_raw_turns": {
            "value": sig["summary_raw_turns"].default, "status": "DESIGN",
            "label": "raw turns kept beside the summary; matched by the rolling-5 control",
            "source": "agent/stateful_agent.py StatefulV2Agent(summary_raw_turns=)", "date": TODAY,
            "interval": "sensitivity: stateful_r5_*", "n": "not applicable"},
        "summary_word_cap": {
            "value": 120, "status": "DESIGN", "label": "the summariser is asked for at most this many words",
            "source": "agent/stateful_agent.py StatefulV2Agent.SUMMARY_PROMPT", "date": TODAY,
            "interval": "not varied", "n": "not applicable"},
        "summary_char_truncation": {
            "value": 1200, "status": "DESIGN", "label": "the summary text is truncated to this many characters",
            "source": "agent/stateful_agent.py StatefulV2Agent.maybe_summarise", "date": TODAY,
            "interval": "not varied", "n": "not applicable"},
        "summary_step_truncation": {
            "value": 160, "status": "DESIGN",
            "label": "each step's reply is truncated to this many characters inside the summariser's prompt (item 34)",
            "source": "agent/stateful_agent.py StatefulV2Agent.maybe_summarise", "date": TODAY,
            "interval": "not varied", "n": "not applicable"},
        "token_count_method": {
            "value": {"order": ["provider", f"tokenizer:{TOKENIZER_NAME}", "chars4"], "tokenizer": TOKENIZER_NAME,
                      "offset_scaling": f"tokenizer:{TOKENIZER_NAME}*provider_scale when the provider count is available"},
            "status": "REGISTERED",
            "label": ("E8.1(d): the provider's usage metadata, else the tokenizer, chars/4 only as a labelled last resort; "
                      "the method reaches the log. MEASURED on the pilot: its Context_Tokens was the provider's count and "
                      "its offset chars/4 -- two units in one log"),
            "source": "PREREG_PHASE_8.md 1.5; docs/env_v2/generated/v2_1/e8_1/pilot_offsets.json", "date": TODAY,
            "interval": "not applicable (a rule)", "n": po["n_runs"]},
        "mandate_offset_definition": {
            "value": {"primary": "nearest copy (min of system copy, injected copy)", "secondary": "system copy",
                      "pilot_logged_day200": po["summary"]["logged_offset_day200_range"],
                      "pilot_nearest_chars4": po["summary"]["nearest_offset_chars4"],
                      "pilot_nearest_o200k": po["summary"]["nearest_offset_o200k"]},
            "status": "REGISTERED",
            "label": ("E8.1(a): the distance to the nearest mandate copy the model can attend to. MEASURED: the pilot "
                      "logged 15,261-16,546 at day 200 where the nearest copy is 409 chars/4 away, a factor of "
                      f"{po['summary']['ratio_logged_over_nearest_day200'][0]:.1f}-{po['summary']['ratio_logged_over_nearest_day200'][1]:.1f}"),
            "source": "PREREG_PHASE_8.md 1.2, 1.7; docs/env_v2/generated/v2_1/e8_1/pilot_offsets.json", "date": TODAY,
            "interval": "exact arithmetic on logged columns (the v2 floor division leaves +-1 unit)", "n": po["n_runs"]},
        "history_injected_block": {
            "value": "rendered empty in retained turns (v2_1); replayed in every retained turn (v2)", "status": "REGISTERED",
            "label": ("E8.1(b): exact parity -- the static and memory histories are byte-identical under the same replies. "
                      f"MEASURED on the pilot: the replayed blocks were {po['summary']['replayed_block_share_of_context_day200']:.1%} "
                      "of the day-200 context (22 copies)"),
            "source": "PREREG_PHASE_8.md 1.3; tests/test_v2_1_phase_8.py::test_context_budget_parity; e8_1/pilot_offsets.json",
            "date": TODAY, "interval": "exact (a byte comparison)", "n": po["n_runs"]},
        "fallback_history_text": {
            "value": FALLBACK_HISTORY_TEXT, "status": "REGISTERED",
            "label": "E8.1(c): what a parse fallback leaves in the history under v2_1 (plan 12.2)",
            "source": "V2_1_IMPROVEMENT_PLAN.md 12.2 E8.1(c); agent/stateful_agent.py FALLBACK_HISTORY_TEXT", "date": TODAY,
            "interval": "not applicable", "n": "not applicable"},
        "placebo_matching": {
            "value": {"v2_pass": pm["v2_pass_count"], "v2_1_pass": pm["v2_1_pass_count"], "of": len(pm["rows"]) // 2,
                      "rows": [{k: r[k] for k in ("persona", "placebo_version", "words_real", "words_placebo",
                                                  "imperatives_real", "imperatives_placebo", "pass")} for r in pm["rows"]]},
            "status": "MEASURED",
            "label": ("E8.1(e): words within 10 % and equal imperative clauses, per persona on the rendered texts. The v2 "
                      "placebo matches ISFJ only; the matched v2_1 placebo meets both criteria for all three"),
            "source": "docs/env_v2/generated/v2_1/e8_1/placebo_matching.json; agent/prompt_matching.py", "date": TODAY,
            "interval": "exact counts (a registered annotation)", "n": len(pm["rows"])},
        "decode_temperature": {
            "value": FACTOR_DEFAULTS["temperature"], "status": "DESIGN",
            "label": ("the sampling temperature of every arm; gpt-5 models accept only 1.0 and langchain_openai drops any "
                      "other value silently, so a gpt-5 run is configured and logged at 1.0"),
            "source": "experiments/arms_v2.py FACTOR_DEFAULTS; langchain_openai BaseChatOpenAI.validate_temperature",
            "date": TODAY, "interval": "not varied", "n": "not applicable"},
        "parse_retries": {
            "value": 3, "status": "DESIGN", "label": "attempts before a parse fallback (1 s pause between)",
            "source": "agent/v2_agent.py V2Agent.decide; agent/stateful_agent.py StatefulV2Agent.decide", "date": TODAY,
            "interval": "not varied", "n": "not applicable"},
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", default="harness")
    a = ap.parse_args(argv)
    files = [f.strip() for f in a.files.split(",") if f.strip()]
    if "harness" in files:
        target = os.path.join(ROOT, "agent", "params", "harness.json")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(build_harness(), fh, indent=1)
        from agent import harness_params as HP
        HP.load(target)
        print("written and read back:", os.path.relpath(target, ROOT))
    if "inference" in files:
        from tools.phase8.e8_write_inference import build_inference
        target = os.path.join(ROOT, "experiments", "params", "inference.json")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(build_inference(), fh, indent=1)
        from experiments import inference_params as IP
        IP.load(target)
        print("written and read back:", os.path.relpath(target, ROOT))


if __name__ == "__main__":
    main()
