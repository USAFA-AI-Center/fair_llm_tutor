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
            prompt_builder=cls._create_manager_prompt()
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
    def _create_manager_prompt() -> PromptBuilder:
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
            "2. Delegate to HintGenerator with problem + student work + misconception + severity\n"
            "3. MANDATORY: Delegate to SafetyGuard to validate the hint\n"
            "4. Only after SafetyGuard approval, provide final synthesized hint\n\n"
            
            "MODE 2: CONCEPT QUESTION (No work submitted)\n"
            "When student is asking a question without work:\n"
            "1. Delegate to MisconceptionDetector with concept question\n"
            "2. MANDATORY: Delegate to SafetyGuard to validate concept teaching\n"
            "3. Only after SafetyGuard approval, provide final concept teaching\n\n"
                
            "ABSOLUTE RULES:\n"
            "- Never skip SafetyGuard validation for hints\n"
        )

        builder.format_instructions.extend([
            FormatInstruction(
                "# === OUTPUT FORMAT ===\n"
                "You MUST respond with EXACTLY ONE 'Thought' and ONE 'Action' per turn.\n"
                "Format:\n"
                "Thought: [Your reasoning about what to do next]\n"
                "Action: {\"tool_name\": \"delegate\", \"tool_input\": {\"worker_name\": \"WorkerName\", \"task\": \"detailed task\"}}\n\n"
                
                "OR for final answer:\n"
                "Thought: [Your reasoning that you have everything needed]\n"
                "Action: {\"tool_name\": \"final_answer\", \"tool_input\": \"Your complete response to the student\"}\n\n"
                
                "CRITICAL: The Action MUST be valid JSON. The 'tool_input' for delegation MUST contain both 'worker_name' and 'task' keys."
            ),
            FormatInstruction(
                "# === DECISION PROCESS ===\n"
                "On every turn:\n"
                "1. Look at the original 'User Request' - what is the goal?\n"
                "2. Look at the MOST RECENT 'Tool Observation' - what did the last worker return?\n"
                "3. Decide the next step:\n"
                "   - Need more information? Delegate to the appropriate worker\n"
                "   - Have everything needed? Use 'final_answer'\n\n"
                
                "Always include the FULL context in your delegation tasks."
            )
        ])
        
        builder.format_instructions.extend([
            FormatInstruction(
                "# === DELEGATION TEMPLATES ===\n\n"
                
                "To MisconceptionDetector (with student work):\n"
                "Action: {\"tool_name\": \"delegate\", \"tool_input\": {\"worker_name\": \"MisconceptionDetector\", "
                "\"task\": \"PROBLEM: [full problem text] ||| STUDENT_WORK: [their work] ||| TOPIC: [subject]\"}}\n\n"
                
                "To MisconceptionDetector (question only, no work):\n"
                "Action: {\"tool_name\": \"delegate\", \"tool_input\": {\"worker_name\": \"MisconceptionDetector\", "
                "\"task\": \"PROBLEM: [problem or question] ||| STUDENT_WORK: ||| STUDENT_QUESTION: [their question] ||| TOPIC: [subject]\"}}\n\n"
                
                "To HintGenerator (MUST include student work and misconception):\n"
                "Action: {\"tool_name\": \"delegate\", \"tool_input\": {\"worker_name\": \"HintGenerator\", "
                "\"task\": \"PROBLEM: [full problem] ||| STUDENT_WORK: [their work] ||| "
                "MISCONCEPTION: [from MisconceptionDetector] ||| SEVERITY: [level] ||| TOPIC: [subject]\"}}\n\n"
                
                "To SafetyGuard:\n"
                "Action: {\"tool_name\": \"delegate\", \"tool_input\": {\"worker_name\": \"SafetyGuard\", "
                "\"task\": \"PROBLEM: [full problem] ||| CORRECT_ANSWER: [if known] ||| "
                "PROPOSED_RESPONSE: [hint or explanation to validate]\"}}\n\n"
                
                "For final answer:\n"
                "Action: {\"tool_name\": \"final_answer\", \"tool_input\": \"Your synthesized response to the student\"}"
            )
        ])
        
        builder.format_instructions.append(
            FormatInstruction(
                "# === CRITICAL SAFETY RULE ===\n"
                "After receiving a response from HintGenerator OR MisconceptionDetector,\n"
                "your NEXT action MUST ALWAYS be to delegate to SafetyGuard.\n"
                "Do NOT skip this step for ANY reason.\n"
                "Do NOT provide final_answer until SafetyGuard has validated the response."
            )
        )

        builder.examples.extend([
            Example(
                "User Request: Student submitted work for: 'Calculate the momentum of a 5 kg object moving at 10 m/s.' Student work: 'p = 5 * 10 = 50'\n\n"
                
                "Thought: The student has submitted work. I must first delegate to MisconceptionDetector to analyze their solution.\n"
                "Action: {\"tool_name\": \"delegate\", \"tool_input\": {\"worker_name\": \"MisconceptionDetector\", \"task\": \"PROBLEM: Calculate the momentum of a 5 kg object moving at 10 m/s. ||| STUDENT_WORK: p = 5 * 10 = 50 ||| TOPIC: physics\"}}\n\n"
                
                "Tool Observation: Result from MisconceptionDetector: Student has correct formula and calculation but is missing units. Severity: minor. The correct answer is 50 kg⋅m/s.\n\n"
                
                "Thought: I have the misconception analysis. Now I need a Socratic hint that guides the student to discover the missing units. I'll delegate to HintGenerator with full context.\n"
                "Action: {\"tool_name\": \"delegate\", \"tool_input\": {\"worker_name\": \"HintGenerator\", \"task\": \"PROBLEM: Calculate the momentum of a 5 kg object moving at 10 m/s. ||| STUDENT_WORK: p = 5 * 10 = 50 ||| MISCONCEPTION: Missing units ||| SEVERITY: minor ||| TOPIC: physics\"}}\n\n"
                
                "Tool Observation: Result from HintGenerator: Excellent calculation! You've correctly applied p = mv. Now think about this: what happens when you multiply a mass (in kg) by a velocity (in m/s)? What units should your answer have?\n\n"
                
                "Thought: I have a good hint. I must validate it with SafetyGuard to ensure it doesn't reveal the answer.\n"
                "Action: {\"tool_name\": \"delegate\", \"tool_input\": {\"worker_name\": \"SafetyGuard\", \"task\": \"PROBLEM: Calculate momentum of 5 kg object at 10 m/s ||| CORRECT_ANSWER: 50 kg⋅m/s ||| PROPOSED_RESPONSE: Excellent calculation! You've correctly applied p = mv. Now think about this: what happens when you multiply a mass (in kg) by a velocity (in m/s)? What units should your answer have?\"}}\n\n"
                
                "Tool Observation: Result from SafetyGuard: SAFE - The hint guides thinking about units without revealing the answer.\n\n"
                
                "Thought: The hint has been validated. I now have everything to satisfy the students query and will give the student the output from the HintGenerator\n"
                "Action: {\"tool_name\": \"final_answer\", \"tool_input\": \"Excellent calculation! You've correctly applied p = mv. Now think about this: what happens when you multiply a mass (in kg) by a velocity (in m/s)? What units should your answer have?\"}"
            ),
            
            Example(
                "User Request: Student asks: 'What is momentum?' (No work submitted)\n\n"
                
                "Thought: The student is asking a conceptual question without submitting work. I'll delegate to MisconceptionDetector to provide a concept explanation.\n"
                "Action: {\"tool_name\": \"delegate\", \"tool_input\": {\"worker_name\": \"MisconceptionDetector\", \"task\": \"PROBLEM: What is momentum? ||| STUDENT_WORK: ||| STUDENT_QUESTION: What is momentum? ||| TOPIC: physics\"}}\n\n"
                
                "Tool Observation: Result from MisconceptionDetector: Momentum is a measure of an object's motion, calculated as mass times velocity (p = mv). It represents how difficult it is to stop a moving object.\n\n"
                
                "Thought: I have a concept explanation. I should validate it with SafetyGuard to ensure it's pedagogically appropriate.\n"
                "Action: {\"tool_name\": \"delegate\", \"tool_input\": {\"worker_name\": \"SafetyGuard\", \"task\": \"PROBLEM: Explain momentum ||| CORRECT_ANSWER: N/A ||| PROPOSED_RESPONSE: Momentum is a measure of an object's motion, calculated as mass times velocity (p = mv). It represents how difficult it is to stop a moving object.\"}}\n\n"
                
                "Tool Observation: Result from SafetyGuard: SAFE - Clear concept explanation appropriate for learning.\n\n"
                
                "Thought: The explanation has been validated. I can now provide the final answer.\n"
                "Action: {\"tool_name\": \"final_answer\", \"tool_input\": \"Momentum is a measure of an object's motion, calculated as mass times velocity (p = mv). It represents how difficult it is to stop a moving object. Think of it this way: a heavy truck moving slowly can have the same momentum as a light car moving quickly!\"}"
            )
        ])
        
        return builder