"""Claude API change proposals for the optimizer loop.

Sends current scores, source code, and history to Claude and receives
structured search/replace change proposals.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

import anthropic

from optimizer.config import MODIFIABLE_FILES, OFF_LIMITS_PATTERNS, OptimizerConfig
from optimizer.tracker import IterationScore, Tracker

logger = logging.getLogger(__name__)


@dataclass
class Change:
    """A single search/replace change."""
    file_path: str
    search: str
    replace: str
    rationale: str = ""


@dataclass
class Proposal:
    """A structured change proposal from Claude."""
    hypothesis: str
    changes: list[Change] = field(default_factory=list)
    expected_impact: str = ""
    risk_assessment: str = ""


SYSTEM_PROMPT = """\
You are an expert optimizer for a Socratic tutoring system. Your job is to \
propose small, targeted changes to improve tutor quality scores.

## System Architecture

The tutor uses a single TutorAgent (SimpleAgent with ReAct planning) and three tools:
1. **student_work_analyzer** — Diagnoses student errors using RAG-backed course materials.
2. **socratic_hint_generator** — Generates Socratic hints (HINT mode) or concept \
explanations (CONCEPT_EXPLANATION mode). Escalating hint levels 1-4.
3. **answer_revelation_analyzer** — Validates responses don't reveal answers (LLM-based).

## Scoring Dimensions (1-5 scale)
- **safety** (weight 0.35): Does the tutor avoid revealing answers?
- **pedagogy** (weight 0.25): Is the response Socratic (guiding questions, not telling)?
- **helpfulness** (weight 0.25): Would the student learn from this?
- **domain_accuracy** (weight 0.15): Is the feedback factually correct?

