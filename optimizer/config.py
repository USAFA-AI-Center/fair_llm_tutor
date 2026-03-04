"""Configuration for the self-improving optimizer loop."""

from dataclasses import dataclass


# Scenarios covering HINT + CONCEPT_EXPLANATION modes, STEM + non-STEM,
# wrong + correct answers.
CORE5_SCENARIOS = [
    "derivatives",       # HINT, STEM, wrong answer
    "algebra",           # HINT, STEM, wrong answer
    "ml_basics",         # CONCEPT_EXPLANATION, STEM
    "history_dates",     # HINT, non-STEM, wrong answer
    "physics_momentum",  # HINT, STEM, correct answer (confirm_correct)
]

# Files the optimizer is allowed to modify.
MODIFIABLE_FILES = [
    "agents/tutor_agent.py",
    "tools/safety_tools.py",
    "tools/diagnostic_tools.py",
    "tools/pedagogical_tools.py",
    "tools/schemas.py",
    "config.py",
]

# Files the optimizer must never touch.
OFF_LIMITS_PATTERNS = [
    "main.py",
    "tests/",
    "student_mode/",
    "optimizer/",
]


@dataclass
class OptimizerConfig:
    """All knobs for the optimizer loop."""

    # ── Scoring weights (must sum to 1.0) ──────────────────────────────
    weight_safety: float = 0.35
    weight_pedagogy: float = 0.25
    weight_helpfulness: float = 0.25
    weight_domain_accuracy: float = 0.15

    # ── Iteration budget ───────────────────────────────────────────────
    max_iterations: int = 10

    # ── Scenario selection ─────────────────────────────────────────────
    # "core5" runs 5 representative scenarios; "all" runs all 17.
    scenario_set: str = "core5"

    # ── LLM models ─────────────────────────────────────────────────────
    optimizer_model: str = "claude-sonnet-4-20250514"
    judge_provider: str = "anthropic"
    judge_model: str = "claude-sonnet-4-20250514"

    # ── Session settings ───────────────────────────────────────────────
    max_turns: int = 8
    min_turns: int = 3
    session_timeout: int = 300

    # ── Change constraints ─────────────────────────────────────────────
    max_files_per_iteration: int = 2
    max_changes_per_file: int = 3

    # ── Plateau detection ──────────────────────────────────────────────
    plateau_threshold: float = 0.02
    plateau_patience: int = 3

    # ── Near-perfect early stop ────────────────────────────────────────
    near_perfect_score: float = 4.8

    # ── Paths ──────────────────────────────────────────────────────────
    tracker_path: str = "optimizer/history.json"
    runs_dir: str = "optimizer/runs"

    @property
    def weights(self) -> dict[str, float]:
        return {
            "safety": self.weight_safety,
            "pedagogy": self.weight_pedagogy,
            "helpfulness": self.weight_helpfulness,
            "domain_accuracy": self.weight_domain_accuracy,
        }

    def get_scenario_names(self) -> list[str]:
        if self.scenario_set == "all":
            from student_mode.scenarios import scenario_names
            return scenario_names()
        return list(CORE5_SCENARIOS)
