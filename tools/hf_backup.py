"""
Off-site backup of everything FinPersona on this machine that GitHub does not have, to a PRIVATE Hugging Face dataset
repo (default ayeshag7/finpersona): the working tree's untracked and git-ignored files, the commits no remote has, the
uncommitted change to tracked files, and any files or folders outside the repo named with --extra.

    python -u -m tools.hf_backup                                    # plan,scan,archive,upload,verify
    python -u -m tools.hf_backup --extra C:/Users/<you>/Downloads/<folder> --extra <another file or folder>
    python -u -m tools.hf_backup --stages verify

`plan`     The candidates are `git ls-files --others`, with and without `--ignored`, less what never leaves this
           machine (below).  `results_v2/<phase>/<group>/` goes up as one archive per group (its ~100k small files
           would exceed the Hub's 100k-files-per-repo guidance); everything else as plain files.  `_git/` gets a
           bundle of the commits no remote has, the uncommitted diff against HEAD and `git status`; each --extra path
           goes to `_outside_repo/<its parent folder>/<its name>`.
`scan`     Nothing leaves before this passes.  Credentials: every key value in `.env` / `env`, and the shapes of
           OpenAI / OpenRouter / Anthropic, Google, Hugging Face, AWS and GitHub keys and of private-key blocks, in
           every planned file and archive member.  Cluster identifiers: the cluster storage roots and UF RC host
           names, plus the names in the local identifiers file (one per line; default
           ~/.finpersona/backup_identifiers.txt, never committed: this repo is public).  A plain file holding either
           is refused; an archive member holding an identifier is redacted by `archive`.  The first scan opens every
           file (47 minutes for 107k files on the laptop, almost all of it per-file overhead); later scans re-read only
           files whose size or mtime changed.
`archive`  Each results_v2 group -> a reproducible .tar.gz (gzip mtime 0, members sorted, owner blank), rebuilt only
           when its files change.  In members holding an identifier, `/<root>/<group>/<user>` reads `<cluster>`, host
           names `<host>` and listed names `<redacted>`; a member that still holds one is refused.  Writes README.md
           (restore steps) and MANIFEST.tsv (path, bytes on disk, archive or "-").
`upload`   Creates the repo private if it is missing and refuses one that is not private.  Uploads every planned file
           that is missing online or differs (size, then sha256 or git blob id) and has not changed since `scan`: 100
           files or 2 GB per commit, metadata and git state first, regenerable caches last.  Rerun to resume.
`verify`   Every planned file online with identical content.  Files only in the backup are listed, never deleted.

Never uploaded: env files; GPU / Kaggle access (the compute guides, tools/cluster/); datasets/ (third-party data that
several sources forbid redistributing: re-download with tools/e1_0_data/); every cluster_logs/ folder; .claude/;
__pycache__/ (regenerable, and bytecode carries the source's strings).  --exclude-file adds repo paths, one per line:
exact, or prefixes ending in '/'.

The work directory (default <temp>/fp_hf_backup) holds the plan, the scan, the archives and the metadata; plain files
are uploaded from where they sit.  Long paths are off on the Windows laptop (MAX_PATH 260): keep --work short.
"""
from __future__ import annotations

import argparse
import collections
import gzip
import hashlib
import io
import json
import os
import re
import subprocess
import tarfile
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HF_REPO = "ayeshag7/finpersona"
WORK = os.path.join(tempfile.gettempdir(), "fp_hf_backup")
IDENTIFIERS = os.path.join(os.path.expanduser("~"), ".finpersona", "backup_identifiers.txt")
STAGES = ("plan", "scan", "archive", "upload", "verify")
TIERS = {0: "metadata and git state", 1: "plain files", 2: "results_v2 archives", 3: "extras", 4: "caches"}
BATCH, BATCH_BYTES = 100, 2_000_000_000  # per commit: the Hub's advice for manual commits; a failed one is cheap to redo
CHUNK, OVERLAP = 64 << 20, 4096
ARCHIVE_FORMAT = "tar.gz v1"  # part of every archive's fingerprint: change it to force rebuilds

