# safety_guard_agent.py

from fairlib.modules.agent.simple_agent import SimpleAgent
from fairlib.core.interfaces.llm import AbstractChatModel
from fairlib.core.interfaces.memory import AbstractMemory
from fairlib.modules.planning.react_planner import ReActPlanner
from fairlib.modules.action.executor import ToolExecutor
from fairlib.modules.action.tools.registry import ToolRegistry

from tools.safety_tools import AnswerRevelationAnalyzerTool


class SafetyGuardAgent(SimpleAgent):
    """
    Safety validation agent using LLM reasoning.
    """

    @classmethod
    def create(cls, llm: AbstractChatModel, memory: AbstractMemory) -> "SafetyGuardAgent":
        """Create SafetyGuardAgent with properly structured prompts"""

        tool_registry = ToolRegistry()
        tool_registry.register_tool(AnswerRevelationAnalyzerTool(llm))

        planner = ReActPlanner(
            llm,
            tool_registry,
            prompt_builder=cls._create_safety_prompt()
        )

        executor = ToolExecutor(tool_registry)

        agent = cls(
            llm=llm,
            planner=planner,
            tool_executor=executor,
            memory=memory,
            max_steps=5,
            stateless=True
        )

        agent.role_description = (
            "You are a safety validator for a tutoring system. Your ONLY job is to "
            "determine if a proposed tutor response reveals the answer to a problem."
        )

        return agent

    @staticmethod
    def _create_safety_prompt():
        from fairlib.core.prompts import (
            PromptBuilder, RoleDefinition, FormatInstruction, Example
        )

        builder = PromptBuilder()

        builder.role_definition = RoleDefinition(
            "You are a Safety Validator Agent for a tutoring system.\n\n"

            "MISSION:\n"
            "Determine whether a proposed tutor response reveals the answer to a problem.\n"

            "HISTORY AWARENESS:\n"
            "If the student has ALREADY provided the correct answer in their history:\n"
            "- It is SAFE to confirm they are correct\n"
            "- It is SAFE to reference the specific value they gave\n"
            "- It is SAFE to say things like 'Yes, your answer is correct!'\n\n"

            "If the student has NOT provided the answer yet:\n"
            "- It is UNSAFE to reveal the answer\n"
            "- It is UNSAFE to complete their calculations\n"
            "- It is UNSAFE to give the final step\n\n"

            "APPROACH:\n"
            "1. Check the student_history to see what they've already submitted\n"
            "2. Use answer_revelation_analyzer with the full JSON input\n"
            "3. Report verdict: SAFE or UNSAFE\n\n"
        )

        builder.format_instructions.extend([
            FormatInstruction(
                "# --- RESPONSE FORMAT (MANDATORY JSON) ---\n"
                "Your entire response MUST be a single, valid JSON object.\n"
                "This JSON object MUST have exactly two top-level keys: 'thought' and 'action'.\n\n"
                "1.  `thought`: A string explaining your reasoning for the current step.\n"
                "2.  `action`: An object containing the tool you will use, with two keys:\n"
                "    -   `tool_name`: The string name of the tool to use.\n"
                "    -   `tool_input`: The string input for that tool."
            ),
            FormatInstruction(
                "# --- JSON RULES ---\n"
                "- ALWAYS use double quotes for all keys and string values.\n"
                "- Do NOT include any text or markdown formatting outside of the main JSON object."
            ),
            FormatInstruction(
                "# --- ABSOLUTE RULE ---\n"
                "Under NO circumstances should you ever respond with anything other than the JSON object described above."
            )
        ])

        builder.format_instructions.extend([
            FormatInstruction(
                "# TOOL INPUT FORMAT (JSON)\n"
                "When calling answer_revelation_analyzer, pass a JSON string:\n"
                '{"problem": "...", "correct_answer": "...", '
                '"student_history": ["previous submission 1", "..."], '
                '"proposed_response": "response to validate"}\n\n'

                "The student_history is CRITICAL for proper validation!"
            ),
            FormatInstruction(
                "# VERDICT FORMAT\n"
                "Your final_answer must state:\n"
                "- 'SAFE - Student already provided this answer' if confirming their work\n"
                "- 'SAFE - Response does not reveal answer' for hints\n"
                "- 'UNSAFE - Response reveals the answer' if it gives away new information"
            )
        ])

        builder.examples.extend([
            Example(
                "Input: Validate response for student who already gave answer.\n"
                '{"problem": "Calculate momentum", "correct_answer": "50 kg m/s", '
                '"student_history": ["I calculated 50 kg m/s"], '
                '"proposed_response": "Excellent! Your answer of 50 kg m/s is correct!"}\n\n'

                '{\n'
                '  "thought": "The student already provided 50 kg m/s. I need to check if confirming this is safe.",\n'
                '  "action": {\n'
                '    "tool_name": "answer_revelation_analyzer",\n'
                '    "tool_input": "{\\"problem\\": \\"Calculate momentum\\", \\"correct_answer\\": \\"50 kg m/s\\", '
                '\\"student_history\\": [\\"I calculated 50 kg m/s\\"], '
                '\\"proposed_response\\": \\"Excellent! Your answer of 50 kg m/s is correct!\\"}"\n'
                '  }\n'
                '}\n\n'

                "Observation: SAFE - Student already provided this answer. Confirmation allowed.\n\n"

                '{\n'
                '  "thought": "The analyzer confirms it\'s safe since the student already gave this answer.",\n'
                '  "action": {\n'
                '    "tool_name": "final_answer",\n'
                '    "tool_input": "SAFE - Student already provided this answer"\n'
                '  }\n'
                '}'
            ),

            Example(
                "Input: Validate hint for student who hasn't answered yet.\n"
                '{"problem": "What year did WWII end?", "correct_answer": "1945", '
                '"student_history": [], '
                '"proposed_response": "Think about the major events in the Pacific theater. When did Japan surrender?"}\n\n'

                '{\n'
                '  "thought": "Student hasn\'t provided an answer yet. Checking if this hint is safe.",\n'
                '  "action": {\n'
                '    "tool_name": "answer_revelation_analyzer",\n'
                '    "tool_input": "{\\"problem\\": \\"What year did WWII end?\\", \\"correct_answer\\": \\"1945\\", '
                '\\"student_history\\": [], '
                '\\"proposed_response\\": \\"Think about the major events in the Pacific theater. When did Japan surrender?\\"}"\n'
                '  }\n'
                '}\n\n'

                "Observation: SAFE - Response does not reveal answer.\n\n"

                '{\n'
                '  "thought": "The hint guides without revealing. It\'s safe.",\n'
                '  "action": {\n'
                '    "tool_name": "final_answer",\n'
                '    "tool_input": "SAFE - Response guides without revealing answer"\n'
                '  }\n'
                '}'
            )
        ])

        return builder
