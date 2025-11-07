# safety_guard_agent.py

from fairlib.modules.agent.simple_agent import SimpleAgent
from fairlib.core.interfaces.llm import AbstractChatModel
from fairlib.core.interfaces.memory import AbstractMemory
from fairlib.modules.planning.react_planner import ReActPlanner
from fairlib.modules.action.executor import ToolExecutor
from fairlib.modules.action.tools.registry import ToolRegistry

from tools.safety_tools import AnswerRevelationAnalyzerTool, SemanticAnswerMatcherTool


class SafetyGuardAgent(SimpleAgent):
    """
    Safety validation agent using LLM reasoning.
    """
    
    @classmethod
    def create(cls, llm: AbstractChatModel, memory: AbstractMemory) -> "SafetyGuardAgent":
        """Create SafetyGuardAgent with properly structured prompts"""
        
        tool_registry = ToolRegistry()
        tool_registry.register_tool(AnswerRevelationAnalyzerTool(llm))
        tool_registry.register_tool(SemanticAnswerMatcherTool(llm))
        
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
        """
        Create properly structured prompt that EXTENDS the ReActPlanner defaults.
        
        Structure:
        1. RoleDefinition: WHO you are + WHAT your mission is + HOW you operate
        2. FormatInstruction: Additional format guidance (not workflow!)
        3. Examples: Demonstrations in the EXACT format ReActPlanner expects
        """
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

        builder.examples.append(
            Example(
                "# Example 1: Detecting Direct Answer Revelation\n\n"
                
                "user: Validate this response for problem 'What is photosynthesis?' "
                "where student answered 'Plants make food' and tutor response is "
                "'The answer is plants convert light to glucose.'\n\n"
                
                "assistant: "
                "Thought: I need to validate if this tutor response reveals the answer. "
                "I'll use the analyzer tool with the proper format.\n"
                "Action:\n"
                "tool_name: answer_revelation_analyzer\n"
                "tool_input: PROBLEM: What is photosynthesis? ||| "
                "CORRECT_ANSWER: plants convert light energy to glucose ||| "
                "PROPOSED_RESPONSE: The answer is plants convert light to glucose.\n\n"
                
                "system: Observation: UNSAFE - Answer revelation detected. Response "
                "directly states the answer with phrase 'The answer is...'\n\n"
                
                "assistant: "
                "Thought: The tool detected unsafe content. I must block this response.\n"
                "Action:\n"
                "tool_name: final_answer\n"
                "tool_input: UNSAFE - Response directly reveals the answer. "
                "Violation: direct_answer_statement"
            )
        )

        builder.examples.append(
            Example(
                "# Example 2: Validating Safe Socratic Question\n\n"
                
                "user: Validate response for 'Find derivative of x^2' where tutor "
                "response is 'What happens to the exponent when you apply the power rule?'\n\n"
                
                "assistant: "
                "Thought: I need to check if this Socratic question reveals the answer.\n"
                "Action:\n"
                "tool_name: answer_revelation_analyzer\n"
                "tool_input: PROBLEM: Find derivative of x^2 ||| "
                "CORRECT_ANSWER: 2x ||| "
                "PROPOSED_RESPONSE: What happens to the exponent when you apply the power rule?\n\n"
                
                "system: Observation: SAFE - Response is a guiding question that prompts "
                "thinking without revealing the solution.\n\n"
                
                "assistant: "
                "Thought: The tool confirmed this is safe. I can approve the response.\n"
                "Action:\n"
                "tool_name: final_answer\n"
                "tool_input: SAFE - Response guides without revealing answer"
            )
        )
        
        return builder