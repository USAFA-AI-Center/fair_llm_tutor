# tutor_agent.py

import re

from fairlib.modules.agent.simple_agent import SimpleAgent
from fairlib.modules.planning.react_planner import ReActPlanner, SimpleReActPlanner
from fairlib.modules.action.executor import ToolExecutor
from fairlib.modules.action.tools.registry import ToolRegistry
from fairlib.core.interfaces.llm import AbstractChatModel
from fairlib.core.interfaces.memory import AbstractMemory, AbstractRetriever

from fairlib.core.prompts import (
    PromptBuilder,
    RoleDefinition,
    FormatInstruction,
    Example,
)

from tools.safety_tools import AnswerRevelationAnalyzerTool
from tools.diagnostic_tools import StudentWorkAnalyzerTool
from tools.pedagogical_tools import SocraticHintGeneratorTool


class TutorAgent(SimpleAgent):
    """
    Single-agent Socratic tutor that speaks directly to the student.

    Replaces the multi-agent hierarchy (manager + 3 workers) with one
    SimpleAgent using a ReActPlanner and three tools:
      - student_work_analyzer (diagnosis)
      - socratic_hint_generator (hints & concept explanations)
      - answer_revelation_analyzer (safety validation)

    The agent reasons via ReAct (Thought → Action → Observation) and
    addresses the student in second person. No delegation, no synthesis
    step, no third-person leakage.
    """

    @classmethod
    def create(
        cls,
        llm: AbstractChatModel,
        memory: AbstractMemory,
        retriever: AbstractRetriever,
        max_steps: int = 10,
    ) -> "TutorAgent":
        """Build a TutorAgent with all three tools."""

        tool_registry = ToolRegistry()
        tool_registry.register_tool(StudentWorkAnalyzerTool(llm, retriever))
        tool_registry.register_tool(SocraticHintGeneratorTool(llm, retriever))
        tool_registry.register_tool(AnswerRevelationAnalyzerTool(llm))

        planner = SimpleReActPlanner(
            llm=llm,
            tool_registry=tool_registry,
            prompt_builder=cls._create_prompt(),
        )

        executor = ToolExecutor(tool_registry)

        agent = cls(
            llm=llm,
            planner=planner,
            tool_executor=executor,
            memory=memory,
            max_steps=max_steps,
            stateless=False,
        )

        agent.role_description = (
            "You are a Socratic tutor that speaks directly to the student, "
            "never reveals answers, and works across all academic domains."
        )

        return agent

    # ------------------------------------------------------------------
    # Mode detection (relocated verbatim from TutorManagerAgent)
    # ------------------------------------------------------------------

    @staticmethod
    def detect_mode(user_input: str) -> str | None:
        """Lightweight heuristic to detect HINT vs CONCEPT_EXPLANATION mode.

        Returns "HINT", "CONCEPT_EXPLANATION", or None if ambiguous/empty.
        """
        if not user_input or not user_input.strip():
            return None

        text = user_input.strip().lower()

        # CONCEPT indicators
        concept_score = 0
        if text.endswith("?"):
            concept_score += 1
        concept_patterns = [r"\bwhat is\b", r"\bhow do\b", r"\bexplain\b",
                           r"\bhelp me\b", r"\bcan you\b", r"\bwhy\b"]
        for pat in concept_patterns:
            if re.search(pat, text):
                concept_score += 1

        # HINT indicators
        hint_score = 0
        hint_patterns = [r"\bmy answer is\b", r"\bi got\b", r"\bi calculated\b"]
        for pat in hint_patterns:
            if re.search(pat, text):
                hint_score += 1
        # Cancel "i got" false positives — help-seeking phrases
        if re.search(r"\bi got\b", text) and re.search(
            r"\bi got\s+(?:confused|stuck|no idea|lost|a question)\b", text
        ):
            hint_score -= 1
            concept_score += 1
        # Numbers with units (e.g., 50kg, 10 m/s)
        if re.search(r"\d+\s*[a-zA-Z]+(?:/[a-zA-Z]+)?", text):
            hint_score += 1
        # = followed by number (e.g., = 50, x = 7)
        if re.search(r"=\s*-?\d+", text):
            hint_score += 1
        # Arithmetic expressions (e.g., 5 * 10, 2x + 3)
        if re.search(r"\d+\s*[+\-*/]\s*\d+", text):
            hint_score += 1
        # Work submission phrases (non-STEM: essays, code, history)
        work_submission_patterns = [
            r"\bhere is my\b",       # "Here is my essay"
            r"\bi think\b.*\d",      # "I think it ended in 1944"
            r"\breturned\b.*\d",     # "My function returned [1, 2, 3]"
            r"\boutput\b.*\d",       # "The output is 15"
            r"\bexpected\b.*\d",     # "expected [3, 2, 1]"
            r"\binstead of\b",       # "got X instead of Y"
            r"\bmy (?:essay|code|function|program|solution)\b",  # "My code/essay..."
        ]
        for pat in work_submission_patterns:
            if re.search(pat, text):
                hint_score += 1

        if hint_score > concept_score:
            return "HINT"
        elif concept_score > hint_score:
            return "CONCEPT_EXPLANATION"
        # Tie with both > 0: default to HINT (safer — HINT always runs safety check)
        elif hint_score > 0:
            return "HINT"
        return None

    @staticmethod
    def has_answer_content(text: str) -> bool:
        """Check if text contains answer-like content that safety check should validate.

        Returns True if the text has numbers combined with answer-indicating
        context (equations, units, 'the answer is', etc.).
        """
        if not text:
            return False
        t = text.lower()
        if not re.search(r'\d', t):
            return False
        answer_indicators = [
            r'\bthe answer\b',
            r'\bmy answer\b',
            r'\banswer is\b',
            r'=\s*-?\d+',
            r'\d+\s*[a-zA-Z]+(?:/[a-zA-Z]+)?',
        ]
        return any(re.search(pat, t) for pat in answer_indicators)

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    @staticmethod
    def _create_prompt() -> PromptBuilder:
        builder = PromptBuilder()

        builder.role_definition = RoleDefinition(
            "You are a Socratic tutor. You speak DIRECTLY to the student in "
            "second person ('you'). You are domain-agnostic — you tutor any "
            "subject (math, physics, literature, history, programming, etc.).\n\n"

            "ABSOLUTE RULE: NEVER reveal, state, or confirm the correct answer. "
            "Guide the student to discover it themselves through questions and hints.\n\n"

            "You have three tools:\n"
            "- student_work_analyzer: Diagnoses errors in student work\n"
            "- socratic_hint_generator: Generates hints (HINT mode) or concept "
            "explanations (CONCEPT_EXPLANATION mode)\n"
            "- answer_revelation_analyzer: Validates that your response does not "
            "reveal the answer (safety check)\n\n"

            "PREPROCESSOR:\n"
            "If the input starts with 'PREPROCESSOR DETECTED MODE:', use that as "
            "strong guidance for mode selection. You may still override if context "
            "clearly contradicts it.\n\n"

            "MODE DETECTION:\n"
            "Determine the interaction mode from the student's input.\n"
            "MODE: HINT — student is submitting work, calculations, or answers "
            "(e.g., 'I got 50', 'My answer is x=6', 'I think it ended in 1944').\n"
            "MODE: CONCEPT_EXPLANATION — student is asking a question or requesting "
            "guidance (e.g., 'What is momentum?', 'How do I balance equations?').\n\n"

            "HINT ESCALATION:\n"
            "If the student already received a hint for the same problem and is "
            "still confused, escalate by increasing hint_level (1=general to "
            "4=most specific).\n"
        )

        builder.format_instructions.extend([
            FormatInstruction(
                "WORKFLOW — MODE: HINT\n"
                "1. Use student_work_analyzer to diagnose the student's error\n"
                "2. Use socratic_hint_generator to create a Socratic hint based on "
                "the diagnosis\n"
                "3. Use answer_revelation_analyzer to verify your planned response "
                "does NOT reveal the answer (REQUIRED for HINT mode)\n"
                "4. Provide final_answer speaking directly to the student\n\n"

                "WORKFLOW — MODE: CONCEPT_EXPLANATION\n"
                "1. Use socratic_hint_generator with mode=CONCEPT_EXPLANATION\n"
                "2. Use answer_revelation_analyzer to verify your response does "
                "NOT reveal the answer (REQUIRED)\n"
                "3. Provide final_answer speaking directly to the student\n"
            ),
            FormatInstruction(
                "TOOL INPUT FORMAT:\n"
                "All tool inputs are JSON strings. Key fields:\n\n"
                'student_work_analyzer: {"problem": "...", "student_work": "...", "topic": "..."}\n'
                'socratic_hint_generator (hint): {"mode": "HINT", "problem": "...", '
                '"student_work": "...", "misconception": "...", "severity": "Major", '
                '"topic": "...", "hint_level": 2}\n'
                'socratic_hint_generator (concept): {"mode": "CONCEPT_EXPLANATION", '
                '"concept": "...", "question": "...", "topic": "..."}\n'
                'answer_revelation_analyzer: {"problem": "...", "correct_answer": "...", '
                '"student_history": ["..."], "proposed_response": "..."}\n'
            ),
        ])

        builder.examples.extend([
            Example(
                "# --- Example: HINT mode (algebra work submission) ---\n"
                'user: I got x = 7 for the equation 2x + 3 = 15\n'
                "assistant: "
                "Thought: The student is submitting work (MODE: HINT). I need to "
                "analyze their answer, generate a hint, then validate safety.\n"
                "Action:\n"
                "tool_name: student_work_analyzer\n"
                'tool_input: {"problem": "Solve 2x + 3 = 15", "student_work": "I got x = 7", "topic": "algebra"}\n'
                "\n"
                "system: Observation: ANALYSIS COMPLETE - Severity: Minor. "
                "Student subtracted 3 correctly but divided by 2 incorrectly "
                "(15-3=12, 12/2=6 not 7).\n"
                "assistant: "
                "Thought: Minor arithmetic error in the division step. "
                "I'll generate a hint pointing them to recheck that step.\n"
                "Action:\n"
                "tool_name: socratic_hint_generator\n"
                'tool_input: {"mode": "HINT", "problem": "Solve 2x + 3 = 15", "student_work": "x = 7", "misconception": "Division error in final step", "severity": "Minor", "topic": "algebra"}\n'
                "\n"
                "system: Observation: COMPLETE HINT (Level 3): You correctly subtracted 3 "
                "from both sides. Now double-check: what is 12 divided by 2?\n"
                "assistant: "
                "Thought: Good hint. I must validate it does not reveal the answer.\n"
                "Action:\n"
                "tool_name: answer_revelation_analyzer\n"
                'tool_input: {"problem": "Solve 2x + 3 = 15", "correct_answer": "x = 6", "student_history": ["I got x = 7"], "proposed_response": "You correctly subtracted 3 from both sides. Now double-check: what is 12 divided by 2?"}\n'
                "\n"
                "system: Observation: SAFE - Guides without revealing answer\n"
                "assistant: "
                "Thought: The hint is safe. I'll deliver it directly to the student.\n"
                "Action:\n"
                "tool_name: final_answer\n"
                "tool_input: Good start! You correctly subtracted 3 from both sides to get 12. "
                "Now double-check: what is 12 divided by 2?"
            ),

            Example(
                "# --- Example: CONCEPT_EXPLANATION mode (literature question) ---\n"
                "user: What is the theme of To Kill a Mockingbird?\n"
                "assistant: "
                "Thought: The student is asking a conceptual question about "
                "literature (MODE: CONCEPT_EXPLANATION). I'll use the hint "
                "generator in concept mode.\n"
                "Action:\n"
                "tool_name: socratic_hint_generator\n"
                'tool_input: {"mode": "CONCEPT_EXPLANATION", "concept": "themes in To Kill a Mockingbird", "question": "What is the theme of To Kill a Mockingbird?", "topic": "literature"}\n'
                "\n"
                "system: Observation: CONCEPT EXPLANATION for 'themes in To Kill a "
                "Mockingbird': The novel explores several themes including racial "
                "injustice, the loss of innocence, and moral courage.\n"
                "assistant: "
                "Thought: I have the concept explanation. I must validate it does "
                "not reveal any specific answer before delivering.\n"
                "Action:\n"
                "tool_name: answer_revelation_analyzer\n"
                'tool_input: {"problem": "What is the theme of To Kill a Mockingbird?", "correct_answer": "N/A - concept question", "student_history": [], "proposed_response": "To Kill a Mockingbird explores several important themes. The most prominent is racial injustice, shown through the trial of Tom Robinson. There\'s also the theme of moral courage and the loss of innocence. Which of these themes stood out to you in your reading?"}\n'
                "\n"
                "system: Observation: SAFE - Concept explanation, no answer revealed\n"
                "assistant: "
                "Thought: The response is safe. I'll deliver it directly.\n"
                "Action:\n"
                "tool_name: final_answer\n"
                "tool_input: To Kill a Mockingbird explores several important themes. The most "
                "prominent is racial injustice, shown through the trial of Tom "
                "Robinson. There's also the theme of moral courage and the loss of "
                "innocence. Which of these themes stood out to you in your reading?"
            ),
        ])

        return builder
