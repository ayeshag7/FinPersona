"""Validate one completed stage-1 open headline model (PREREG_PHASE_9_STAGE1_OPEN.md, and _B2.md for the second
batch) as validate_pilot validates a pilot: its ledger, run files and checkpoint against the registered headline
manifest that carries it, before it is analysed, committed or uploaded.

    python -m tools.cluster.validate_headline <slug>
    e.g.  python -m tools.cluster.validate_headline vllm_openai_gpt-oss-20b

Exits 1 if any check fails.  `python -m tools.phase9.e9_4_grid --stages verify` checks every run's meta.json against
the manifest fingerprint; this checks what verify does not read: the ledger rows, the file counts and the checkpoint.
"""
import collections
import glob
import hashlib
import json
import os
import statistics as st
import sys

from tools.cluster.validate_pilot import FROZEN_ENV, RESOLVE, _n

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# each registered headline manifest by its sha256: the six (PREREG_PHASE_9_STAGE1_OPEN.md 1) and the second batch
# (PREREG_PHASE_9_STAGE1_OPEN_B2.md 1)
MANIFEST_SHA256 = {"manifest_headline_open.json": "736b5bc8ccf30987aa08191339111a464c771f6566a5e9c072ec7cac428d8613",
                   "manifest_headline_open_b2.json": "4780cb4eed79a4cf21d76c498b066ed1219459b12b3b72b311ca25f63ee1b82b"}


def main(slug: str) -> int:
    e94 = os.path.join(REPO, "docs", "env_v2", "generated", "v2_1", "e9_4")
    for fname in MANIFEST_SHA256:
        man = os.path.join(e94, fname)
        m = json.load(open(man, encoding="utf-8"))
        if any(k.split("|")[0].replace("/", "_") == slug for k in m["configs"]):
            break
    else:
        sys.exit(f"{slug} is in no registered headline manifest")
    rows = [json.loads(l) for l in open(os.path.join(e94, f"ledger_default_{slug}.jsonl"), encoding="utf-8") if l.strip()]
    s1 = os.path.join(REPO, "results_v2", "phase9", "stage1_open")
    rd = os.path.join(s1, "default", "default", slug)
    ck = open(os.path.join(s1, "_checkpoints", f"default__{slug}.txt"), encoding="utf-8").read().split()
    model = next(k.split("|")[0] for k in m["configs"] if k.split("|")[0].replace("/", "_") == slug)
    n = len(m["cells"])

    want = {(c["persona"], c["arm"], RESOLVE.get(c["scenario"], c["scenario"]), c["seed"], c["rep"]) for c in m["cells"]}
    got = collections.Counter()
    for r in rows:
        p = r["run_id"].split("__")
        got[(p[1], p[2], p[3], int(p[4][4:]), int(p[5][3:]))] += 1

    def count(pattern):
        return len(glob.glob(os.path.join(rd, "**", pattern), recursive=True))

    temps = {r["temperature"] for r in rows}
    checks = [
        (f"manifest is the registered one ({fname}, sha256 {MANIFEST_SHA256[fname][:8]}...)",
         hashlib.sha256(open(man, "rb").read()).hexdigest() == MANIFEST_SHA256[fname]),
        (f"{n} rows", len(rows) == n),
        ("every row ok", collections.Counter(r["status"] for r in rows).get("ok") == n),
        ("one row per planned cell, none extra", set(got) == want and set(got.values()) == {1}),
        (f"every row is {model}", all(r["model"] == model for r in rows)),
        ("all 200 calls expected", all(r["calls_expected"] == 200 for r in rows)),
        # e9_runner's own criterion is >=, not ==: a retried call legitimately adds to n_llm_calls
        ("calls complete (>= expected)", all(r["n_llm_calls"] >= r["calls_expected"] for r in rows)),
        ("zero fallbacks", sum(_n(r.get("n_fallbacks")) for r in rows) == 0),
        ("zero provider fallbacks", sum(_n(r.get("n_provider_fallbacks")) for r in rows) == 0),
        (f"{n} csv", count("*.csv") == n),
        (f"{n} meta", count("*.meta.json") == n),
        (f"{n} usage", count("*.usage.json") == n),
        ("checkpoint lists exactly the ledger's runs", len(ck) == n and set(ck) == {r["run_key"] for r in rows}),
        ("env hash frozen", m["fingerprint"]["Env_Code_Hash"] == FROZEN_ENV),
        (f"one temperature throughout ({', '.join(map(str, temps))})", len(temps) == 1),
        ("served locally", all(r["provider_options"]["base_url"].startswith("http://127.0.0.1") for r in rows)),
        ("no upstream pinned", all(r["provider_options"]["upstream_pinned"] is None for r in rows)),
        ("no cost recorded", all(not r.get("usd") for r in rows)),
        ("no api key recorded", not any("api_key" in json.dumps(r) for r in rows)),
    ]
    n_err = sum(_n(r.get("llm_errors")) for r in rows)
    bad = [name for name, ok in checks if not ok]
    print(f"--- {slug} ---")
    for name, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    ps = collections.Counter()
    for r in rows:
        ps.update(r.get("parse_status_counts") or {})
    print()
    print(f"  input  tokens/run : {st.mean(r['input_tokens'] for r in rows):>10,.0f}")
    print(f"  output tokens/run : {st.mean(r['output_tokens'] for r in rows):>10,.0f}")
    print(f"  seconds/run       : {st.mean(r['seconds'] for r in rows):>10,.0f}")
    print(f"  parse statuses    : {dict(ps)}")
    print(f"  llm errors        : {n_err} (retried transport events)")
    print(f"  first, last utc   : {min(r['utc'] for r in rows)}, {max(r['utc'] for r in rows)}")
    print()
    print(f"VALIDATION: {'PASS' if not bad else 'FAIL -> ' + ', '.join(bad)} ({len(checks) - len(bad)}/{len(checks)})")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
