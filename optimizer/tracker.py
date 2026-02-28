"""Score history persistence for the optimizer loop.

Reads/writes ``optimizer/history.json`` so the loop can resume, detect
plateaus, and feed previous-change context to the proposer.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from optimizer.config import OptimizerConfig

logger = logging.getLogger(__name__)


@dataclass
class DimensionScores:
    """Per-dimension averages across all scenarios in one run."""
    safety: float = 0.0
    pedagogy: float = 0.0
    helpfulness: float = 0.0
    domain_accuracy: float = 0.0


@dataclass
class ScenarioScore:
    """Scores for a single scenario in one run."""
    scenario: str
    dimensions: DimensionScores = field(default_factory=DimensionScores)
    weighted: float = 0.0
    turn_count: int = 0
    judge_reasoning: list[str] = field(default_factory=list)


@dataclass
class IterationScore:
    """Aggregate score for one optimizer iteration."""
    iteration: int
    per_scenario: list[ScenarioScore] = field(default_factory=list)
    dimensions: DimensionScores = field(default_factory=DimensionScores)
    weighted: float = 0.0


@dataclass
class IterationRecord:
    """Full record of one optimizer iteration, persisted to history.json."""
    iteration: int
    scores: IterationScore = field(default_factory=lambda: IterationScore(iteration=-1))
    hypothesis: str = ""
    branch: str = ""
    status: str = ""  # improved, regressed, tests_failed, apply_failed
    changes: list[dict] = field(default_factory=list)


class Tracker:
    """Manages optimizer/history.json."""

    def __init__(self, config: OptimizerConfig):
        self.config = config
        self.path = Path(config.tracker_path)
        self._history: dict = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            with open(self.path, "r") as f:
                return json.load(f)
        return {"baseline": None, "iterations": [], "best_iteration": None}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self._history, f, indent=2)

    def record_baseline(self, scores: IterationScore) -> None:
        self._history["baseline"] = asdict(scores)
        self._history["best_iteration"] = None  # baseline is the starting point
        self._save()
        logger.info("Recorded baseline: weighted=%.3f", scores.weighted)

    def record_iteration(self, record: IterationRecord) -> None:
        self._history["iterations"].append(asdict(record))
        if record.status == "improved":
            self._history["best_iteration"] = record.iteration
        self._save()
        logger.info(
            "Recorded iteration %d: status=%s weighted=%.3f",
            record.iteration, record.status, record.scores.weighted,
        )

    def get_baseline_score(self) -> Optional[float]:
        b = self._history.get("baseline")
        return b["weighted"] if b else None

    def get_best(self) -> tuple[Optional[int], float]:
        """Return (iteration_number, weighted_score) of the best run.

        Returns (None, baseline_weighted) if baseline is still best.
        """
        best_iter = self._history.get("best_iteration")
        if best_iter is not None:
            for rec in self._history["iterations"]:
                if rec["iteration"] == best_iter:
                    return best_iter, rec["scores"]["weighted"]
        # Fall back to baseline
        baseline = self._history.get("baseline")
        if baseline:
            return None, baseline["weighted"]
        return None, 0.0

    def get_best_branch(self) -> Optional[str]:
        best_iter = self._history.get("best_iteration")
        if best_iter is not None:
            for rec in self._history["iterations"]:
                if rec["iteration"] == best_iter:
                    return rec.get("branch")
        return None

    def is_plateaued(self) -> bool:
        """True if the last ``patience`` iterations all improved less than threshold."""
        iters = self._history.get("iterations", [])
        patience = self.config.plateau_patience
        threshold = self.config.plateau_threshold

        if len(iters) < patience:
            return False

        _, best_score = self.get_best()
        recent = iters[-patience:]
        return all(
            abs(r["scores"]["weighted"] - best_score) < threshold
            for r in recent
        )

    def get_previous_changes(self) -> list[dict]:
        """Return all changes from previous iterations for prompt context."""
        changes = []
        for rec in self._history.get("iterations", []):
            for change in rec.get("changes", []):
                changes.append({
                    "iteration": rec["iteration"],
                    "status": rec["status"],
                    "hypothesis": rec["hypothesis"],
                    **change,
                })
        return changes

    def get_iteration_count(self) -> int:
        return len(self._history.get("iterations", []))

    def get_score_trend(self) -> list[dict]:
        """Return a compact score trend for the proposer prompt."""
        trend = []
        baseline = self._history.get("baseline")
        if baseline:
            trend.append({
                "iteration": "baseline",
                "weighted": baseline["weighted"],
                "safety": baseline["dimensions"]["safety"],
                "pedagogy": baseline["dimensions"]["pedagogy"],
                "helpfulness": baseline["dimensions"]["helpfulness"],
                "domain_accuracy": baseline["dimensions"]["domain_accuracy"],
            })
        for rec in self._history.get("iterations", []):
            trend.append({
                "iteration": rec["iteration"],
                "weighted": rec["scores"]["weighted"],
                "safety": rec["scores"]["dimensions"]["safety"],
                "pedagogy": rec["scores"]["dimensions"]["pedagogy"],
                "helpfulness": rec["scores"]["dimensions"]["helpfulness"],
                "domain_accuracy": rec["scores"]["dimensions"]["domain_accuracy"],
                "status": rec["status"],
            })
        return trend
