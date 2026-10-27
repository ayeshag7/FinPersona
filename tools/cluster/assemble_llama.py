"""Assemble a gated Llama 3.1 model directory from its open copy and Meta's own tokenizer_config.json, and refuse it
unless every file equals Meta's (DECISION_LOG P9-17).

    python -m tools.cluster.assemble_llama <key> <copy snapshot dir> <Meta's tokenizer_config.json> <out dir>

<key> is a model in e9_2/llama_meta_files.json (llama-3.1-8b-instruct, llama-3.1-70b-instruct), which holds Meta's
hashes as read with an approved account on 26 Oct 2026: the LFS sha256 of each weight shard and the git blob id of
every other file.  The weights are symlinked from the copy's snapshot, so nothing large is duplicated.  Exits 5 on any
mismatch, after which the directory must not be served.
"""
import hashlib
import json
import os
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REF = os.path.join(REPO, "docs", "env_v2", "generated", "v2_1", "e9_2", "llama_meta_files.json")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 24), b""):
            h.update(block)
    return h.hexdigest()


def git_blob(path: str) -> str:
    data = open(path, "rb").read()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def main(key: str, snap: str, tok: str, out: str) -> int:
    ref = json.load(open(REF, encoding="utf-8"))["models"][key]
    if sha256(tok) != ref["tokenizer_config_sha256"]:
        print(f"REFUSED: {tok} is not Meta's tokenizer_config.json")
        return 5
    for rel in ref["files"]:
        dst = os.path.join(out, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.lexists(dst):
            os.remove(dst)
        if rel == "tokenizer_config.json":
            shutil.copyfile(tok, dst)
        else:
            os.symlink(os.path.realpath(os.path.join(snap, rel)), dst)

    def check(rel):
        want, p = ref["files"][rel], os.path.join(out, rel)
        return rel, (sha256(p) == want["sha256"]) if "sha256" in want else (git_blob(p) == want["git_blob"])

    with ThreadPoolExecutor(6) as ex:
        bad = sorted(rel for rel, ok in ex.map(check, ref["files"]) if not ok)
    n = len(ref["files"])
    if bad:
        print(f"REFUSED: {len(bad)} of {n} files differ from Meta's {ref['meta_repo']}@{ref['meta_revision']}: {bad}")
        return 5
    print(f"all {n} files equal Meta's {ref['meta_repo']}@{ref['meta_revision']} (weights from "
          f"{ref['copy_repo']}@{ref['copy_revision'][:7]}, tokenizer_config.json Meta's)")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:5]))
