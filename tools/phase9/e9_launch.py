"""
v2.1 Phase 9 -- launch every configuration of a manifest at once, one runner process per model (P9-1: the concurrency
cap is per model, so models never wait for each other), each with its own log; print a line as each process ends.

    python -u -m tools.phase9.e9_launch --manifest docs/env_v2/generated/v2_1/e9_2/manifest.json --workers 15

Logs: <manifest dir>/run_<config_tag>_<model>.log.  The runner itself checkpoints, ledgers and refuses above the cap;
this file only starts and waits.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def main(argv=None):
    from tools.phase9 import e9_roster as RO
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--workers", type=int, default=15)
    ap.add_argument("--configs", default="", help="comma list; default every configuration in the manifest")
    a = ap.parse_args(argv)
    m = json.load(open(a.manifest, encoding="utf-8"))
    keys = [k.strip() for k in a.configs.split(",") if k.strip()] or m["configs"]
    logdir = os.path.dirname(os.path.abspath(a.manifest))
    procs = {}
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    for k in keys:
        mc = RO.by_key(k)
        log = os.path.join(logdir, f"run_{mc.config_tag}_{mc.slug}.log")
        fh = open(log, "a", encoding="utf-8")
        p = subprocess.Popen([sys.executable, "-u", "-m", "tools.phase9.e9_runner", "run", "--manifest", a.manifest,
                              "--config", k, "--workers", str(a.workers)], cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT, env=env)
        procs[k] = (p, fh, log, time.time())
        print(f"[launch] {k}: pid {p.pid} -> {os.path.relpath(log, ROOT)}", flush=True)
    while procs:
        for k in list(procs):
            p, fh, log, t0 = procs[k]
            if p.poll() is not None:
                fh.close()
                print(f"[launch] {k}: exit {p.returncode} after {(time.time() - t0) / 3600:.2f} h", flush=True)
                del procs[k]
        time.sleep(30)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
