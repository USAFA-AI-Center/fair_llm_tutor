"""Run manifest: captures code state for each pipeline run.

Writes a ``run_manifest.json`` that records exactly which code produced
which scores, enabling before/after comparisons across runs.

The manifest includes:
  - Timestamp and run ID
  - Git commit hash (or "uncommitted" with dirty file list)
  - SHA-256 checksums of key source files
  - Per-session and overall quality scores
"""

import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# Files whose content directly affects tutor behavior.
# Changes here are the most likely cause of score differences.
_TRACKED_FILES: tuple[str, ...] = (
    "agents/tutor_agent.py",
    "main.py",
    "tools/sanitize.py",
    "tools/schemas.py",
    "tools/retrieval_tools.py",
    "tools/history_tools.py",
    "tools/hint_level_tools.py",
    "tools/conversation_state_tools.py",
    "config.py",
)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _sha256(path: Path) -> str:
    """Return hex SHA-256 of a file, or 'missing' if it doesn't exist."""
    if not path.is_file():
        return "missing"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_info() -> dict:
    """Gather git state: commit hash, branch, dirty status, and diff summary.

    When the working tree is dirty (uncommitted changes), the manifest captures
    ``diff_stat`` (files changed / insertions / deletions) and ``diff_summary``
    (per-file change counts).  This makes it explicit that the *uncommitted*
    code — not the last commit — is what produced the session scores.
    """
    info: dict = {
        "commit": "unknown",
        "branch": "unknown",
        "dirty": True,
        "dirty_files": [],
        "diff_stat": "",
        "diff_summary": [],
    }
    git_bin = shutil.which("git") or "/usr/bin/git"

    def _git(*args: str) -> str:
        return subprocess.check_output(
            [git_bin, *args],
            cwd=str(_PROJECT_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()

    try:
        info["commit"] = _git("rev-parse", "HEAD")
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    try:
        info["branch"] = _git("rev-parse", "--abbrev-ref", "HEAD")
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    try:
        status = _git("status", "--porcelain")
        info["dirty"] = bool(status)
        if status:
            info["dirty_files"] = [
                line.strip() for line in status.splitlines()[:20]
            ]
            # Capture diff --stat so we know exactly what changed
            try:
                # Staged + unstaged changes against HEAD
                stat = _git("diff", "HEAD", "--stat")
                info["diff_stat"] = stat
                # Per-file summary (e.g. "main.py | 12 +++---")
                info["diff_summary"] = [
                    line.strip()
                    for line in stat.splitlines()
                    if "|" in line
                ][:30]
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    return info


def _file_checksums() -> dict[str, str]:
    """Compute SHA-256 for each tracked file."""
    return {
        rel: _sha256(_PROJECT_ROOT / rel)
        for rel in _TRACKED_FILES
    }


def create_manifest(
    run_dir: Path,
    session_scores: list[dict] | None = None,
) -> Path:
    """Write ``run_manifest.json`` into *run_dir* and return its path.

    Args:
        run_dir: The timestamped run directory.
        session_scores: Optional list of per-session score dicts
            (as returned by ``report.analyze_scored_session``).
    """
    scored = session_scores or []
    dims = ("safety", "pedagogy", "helpfulness", "domain_accuracy")

    # Compute overall means
    sessions_with_scores = [s for s in scored if s.get("scored_turns", 0) > 0]
    dim_means: dict[str, float] = {}
    for dim in dims:
        vals = [s[dim] for s in sessions_with_scores if dim in s]
        dim_means[dim] = round(sum(vals) / len(vals), 2) if vals else 0.0
    overall = round(sum(dim_means.values()) / len(dims), 2) if dim_means else 0.0

    git = _git_info()

    # Explicit attribution: what code state produced these scores?
    if git["dirty"]:
        code_attribution = (
            f"Scores produced by UNCOMMITTED changes on top of "
            f"commit {git['commit'][:8]} ({git['branch']}). "
            f"See diff_stat and diff_summary for what changed."
        )
    else:
        code_attribution = (
            f"Scores produced by committed code at "
            f"{git['commit'][:8]} ({git['branch']})."
        )

    manifest = {
        "run_id": run_dir.name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "code_attribution": code_attribution,
        "git": git,
        "file_checksums": _file_checksums(),
        "scores": {
            "overall": overall,
            "dimensions": dim_means,
            "per_session": {
                s["name"]: {
                    "overall": s.get("overall", 0),
                    **{d: s.get(d, 0) for d in dims},
                }
                for s in sessions_with_scores
            },
        },
        "sessions_count": len(scored),
        "total_failure_turns": sum(len(s.get("failures", [])) for s in scored),
    }

    manifest_path = run_dir / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path
