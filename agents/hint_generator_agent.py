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
            "You generate Socratic hints AND concept explanations based on the MODE specified."
        )
        
        return agent

    #TODO:: getting error: 'Invalid \escape: line 1 column 76 (char 75)': add prompting for this
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
            "Look for 'MODE:' in your input:\n"
            "- If MODE: HINT -> Generate a hint based on student work and misconception\n"
            "- If MODE: CONCEPT_EXPLANATION -> Explain the concept clearly\n\n"
            
            "YOUR WORKFLOW:\n"
            "1. Check the MODE in your input\n"
            "2. Call socratic_hint_generator with ALL the context\n"
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
                "# --- TOOL INPUT FORMATS ---\n\n"
                "FOR HINT MODE:\n"
                "'MODE: HINT ||| PROBLEM: [full problem text] ||| STUDENT_WORK: [their actual work] ||| "
                "MISCONCEPTION: [description] ||| SEVERITY: [Critical/Major/Minor] ||| TOPIC: [subject]'\n\n"
                
                "FOR CONCEPT EXPLANATION MODE:\n"
                "'MODE: CONCEPT_EXPLANATION ||| CONCEPT: [what to explain] ||| "
                "QUESTION: [student's question] ||| TOPIC: [subject]'"
            )
        )
        
        builder.examples.extend([
            Example(
                "User Request: Generate hint for student who calculated momentum without units.\n"
                "Task Details: MODE: HINT ||| PROBLEM: Calculate the momentum of a 5 kg object moving at 10 m/s. ||| "
                "STUDENT_WORK: p = 5 * 10 = 50 ||| MISCONCEPTION: Missing units ||| SEVERITY: Minor ||| TOPIC: physics\n\n"
                
                '{\n'
                '  "thought": "This is HINT mode. I need to generate a Socratic hint for missing units.",\n'
                '  "action": {\n'
                '    "tool_name": "socratic_hint_generator",\n'
                '    "tool_input": "MODE: HINT ||| PROBLEM: Calculate the momentum of a 5 kg object moving at 10 m/s. ||| STUDENT_WORK: p = 5 * 10 = 50 ||| MISCONCEPTION: Missing units ||| SEVERITY: Minor ||| TOPIC: physics"\n'
                '  }\n'
                '}\n\n'
                
                "Observation: Excellent calculation! You've correctly applied p = mv. Now think: what units result from kg times m/s?\n\n"
                
                '{\n'
                '  "thought": "The hint has been generated. I will return it using final_answer.",\n'
                '  "action": {\n'
                '    "tool_name": "final_answer",\n'
                '    "tool_input": "Excellent calculation! You\'ve correctly applied p = mv. Now think: what units result from kg times m/s?"\n'
                '  }\n'
                '}'
            ),
            
            Example(
                "User Request: Explain momentum to student.\n"
                "Task Details: MODE: CONCEPT_EXPLANATION ||| CONCEPT: momentum ||| "
                "QUESTION: What is momentum? ||| TOPIC: physics\n\n"
                
                '{\n'
                '  "thought": "This is CONCEPT_EXPLANATION mode. I need to explain the concept of momentum.",\n'
                '  "action": {\n'
                '    "tool_name": "socratic_hint_generator",\n'
                '    "tool_input": "MODE: CONCEPT_EXPLANATION ||| CONCEPT: momentum ||| QUESTION: What is momentum? ||| TOPIC: physics"\n'
                '  }\n'
                '}\n\n'
                
                "Observation: Momentum is a measure of an object's motion, calculated as mass times velocity (p = mv). It tells us how difficult it is to stop a moving object.\n\n"
                
                '{\n'
                '  "thought": "The concept explanation is ready. I will return it.",\n'
                '  "action": {\n'
                '    "tool_name": "final_answer",\n'
                '    "tool_input": "Momentum is a measure of an object\'s motion, calculated as mass times velocity (p = mv). It tells us how difficult it is to stop a moving object."\n'
                '  }\n'
                '}'
            )
        ])
        
        return builder