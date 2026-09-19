"""Validate one completed E9.2 vLLM pilot against its manifest, before it is copied, committed or uploaded.

    python -m tools.cluster.validate_pilot <short> <slug>
    e.g.  python -m tools.cluster.validate_pilot gemma12 vllm_google_gemma-4-12b-it

<slug> is the roster model with "/" replaced by "_" (e9_roster.ModelConfig.slug).  Exits 1 if any check fails, so it
can gate the steps after it.  Reads the ledger's REAL field names -- `n_fallbacks`, `n_provider_fallbacks`,
`llm_errors` -- since a check on a missing field passes vacuously.
"""
import collections
import glob
import json
import os
import statistics as st
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FROZEN_ENV = "1d689aaf82a33a2e"                     # tests/v2_freeze_manifest.json, first 16 hex
# the runner resolves the 'crash' scenario to its parameterised label in every run id, as every ledger on disk does
RESOLVE = {"crash": "crash_d0.7"}


def _n(v) -> int:
    """A ledger count field: an int on some routes, a list of events (e.g. llm_errors on OpenRouter) on others."""
    return len(v) if isinstance(v, list) else int(v or 0)


def main(short: str, slug: str) -> int:
    e92 = os.path.join(REPO, "docs", "env_v2", "generated", "v2_1", "e9_2")
    led = os.path.join(e92, f"ledger_default_{slug}.jsonl")
    # a pilot served on our GPUs has manifest_vllm_<short>; one bought through OpenRouter has manifest_openrouter_<short>
    man = next((p for p in (os.path.join(e92, f"manifest_vllm_{short}.json"),
                            os.path.join(e92, f"manifest_openrouter_{short}.json")) if os.path.exists(p)), None)
    if man is None:
        sys.exit(f"no manifest_vllm_{short}.json or manifest_openrouter_{short}.json in {e92}")
    rd = os.path.join(REPO, "results_v2", "phase9", "pilot", "default", "default", slug)

    rows = [json.loads(l) for l in open(led, encoding="utf-8") if l.strip()]
    m = json.load(open(man, encoding="utf-8"))
    n = len(m["cells"])
    provider = rows[0]["provider_options"]["provider"]

    want = {(c["persona"], c["arm"], RESOLVE.get(c["scenario"], c["scenario"]), c["seed"], c["rep"])
            for c in m["cells"]}
    got = set()
    for r in rows:
        p = r["run_id"].split("__")
        got.add((p[1], p[2], p[3], int(p[4][4:]), int(p[5][3:])))

    def count(pattern):
        return len(glob.glob(os.path.join(rd, "**", pattern), recursive=True))

    checks = [
        (f"{n} rows", len(rows) == n),
        ("every row ok", collections.Counter(r["status"] for r in rows).get("ok") == n),
        ("all 200 calls expected", all(r["calls_expected"] == 200 for r in rows)),
        # e9_runner's own criterion is >=, not ==: a retried call legitimately adds to n_llm_calls
        ("calls complete (>= expected)", all(r["n_llm_calls"] >= r["calls_expected"] for r in rows)),
        ("zero fallbacks", sum(_n(r.get("n_fallbacks")) for r in rows) == 0),
        ("zero provider fallbacks", sum(_n(r.get("n_provider_fallbacks")) for r in rows) == 0),
        ("cells match manifest", want == got),
        (f"{n} csv", count("*.csv") == n),
        (f"{n} meta", count("*.meta.json") == n),
        (f"{n} usage", count("*.usage.json") == n),
        ("env hash frozen", m["fingerprint"]["Env_Code_Hash"] == FROZEN_ENV),
        ("one provider throughout", len({r["provider_options"]["provider"] for r in rows}) == 1),
        ("no api key recorded", "api_key" not in json.dumps(rows[0])),
    ]
    if provider == "vllm":
        checks += [
            ("served locally", all(r["provider_options"]["base_url"].startswith("http://127.0.0.1") for r in rows)),
            ("no upstream pinned", all(r["provider_options"]["upstream_pinned"] is None for r in rows)),
            ("no cost recorded", all(not r.get("usd") for r in rows)),
        ]
    else:
        pins = {r["provider_options"]["upstream_pinned"] for r in rows}
        checks += [
            (f"one upstream pinned throughout ({', '.join(map(str, pins))})", len(pins) == 1 and None not in pins),
            ("cost recorded on every run", all(r.get("usd") for r in rows)),
        ]
    # LLM errors are transport events the SDK retried (e.g. an OpenRouter 504); they do not fail a pilot whose runs
    # are all ok, but they are counted and reported
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
    if provider != "vllm":
        usd = sum(r.get("usd") or 0 for r in rows)
        print(f"  cost              : ${usd:.2f} total, ${usd / len(rows):.4f}/run")
    print()
    print(f"VALIDATION: {'PASS' if not bad else 'FAIL -> ' + ', '.join(bad)} ({len(checks) - len(bad)}/{len(checks)})")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
