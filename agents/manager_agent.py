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
        - Better mode detection (work submission vs question)
        - Conversation history tracking for safety validation
        - Proper routing based on student intent
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
            "- MisconceptionDetector: Analyzes student work for errors\n"
            "- HintGenerator: Creates hints AND provides concept explanations\n"
            "- SafetyGuard: Validates responses\n\n"
                
            "MODE DETECTION:\n"
            "First, determine the interaction mode.\n"
            "You are SOLELY RESPONSIBLE for determining the mode.\n"
            "There are two modes to choose from. MODE: CONCEPT_EXPLANATION, and MODE: HINT.\n"
            "Analyze the user input, if the student is asking for guidance on how to approach the problem, delegate adhearing to MODE: CONCEPT_EXPLANATION.\n"
            "If the student is asking if their answer is correct, showing work, delegate adhearing to MODE: HINT.\n"
            "This step is CRUTIAL in getting this system to work, if they are asking for guidance MODE 2, if they are submitting work and needing verification MODE: CONCEPT_EXPLANATION\n"
            
            "\tMODE: HINT\n"
            "\t\tIndicators: Student shows calculations, states 'my answer is', provides numerical values\n"
            "\t\tExamples: 'I got 500', 'My answer is 50kg*m/s', 'p = 5 * 10 = 50'\n"
            "\t\tAction: Analyze work -> Generate hint -> Validate safety\n"
            "\t\tDELEGATION INPUT MUST CONTAIN: MODE: HINT\n\n"
            
            "\tMODE: CONCEPT_EXPLANATION\n"
            "\t\tIndicators: Questions words (what, how, why), ends with '?', 'explain', 'help'\n"
            "\t\tExamples: 'What is momentum?', 'How do I calculate this?', 'Can you explain?'\n"
            "\t\tAction: HintGenerator provides concept explanation -> Validate safety\n"
            "\t\tDELEGATION INPUT MUST CONTAIN: MODE: CONCEPT_EXPLANATION\n\n"
            
            "SAFETY WITH HISTORY:\n"
            "Track conversation history. If student has already stated an answer,\n"
            "SafetyGuard can allow confirmation of that answer.\n"
            "Pass history to SafetyGuard: STUDENT_HISTORY: [previous student submissions]\n\n"
            
            "CONCEPT IN HINTGENERATOR:\n"
            "HintGenerator handles BOTH hints AND concept explanations\n"
            "Route concept questions directly to HintGenerator with MODE flag\n\n"
                
            "WORKFLOW:\n"
            "1. Detect mode from student input\n"
            "2. Route appropriately based on mode\n"
            "3. ALWAYS validate with SafetyGuard (include history)\n"
            "4. Provide final response\n"
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
                
                "CRITICAL: The Action MUST be valid JSON."
            ),
            FormatInstruction(
                "# === MODE DETECTION PROCESS ===\n"
                "On FIRST turn, analyze the student input:\n"
                "1. Look for work submission patterns (calculations, 'my answer', numbers with units)\n"
                "2. Look for question patterns ('what', 'how', 'explain', '?')\n"
                "3. Decide mode and route accordingly\n\n"
                
                "Include MODE in your delegations:\n"
                "- Add 'MODE: WORK_VALIDATION' or 'MODE: QUESTION_ANSWERING'"
            )
        ])
        
        builder.format_instructions.extend([
            FormatInstruction(
                "# === IMPROVED DELEGATION TEMPLATES ===\n\n"
                
                "To MisconceptionDetector (work validation):\n"
                "Action: {\"tool_name\": \"delegate\", \"tool_input\": {\"worker_name\": \"MisconceptionDetector\", "
                "\"task\": \"PROBLEM: [full problem text] ||| STUDENT_WORK: [their work] ||| TOPIC: [subject]\"}}\n\n"
                
                "To HintGenerator (for hint generation mode):\n"
                "Action: {\"tool_name\": \"delegate\", \"tool_input\": {\"worker_name\": \"HintGenerator\", "
                "\"task\": \"MODE: HINT ||| PROBLEM: [full problem] ||| STUDENT_WORK: [their work] ||| "
                "MISCONCEPTION: [from detector] ||| SEVERITY: [level] ||| TOPIC: [subject]\"}}\n\n"
                
                "To HintGenerator (for concept explanation mode):\n"
                "Action: {\"tool_name\": \"delegate\", \"tool_input\": {\"worker_name\": \"HintGenerator\", "
                "\"task\": \"MODE: CONCEPT_EXPLANATION ||| CONCEPT: [what to explain] ||| "
                "QUESTION: [student's question] ||| TOPIC: [subject]\"}}\n\n"
                
                "To SafetyGuard (with history):\n"
                "Action: {\"tool_name\": \"delegate\", \"tool_input\": {\"worker_name\": \"SafetyGuard\", "
                "\"task\": \"PROBLEM: [full problem] ||| CORRECT_ANSWER: [if known] ||| "
                "STUDENT_HISTORY: [list of previous student submissions] ||| "
                "PROPOSED_RESPONSE: [hint or explanation to validate]\"}}\n\n"
                
                "For final answer:\n"
                "Action: {\"tool_name\": \"final_answer\", \"tool_input\": \"Your synthesized response to the student\"}"
            )
        ])

        builder.examples.extend([
            Example(
                "User Request: Student says: 'I calculated 50kg*m/s'\n\n"
                
                "Thought: This is MODE 1 (WORK VALIDATION) - student is showing their calculated answer with units. "
                "I need to analyze their work first.\n"
                "Action: {\"tool_name\": \"delegate\", \"tool_input\": {\"worker_name\": \"MisconceptionDetector\", "
                "\"task\": \"PROBLEM: Calculate momentum of 5kg object at 10 m/s ||| "
                "STUDENT_WORK: I calculated 50kg*m/s ||| TOPIC: physics\"}}\n\n"
                
                "Tool Observation: Student has correct answer with proper units (50 kg·m/s)\n\n"
                
                "Thought: Student is correct! I'll generate an appropriate response.\n"
                "Action: {\"tool_name\": \"delegate\", \"tool_input\": {\"worker_name\": \"HintGenerator\", "
                "\"task\": \"MODE: HINT ||| PROBLEM: Calculate momentum ||| STUDENT_WORK: 50kg*m/s ||| "
                "MISCONCEPTION: None - correct answer ||| SEVERITY: none ||| TOPIC: physics\"}}\n\n"
                
                "Tool Observation: Excellent work! You correctly calculated 50 kg·m/s.\n\n"
                
                "Thought: Need to validate with SafetyGuard, including history showing student already gave answer.\n"
                "Action: {\"tool_name\": \"delegate\", \"tool_input\": {\"worker_name\": \"SafetyGuard\", "
                "\"task\": \"PROBLEM: Calculate momentum ||| CORRECT_ANSWER: 50 kg·m/s ||| "
                "STUDENT_HISTORY: ['I calculated 50kg*m/s'] ||| "
                "PROPOSED_RESPONSE: Excellent work! You correctly calculated 50 kg·m/s.\"}}\n\n"
                
                "Tool Observation: SAFE - Student already provided this answer\n\n"
                
                "Thought: Validated. Can provide final response.\n"
                "Action: {\"tool_name\": \"final_answer\", \"tool_input\": \"Excellent work! You correctly calculated "
                "50 kg·m/s. You applied p = mv perfectly and included the proper units!\"}"
            ),
            
            Example(
                "User Request: 'What is momentum?'\n\n"
                
                "Thought: This is MODE 2 (QUESTION ANSWERING) - student asking conceptual question. "
                "Route to HintGenerator for concept explanation.\n"
                "Action: {\"tool_name\": \"delegate\", \"tool_input\": {\"worker_name\": \"HintGenerator\", "
                "\"task\": \"MODE: CONCEPT_EXPLANATION ||| CONCEPT: momentum ||| "
                "QUESTION: What is momentum? ||| TOPIC: physics\"}}\n\n"
                
                "Tool Observation: Momentum is a measure of an object's motion, calculated as mass times velocity (p = mv).\n\n"
                
                "Thought: Validate the concept explanation.\n"
                "Action: {\"tool_name\": \"delegate\", \"tool_input\": {\"worker_name\": \"SafetyGuard\", "
                "\"task\": \"PROBLEM: Explain momentum ||| CORRECT_ANSWER: N/A ||| "
                "STUDENT_HISTORY: [] ||| PROPOSED_RESPONSE: Momentum is a measure of an object's motion, "
                "calculated as mass times velocity (p = mv).\"}}\n\n"
                
                "Tool Observation: SAFE - Conceptual explanation\n\n"
                
                "Thought: Validated. Provide final answer.\n"
                "Action: {\"tool_name\": \"final_answer\", \"tool_input\": \"Momentum is a measure of an object's "
                "motion, calculated as mass times velocity (p = mv). Think of it as how hard it would be to stop "
                "a moving object.\"}"
            )
        ])
        
        return builder
