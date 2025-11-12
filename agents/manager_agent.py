# manager_agent.py

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
    """
    
    @classmethod
    def create(cls, llm: AbstractChatModel, memory: AbstractMemory, 
               workers: Dict) -> "TutorManagerAgent":
        """Create manager with improved prompt for context preservation"""
        
        planner = ManagerPlanner(
            llm=llm,
            workers=workers,
            prompt_builder=cls._create_improved_prompt()
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
    def _create_improved_prompt() -> PromptBuilder:
        builder = PromptBuilder()
        
        builder.role_definition = RoleDefinition(
            "You are a Socratic Tutor Manager coordinating specialist agents.\n\n"
            
            "YOUR TEAM:\n"
            "- MisconceptionDetector: Analyzes student work OR explains concepts\n"
            "- HintGenerator: Creates Socratic hints using full context\n"
            "- SafetyGuard: Validates HintGenerator responses don't reveal answers\n\n"
            
            "TWO MODES OF OPERATION:\n\n"
            
            "MODE 1: WORK ANALYSIS (Student submitted work)\n"
            "When student has submitted work:\n"
            "1. Delegate to MisconceptionDetector with problem + student work\n"
            "2. Delegate to HintGenerator with problem + student work + misconception\n"
            "3. Delegate to SafetyGuard to validate hint\n"
            "4. Provide final synthesized response\n\n"
            
            "MODE 2: CONCEPT QUESTION (No work submitted)\n"
            "When student is asking a question without work:\n"
            "1. Delegate to MisconceptionDetector with concept question\n"
            "2. Delegate to SafetyGuard to concept teaching\n"
            "3. Provide concept teaching as final synthesized response\n\n"
            
            "CONSTRAINTS:\n"
            "- Never skip SafetyGuard validation for hints\n"
            "- Always include complete context in delegations\n"
            "- Always provide a clear answer to the student, either a concept explanation or a hint!\n"
        )
        
        builder.format_instructions.extend([
            FormatInstruction(
                "# --- DELEGATION FORMATS ---\n\n"
                
                "To MisconceptionDetector (with work):\n"
                '{"worker_name": "MisconceptionDetector", '
                '"task": "PROBLEM: [text] ||| STUDENT_WORK: [their work] ||| TOPIC: [subject]"}\n\n'
                
                "To MisconceptionDetector (question only):\n"
                '{"worker_name": "MisconceptionDetector", '
                '"task": "PROBLEM: [text] ||| STUDENT_WORK: ||| STUDENT_QUESTION: [question] ||| TOPIC: [subject]"}\n\n'
                
                "To HintGenerator (MUST include student work!):\n"
                '{"worker_name": "HintGenerator", '
                '"task": "PROBLEM: [text] ||| STUDENT_WORK: [their work] ||| '
                'MISCONCEPTION: [from detector] ||| SEVERITY: [level] ||| TOPIC: [subject]"}\n\n'
                
                "To SafetyGuard:\n"
                '{"worker_name": "SafetyGuard", '
                '"task": "PROBLEM: [text] ||| CORRECT_ANSWER: [if known] ||| '
                'PROPOSED_RESPONSE: [hint or concept explanation to validate]"}'
            ),
        ])
        
        # TODO:: Integrate Chads prompting changes, track a turn through this system and capture as an example!
        builder.examples.append(
            Example("")
        )
        
        return builder