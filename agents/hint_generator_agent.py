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
    
    Simple workflow:
    1. Call socratic_hint_generator with full context
    2. Immediately use final_answer to return the hint
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
            "You generate Socratic hints by analyzing the student's work and misconception, "
            "then immediately return the generated hint."
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
            
            "YOUR SIMPLE WORKFLOW:\n"
            "1. Call socratic_hint_generator with ALL the context you received\n"
            "2. Immediately use final_answer to return the generated hint to the Manager\n\n"
            
            "YOUR GOAL:\n"
            "Create pedagogical hints that guide students to understanding WITHOUT revealing answers.\n"
            "Your hints are grounded in:\n"
            "1. The student's ACTUAL WORK (what they wrote/attempted)\n"
            "2. The identified MISCONCEPTION (what's wrong)\n"
            "3. The SEVERITY of the misconception\n"
            "4. Course MATERIALS (for context)\n\n"
            
            "CRITICAL CONSTRAINTS:\n"
            "- NEVER provide final answers in hints\n"
            "- NEVER complete work for student\n"
            "- NEVER reveal the last step\n"
            "- Always acknowledge what student did correctly\n"
            "- Reference their specific work in your hint\n\n"
            
            "YOU MUST COMPLETE IN EXACTLY 2 STEPS:\n"
            "Step 1: Use socratic_hint_generator tool\n"
            "Step 2: Use final_answer with the generated hint (Manager will validate it)"
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
                "- CRITICAL: When the hint contains backslashes (like LaTeX \\times), you MUST double-escape them: \\\\times\n"
                "- If hint has \\(, use \\\\( in the JSON. If hint has \\), use \\\\) in the JSON."
            ),
            FormatInstruction(
                "# --- COMPLETION RULE ---\n"
                "After receiving the hint from socratic_hint_generator, you MUST immediately "
                "use final_answer to return it to the Manager. The Manager will then validate it with SafetyGuard."
            )
        ])
        
        builder.format_instructions.append(
            FormatInstruction(
                "# --- socratic_hint_generator TOOL INPUT FORMAT ---\n"
                "'PROBLEM: [full problem text] ||| STUDENT_WORK: [their actual work] ||| "
                "MISCONCEPTION: [description] ||| SEVERITY: [Critical/Major/Minor] ||| TOPIC: [subject]'"
            )
        )
        
        builder.examples.extend([
            Example(
                "User Request: Generate hint for student who calculated momentum without units.\n"
                "Task Details: PROBLEM: Calculate the momentum of a 5 kg object moving at 10 m/s. ||| "
                "STUDENT_WORK: p = 5 * 10 = 50 ||| MISCONCEPTION: Missing units ||| SEVERITY: Minor ||| TOPIC: physics\n\n"
                
                '{\n'
                '  "thought": "I need to generate a Socratic hint for this student. I will call socratic_hint_generator with all the provided context.",\n'
                '  "action": {\n'
                '    "tool_name": "socratic_hint_generator",\n'
                '    "tool_input": "PROBLEM: Calculate the momentum of a 5 kg object moving at 10 m/s. ||| STUDENT_WORK: p = 5 * 10 = 50 ||| MISCONCEPTION: Missing units ||| SEVERITY: Minor ||| TOPIC: physics"\n'
                '  }\n'
                '}\n\n'
                
                "Observation: Excellent calculation! You've correctly applied p = mv. Now think about this: what happens when you multiply a mass (in kg) by a velocity (in m/s)? What units should your answer have?\n\n"
                
                '{\n'
                '  "thought": "The socratic_hint_generator has provided a complete hint. I will now return it to the Manager using final_answer.",\n'
                '  "action": {\n'
                '    "tool_name": "final_answer",\n'
                '    "tool_input": "Excellent calculation! You\'ve correctly applied p = mv. Now think about this: what happens when you multiply a mass (in kg) by a velocity (in m/s)? What units should your answer have?"\n'
                '  }\n'
                '}'
            ),
            
            Example(
                "User Request: Generate hint for student who used wrong formula.\n"
                "Task Details: PROBLEM: Find the area of a circle with radius 5 cm ||| "
                "STUDENT_WORK: A = 2πr = 10π ||| MISCONCEPTION: Used circumference formula ||| "
                "SEVERITY: Major ||| TOPIC: geometry\n\n"
                
                '{\n'
                '  "thought": "Major misconception - wrong formula used. I will generate an appropriate hint.",\n'
                '  "action": {\n'
                '    "tool_name": "socratic_hint_generator",\n'
                '    "tool_input": "PROBLEM: Find the area of a circle with radius 5 cm ||| STUDENT_WORK: A = 2πr = 10π ||| MISCONCEPTION: Used circumference formula ||| SEVERITY: Major ||| TOPIC: geometry"\n'
                '  }\n'
                '}\n\n'
                
                "Observation: I can see you're working with circles and using π correctly! However, let's think about what we're measuring. The formula 2πr gives us something different than area. What does 2πr actually calculate? And what formula involves π and r that would give us area (measured in square units)?\n\n"
                
                '{\n'
                '  "thought": "The hint has been generated. I will return it to the Manager using final_answer.",\n'
                '  "action": {\n'
                '    "tool_name": "final_answer",\n'
                '    "tool_input": "I can see you\'re working with circles and using π correctly! However, let\'s think about what we\'re measuring. The formula 2πr gives us something different than area. What does 2πr actually calculate? And what formula involves π and r that would give us area (measured in square units)?"\n'
                '  }\n'
                '}'
            )
        ])
        
        return builder