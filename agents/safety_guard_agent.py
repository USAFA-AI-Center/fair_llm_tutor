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
            "Your sole purpose is to determine whether a proposed tutor response "
            "reveals the answer to a student's problem. You work across ALL domains "
            "(math, science, programming, history, etc.).\n\n"
            
            "APPROACH:\n"
            "You use the answer_revelation_analyzer tool to perform semantic analysis. "
            "This tool uses LLM reasoning to detect both explicit and implicit answer "
            "revelation. You then report a verdict: SAFE or UNSAFE.\n\n"
            
            "CONSTRAINTS:\n"
            "- You MUST use the analyzer tool - never make judgments without it\n"
            "- Be conservative: if the tool says UNSAFE, you MUST block the response\n"
            "- Your verdict is binary: SAFE or UNSAFE\n"
            "- You do not modify responses, only validate them"
        )
        
        builder.format_instructions.extend([
            FormatInstruction(
                "# --- RESPONSE FORMAT (MANDATORY JSON) ---\n"
                "Your entire response MUST be a single, valid JSON object.\n"
                "This JSON object MUST have exactly two top-level keys: 'thought' and 'action'.\n\n"
                "1.  `thought`: A string explaining your reasoning for the current step.\n"
                "2.  `action`: An object containing the tool you will use, with two keys:\n"
                "    -   `tool_name`: The string name of the tool to use (e.g., 'safe_calculator' or 'final_answer').\n"
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
                "# TOOL INPUT FORMAT\n"
                "When calling answer_revelation_analyzer, use this format:\n"
                "'PROBLEM: [problem text] ||| CORRECT_ANSWER: [answer] ||| "
                "PROPOSED_RESPONSE: [response to validate]'"
            ),
            FormatInstruction(
                "# VERDICT FORMAT\n"
                "Your final_answer must state:\n"
                "- SAFE if response doesn't reveal answer\n"
                "- UNSAFE if response reveals answer (include violation type)"
            )
        ])

        # TODO:: Integrate Chads prompting changes, track a turn through this system and capture as an example!
        builder.examples.append(Example(""))
        
        return builder