ENV_NAME = re.compile(r"(^|/)(\.env(\..*)?|env|[^/]*\.env)$")
ACCESS = {"docs/COMPUTE_HIPERGATOR_GUIDE.md", "docs/HIPERGATOR_GPU_GUIDE.md", "docs/COMPUTE_GPU_ACCESS.md",
          "docs/COMPUTE_KAGGLE_GUIDE.md"}
CACHE = re.compile(r"_prepared\.pkl$|/_?cache/|_panels/.*\.pkl$|__pycache__")

KEY_SHAPES = [  # (label, anchors, pattern): the pattern runs only around an anchor
    ("OpenAI / OpenRouter / Anthropic key", (b"sk-",),
     rb"(?<![A-Za-z0-9])sk-(?:or-v1-|ant-|proj-)?[A-Za-z0-9_\-]{20,}"),
    ("Google API key", (b"AIza",), rb"(?<![A-Za-z0-9+/_\-])AIza[0-9A-Za-z_\-]{35}(?![0-9A-Za-z_\-])"),
    ("Hugging Face token", (b"hf_",), rb"(?<![A-Za-z0-9_])hf_[A-Za-z0-9]{30,}"),
    ("AWS key", (b"AKIA",), rb"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![0-9A-Z])"),
    ("GitHub token", (b"ghp_", b"gho_", b"ghu_", b"ghs_", b"ghr_", b"github_pat_"),
     rb"gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{60,}"),
    ("private key", (b"-----BEGIN",), rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ("assigned key", (b"_API_KEY", b"_TOKEN", b"_SECRET"),  # placeholders such as your_openai_key_here pass
     rb"_(?:API_KEY|TOKEN|SECRET)\s*[=:]\s*['\"]?(?!your_|<|xxx|changeme)[A-Za-z0-9_\-]{16,}"),
]
CLUSTER_ROOTS = tuple(f"/{r}/".encode() for r in ("blue", "orange", "nfs1"))
CLUSTER_HOSTS = (b"ufhpc", b"hpg.rc.ufl", b".rc.ufl.edu")
SCRUB = [(re.compile(rb"/(?:blue|orange)/[^/\s\"'\\]+/[^/\s\"'\\]+"), b"<cluster>"),
         (re.compile(rb"/(?:nfs1)/[^/\s\"'\\]+"), b"<lab-box>"),
         (re.compile(rb"[A-Za-z0-9.\-]*(?:ufhpc|hpg\.rc\.ufl\.edu|rc\.ufl\.edu)"), b"<host>")]

README = """---
license: other
---
# FinPersona machine backup

Private backup of the FinPersona state on one machine that is not on GitHub, written by `tools/hf_backup.py` on
{date} at commit {head} of github.com/ayeshag7/FinPersona:

- the working tree's untracked and git-ignored files, at their paths from the repository root;
- `_git/`: `local-only.bundle` (the commits no remote had, when there were any), `uncommitted.patch` (the
  uncommitted change to tracked files) and `status.txt` (`git status` at backup time);
- `_outside_repo/<folder>/<name>`: files kept outside the repository.

`results_v2/` is stored as one `.tar.gz` per run group (`results_v2/<phase>/<group>.tar.gz`); member paths are
relative to the repository root. Inside them, cluster storage paths read `<cluster>`, cluster host names `<host>` and
other listed names `<redacted>`; every other byte is as on disk. `MANIFEST.tsv` lists every backed-up file: its path,
its size on disk and the archive that holds it (`-` for a plain file).

Never uploaded: credentials, GPU / Kaggle access files, `datasets/` (third-party data; re-download with
`tools/e1_0_data/`), cluster logs, `.claude/` and Python bytecode.

## Restore

    hf download {repo} --repo-type dataset --local-dir finpersona_backup
    cd finpersona_backup
    for a in results_v2/*/*.tar.gz; do tar -xzf "$a" && rm "$a"; done

Clone github.com/ayeshag7/FinPersona, copy everything except `_git/`, `_outside_repo/`, `README.md` and
`MANIFEST.tsv` into the clone, then inside it:

    git fetch <backup>/_git/local-only.bundle 'refs/heads/*:refs/remotes/backup/*' 'refs/tags/*:refs/tags/*'
    git apply <backup>/_git/uncommitted.patch
"""


def git(*args):
    return subprocess.run(["git", "-c", "core.quotepath=off", *args], cwd=ROOT, capture_output=True, check=True).stdout


def exclusion(rel, extra=()):
    """Why `rel` never leaves this machine, or None."""
    if ENV_NAME.search(rel):
        return "credentials"
    if rel in ACCESS or rel.startswith("tools/cluster/"):
        return "GPU / Kaggle access"
    if "/cluster_logs/" in "/" + rel:
        return "cluster logs"
    if rel.startswith("datasets/"):
        return "third-party data"
    if rel.startswith(".claude/"):
        return "Claude Code settings"
    if "/__pycache__/" in "/" + rel:
        return "Python bytecode"
    if any(rel == e or (e.endswith("/") and rel.startswith(e)) for e in extra):
        return "--exclude-file"
    return None


def archive_of(rel):
    """results_v2/<phase>/<group>/... -> 'results_v2/<phase>/<group>.tar.gz'; anything else '-' (a plain file)."""
    parts = rel.split("/")
    return "/".join(parts[:3]) + ".tar.gz" if parts[0] == "results_v2" and len(parts) >= 4 else "-"


def tier(path):
    """Upload order: metadata and git state, plain files, archives, extras, regenerable caches."""
    if path in ("README.md", "MANIFEST.tsv") or path.startswith("_git/"):
        return 0
    if path.startswith("results_v2/") and path.endswith(".tar.gz"):
        return 2
    if path.startswith("_outside_repo/"):
        return 3
    return 4 if CACHE.search(path) else 1


def plan_path(work):
    return os.path.join(work, "plan.tsv")


def read_plan(work):
    """[(path in the repo, local file, archive or '-')]."""
    if not os.path.exists(plan_path(work)):
        raise SystemExit(f"no plan in {work}: run --stages plan first")
    with open(plan_path(work), encoding="utf-8") as f:
        return [tuple(ln.rstrip("\n").split("\t")) for ln in f]


def plan_sha(work):
    with open(plan_path(work), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def git_state(work):
    """_git/: a bundle of the commits no remote has, the uncommitted diff against HEAD, `git status`.  The bundle's
    commits are also written out as a patch (scanned in its place, never uploaded)."""
    out = os.path.join(work, "meta", "_git")
    os.makedirs(out, exist_ok=True)
    for n in os.listdir(out):
        os.remove(os.path.join(out, n))
    local_only = ("--branches", "--tags", "--not", "--remotes")
    if int(git("rev-list", "--count", *local_only)):
        bundle = os.path.join(out, "local-only.bundle")
        git("bundle", "create", bundle, *local_only)
        git("bundle", "verify", "-q", bundle)
        with open(os.path.join(work, "meta", "local-only.patch"), "wb") as f:
            f.write(git("log", "-p", "--binary", *local_only))
    patch = git("diff", "--binary", "HEAD")
    if patch:
        with open(os.path.join(out, "uncommitted.patch"), "wb") as f:
            f.write(patch)
    with open(os.path.join(out, "status.txt"), "wb") as f:
        f.write(git("status", "--porcelain=v1", "--branch") + git("log", "-1", "--format=HEAD %H %s"))
    return [(f"_git/{n}", os.path.join(out, n)) for n in sorted(os.listdir(out))]


def plan(work, extras, exclude_file):
    more = []
    if exclude_file:
        with open(exclude_file, encoding="utf-8") as f:
            more = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
    listed = [p for args in ((), ("--ignored",))
              for p in git("ls-files", "-z", "--others", "--exclude-standard", *args).decode("utf-8").split("\0") if p]
    rows, dropped = [], collections.Counter()
    for rel in sorted(set(listed)):
        why = exclusion(rel, more)
        if why:
            dropped[why] += 1
        else:
            rows.append((rel, os.path.join(ROOT, *rel.split("/")), archive_of(rel)))
    rows += [(r, p, "-") for r, p in git_state(work)]
    for x in extras:
        x = os.path.abspath(os.path.expanduser(x))
        if not os.path.exists(x):
            raise SystemExit(f"--extra {x} does not exist")
        parent = os.path.dirname(x)
        found = [x] if os.path.isfile(x) else sorted(os.path.join(d, f) for d, _, fs in os.walk(x) for f in fs)
        for p in found:
            rel = os.path.relpath(p, parent).replace(os.sep, "/")
            if ENV_NAME.search(rel):
                dropped["credentials"] += 1
            else:
                rows.append((f"_outside_repo/{os.path.basename(parent)}/{rel}", p, "-"))
    twice = [r for r, n in collections.Counter(r for r, _, _ in rows).items() if n > 1]
    if twice:
        raise SystemExit(f"two --extra paths map to the same backup path, e.g. {twice[0]}")
    with open(plan_path(work), "w", encoding="utf-8", newline="\n") as f:
        f.writelines(f"{r}\t{p}\t{a}\n" for r, p, a in rows)
    plain = [r for r, _, a in rows if a == "-"]
    print(f"{len(listed):,} untracked or ignored; never uploaded: "
          + (", ".join(f"{why} {n:,}" for why, n in dropped.most_common()) or "none"))
    print(f"planned {len(rows):,} files: {len(plain):,} plain, {len(rows) - len(plain):,} in "
          f"{len({a for _, _, a in rows if a != '-'})} results_v2 archives")


def secret_values():
    """[(label, value)]: every key value held in .env / env, which no uploaded byte may contain."""
    out = []
    for name in (".env", "env"):
        path = os.path.join(ROOT, name)
        if not os.path.exists(path):
            continue
        with open(path, "rb") as f:
            for n, line in enumerate(f.read().splitlines(), 1):
                if b"=" in line:
                    key, val = line.split(b"=", 1)
                    val = val.strip().strip(b"'\"")
                    if re.search(rb"KEY|TOKEN|SECRET", key.upper()) and len(val) >= 16:
                        out.append((f"{name}:{key.strip().decode(errors='replace')}", val))
                out += [(f"{name} line {n}", m.group(0)) for _, _, pat in KEY_SHAPES for m in re.finditer(pat, line)]
    return out


def identifiers(path):
    """The generic cluster markers plus the local file's names, as bytes."""
    names = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            names = [ln.strip().encode() for ln in f if ln.strip() and not ln.lstrip().startswith("#")]
    else:
        print(f"no identifiers file at {path}: checking the generic cluster markers only")
    return list(CLUSTER_ROOTS + CLUSTER_HOSTS) + names


def find(path, literals, idents):
    """(credential labels, identifiers) found in one file; never the matched bytes."""
    shapes = [(label, anchors, re.compile(pat)) for label, anchors, pat in KEY_SHAPES]
    secrets, found = set(), set()
    with open(path, "rb") as f:
        tail = b""
        while True:
            block = f.read(CHUNK)
            if not block:
                break
            buf = tail + block
            secrets.update(label for label, value in literals if value in buf)
            for label, anchors, rx in shapes:
                for a in anchors:
                    i = buf.find(a)
                    while i >= 0 and label not in secrets:
                        if rx.search(buf, max(0, i - 64), i + 512):
                            secrets.add(label)
                        i = buf.find(a, i + 1)
            found.update(i.decode() for i in idents if i in buf)
            tail = buf[-OVERLAP:]
    return sorted(secrets), sorted(found)


def _find(job):
    return find(*job)


def load_scan(work):
    path = os.path.join(work, "scan.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def stamp(path):
    st = os.stat(path)
    return [st.st_size, st.st_mtime_ns]


def scan(work, ident_file):
    rows = read_plan(work)
    literals = secret_values()
    idents = identifiers(ident_file)
    rules = hashlib.sha256(repr((sorted(v for _, v in literals), idents, KEY_SHAPES)).encode()).hexdigest()
    before = load_scan(work)
    reuse = before.get("files", {}) if before.get("rules") == rules else {}
    proxy = {"_git/local-only.bundle": os.path.join(work, "meta", "local-only.patch")}
    results, todo = {}, []
    for r, p, _ in rows:
        s = stamp(p)
        if r not in proxy and r in reuse and reuse[r]["stamp"] == s:
            results[r] = reuse[r]
        else:
            results[r] = {"stamp": s}
            todo.append(r)
    paths = dict((r, proxy.get(r, p)) for r, p, _ in rows)
    print(f"{len(literals)} key values from .env / env, {len(idents)} identifiers; scanning {len(todo):,} files "
          f"({len(rows) - len(todo):,} unchanged since the last scan)", flush=True)
    with ProcessPoolExecutor(max_workers=max(1, (os.cpu_count() or 2) - 2)) as ex:
        jobs = ((paths[r], literals, idents) for r in todo)
        for r, (sec, ids) in zip(todo, ex.map(_find, jobs, chunksize=64)):
            results[r].update(secrets=sec, identifiers=ids)
    with open(os.path.join(work, "scan.json"), "w", encoding="utf-8") as f:
        json.dump({"rules": rules, "plan": plan_sha(work), "files": results}, f)
    archived = collections.Counter(a for r, _, a in rows if a != "-" and results[r]["identifiers"])
    for a, n in sorted(archived.items()):
        print(f"  {a}: {n:,} members hold cluster identifiers (redacted when archived)")
    blocked(rows, results, report=True)


def blocked(rows, results, report=False):
    """Files that may not leave: any credential, or an identifier in a plain file."""
    bad = [f"{r}: {', '.join(results[r]['secrets'])}" for r, _, _ in rows if results[r]["secrets"]]
    bad += [f"{r}: {', '.join(results[r]['identifiers'])}" for r, _, a in rows
            if a == "-" and results[r]["identifiers"]]
    if report:
        print(f"refused: {len(bad):,}" + "".join(f"\n  {b}" for b in bad[:40]))
        if bad:
            print("leave these out with --exclude-file (or remove the credential), then plan and scan again")
    return bad


def gate(work, rows):
    """The scan of this exact plan, or refuse: no scan, a stale one, or anything that may not leave."""
    s = load_scan(work)
    if s.get("plan") != plan_sha(work):
        raise SystemExit("no scan of the current plan: run --stages scan")
    if blocked(rows, s["files"]):
        raise SystemExit("REFUSING: the scan found credentials or cluster identifiers: run --stages scan to list them")
    return s["files"]


def scrub(data, idents, name):
    """`data` with cluster paths, host names and listed names replaced; refuses if any identifier survives."""
    for rx, sub in SCRUB:
        data = rx.sub(sub, data)
    for i in idents:
        if i not in CLUSTER_ROOTS + CLUSTER_HOSTS:
            data = data.replace(i, b"<redacted>")
    left = [i.decode() for i in idents if i in data]
    if left:
        raise SystemExit(f"{name} still holds {left} after redaction: leave it out with --exclude-file")
    return data


def build_archive(job):
    """One results_v2 group -> a reproducible .tar.gz, unless an archive of these exact files already exists."""
    arch, members, idents, dst = job
    fingerprint = hashlib.sha256(repr((ARCHIVE_FORMAT, [(r, s) for r, _, s in members], idents)).encode()).hexdigest()
    side = dst + ".json"
    if os.path.exists(dst) and os.path.exists(side):
        with open(side, encoding="utf-8") as f:
            done = json.load(f)
        if done["fingerprint"] == fingerprint:
            return arch, done["members"], done["scrubbed"], "kept", os.path.getsize(dst)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    scrubbed = 0
    with open(dst + ".part", "wb") as raw, \
            gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=6) as gz, \
            tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for rel, path, _ in members:
            info = tar.gettarinfo(path, arcname=rel)
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            with open(path, "rb") as f:
                data = f.read()
            if any(i in data for i in idents):
                data = scrub(data, idents, rel)
                info.size = len(data)
                scrubbed += 1
            tar.addfile(info, io.BytesIO(data))
    with tarfile.open(dst + ".part", "r:gz") as tar:  # read it back: complete and readable
        n = sum(1 for m in tar if m.isfile())
    if n != len(members):
        raise SystemExit(f"{arch}: {n} members read back, {len(members)} written")
    os.replace(dst + ".part", dst)
    with open(side, "w", encoding="utf-8") as f:
        json.dump({"fingerprint": fingerprint, "members": n, "scrubbed": scrubbed}, f)
    return arch, n, scrubbed, "built", os.path.getsize(dst)


def archive(work, ident_file):
    rows = read_plan(work)
    results = gate(work, rows)
    idents = identifiers(ident_file)
    groups = collections.defaultdict(list)
    for r, p, a in rows:
        if a != "-":
            if stamp(p) != results[r]["stamp"]:
                raise SystemExit(f"{r} changed since the scan: run --stages scan,archive again")
            groups[a].append((r, p, results[r]["stamp"]))
    jobs = [(a, sorted(m), idents, os.path.join(work, "archives", *a.split("/")))
            for a, m in sorted(groups.items(), key=lambda kv: -len(kv[1]))]
    with ProcessPoolExecutor(max_workers=2) as ex:
        for a, n, scrubbed, how, size in ex.map(build_archive, jobs):
            print(f"  {how}: {a}  {n:,} files ({scrubbed:,} redacted) -> {size / 1e9:.2f} GB", flush=True)
    meta = os.path.join(work, "meta")
    with open(os.path.join(meta, "MANIFEST.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("path\tbytes\tstored_in\n")
        f.writelines(f"{r}\t{os.path.getsize(p)}\t{a}\n" for r, p, a in rows)
    head = git("rev-parse", "--short", "HEAD").decode().strip()
    with open(os.path.join(meta, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(README.format(date=time.strftime("%d %b %Y"), head=head, repo=HF_REPO))


def items(work, rows):
    """[(path in the repo, local file)] for everything that goes up."""
    meta = os.path.join(work, "meta")
    out = [("README.md", os.path.join(meta, "README.md")), ("MANIFEST.tsv", os.path.join(meta, "MANIFEST.tsv"))]
    out += [(r, p) for r, p, a in rows if a == "-"]
    out += [(a, os.path.join(work, "archives", *a.split("/"))) for a in sorted({a for _, _, a in rows if a != "-"})]
    return out


def digest(path, kind):
    """sha256 of the content, or its git blob id ('blob'), as the Hub reports them."""
    h = hashlib.sha256() if kind == "sha256" else hashlib.sha1(b"blob %d\0" % os.path.getsize(path))
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def same(remote, path):
    """True when the online file holds this local file's content."""
    if remote is None or remote.size != os.path.getsize(path):
        return False
    if remote.lfs is not None:
        return digest(path, "sha256") == remote.lfs.sha256
    return digest(path, "blob") == remote.blob_id


def online(api, repo):
    from huggingface_hub.hf_api import RepoFile
    return {f.path: f for f in api.list_repo_tree(repo, repo_type="dataset", recursive=True) if isinstance(f, RepoFile)}


def compare(api, repo, wanted):
    """[(path, local file, True when online and identical)]."""
    remote = online(api, repo)
    with ThreadPoolExecutor(max_workers=8) as ex:
        ok = list(ex.map(lambda it: same(remote.get(it[0]), it[1]), wanted))
    return remote, [(r, p, good) for (r, p), good in zip(wanted, ok)]


def upload(work, repo, tiers):
    from huggingface_hub import CommitOperationAdd, HfApi
    rows = read_plan(work)
    results = gate(work, rows)
    moved = [r for r, p, a in rows if a == "-" and stamp(p) != results[r]["stamp"]]
    if moved:
        raise SystemExit(f"{len(moved):,} files changed since the scan, e.g. {moved[0]}: run --stages scan again")
    wanted = [it for it in items(work, rows) if tiers is None or tier(it[0]) in tiers]
    unbuilt = [r for r, p in wanted if not os.path.exists(p)]
    if unbuilt:
        raise SystemExit(f"not built: {unbuilt[0]} and {len(unbuilt) - 1} more: run --stages archive first")
    api = HfApi()
    api.create_repo(repo, repo_type="dataset", private=True, exist_ok=True)
    if not api.repo_info(repo, repo_type="dataset").private:
        raise SystemExit(f"REFUSING: {repo} is not private")
    _, checked = compare(api, repo, wanted)
    todo = sorted(((r, p) for r, p, good in checked if not good), key=lambda it: tier(it[0]))
    total = sum(os.path.getsize(p) for _, p in todo)
    print(f"{len(checked) - len(todo):,} files already online and identical; {len(todo):,} to upload "
          f"({total / 1e9:.2f} GB)", flush=True)
    batches, cur, cur_bytes = [], [], 0
    for r, p in todo:
        size = os.path.getsize(p)
        if cur and (len(cur) >= BATCH or cur_bytes + size > BATCH_BYTES or tier(r) != tier(cur[0][0])):
            batches.append(cur)
            cur, cur_bytes = [], 0
        cur.append((r, p))
        cur_bytes += size
    if cur:
        batches.append(cur)
    done = done_bytes = 0
    for k, batch in enumerate(batches, 1):
        msg = f"Backup {batch[0][0]}" if len(batch) == 1 else f"Backup {len(batch)} files from {batch[0][0]}"
        for attempt in range(1, 4):
            try:
                api.create_commit(repo, [CommitOperationAdd(path_in_repo=r, path_or_fileobj=p) for r, p in batch],
                                  repo_type="dataset", commit_message=msg)
                break
            except Exception as e:  # network hiccups: retry, then stop; a rerun resumes
                if attempt == 3:
                    raise
                print(f"  commit {k} failed ({type(e).__name__}: {e}); retry {attempt}", flush=True)
                time.sleep(30 * attempt)
        done += len(batch)
        done_bytes += sum(os.path.getsize(p) for _, p in batch)
        print(f"  commit {k}/{len(batches)}: {done:,}/{len(todo):,} files, {done_bytes / 1e9:.2f}/{total / 1e9:.2f} GB",
              flush=True)


def verify(work, repo):
    from huggingface_hub import HfApi
    rows = read_plan(work)
    api = HfApi()
    planned = items(work, rows)
    wanted = [(r, p) for r, p in planned if os.path.exists(p)]
    remote, checked = compare(api, repo, wanted)
    missing = [r for r, _, good in checked if not good and r not in remote]
    differ = [r for r, _, good in checked if not good and r in remote]
    only_online = sorted(set(remote) - {r for r, _ in planned} - {".gitattributes"})
    print(f"{repo} private: {api.repo_info(repo, repo_type='dataset').private}; {len(checked):,} planned files "
          f"checked: missing {len(missing)}, different {len(differ)}"
          + (f"; {len(planned) - len(wanted)} not built here" if len(wanted) < len(planned) else "")
          + f"; {len(only_online)} only in the backup")
    for label, lst in (("missing", missing), ("different", differ), ("only in the backup", only_online)):
        for r in lst[:10]:
            print(f"  {label}: {r}")
    if missing or differ:
        raise SystemExit(1)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Back up what GitHub does not have to a private Hugging Face repo.")
    ap.add_argument("--stages", default=",".join(STAGES))
    ap.add_argument("--extra", action="append", default=[], help="a file or folder outside the repo (repeatable)")
    ap.add_argument("--exclude-file", help="more repo paths to leave out, one per line: exact, or prefixes ending '/'")
    ap.add_argument("--identifiers", default=IDENTIFIERS, help="names that must never leave this machine")
    ap.add_argument("--work", default=WORK)
    ap.add_argument("--repo", default=HF_REPO)
    ap.add_argument("--tiers", help="upload only these, comma-separated: "
                                    + "; ".join(f"{k} {v}" for k, v in TIERS.items()))
    args = ap.parse_args(argv)
    stages = args.stages.split(",")
    if set(stages) - set(STAGES):
        ap.error(f"unknown stage(s) {sorted(set(stages) - set(STAGES))}; known: {', '.join(STAGES)}")
    os.makedirs(args.work, exist_ok=True)
    for stage in stages:
        print(f"== {stage}", flush=True)
        if stage == "plan":
            plan(args.work, args.extra, args.exclude_file)
        elif stage == "scan":
            scan(args.work, args.identifiers)
        elif stage == "archive":
            archive(args.work, args.identifiers)
        elif stage == "upload":
            upload(args.work, args.repo, {int(t) for t in args.tiers.split(",")} if args.tiers else None)
        else:
            verify(args.work, args.repo)


if __name__ == "__main__":
    main()
