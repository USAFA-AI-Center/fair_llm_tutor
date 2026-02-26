# hint_generator_agent.py

from fairlib.modules.agent.simple_agent import SimpleAgent
from fairlib.core.interfaces.llm import AbstractChatModel
from fairlib.core.interfaces.memory import AbstractMemory
from fairlib.modules.planning.react_planner import ReActPlanner
from fairlib.modules.action.executor import ToolExecutor
from fairlib.modules.action.tools.registry import ToolRegistry
from fairlib.core.interfaces.memory import AbstractRetriever

from tools.pedagogical_tools import SocraticHintGeneratorTool


class HintGeneratorAgent(SimpleAgent):
    """
    Generates Socratic hints using LLM + RAG + student work context.

    Dual-mode operation:
    1. HINT mode: Generate hints for student work with misconceptions
    2. CONCEPT_EXPLANATION mode: Explain concepts when students ask questions
    """

    @classmethod
    def create(cls, llm: AbstractChatModel, memory: AbstractMemory,
               retriever: AbstractRetriever) -> "HintGeneratorAgent":
        tool_registry = ToolRegistry()

        tool_registry.register_tool(SocraticHintGeneratorTool(llm, retriever))

        planner = ReActPlanner(
            llm,
            tool_registry,
            prompt_builder=cls._create_hint_prompt()
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
            "You generate Socratic hints AND concept explanations based on the mode specified."
        )

        return agent

    @staticmethod
    def _create_hint_prompt():
        from fairlib.core.prompts import (
            PromptBuilder, RoleDefinition, FormatInstruction, Example
        )

        builder = PromptBuilder()

        builder.role_definition = RoleDefinition(
            "You are a Hint Generator Agent with DUAL capabilities.\n\n"

            "YOUR TWO MODES:\n"
            "1. HINT MODE - Generate Socratic hints for student work\n"
            "2. CONCEPT_EXPLANATION MODE - Explain concepts when students ask questions\n\n"

            "HOW TO DETERMINE MODE:\n"
            'Look for the "mode" field in your JSON input:\n'
            '- If mode is "HINT" -> Generate a hint based on student work and misconception\n'
            '- If mode is "CONCEPT_EXPLANATION" -> Explain the concept clearly\n\n'

            "YOUR WORKFLOW:\n"
            "1. Check the mode in your input\n"
            "2. Call socratic_hint_generator with the full JSON input\n"
            "3. Immediately use final_answer to return the result\n\n"

            "CRITICAL CONSTRAINTS:\n"
            "- NEVER provide final answers in hints\n"
            "- For concepts, explain clearly but don't solve specific problems\n"
            "- Always acknowledge student's correct work\n"
            "- Reference their specific notation/approach\n\n"
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
                "- Do NOT include any text or markdown formatting outside the JSON object.\n"
            ),
            FormatInstruction(
                "# --- COMPLETION RULE ---\n"
                "After receiving the output from socratic_hint_generator, you MUST immediately "
                "use final_answer to return it to the Manager."
            )
        ])

        builder.format_instructions.append(
            FormatInstruction(
                "# --- TOOL INPUT FORMATS (JSON) ---\n\n"
                "FOR HINT MODE:\n"
                '{"mode": "HINT", "problem": "full problem text", "student_work": "their actual work", '
                '"misconception": "description", "severity": "Critical/Major/Minor", "topic": "subject"}\n\n'

                "FOR CONCEPT EXPLANATION MODE:\n"
                '{"mode": "CONCEPT_EXPLANATION", "concept": "what to explain", '
                '"question": "student question", "topic": "subject"}'
            )
        )

        builder.examples.extend([
            Example(
                "User Request: Generate hint for student who got a history date wrong.\n"
                'Task Details: {"mode": "HINT", "problem": "What year did WWII end?", '
                '"student_work": "I think it ended in 1944", '
                '"misconception": "Off by one year", "severity": "Minor", "topic": "history"}\n\n'

                '{\n'
                '  "thought": "This is HINT mode. I need to generate a Socratic hint for a history date error.",\n'
                '  "action": {\n'
                '    "tool_name": "socratic_hint_generator",\n'
                '    "tool_input": "{\\"mode\\": \\"HINT\\", \\"problem\\": \\"What year did WWII end?\\", '
                '\\"student_work\\": \\"I think it ended in 1944\\", '
                '\\"misconception\\": \\"Off by one year\\", \\"severity\\": \\"Minor\\", \\"topic\\": \\"history\\"}"\n'
                '  }\n'
                '}\n\n'

                "Observation: COMPLETE HINT (Level 3): You're close! Think about the key events that marked the end. "
                "When did Germany surrender, and what happened in the Pacific?\n\n"

                '{\n'
                '  "thought": "The hint has been generated. I will return it using final_answer.",\n'
                '  "action": {\n'
                '    "tool_name": "final_answer",\n'
                '    "tool_input": "You\'re close! Think about the key events that marked the end of the war. '
                'When did Germany surrender, and what happened in the Pacific?"\n'
                '  }\n'
                '}'
            ),

            Example(
                "User Request: Explain a concept to student.\n"
                'Task Details: {"mode": "CONCEPT_EXPLANATION", "concept": "balancing chemical equations", '
                '"question": "How do I balance equations?", "topic": "chemistry"}\n\n'

                '{\n'
                '  "thought": "This is CONCEPT_EXPLANATION mode. I need to explain balancing equations.",\n'
                '  "action": {\n'
                '    "tool_name": "socratic_hint_generator",\n'
                '    "tool_input": "{\\"mode\\": \\"CONCEPT_EXPLANATION\\", '
                '\\"concept\\": \\"balancing chemical equations\\", '
                '\\"question\\": \\"How do I balance equations?\\", \\"topic\\": \\"chemistry\\"}"\n'
                '  }\n'
                '}\n\n'

                "Observation: CONCEPT EXPLANATION: Balancing means ensuring equal atoms on both sides. "
                "Start by counting atoms, then adjust coefficients.\n\n"

                '{\n'
                '  "thought": "The concept explanation is ready. I will return it.",\n'
                '  "action": {\n'
                '    "tool_name": "final_answer",\n'
                '    "tool_input": "Balancing chemical equations means ensuring you have the same number of each atom on both sides. '
                'Start by counting atoms, then adjust coefficients."\n'
                '  }\n'
                '}'
            )
        ])

        return builder
