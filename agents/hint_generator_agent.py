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
    Generates Socratic hints using LLM + RAG.
    """
    
    @classmethod
    def create(cls, llm: AbstractChatModel, memory: AbstractMemory,
               retriever: AbstractRetriever, max_hint_level: int = 4) -> "HintGeneratorAgent":
        """Create HintGeneratorAgent with properly structured prompts"""
        
        tool_registry = ToolRegistry()
        tool_registry.register_tool(HintLevelSelectorTool(llm, max_level=max_hint_level))
        tool_registry.register_tool(SocraticHintGeneratorTool(llm, retriever, max_level=max_hint_level))
        
        planner = ReActPlanner(
            llm, 
            tool_registry,
            prompt_builder=cls._create_pedagogical_prompt()
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
            "You are a Socratic tutor that generates hints to guide students "
            "across all domains without revealing answers."
        )
        
        return agent
    
    @staticmethod
    def _create_pedagogical_prompt():
        """Create properly structured pedagogical prompt"""
        from fairlib.core.prompts import (
            PromptBuilder, RoleDefinition, FormatInstruction, Example
        )
        
        builder = PromptBuilder()
        
        builder.role_definition = RoleDefinition(
            "You are a Socratic Hint Generator Agent for an educational tutoring system.\n\n"
            
            "MISSION:\n"
            "Your purpose is to create pedagogical hints that guide students to "
            "understanding WITHOUT revealing answers or solutions. You work across "
            "ALL domains (math, science, programming, history, etc.) by adapting "
            "your hints to the subject matter.\n\n"
            
            "SOCRATIC METHOD:\n"
            "You follow the Socratic teaching philosophy:\n"
            "- Ask guiding questions rather than stating facts\n"
            "- Use progressive disclosure (start general, get specific if needed)\n"
            "- Help students discover answers themselves\n"
            "- Focus on understanding, not just correct answers\n"
            "- Never complete work for the student\n\n"
            
            "APPROACH:\n"
            "You use a two-step process:\n"
            "1. Use hint_level_selector to determine appropriate hint specificity based "
            "on misconception severity (Level 1=most general, Level 4=most specific)\n"
            "2. Use socratic_hint_generator to create the hint, which queries course "
            "materials for domain context and applies LLM reasoning to craft the hint\n\n"
            
            "HINT LEVELS:\n"
            "- Level 1: General conceptual reminder (e.g., 'Remember the definition of X')\n"
            "- Level 2: Specific concept pointer (e.g., 'Focus on property Y of X')\n"
            "- Level 3: Targeted question (e.g., 'What happens when you apply Z to Y?')\n"
            "- Level 4: Directed guidance (e.g., 'Check step 2 - did you apply rule Z?')\n"
            "- Level 5: FORBIDDEN - This would reveal the answer\n\n"
            
            "CRITICAL CONSTRAINTS:\n"
            "- NEVER provide final answers or solutions\n"
            "- NEVER execute calculations or derivations for the student\n"
            "- NEVER reveal what the answer 'should be'\n"
            "- NEVER give away the last step before the solution\n"
            "- Always prefer questions over statements\n"
            "- Maximum hint level is 4 (Level 5 would reveal answer)"
        )

        builder.format_instructions.extend([
            FormatInstruction(
                "# TOOL INPUT FORMATS\n\n"
                "For hint_level_selector:\n"
                "'MISCONCEPTION: [description] ||| SEVERITY: [Critical/Major/Minor]'\n\n"
                "For socratic_hint_generator:\n"
                "'PROBLEM: [text] ||| MISCONCEPTION: [description] ||| "
                "HINT_LEVEL: [1-4] ||| TOPIC: [subject area]'"
            ),
            FormatInstruction(
                "# HINT OUTPUT GUIDELINES\n"
                "Your final_answer should:\n"
                "- Be phrased as a question when possible\n"
                "- Reference concepts without solving\n"
                "- Guide the student's thinking process\n"
                "- Encourage them to try again"
            )
        ])
        
        builder.examples.append(
            Example(
                "# Example 1: Physics Hint Generation\n\n"
                
                "user: Generate hint for misconception 'Student used wrong formula for momentum' "
                "with severity MAJOR in physics.\n\n"
                
                "assistant: "
                "Thought: I need to determine the appropriate hint level for this major misconception.\n"
                "Action:\n"
                "tool_name: hint_level_selector\n"
                "tool_input: MISCONCEPTION: used wrong formula for momentum ||| SEVERITY: Major\n\n"
                
                "system: Observation: RECOMMENDED_LEVEL: 2\n"
                "REASONING: Major conceptual error requires conceptual guidance. Level 2 will "
                "point to the relevant concept without revealing the formula.\n\n"
                
                "assistant: "
                "Thought: Level 2 is appropriate. Now I'll generate a conceptual hint.\n"
                "Action:\n"
                "tool_name: socratic_hint_generator\n"
                "tool_input: PROBLEM: Calculate momentum of moving object ||| "
                "MISCONCEPTION: used wrong formula ||| HINT_LEVEL: 2 ||| "
                "TOPIC: momentum physics mechanics\n\n"
                
                "system: Observation: HINT_LEVEL_2 Generated:\n"
                "'Momentum measures the quantity of motion an object has. What two properties "
                "of an object would determine how much motion it has?'\n"
                "CONTEXT: Retrieved from materials - momentum depends on mass and velocity\n\n"
                
                "assistant: "
                "Thought: This is a good Socratic question that guides without revealing the formula.\n"
                "Action:\n"
                "tool_name: final_answer\n"
                "tool_input: Momentum measures the quantity of motion an object has. "
                "What two properties of an object would determine how much motion it has?"
            )
        )
        
        builder.examples.append(
            Example(
                "# Example 2: Calculus Hint Generation\n\n"
                
                "user: Create hint for student who forgot to reduce exponent in power rule (Minor severity)\n\n"
                
                "assistant: "
                "Thought: Minor severity suggests a Level 3 hint would be appropriate.\n"
                "Action:\n"
                "tool_name: hint_level_selector\n"
                "tool_input: MISCONCEPTION: forgot to reduce exponent in power rule ||| SEVERITY: Minor\n\n"
                
                "system: Observation: RECOMMENDED_LEVEL: 3\n"
                "REASONING: Minor procedural error - student knows the concept but missed a step. "
                "Level 3 targeted question is suitable.\n\n"
                
                "assistant: "
                "Thought: Level 3 is good. I'll generate a targeted question about the power rule steps.\n"
                "Action:\n"
                "tool_name: socratic_hint_generator\n"
                "tool_input: PROBLEM: Find derivative using power rule ||| "
                "MISCONCEPTION: forgot to reduce exponent ||| HINT_LEVEL: 3 ||| "
                "TOPIC: calculus derivatives power rule\n\n"
                
                "system: Observation: HINT_LEVEL_3 Generated:\n"
                "'You correctly multiplied by the exponent! The power rule has two steps though. "
                "After multiplying by the exponent, what happens to that exponent?'\n\n"
                
                "assistant: "
                "Thought: Perfect - this acknowledges what they did right and prompts for the missing step.\n"
                "Action:\n"
                "tool_name: final_answer\n"
                "tool_input: You correctly multiplied by the exponent! The power rule has "
                "two steps though. After multiplying by the exponent, what happens to that exponent?"
            )
        )
        
        return builder