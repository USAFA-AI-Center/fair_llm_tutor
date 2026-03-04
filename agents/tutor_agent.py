# tutor_agent.py

import re

from fairlib.modules.agent.simple_agent import SimpleAgent
from fairlib.modules.planning.react_planner import SimpleReActPlanner
from fairlib.modules.action.executor import ToolExecutor
from fairlib.modules.action.tools.registry import ToolRegistry
from fairlib.modules.action.tools.builtin_tools.safe_calculator import SafeCalculatorTool
from fairlib.core.interfaces.llm import AbstractChatModel
from fairlib.core.interfaces.memory import AbstractMemory, AbstractRetriever

from fairlib.core.prompts import (
    PromptBuilder,
    RoleDefinition,
    FormatInstruction,
    Example,
)

from tools.retrieval_tools import RetrieveCourseMaterialsTool
from tools.history_tools import CheckStudentHistoryTool
from tools.hint_level_tools import GetHintLevelTool


class TutorAgent(SimpleAgent):
    """
    Single-agent Socratic tutor that speaks directly to the student.

    Uses a ReActPlanner with four computational tools (no LLM-wrapper
    tools). The agent's own reasoning handles diagnosis, hint generation,
    and safety judgment. Tools provide DATA and COMPUTATION only:

      - retrieve_course_materials  (RAG retrieval)
      - check_student_history      (answer matching)
      - get_hint_level             (severity → level mapping)
      - safe_calculator            (arithmetic evaluation)
    """

    @classmethod
    def create(
        cls,
        llm: AbstractChatModel,
        memory: AbstractMemory,
        retriever: AbstractRetriever,
        max_steps: int = 10,
    ) -> "TutorAgent":
        """Build a TutorAgent with four computational tools."""

        tool_registry = ToolRegistry()
        tool_registry.register_tool(RetrieveCourseMaterialsTool(retriever))
        tool_registry.register_tool(CheckStudentHistoryTool())
        tool_registry.register_tool(GetHintLevelTool())
        tool_registry.register_tool(SafeCalculatorTool())

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
    # Mode detection (heuristic-based, no LLM)
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

            "ABSOLUTE RULE: NEVER reveal, state, or confirm the correct answer "
            "unless the student has already stated it correctly (verified by "
            "check_student_history). Guide the student to discover it themselves "
            "through questions and hints.\n\n"

            "You have four computational tools (DATA and COMPUTATION only — "
            "none of these use LLM reasoning):\n"
            "- retrieve_course_materials: Gets relevant course material passages\n"
            "- check_student_history: Checks if student already gave the correct "
            "answer (text matching)\n"
            "- get_hint_level: Calculates hint specificity level (1-4) from "
            "error severity\n"
            "- safe_calculator: Evaluates arithmetic expressions safely\n\n"

            "YOUR ROLE: You are the diagnostician, the hint generator, AND the "
            "safety judge. Use the tools to gather data, then reason about "
            "student work yourself.\n\n"

            "PREPROCESSOR:\n"
            "If the input starts with 'PREPROCESSOR DETECTED MODE:', use that "
            "as strong guidance for mode selection.\n\n"

            "MODE DETECTION:\n"
            "MODE: HINT — student is submitting work, calculations, or answers "
            "(e.g., 'I got 50', 'My answer is x=6', 'I think it ended in 1944').\n"
            "MODE: CONCEPT_EXPLANATION — student is asking a question or requesting "
            "guidance (e.g., 'What is momentum?', 'How do I balance equations?').\n"
        )

        builder.format_instructions.extend([
            FormatInstruction(
                "WORKFLOW — MODE: HINT\n"
                "1. Use retrieve_course_materials to get relevant context for "
                "the problem/topic\n"
                "2. Use check_student_history if a correct answer is known "
                "(to verify if student already answered correctly)\n"
                "3. Diagnose the student's error YOURSELF based on: their work, "
                "the problem, and retrieved materials\n"
                "4. Determine severity (Critical/Major/Minor) and use "
                "get_hint_level to get the appropriate hint level\n"
                "5. Generate a Socratic hint at that level — acknowledge what "
                "they did correctly, then guide toward the error\n"
                "6. SAFETY SELF-CHECK (REQUIRED): Before delivering your "
                "response, verify it does NOT:\n"
                "   - State the final answer directly or indirectly\n"
                "   - Complete calculations that give away the answer\n"
                "   - Provide the last step that leads immediately to the answer\n"
                "   If your response fails this check, rewrite it to be safer.\n"
                "7. Provide final_answer speaking directly to the student\n\n"

                "WORKFLOW — MODE: CONCEPT_EXPLANATION\n"
                "1. Use retrieve_course_materials to get relevant context\n"
                "2. Generate a clear, helpful concept explanation YOURSELF\n"
                "3. SAFETY SELF-CHECK (REQUIRED): Verify you haven't solved a "
                "specific problem in your explanation\n"
                "4. Provide final_answer speaking directly to the student\n"
            ),
            FormatInstruction(
                "TOOL INPUT FORMAT:\n"
                "All tool inputs are JSON strings. Key fields:\n\n"
                'retrieve_course_materials: {"query": "topic keywords", "top_k": 3}\n'
                'check_student_history: {"correct_answer": "...", '
                '"student_history": ["previous answer 1", "..."]}\n'
                'get_hint_level: {"severity": "Major", "hint_level_override": null}\n'
                'safe_calculator: "expression like 2 + 3 * 4"\n\n'

                "HINT LEVELS:\n"
                "Level 1: General conceptual reminder — 'Remember the definition "
                "of [concept]'\n"
                "Level 2: Specific concept pointer — 'Think about the relationship "
                "between [concepts]'\n"
                "Level 3: Targeted Socratic question — 'What happens when you "
                "[specific action]?'\n"
                "Level 4: Directed guidance — 'Look at your [specific part]. Does "
                "it account for [consideration]?'\n\n"

                "HINT ESCALATION:\n"
                "If the student already received a hint for the same problem and "
                "is still confused, escalate by passing a higher hint_level_override "
                "to get_hint_level.\n\n"

                "SAFETY RULES:\n"
                "- If check_student_history returns STUDENT_ALREADY_ANSWERED: YES, "
                "you MAY confirm their answer and celebrate\n"
                "- Otherwise, NEVER state the answer, complete calculations to the "
                "answer, or give the final step\n"
                "- When in doubt, ask a guiding question instead of providing "
                "information\n"
            ),
        ])

        builder.examples.extend([
            Example(
                "# --- Example: HINT mode (algebra work submission) ---\n"
                "user: PREPROCESSOR DETECTED MODE: HINT\n"
                "Safety check REQUIRED.\n\n"
                "PROBLEM: Solve 2x + 3 = 15\n\n"
                "STUDENT WORK: I got x = 7\n\n"
                "TOPIC: algebra\n\n"
                "CORRECT ANSWER (for safety check): x = 6\n"
                "assistant: "
                "Thought: The student is submitting work (HINT mode). First I'll "
                "retrieve relevant materials, then check history, then diagnose "
                "the error myself.\n"
                "Action:\n"
                "tool_name: retrieve_course_materials\n"
                'tool_input: {"query": "algebra solving linear equations common errors"}\n'
                "\n"
                "system: Observation: [1] When solving linear equations, isolate the "
                "variable by performing inverse operations. Common errors include "
                "arithmetic mistakes in the final division step.\n"
                "assistant: "
                "Thought: Good context. Now let me check if the student already "
                "provided the correct answer.\n"
                "Action:\n"
                "tool_name: check_student_history\n"
                'tool_input: {"correct_answer": "x = 6", "student_history": ["I got x = 7"]}\n'
                "\n"
                "system: Observation: STUDENT_ALREADY_ANSWERED: NO\n"
                "assistant: "
                "Thought: Student has NOT answered correctly yet — I must NOT reveal "
                "the answer. Let me diagnose: 2x + 3 = 15 → 2x = 12 → x = 6. The "
                "student got x = 7, so they subtracted 3 correctly (getting 12) but "
                "divided incorrectly. This is a Minor arithmetic error. Let me get "
                "the hint level.\n"
                "Action:\n"
                "tool_name: get_hint_level\n"
                'tool_input: {"severity": "Minor"}\n'
                "\n"
                "system: Observation: Hint Level: 3\n"
                "Description: Targeted Socratic question — guide toward the specific "
                "error\n"
                "assistant: "
                "Thought: Level 3 = targeted Socratic question. I'll ask about the "
                "division step. My response: 'You correctly subtracted 3 from both "
                "sides to get 12. Now double-check: what is 12 divided by 2?'\n"
                "SAFETY CHECK: This asks the student to compute 12/2 themselves — it "
                "does NOT state x=6. SAFE.\n"
                "Action:\n"
                "tool_name: final_answer\n"
                "tool_input: Good start! You correctly subtracted 3 from both sides "
                "to get 12. Now double-check: what is 12 divided by 2?"
            ),

            Example(
                "# --- Example: CONCEPT_EXPLANATION mode (literature question) ---\n"
                "user: PREPROCESSOR DETECTED MODE: CONCEPT_EXPLANATION\n"
                "Safety check REQUIRED.\n\n"
                "PROBLEM: [none]\n\n"
                "STUDENT WORK: What is the theme of To Kill a Mockingbird?\n\n"
                "TOPIC: literature\n"
                "assistant: "
                "Thought: The student is asking a concept question about literature. "
                "I'll retrieve relevant materials first.\n"
                "Action:\n"
                "tool_name: retrieve_course_materials\n"
                'tool_input: {"query": "themes in To Kill a Mockingbird"}\n'
                "\n"
                "system: Observation: [1] To Kill a Mockingbird by Harper Lee explores "
                "themes of racial injustice, moral growth, and the coexistence of good "
                "and evil. [2] The trial of Tom Robinson serves as the central narrative "
                "device for examining prejudice.\n"
                "assistant: "
                "Thought: I have good context. I'll explain the major themes myself. "
                "SAFETY CHECK: This is a concept question — I'm explaining themes, not "
                "solving a specific problem. SAFE.\n"
                "Action:\n"
                "tool_name: final_answer\n"
                "tool_input: Great question! To Kill a Mockingbird explores several "
                "important themes. The most prominent is racial injustice, shown through "
                "the trial of Tom Robinson. There's also the theme of moral courage — "
                "Atticus Finch standing up for what's right despite community pressure — "
                "and the loss of innocence as Scout and Jem witness these events. "
                "Which of these themes stood out to you in your reading?"
            ),
        ])

        return builder
