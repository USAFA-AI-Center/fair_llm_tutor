# manager_agent.py

import re

from fairlib.modules.agent.simple_agent import SimpleAgent
from fairlib.modules.agent.multi_agent_runner import ManagerPlanner
from fairlib.core.interfaces.llm import AbstractChatModel
from fairlib.core.interfaces.memory import AbstractMemory

from fairlib.core.prompts import (
    PromptBuilder,
    RoleDefinition,
    FormatInstruction,
    Example
)

from typing import Dict


class TutorManagerAgent(SimpleAgent):
    """
    Socratic Tutor Manager that preserves student work context.
        - Better mode detection (work submission vs question)
        - Conversation history tracking for safety validation
        - Proper routing based on student intent
    """
    
    @classmethod
    def create(cls, llm: AbstractChatModel, memory: AbstractMemory, 
               workers: Dict) -> "TutorManagerAgent":
        """Create manager with improved prompt for context preservation"""
        
        planner = ManagerPlanner(
            llm=llm,
            workers=workers,
            prompt_builder=cls._create_manager_prompt()
        )
        
        agent = cls(
            llm=llm,
            planner=planner,
            tool_executor=None,
            memory=memory,
            max_steps=15,
            stateless=False
        )
        
        agent.role_description = (
            "You are a Socratic tutor manager coordinating specialist agents."
        )
        
        return agent
    
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

        if hint_score > concept_score:
            return "HINT"
        elif concept_score > hint_score:
            return "CONCEPT_EXPLANATION"
        # Tie with both > 0: default to HINT (safer — HINT always runs SafetyGuard)
        elif hint_score > 0:
            return "HINT"
        return None

    @staticmethod
    def has_answer_content(text: str) -> bool:
        """Check if text contains answer-like content that SafetyGuard should validate.

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

    @staticmethod
    def _create_manager_prompt() -> PromptBuilder:
        builder = PromptBuilder()
        
        builder.role_definition = RoleDefinition(
            "You are a Socratic Tutor Manager coordinating specialist agents.\n\n"
            
            "YOUR TEAM:\n"
            "- MisconceptionDetector: Analyzes student work for errors\n"
            "- HintGenerator: Creates hints AND provides concept explanations\n"
            "- SafetyGuard: Validates responses\n\n"
                
            "PREPROCESSOR:\n"
            "If the input starts with 'PREPROCESSOR DETECTED MODE:', use that as strong guidance "
            "for mode selection. You may still override if context clearly contradicts it.\n\n"

            "MODE DETECTION:\n"
            "First, determine the interaction mode.\n"
            "You are SOLELY RESPONSIBLE for determining the mode.\n"
            "There are two modes to choose from. MODE: CONCEPT_EXPLANATION, and MODE: HINT.\n"
            "Analyze the user input. If the student is asking for guidance on how to approach the problem, delegate adhering to MODE: CONCEPT_EXPLANATION.\n"
            "If the student is asking if their answer is correct, showing work, or submitting calculations, delegate adhering to MODE: HINT.\n"
            "This step is CRUCIAL in getting this system to work. If they are asking for guidance, route to MODE: CONCEPT_EXPLANATION. If they are submitting work and needing verification, route to MODE: HINT.\n"
            
            "\tMODE: HINT\n"
            "\t\tIndicators: Student shows calculations, states 'my answer is', provides numerical values\n"
            "\t\tExamples: 'I got 500', 'My answer is 50kg*m/s', 'p = 5 * 10 = 50'\n"
            "\t\tAction: Analyze work -> Generate hint -> Validate safety\n"
            "\t\tDELEGATION INPUT MUST CONTAIN: MODE: HINT\n\n"
            
            "\tMODE: CONCEPT_EXPLANATION\n"
            "\t\tIndicators: Questions words (what, how, why), ends with '?', 'explain', 'help'\n"
            "\t\tExamples: 'What is momentum?', 'How do I calculate this?', 'Can you explain?'\n"
            "\t\tAction: HintGenerator provides concept explanation -> Validate safety\n"
            "\t\tDELEGATION INPUT MUST CONTAIN: MODE: CONCEPT_EXPLANATION\n\n"
            
            "SAFETY WITH HISTORY:\n"
            "Track conversation history. If student has already stated an answer,\n"
            "SafetyGuard can allow confirmation of that answer.\n"
            "Pass history to SafetyGuard: STUDENT_HISTORY: [previous student submissions]\n\n"
            
            "CONCEPT IN HINTGENERATOR:\n"
            "HintGenerator handles BOTH hints AND concept explanations\n"
            "Route concept questions directly to HintGenerator with MODE flag\n\n"
                
            "HINT ESCALATION:\n"
            "If student already received a hint for the same problem and is still confused,\n"
            "escalate by adding HINT_LEVEL: [previous level + 1] to HintGenerator delegation.\n"
            "Hint levels: 1 (general) to 4 (most specific).\n\n"

            "WORKFLOW:\n"
            "1. Detect mode from student input\n"
            "2. Route appropriately based on mode\n"
            "3. ALWAYS validate with SafetyGuard for HINT mode (include history). "
            "SafetyGuard is OPTIONAL for CONCEPT_EXPLANATION ONLY when the preprocessor "
            "does NOT warn about answer content. If PREPROCESSOR WARNING mentions answer content, "
            "ALWAYS use SafetyGuard even for concept questions.\n"
            "4. Provide final response\n"
        )

        builder.format_instructions.extend([
            FormatInstruction(
                "# === OUTPUT FORMAT ===\n"
                "You MUST respond with EXACTLY ONE 'Thought' and ONE 'Action' per turn.\n"
                "Format:\n"
                "Thought: [Your reasoning about what to do next]\n"
                "Action: {\"tool_name\": \"delegate\", \"tool_input\": {\"worker_name\": \"WorkerName\", \"task\": \"detailed task\"}}\n\n"
                
                "OR for final answer:\n"
                "Thought: [Your reasoning that you have everything needed]\n"
                "Action: {\"tool_name\": \"final_answer\", \"tool_input\": \"Your complete response to the student\"}\n\n"
                
                "CRITICAL: The Action MUST be valid JSON."
            ),
            FormatInstruction(
                "# === MODE DETECTION PROCESS ===\n"
                "On FIRST turn, analyze the student input:\n"
                "1. Look for work submission patterns (calculations, 'my answer', numbers with units)\n"
                "2. Look for question patterns ('what', 'how', 'explain', '?')\n"
                "3. Decide mode and route accordingly\n\n"
                
                "Include MODE in your delegations:\n"
                "- Add 'MODE: HINT' or 'MODE: CONCEPT_EXPLANATION'"
            )
        ])
        
        builder.format_instructions.extend([
            FormatInstruction(
                "# === DELEGATION TEMPLATES ===\n"
                "MisconceptionDetector: PROBLEM: ... ||| STUDENT_WORK: ... ||| TOPIC: ...\n"
                "HintGenerator (hint): MODE: HINT ||| PROBLEM: ... ||| STUDENT_WORK: ... ||| "
                "MISCONCEPTION: ... ||| SEVERITY: ... ||| TOPIC: ... ||| HINT_LEVEL: [optional 1-4]\n"
                "HintGenerator (concept): MODE: CONCEPT_EXPLANATION ||| CONCEPT: ... ||| QUESTION: ... ||| TOPIC: ...\n"
                "SafetyGuard: PROBLEM: ... ||| CORRECT_ANSWER: ... ||| STUDENT_HISTORY: [...] ||| PROPOSED_RESPONSE: ...\n"
                "final_answer: Your synthesized response to the student"
            )
        ])

        builder.examples.extend([
            Example(
                "User Request: 'What is momentum?'\n\n"

                "Thought: This is MODE: CONCEPT_EXPLANATION - student asking conceptual question. "
                "Route to HintGenerator for concept explanation. No specific answer involved, "
                "so SafetyGuard is not needed.\n"
                "Action: {\"tool_name\": \"delegate\", \"tool_input\": {\"worker_name\": \"HintGenerator\", "
                "\"task\": \"MODE: CONCEPT_EXPLANATION ||| CONCEPT: momentum ||| "
                "QUESTION: What is momentum? ||| TOPIC: physics\"}}\n\n"

                "Tool Observation: Momentum is a measure of an object's motion, calculated as mass times velocity (p = mv).\n\n"

                "Thought: This is a concept explanation with no specific answer to reveal. Provide final answer directly.\n"
                "Action: {\"tool_name\": \"final_answer\", \"tool_input\": \"Momentum is a measure of an object's "
                "motion, calculated as mass times velocity (p = mv). Think of it as how hard it would be to stop "
                "a moving object.\"}"
            ),

            Example(
                "User Request: Student says: 'I got x = 7 for the equation 2x + 3 = 15'\n\n"

                "Thought: This is MODE: HINT - student is submitting their work for a math problem. "
                "I need to check their answer.\n"
                "Action: {\"tool_name\": \"delegate\", \"tool_input\": {\"worker_name\": \"MisconceptionDetector\", "
                "\"task\": \"PROBLEM: Solve 2x + 3 = 15 ||| "
                "STUDENT_WORK: I got x = 7 ||| TOPIC: algebra\"}}\n\n"

                "Tool Observation: ANALYSIS COMPLETE - Severity: Minor. "
                "Student subtracted 3 correctly but divided by 2 incorrectly (15-3=12, 12/2=6 not 7).\n\n"

                "Thought: Minor arithmetic error. Generate a hint.\n"
                "Action: {\"tool_name\": \"delegate\", \"tool_input\": {\"worker_name\": \"HintGenerator\", "
                "\"task\": \"MODE: HINT ||| PROBLEM: Solve 2x + 3 = 15 ||| STUDENT_WORK: x = 7 ||| "
                "MISCONCEPTION: Division error in final step ||| SEVERITY: Minor ||| TOPIC: algebra\"}}\n\n"

                "Tool Observation: You correctly subtracted 3 from both sides. Now double-check: what is 12 divided by 2?\n\n"

                "Thought: Validate hint with SafetyGuard.\n"
                "Action: {\"tool_name\": \"delegate\", \"tool_input\": {\"worker_name\": \"SafetyGuard\", "
                "\"task\": \"PROBLEM: Solve 2x + 3 = 15 ||| CORRECT_ANSWER: x = 6 ||| "
                "STUDENT_HISTORY: ['I got x = 7'] ||| "
                "PROPOSED_RESPONSE: You correctly subtracted 3 from both sides. Now double-check: what is 12 divided by 2?\"}}\n\n"

                "Tool Observation: SAFE - Guides without revealing answer\n\n"

                "Thought: Validated. Provide final response.\n"
                "Action: {\"tool_name\": \"final_answer\", \"tool_input\": \"Good start! You correctly subtracted 3 "
                "from both sides to get 12. Now double-check: what is 12 divided by 2?\"}"
            )
        ])
        
        return builder
