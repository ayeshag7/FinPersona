"""
v2.1 Phase 8 -- E8.1's before/after on the pilot's logged context (PREREG_PHASE_8.md 1.7).

    python -u -m tools.phase8.e8_1_pilot_offsets

The pilot cannot be re-run (P7-8).  What its three `stateful_memory` logs determine exactly, per run at days 1, 2, 20,
21 and 200:

* **v2 as logged** -- `Mandate_Offset_Tokens` is `chars/4` of the text from the END of the system prompt's mandate
  copy to the generation point (`agent/stateful_agent.build_messages`), i.e. it counts every replayed copy in between;
* **v2_1, system copy** -- the same distance with the replayed blocks removed: logged − turns × len(block) / 4
  (the v2 floor division leaves ±1 unit);
* **v2_1, nearest copy** -- the injected block sits in the current turn, followed only by "\\n\\n" and the format
  instructions (`HUMAN_TEMPLATE_V2`), so the nearest-copy distance is that text, in `chars/4` and in o200k tokens;
* the mandate copies in the context: v2 = turns + 2, v2_1 = 2;
* the context: `Context_Tokens` as logged (the provider's count -- it differs from the context's own `chars/4`)
  against the logged value less the replayed blocks' share of the characters.

Output: docs/env_v2/generated/v2_1/e8_1/pilot_offsets.{csv,json,md}
"""
from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
import time

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e8_1")
PILOT = os.path.join(ROOT, "results_v2_pilot", "stateful")
DAYS = (1, 2, 20, 21, 200)


def main():
    import tiktoken
    from langchain_core.output_parsers import PydanticOutputParser
    from agent.schemas import TargetAllocation
    from agent import v2_prompts as P
    enc = tiktoken.get_encoding("o200k_base")
    fi = PydanticOutputParser(pydantic_object=TargetAllocation).get_format_instructions()
    tail = "\n\n" + fi                                   # after the injected block: HUMAN_TEMPLATE_V2's "\n\n{format_instructions}"
    assert P.HUMAN_TEMPLATE_V2.endswith("{mandate_block}\n\n{format_instructions}"), "the template moved; 1.7's arithmetic does not apply"
    schemas_last = subprocess.run(["git", "log", "-1", "--format=%h %cd", "--date=short", "--", "agent/schemas.py"],
                                  cwd=ROOT, capture_output=True, text=True).stdout.strip()
    rows = []
    files = sorted(glob.glob(os.path.join(PILOT, "*", "*", "*", "*stateful_memory*.csv")))
    for f in files:
        d = pd.read_csv(f)
        meta = json.load(open(f.replace(".csv", ".meta.json"), encoding="utf-8"))
        persona = str(d["Persona"].iloc[0])
        block = meta["mandate_block_text"]
        sysp = meta["system_prompt"]
        m = P.mandate_text(persona, meta["run_config"]["wording"])
        end = sysp.find(m) + len(m)
        assert sysp.find(m) >= 0, f"{persona}: the mandate text is not in the logged system prompt"
        assert block.find(m) >= 0, f"{persona}: the logged block does not carry the mandate text"
        for day in DAYS:
            r = d[d["Day"] == day].iloc[0]
            turns = int(r["Context_Turns"])
            logged_off = int(r["Mandate_Offset_Tokens"])
            logged_ctx = int(r["Context_Tokens"])
            total_chars_est = 4 * logged_off + end            # the v2 offset is (total_chars - end) // 4
            removed = turns * len(block)
            rows.append({
                "persona": persona, "day": day, "context_turns": turns,
                "v2_offset_system_logged_chars4": logged_off,
                "v21_offset_system_chars4": (4 * logged_off - removed) / 4.0,
                "v21_offset_nearest_chars4": len(tail) // 4,
                "v21_offset_nearest_o200k": len(enc.encode(tail)),
                "ratio_logged_over_nearest_chars4": logged_off / (len(tail) // 4),
                "copies_v2": turns + 2, "copies_v21": 2,
                "context_tokens_logged": logged_ctx,
                "context_chars4_of_same_context": total_chars_est // 4,
                "replayed_block_share_of_chars": removed / total_chars_est,
                "v21_context_tokens_est": logged_ctx * (1 - removed / total_chars_est),
                "block_chars": len(block), "block_o200k": len(enc.encode(block)),
                "parse_fallbacks_in_run": int((d["Parse_Status"].astype(str) == "fallback").sum()),
            })
    t = pd.DataFrame(rows)
    os.makedirs(OUT, exist_ok=True)
    t.to_csv(os.path.join(OUT, "pilot_offsets.csv"), index=False)
    d200 = t[t.day == 200]
    doc = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "n_runs": int(len(files)),
           "runs": [os.path.relpath(f, ROOT).replace("\\", "/") for f in files],
           "format_instructions_chars": len(fi), "tail_chars": len(tail), "tail_o200k": len(enc.encode(tail)),
           "agent_schemas_last_commit": schemas_last,
           "day200": json.loads(d200.to_json(orient="records")),
           "summary": {"logged_offset_day200_range": [int(d200.v2_offset_system_logged_chars4.min()), int(d200.v2_offset_system_logged_chars4.max())],
                       "nearest_offset_chars4": int(len(tail) // 4), "nearest_offset_o200k": int(len(enc.encode(tail))),
                       "ratio_logged_over_nearest_day200": [float(d200.ratio_logged_over_nearest_chars4.min()), float(d200.ratio_logged_over_nearest_chars4.max())],
                       "v21_system_offset_reduction_share_day200": float((1 - d200.v21_offset_system_chars4 / d200.v2_offset_system_logged_chars4).mean()),
                       "replayed_block_share_of_context_day200": float(d200.replayed_block_share_of_chars.mean())},
           "note": ("The logged Context_Tokens is the provider's count: it differs from the context's own chars/4 (day 1, "
                    "the three runs: logged vs chars/4 in the csv). The logged offset is chars/4. The two columns of "
                    "the pilot's log are therefore in different units, which is E8.1(d).")}
    json.dump(doc, open(os.path.join(OUT, "pilot_offsets.json"), "w", encoding="utf-8"), indent=1, default=float)
    print(json.dumps(doc["summary"], indent=1))
    print(t[["persona", "day", "context_turns", "v2_offset_system_logged_chars4", "v21_offset_system_chars4",
             "v21_offset_nearest_chars4", "v21_offset_nearest_o200k", "copies_v2", "copies_v21", "context_tokens_logged",
             "context_chars4_of_same_context", "v21_context_tokens_est"]].round(1).to_string(index=False))


if __name__ == "__main__":
    main()
