# misconception_detector_agent.py

from fairlib.modules.agent.simple_agent import SimpleAgent
from fairlib.core.interfaces.llm import AbstractChatModel
from fairlib.core.interfaces.memory import AbstractMemory
from fairlib.modules.planning.react_planner import ReActPlanner
from fairlib.modules.action.executor import ToolExecutor
from fairlib.modules.action.tools.registry import ToolRegistry
from fairlib.core.interfaces.memory import AbstractRetriever

from tools.diagnostic_tools import StudentWorkAnalyzerTool


class MisconceptionDetectorAgent(SimpleAgent):
    """
    Diagnoses student errors using LLM + RAG.
    """

    @classmethod
    def create(cls, llm: AbstractChatModel, memory: AbstractMemory,
               retriever: AbstractRetriever) -> "MisconceptionDetectorAgent":
        """Create MisconceptionDetectorAgent with properly structured prompts"""

        tool_registry = ToolRegistry()
        tool_registry.register_tool(StudentWorkAnalyzerTool(llm, retriever))

        planner = ReActPlanner(
            llm,
            tool_registry,
            prompt_builder=cls._create_diagnostic_prompt()
        )

        executor = ToolExecutor(tool_registry)

        agent = cls(
            llm=llm,
            planner=planner,
            tool_executor=executor,
            memory=memory,
            max_steps=10,
            stateless=True
        )

        agent.role_description = (
            "You analyze student work for errors OR explain concepts when students ask questions."
        )

        return agent

    @staticmethod
    def _create_diagnostic_prompt():
        """Create properly structured diagnostic prompt"""
        from fairlib.core.prompts import (
            PromptBuilder, RoleDefinition, FormatInstruction, Example
        )

        builder = PromptBuilder()

        builder.role_definition = RoleDefinition(
            "You are a Diagnostic Agent that analyzes student work.\n\n"

            "YOUR JOB:\n"
            "When the student has shown their work/answer:\n"
            "- Use student_work_analyzer to diagnose errors\n"
            "- Identify the specific misconception\n"
            "- Determine severity (Critical/Major/Minor)\n\n"

            "CRITICAL:\n"
            "Use the student_work_analyzer tool with JSON input!"
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
                "- Do NOT include any text or markdown formatting (like ```json) outside of the main JSON object."
            ),
            FormatInstruction(
                "# --- ABSOLUTE RULE ---\n"
                "Under NO circumstances should you ever respond with anything other than the JSON object described above. Your adherence to this format is non-negotiable."
            )
        ])

        builder.format_instructions.extend([
            FormatInstruction(
                "# TOOL INPUT FORMAT (JSON)\n\n"
                "For student_work_analyzer:\n"
                '{"problem": "the problem text", "student_work": "their work", "topic": "subject area"}'
            ),
            FormatInstruction(
                "# OUTPUT FORMAT\n\n"
                "After receiving analysis, use final_answer to report:\n"
                "- MISCONCEPTION: [specific error]\n"
                "- Severity: [Critical/Major/Minor]"
            )
        ])

        return builder
