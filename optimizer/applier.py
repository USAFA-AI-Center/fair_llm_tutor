"""Git branch management and test guardrail for the optimizer loop.

Creates iteration branches, applies search/replace changes, runs the
test suite, and commits or reverts.
"""

import logging
import py_compile
import subprocess
from pathlib import Path

from optimizer.proposer import Proposal

logger = logging.getLogger(__name__)


def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + list(args),
        capture_output=True, text=True, check=check,
    )


def get_current_branch() -> str:
    result = run_git("rev-parse", "--abbrev-ref", "HEAD")
    return result.stdout.strip()


def create_iteration_branch(iteration: int) -> str:
    """Create and checkout ``optimizer/iter-{NNN}`` from the current best.

    Returns the branch name.
    """
    branch = f"optimizer/iter-{iteration:03d}"
    run_git("checkout", "-b", branch)
    logger.info("Created branch %s", branch)
    return branch


def apply_changes(proposal: Proposal) -> tuple[bool, list[str]]:
    """Apply search/replace changes from a proposal.

    For each change:
      1. Verify the search string appears exactly once.
      2. Apply the replacement.
      3. Syntax-check the modified file with py_compile.

    Returns:
        (success, errors) — True if all changes applied, list of error messages.
    """
    errors = []
    modified_files = []

    for i, change in enumerate(proposal.changes):
        path = Path(change.file_path)
        if not path.exists():
            errors.append(f"Change {i}: file not found: {change.file_path}")
            continue

        content = path.read_text(encoding="utf-8")

        # Verify search string appears exactly once
        count = content.count(change.search)
        if count == 0:
            errors.append(
                f"Change {i} ({change.file_path}): search string not found. "
                f"First 80 chars: {change.search[:80]!r}"
            )
            continue
        if count > 1:
            errors.append(
                f"Change {i} ({change.file_path}): search string appears {count} times "
                f"(must be unique). First 80 chars: {change.search[:80]!r}"
            )
            continue

        # Apply replacement
        new_content = content.replace(change.search, change.replace, 1)
        path.write_text(new_content, encoding="utf-8")
        modified_files.append(change.file_path)
        logger.info("Applied change %d to %s", i, change.file_path)

    # Syntax-check all modified files
    for fpath in modified_files:
        try:
            py_compile.compile(fpath, doraise=True)
        except py_compile.PyCompileError as e:
            errors.append(f"Syntax error in {fpath}: {e}")
            logger.error("Syntax error after change: %s", e)

    if errors:
        return False, errors
    return True, []


def run_tests() -> tuple[bool, str]:
    """Run the full test suite. Returns (passed, output)."""
    logger.info("Running pytest...")
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
        capture_output=True, text=True, timeout=300,
    )
    output = result.stdout + "\n" + result.stderr
    passed = result.returncode == 0
    if passed:
        logger.info("All tests passed")
    else:
        logger.warning("Tests failed (exit code %d)", result.returncode)
    return passed, output


def commit_changes(proposal: Proposal, iteration: int) -> bool:
    """Stage and commit all modified files.

    Returns True if commit succeeded.
    """
    files = list({c.file_path for c in proposal.changes})
    for f in files:
        run_git("add", f)

    msg = (
        f"optimizer: iteration {iteration}\n\n"
        f"Hypothesis: {proposal.hypothesis}\n"
        f"Expected impact: {proposal.expected_impact}\n"
        f"Risk: {proposal.risk_assessment}"
    )
    result = run_git("commit", "-m", msg, check=False)
    if result.returncode != 0:
        logger.error("Commit failed: %s", result.stderr)
        return False
    logger.info("Committed iteration %d", iteration)
    return True


def revert_and_return(original_branch: str) -> None:
    """Discard uncommitted changes and switch back to the given branch."""
    run_git("checkout", "--", ".", check=False)
    run_git("checkout", original_branch, check=False)
    logger.info("Reverted to %s", original_branch)
