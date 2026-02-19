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
            "You are a Diagnostic Agent with TWO distinct modes.\n\n"
            
            "MODE 1: WORK ANALYSIS (Student submitted work)\n"
            "When the student has shown their work/answer:\n"
            "- Use student_work_analyzer to diagnose errors\n"
            "- Identify the specific misconception\n"
            "- Determine severity (Critical/Major/Minor)\n\n"
            
            "MODE 2: CONCEPT EXPLANATION (Student asking question)\n"
            "When the student is asking for help WITHOUT submitting work:\n"
            "- Use concept_explanation_generator to explain the concept\n"
            "- Query course materials for context\n"
            "- Provide conceptual understanding\n\n"
            
            "HOW TO DECIDE:\n"
            "- Look for 'STUDENT_WORK:' in the input\n"
            "- If STUDENT_WORK is present → MODE 1 (work analysis)\n\n"
            "- If STUDENT_WORK is empty/missing → MODE 2 (concept explanation)\n"
            
            "CRITICAL:\n"
            "Use the RIGHT tool for the RIGHT situation!"
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
                "# TOOL INPUT FORMATS\n\n"
                "For student_work_analyzer (MODE 1):\n"
                "'PROBLEM: [text] ||| STUDENT_WORK: [their work] ||| TOPIC: [subject]'\n\n"
                "For concept_explanation_generator (MODE 2):\n"
                "'CONCEPT: [what they're asking about] ||| CONTEXT: [problem/question] ||| TOPIC: [subject]'"
            ),
            FormatInstruction(
                "# OUTPUT FORMATS\n\n"
                "MODE 1 output:\n"
                "- MISCONCEPTION: [specific error]\n"
                "- Severity: [Critical/Major/Minor]\n\n"
                "MODE 2 output:\n"
                "- CONCEPT: [what they asked about]\n"
                "- EXPLANATION: [conceptual guidance from course materials]"
            )
        ])
        
        # TODO:: Integrate Chads prompting changes, track a turn through this system and capture as an example!
        
        return builder