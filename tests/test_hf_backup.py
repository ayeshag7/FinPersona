"""tools/hf_backup.py: what never leaves the machine, the key shapes, redaction and reproducible archives."""
import os
import tarfile

import pytest

from tools import hf_backup as hb

ROOT_DIR = hb.CLUSTER_ROOTS[0]  # a cluster storage root, as bytes
IDENTS = list(hb.CLUSTER_ROOTS + hb.CLUSTER_HOSTS)


def test_never_uploaded():
    for rel in (".env", "env", ".env.local", "sub/x.env", "docs/COMPUTE_GPU_ACCESS.md", "docs/COMPUTE_KAGGLE_GUIDE.md",
                "tools/cluster/pilot.sbatch", "datasets/01_prices/daily/A.parquet",
                "docs/env_v2/generated/v2_1/e9_2/cluster_logs/a.out", ".claude/settings.local.json",
                "tools/phase9/__pycache__/e9_roster.cpython-313.pyc"):
        assert hb.exclusion(rel), rel
    for rel in ("results_v2/phase9/pilot/x.csv", "envs/market.py", "docs/env_v2/generated/v2_1/e9_4/verify.json"):
        assert hb.exclusion(rel) is None, rel
    assert hb.exclusion("references/a.pdf", ["references/"]) == "--exclude-file"
    assert hb.exclusion("references/a.pdf", ["references"]) is None  # only '/'-terminated entries are prefixes


def test_results_v2_groups_and_tiers():
    assert hb.archive_of("results_v2/phase9/pilot/default/r.csv") == "results_v2/phase9/pilot.tar.gz"
    assert hb.archive_of("results_v2/phase9/x.json") == "-"
    assert hb.archive_of("docs/a/b/c/d.md") == "-"
    assert [hb.tier(p) for p in ("MANIFEST.tsv", "_git/status.txt", "docs/x.md", "results_v2/phase9/pilot.tar.gz",
                                 "_outside_repo/Downloads/a.pdf", "docs/v2_1/e5/_prepared.pkl")] == [0, 0, 1, 2, 3, 4]


@pytest.mark.parametrize("data", [
    b"key = " + b"sk-" + b"or-v1-" + b"a1" * 32,
    b"k=" + b"AI" + b"za" + b"B" * 35 + b"\n",
    b"tok " + b"hf" + b"_" + b"Q" * 34,
    b"OPENAI" + b"_API_KEY=" + b"s9Zq" * 6,
])
def test_key_shapes_are_found(tmp_path, data):
    p = tmp_path / "f"
    p.write_bytes(data)
    assert hb.find(str(p), [], [])[0]


@pytest.mark.parametrize("data", [
    b"OPENAI_API_KEY=your_openai_key_here\n",  # README placeholder
    b"data:image/png;base64,iVBORw0KGgoP" + b"AI" + b"za" + b"x" * 60,  # inside base64
    b"a risk-adjusted return over the long horizon of the sample\n",
])
def test_lookalikes_pass(tmp_path, data):
    p = tmp_path / "f"
    p.write_bytes(data)
    assert hb.find(str(p), [], []) == ([], [])


def test_key_values_and_identifiers(tmp_path):
    p = tmp_path / "f.json"
    p.write_bytes(b'{"output_dir": "' + ROOT_DIR + b'grp/usr/run", "note": "s3cr3t-v4lue-0123456789"}')
    assert hb.find(str(p), [("demo", b"s3cr3t-v4lue-0123456789")], IDENTS + [b"usr"]) == (
        ["demo"], sorted([ROOT_DIR.decode(), "usr"]))


def test_scrub():
    data = b'{"output_dir": "' + ROOT_DIR + b'grp/usr/finpersona/out", "host": "c0000a-s00.ufhpc", "who": "usr"}'
    assert hb.scrub(data, IDENTS + [b"usr"], "x") == (
        b'{"output_dir": "<cluster>/finpersona/out", "host": "<host>", "who": "<redacted>"}')
    with pytest.raises(SystemExit):
        hb.scrub(ROOT_DIR + b"onlyone", IDENTS, "y")


def test_archive_is_reproducible_and_redacted(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.meta.json").write_bytes(b'{"output_dir": "' + ROOT_DIR + b'grp/usr/x"}')
    (src / "b.csv").write_bytes(b"day,cash\n1,100\n")
    members = [(f"results_v2/p/g/{n}", str(src / n), [os.path.getsize(src / n), 0]) for n in ("a.meta.json", "b.csv")]
    one, two = (str(tmp_path / d / "g.tar.gz") for d in ("one", "two"))
    assert hb.build_archive(("results_v2/p/g.tar.gz", members, IDENTS, one))[1:4] == (2, 1, "built")
    hb.build_archive(("results_v2/p/g.tar.gz", members, IDENTS, two))
    with open(one, "rb") as f1, open(two, "rb") as f2:
        assert f1.read() == f2.read()
    with tarfile.open(one) as t:
        assert t.extractfile("results_v2/p/g/a.meta.json").read() == b'{"output_dir": "<cluster>/x"}'
    assert hb.build_archive(("results_v2/p/g.tar.gz", members, IDENTS, one))[3] == "kept"


def test_git_blob_id(tmp_path):
    p = tmp_path / "empty"
    p.write_bytes(b"")
    assert hb.digest(str(p), "blob") == "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"
