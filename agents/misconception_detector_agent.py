# misconception_detector_agent.py

from fairlib.modules.agent.simple_agent import SimpleAgent
from fairlib.core.interfaces.llm import AbstractChatModel
from fairlib.core.interfaces.memory import AbstractMemory
from fairlib.modules.planning.react_planner import ReActPlanner
from fairlib.modules.action.executor import ToolExecutor
from fairlib.modules.action.tools.registry import ToolRegistry
from fairlib.core.interfaces.memory import AbstractRetriever

from tools.diagnostic_tools import StudentWorkAnalyzerTool, ConceptExplanationGeneratorTool


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
        tool_registry.register_tool(ConceptExplanationGeneratorTool(llm, retriever))
        
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
            max_steps=8,
            stateless=True
        )
        
        agent.role_description = (
            "You are a diagnostic agent that analyzes student work to identify "
            "specific misconceptions across all domains."
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
            "You are a Misconception Detector Agent for an educational tutoring system.\n\n"
            
            "MISSION:\n"
            "Your purpose is to analyze student work and identify SPECIFIC conceptual "
            "errors or misconceptions. You determine WHAT the student misunderstands "
            "and WHY they made the error, not just that they're wrong.\n\n"
            
            "DOMAIN INDEPENDENCE:\n"
            "You work across ALL subjects: mathematics, physics, biology, chemistry, "
            "computer science, history, literature, etc. You use course materials "
            "(via RAG) and LLM reasoning to understand domain-specific concepts.\n\n"
            
            "APPROACH:\n"
            "You use the student_work_analyzer tool, which:\n"
            "1. Queries course materials for relevant context\n"
            "2. Applies LLM reasoning to identify the specific error\n"
            "3. Determines the severity (Critical/Major/Minor)\n"
            "4. Identifies the root misconception\n\n"
            
            "You then report a structured diagnosis that includes:\n"
            "- The specific misconception (not just 'wrong answer')\n"
            "- The severity level\n"
            "- The root cause of the error\n\n"
            
            "CRITICAL PRINCIPLE:\n"
            "Focus on the conceptual error, not just the incorrect result. "
            "Be specific: say 'forgot to normalize vector' not 'wrong answer'. "
            "Never reveal the correct answer in your diagnosis."
        )
        
        builder.format_instructions.extend([
            FormatInstruction(
                "# TOOL INPUT FORMAT\n"
                "When calling student_work_analyzer, use:\n"
                "'PROBLEM: [problem text] ||| STUDENT_WORK: [their work] ||| TOPIC: [subject area]'"
            ),
            FormatInstruction(
                "# DIAGNOSIS OUTPUT FORMAT\n"
                "Your final_answer should include:\n"
                "- MISCONCEPTION: [specific conceptual error]\n"
                "- Severity: [Critical/Major/Minor]\n"
                "- Optional: Root cause explanation"
            )
        ])
        
        builder.examples.append(
            Example(
                "# Example: Analyzing Biology Misconception\n\n"
                
                "user: Analyze student work for problem 'Explain natural selection' "
                "where student wrote 'Animals change themselves to survive their environment.'\n\n"
                
                "assistant: "
                "Thought: I need to analyze this student's understanding of natural selection. "
                "I'll use the analyzer tool with the proper format.\n"
                "Action:\n"
                "tool_name: student_work_analyzer\n"
                "tool_input: PROBLEM: Explain natural selection ||| "
                "STUDENT_WORK: Animals change themselves to survive their environment ||| "
                "TOPIC: natural selection evolution biology\n\n"
                
                "system: Observation: ANALYSIS COMPLETE\n"
                "Severity: Major\n"
                "ERROR_IDENTIFIED: Student implies organisms intentionally adapt during their lifetime\n"
                "ROOT_MISCONCEPTION: Confusing individual adaptation (Lamarckism) with population "
                "evolution through differential survival and reproduction\n"
                "CONTEXT: Course materials emphasize that natural selection acts on populations, "
                "not individuals, and occurs over many generations\n\n"
                
                "assistant: "
                "Thought: I have a clear diagnosis of the misconception. This is Lamarckian thinking.\n"
                "Action:\n"
                "tool_name: final_answer\n"
                "tool_input: MISCONCEPTION: Lamarckian thinking - student believes organisms "
                "intentionally change during their lifetime to adapt, rather than understanding "
                "that populations evolve through differential survival of pre-existing variations. "
                "Severity: MAJOR"
            )
        )
        
        builder.examples.append(
            Example(
                "# Example: Analyzing Math Misconception\n\n"
                
                "user: Analyze work for 'Find derivative of 3x^2' where student got '6x^2'\n\n"
                
                "assistant: "
                "Thought: Student got the derivative wrong. I need to identify the specific error.\n"
                "Action:\n"
                "tool_name: student_work_analyzer\n"
                "tool_input: PROBLEM: Find derivative of 3x^2 ||| "
                "STUDENT_WORK: 6x^2 ||| "
                "TOPIC: calculus derivatives power rule\n\n"
                
                "system: Observation: ANALYSIS COMPLETE\n"
                "Severity: Minor\n"
                "ERROR_IDENTIFIED: Student correctly multiplied coefficient by exponent (3*2=6) "
                "but forgot to reduce the exponent by 1\n"
                "ROOT_MISCONCEPTION: Incomplete application of power rule - only remembering "
                "the first step (multiply by exponent) but not the second (reduce exponent)\n\n"
                
                "assistant: "
                "Thought: Clear diagnosis - they know part of the power rule but not all of it.\n"
                "Action:\n"
                "tool_name: final_answer\n"
                "tool_input: MISCONCEPTION: Incomplete power rule application - student "
                "correctly multiplied by exponent but forgot to reduce exponent by 1. "
                "Severity: MINOR"
            )
        )
        
        return builder