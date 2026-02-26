"""Eval harness that orchestrates simulated student conversations and scoring."""

import json
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Callable, Awaitable

from eval.eval_config import EvalConfig
from eval.scenarios import Scenario, load_scenarios
from eval.simulated_student import SimulatedStudent
from eval.eval_judge import EvalJudge, JudgeScores

from fairlib.core.interfaces.llm import AbstractChatModel

logger = logging.getLogger(__name__)


@dataclass
class ConversationResult:
    """Result of a single simulated conversation."""
    scenario_name: str
    turns: List[Dict[str, str]]
    scores: List[JudgeScores]

    def avg_score(self, dimension: str) -> float:
        if not self.scores:
            return 0.0
        values = [getattr(s, dimension) for s in self.scores]
        return sum(values) / len(values)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_name": self.scenario_name,
            "turns": self.turns,
            "scores": [s.model_dump() for s in self.scores],
            "avg_safety": self.avg_score("safety"),
            "avg_pedagogy": self.avg_score("pedagogy"),
            "avg_helpfulness": self.avg_score("helpfulness"),
            "avg_domain_accuracy": self.avg_score("domain_accuracy"),
        }


@dataclass
class EvalReport:
    """Aggregated evaluation report."""
    results: List[ConversationResult]

    def aggregate(self) -> Dict[str, float]:
        if not self.results:
            return {"safety": 0, "pedagogy": 0, "helpfulness": 0, "domain_accuracy": 0}
        dims = ["safety", "pedagogy", "helpfulness", "domain_accuracy"]
        return {
            dim: sum(r.avg_score(dim) for r in self.results) / len(self.results)
            for dim in dims
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "aggregate": self.aggregate(),
            "conversations": [r.to_dict() for r in self.results],
            "num_scenarios": len(self.results),
        }


class EvalHarness:
    """Orchestrator that runs simulated conversations and scores them."""

    def __init__(
        self,
        config: EvalConfig,
        tutor_fn: Callable[[str, str, str], Awaitable[str]],
        student_llm: AbstractChatModel,
        judge_llm: AbstractChatModel,
    ):
        """
        Args:
            config: Evaluation configuration
            tutor_fn: Async function (problem, student_work, topic) -> tutor_response.
                      Typically TutorSession.process_student_work.
            student_llm: LLM for simulated student
            judge_llm: LLM for judge
        """
        self.config = config
        self.tutor_fn = tutor_fn
        self.student_llm = student_llm
        self.judge_llm = judge_llm
        self.judge = EvalJudge(judge_llm)

    async def run_scenario(self, scenario: Scenario) -> ConversationResult:
        """Run a single scenario: initial submission + multi-turn conversation."""
        student = SimulatedStudent(self.student_llm, scenario)
        turns: List[Dict[str, str]] = []
        scores: List[JudgeScores] = []

        # Initial student submission
        student_msg = scenario.student_work

        for turn_num in range(self.config.max_turns_per_conversation):
            # Tutor responds
            tutor_response = await self.tutor_fn(
                scenario.problem, student_msg, scenario.domain
            )

            turns.append({
                "turn": turn_num + 1,
                "student": student_msg,
                "tutor": tutor_response,
            })

            # Judge scores the tutor response
            score = self.judge.score(scenario, tutor_response)
            scores.append(score)

            # Simulated student responds for next turn
            if turn_num < self.config.max_turns_per_conversation - 1:
                student_msg = student.respond(tutor_response)

        return ConversationResult(
            scenario_name=scenario.name,
            turns=turns,
            scores=scores,
        )

    async def run(self, scenarios: List[Scenario] | None = None) -> EvalReport:
        """Run eval across all scenarios."""
        if scenarios is None:
            scenarios = load_scenarios(self.config.scenarios_path)

        results = []
        for i, scenario in enumerate(scenarios):
            logger.info(f"Running scenario {i+1}/{len(scenarios)}: {scenario.name}")
            result = await self.run_scenario(scenario)
            results.append(result)

        report = EvalReport(results=results)
        logger.info(f"Eval complete. Aggregate: {report.aggregate()}")
        return report
