"""
Session-level reporting for the v2.1 test suite: print the known-defect registry (tests/known_defects.py)
with the observed outcome of every registered test at the end of the run (plan Phase 0, item 0.5:
"CI target: pytest tests/ -q green, with the known-defect registry printed").
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _outcomes(terminalreporter):
    out = {}
    for key in ("passed", "failed", "xfailed", "xpassed", "skipped", "error"):
        for rep in terminalreporter.stats.get(key, []):
            nodeid = getattr(rep, "nodeid", None)
            if nodeid:
                out[nodeid.replace("\\", "/")] = key
    return out


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    try:
        from tests.known_defects import V2_DEFECTS, V1_BASELINE_XFAILS
    except Exception as exc:  # pragma: no cover
        terminalreporter.write_line(f"[known-defect registry unavailable: {exc}]")
        return
    seen = _outcomes(terminalreporter)
    terminalreporter.write_sep("=", "known-defect registry (v2 generator; v2.1 acceptance = empty)")
    if not V2_DEFECTS:
        terminalreporter.write_line("  (empty)")
    for d in V2_DEFECTS:
        obs = seen.get(d["test"], "not run")
        terminalreporter.write_line(f"  {d['test']}  items {d['items']}  -> Phase {d['phase']}  [{obs}]  {d['reason']}")
    terminalreporter.write_line("v1 baseline defects (permanent):")
    for t in V1_BASELINE_XFAILS:
        terminalreporter.write_line(f"  {t}  [{seen.get(t, 'not run')}]")
