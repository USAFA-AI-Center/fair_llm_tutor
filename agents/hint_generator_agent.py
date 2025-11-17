# hint_generator_agent.py

from fairlib.modules.agent.simple_agent import SimpleAgent
from fairlib.core.interfaces.llm import AbstractChatModel
from fairlib.core.interfaces.memory import AbstractMemory
from fairlib.modules.planning.react_planner import ReActPlanner
from fairlib.modules.action.executor import ToolExecutor
from fairlib.modules.action.tools.registry import ToolRegistry
from fairlib.core.interfaces.memory import AbstractRetriever

from tools.pedagogical_tools import HintLevelSelectorTool, SocraticHintGeneratorTool


class HintGeneratorAgent(SimpleAgent):
    """
    Generates Socratic hints using LLM + RAG + student work context.
    
    Inputs to this agent:
    - Student misconception
    - Student work
    - Problem the student is working on
    - General problem domain
    """
    
    @classmethod
    def create(cls, llm: AbstractChatModel, memory: AbstractMemory,
               retriever: AbstractRetriever, max_hint_level: int = 4) -> "HintGeneratorAgent":        
        tool_registry = ToolRegistry()
        tool_registry.register_tool(HintLevelSelectorTool(llm, max_level=max_hint_level))
        tool_registry.register_tool(SocraticHintGeneratorTool(llm, retriever, max_level=max_hint_level))
        
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
            max_steps=6,
            stateless=True
        )
        
        agent.role_description = (
            "You generate Socratic hints using:" \
            "   1. The students misconception." \
            "   2. The students work." \
            "   3. The problem that the student is working on." \
            "   4. The domain of the current problem."
        )
        
        return agent
    
    @staticmethod
    def _create_hint_prompt():
        from fairlib.core.prompts import (
            PromptBuilder, RoleDefinition, FormatInstruction, Example
        )
        
        builder = PromptBuilder()
        
        builder.role_definition = RoleDefinition(
            "You are a Socratic Hint Generator Agent.\n\n"
            
            "YOUR GOAL:\n"
            "Create pedagogical hints that guide students to understanding WITHOUT revealing answers!"
            "Your hints are grounded in:\n"
            "1. The student's ACTUAL WORK (what they wrote/attempted)\n"
            "2. The identified MISCONCEPTION (what the student is doing wrong)\n"
            "3. Course MATERIALS (for context)\n\n"
            
            "YOUR APPROACH:\n"
            "1. FIRST use hint_level_selector to determine appropriate hint level based on misconception severity\n"
            "2. THEN use socratic_hint_generator with FULL CONTEXT (from using the hint_level_selector tool):\n"
            "   - Problem statement\n"
            "   - Student's actual work\n"
            "   - Identified misconception\n"
            "   - Hint level\n"
            "   - Topic\n\n"
            
            "ABAILABLE HINT LEVELS:\n"
            "- Level 1: General conceptual reminder\n"
            "- Level 2: Specific concept pointer\n"
            "- Level 3: Targeted question\n"
            "- Level 4: Directed guidance\n"
            "- Level 5: FORBIDDEN (reveals answer)\n\n"
            
            "CRITICAL CONSTRAINTS:\n"
            "- NEVER provide final answers\n"
            "- NEVER complete work for student\n"
            "- NEVER reveal the last step\n"
            "- Always acknowledge what student did correctly\n"
            "- Reference their specific work in your hint"

            "MANDATORY HINT QUALITY GUIDELINES\n\n"
                "Your hint should:\n"
                "1. Start by acknowledging what student did right (from their work)\n"
                "2. Guide toward the specific error (the misconception)\n"
                "3. Use a Socratic question when possible\n"
                "4. Reference their exact approach/notation\n"
                "5. Encourage them to try again"
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
                "hint_level_selector TOOL INPUT FORMAT:\n"
                "   'MISCONCEPTION: [description] ||| SEVERITY: [Critical/Major/Minor]'\n\n"
            ),
            FormatInstruction(
                "socratic_hint_generator TOOL INPUT FORMAT:\n"
                "   'PROBLEM: [text] ||| STUDENT_WORK: [their actual work] ||| MISCONCEPTION: [description] ||| HINT_LEVEL: [1-4] ||| TOPIC: [subject]'\n"
            )
        ])
        
        # TODO:: Integrate Chads prompting changes, track a turn through this system and capture as an example!
        builder.examples.append(Example(""))
        
        return builder