"""Configuration for the evaluation harness."""

from dataclasses import dataclass


@dataclass
class EvalConfig:
    """Configuration for running tutor evaluations."""

    # Model settings — default to same model for all roles
    tutor_model: str = "Qwen/Qwen2.5-14B-Instruct"
    judge_model: str = "Qwen/Qwen2.5-14B-Instruct"
    student_model: str = "Qwen/Qwen2.5-14B-Instruct"

    # Eval settings
    num_conversations: int = 10
    max_turns_per_conversation: int = 5

    # Paths
    scenarios_path: str = "eval/scenarios.json"
    output_path: str = "eval/results.json"
    course_materials_path: str = "course_materials"