## Constraints
- You may ONLY modify these files: {modifiable_files}
- You must NEVER modify: main.py, tests/*, student_mode/*, optimizer/*
- Maximum {max_files} files per proposal
- Maximum {max_changes} changes per file
- Use exact search/replace blocks — the search string must appear exactly once in the file
- Focus on prompt engineering, heuristic tuning, and configuration — not structural refactors
- Never remove safety checks or weaken answer-revelation detection
- The tutor must remain domain-agnostic

## Response Format
Respond with ONLY valid JSON (no markdown fences, no commentary):
{{
    "hypothesis": "Brief description of what you're changing and why",
    "changes": [
        {{
            "file_path": "relative/path/to/file.py",
            "search": "exact text to find (must be unique in file)",
            "replace": "replacement text",
            "rationale": "why this change should improve scores"
        }}
    ],
    "expected_impact": "Which dimensions should improve and by roughly how much",
    "risk_assessment": "What could go wrong; which dimensions might regress"
}}
"""


def _read_modifiable_sources() -> dict[str, str]:
    """Read all modifiable source files, returning {path: content}."""
    sources = {}
    for rel_path in MODIFIABLE_FILES:
        path = Path(rel_path)
        if path.exists():
            sources[rel_path] = path.read_text(encoding="utf-8")
        else:
            logger.warning("Modifiable file not found: %s", rel_path)
    return sources


def _build_user_prompt(
    scores: IterationScore,
    tracker: Tracker,
    sources: dict[str, str],
) -> str:
    """Build the dynamic user prompt with scores, history, and source code."""
    parts = []

    # Current scores
    parts.append("## Current Scores\n")
    parts.append(f"Weighted aggregate: {scores.weighted:.3f}\n")
    parts.append(f"  safety:          {scores.dimensions.safety:.2f}\n")
    parts.append(f"  pedagogy:        {scores.dimensions.pedagogy:.2f}\n")
    parts.append(f"  helpfulness:     {scores.dimensions.helpfulness:.2f}\n")
    parts.append(f"  domain_accuracy: {scores.dimensions.domain_accuracy:.2f}\n\n")

    # Per-scenario breakdown
    parts.append("## Per-Scenario Breakdown\n")
    for s in scores.per_scenario:
        parts.append(f"\n### {s.scenario} (weighted: {s.weighted:.3f}, turns: {s.turn_count})\n")
        parts.append(f"  safety={s.dimensions.safety:.2f} pedagogy={s.dimensions.pedagogy:.2f} "
                      f"helpfulness={s.dimensions.helpfulness:.2f} accuracy={s.dimensions.domain_accuracy:.2f}\n")
        if s.judge_reasoning:
            # Include first 2 reasoning samples to keep prompt manageable
            for i, reason in enumerate(s.judge_reasoning[:2]):
                if reason:
                    parts.append(f"  Judge reasoning (turn {i+1}): {reason[:300]}\n")

    # Highlight worst dimension and worst scenario
    dims = {
        "safety": scores.dimensions.safety,
        "pedagogy": scores.dimensions.pedagogy,
        "helpfulness": scores.dimensions.helpfulness,
        "domain_accuracy": scores.dimensions.domain_accuracy,
    }
    worst_dim = min(dims, key=dims.get)
    parts.append(f"\n## Attention: Worst dimension is **{worst_dim}** ({dims[worst_dim]:.2f})\n")

    if scores.per_scenario:
        worst_scenario = min(scores.per_scenario, key=lambda s: s.weighted)
        parts.append(f"Worst scenario is **{worst_scenario.scenario}** ({worst_scenario.weighted:.3f})\n\n")

    # Score trend
    trend = tracker.get_score_trend()
    if trend:
        parts.append("## Score History\n")
        for entry in trend:
            parts.append(f"  iter={entry['iteration']} weighted={entry['weighted']:.3f}")
            if "status" in entry:
                parts.append(f" ({entry['status']})")
            parts.append("\n")
        parts.append("\n")

    # Previous changes tried
    prev_changes = tracker.get_previous_changes()
    if prev_changes:
        parts.append("## Previous Changes (avoid repeating failed approaches)\n")
        for pc in prev_changes[-10:]:  # Last 10 changes max
            parts.append(f"  iter={pc['iteration']} status={pc['status']}: "
                          f"{pc.get('hypothesis', 'N/A')}\n")
            parts.append(f"    file={pc.get('file_path', '?')}: {pc.get('rationale', '')[:150]}\n")
        parts.append("\n")

    # Source code of all modifiable files
    parts.append("## Source Code of Modifiable Files\n")
    for rel_path, content in sources.items():
        parts.append(f"\n### {rel_path}\n```python\n{content}\n```\n")

    return "".join(parts)


def propose_changes(
    config: OptimizerConfig,
    scores: IterationScore,
    tracker: Tracker,
) -> Proposal:
    """Call Claude API to propose code changes based on current scores.

    Args:
        config: Optimizer configuration.
        scores: Current iteration's scores.
        tracker: Score history tracker.

    Returns:
        A Proposal with hypothesis, changes, expected impact, and risk.
    """
    sources = _read_modifiable_sources()
    user_prompt = _build_user_prompt(scores, tracker, sources)

    system = SYSTEM_PROMPT.format(
        modifiable_files=", ".join(MODIFIABLE_FILES),
        max_files=config.max_files_per_iteration,
        max_changes=config.max_changes_per_file,
    )

    client = anthropic.Anthropic()
    logger.info("Calling %s for change proposal...", config.optimizer_model)

    response = client.messages.create(
        model=config.optimizer_model,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text.strip()

    # Parse JSON — strip markdown fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse proposal JSON: %s\nRaw:\n%s", e, raw[:500])
        return Proposal(
            hypothesis="PARSE_FAILURE",
            expected_impact="N/A",
            risk_assessment=f"JSON parse error: {e}",
        )

    # Validate changes
    changes = []
    files_touched = set()
    for c in data.get("changes", []):
        file_path = c.get("file_path", "")

        # Security: normalize and reject path traversal
        file_path = os.path.normpath(file_path)
        if ".." in file_path or os.path.isabs(file_path):
            logger.warning("Rejecting path traversal attempt: %s", file_path)
            continue

        # Security: reject off-limits files
        if any(file_path.startswith(pat) or file_path == pat for pat in OFF_LIMITS_PATTERNS):
            logger.warning("Rejecting change to off-limits file: %s", file_path)
            continue

        if file_path not in MODIFIABLE_FILES:
            logger.warning("Rejecting change to non-modifiable file: %s", file_path)
            continue

        # Enforce max_files constraint
        files_touched.add(file_path)
        if len(files_touched) > config.max_files_per_iteration:
            logger.warning("Skipping change — max files (%d) exceeded", config.max_files_per_iteration)
            continue

        # Enforce max_changes_per_file constraint
        file_change_count = sum(1 for ch in changes if ch.file_path == file_path)
        if file_change_count >= config.max_changes_per_file:
            logger.warning("Skipping change — max changes per file (%d) for %s",
                            config.max_changes_per_file, file_path)
            continue

        changes.append(Change(
            file_path=file_path,
            search=c.get("search", ""),
            replace=c.get("replace", ""),
            rationale=c.get("rationale", ""),
        ))

    return Proposal(
        hypothesis=data.get("hypothesis", ""),
        changes=changes,
        expected_impact=data.get("expected_impact", ""),
        risk_assessment=data.get("risk_assessment", ""),
    )
