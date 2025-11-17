# pedagogical_tools.py

from fairlib.core.interfaces.tools import AbstractTool
from fairlib.core.interfaces.llm import AbstractChatModel
from fairlib.core.interfaces.memory import AbstractRetriever


class SocraticHintGeneratorTool(AbstractTool):
    """
    Generates Socratic hints using LLM + RAG + STUDENT WORK context.
    """
    
    def __init__(self, llm: AbstractChatModel, retriever: AbstractRetriever):
        self.name = "socratic_hint_generator"
        self.description = (
            "Generates a complete Socratic hint using problem, student work, and misconception. "
            "Input format: 'PROBLEM: [text] ||| STUDENT_WORK: [their work] ||| "
            "MISCONCEPTION: [text] ||| SEVERITY: [Critical/Major/Minor] ||| TOPIC: [subject]'"
        )
        self.llm = llm
        self.retriever = retriever
    
    def use(self, tool_input: str) -> str:
        """Generate hint with full context"""
        
        # Parse input
        parts = tool_input.split("|||")
        problem = ""
        student_work = ""
        misconception = ""
        severity = "Minor"
        topic = ""
        
        for part in parts:
            part = part.strip()
            if part.upper().startswith("PROBLEM:"):
                problem = part.split(":", 1)[1].strip()
            elif part.upper().startswith("STUDENT_WORK:"):
                student_work = part.split(":", 1)[1].strip()
            elif part.upper().startswith("MISCONCEPTION:"):
                misconception = part.split(":", 1)[1].strip()
            elif part.upper().startswith("SEVERITY:"):
                severity = part.split(":", 1)[1].strip()
            elif part.upper().startswith("TOPIC:"):
                topic = part.split(":", 1)[1].strip()
        
        # Determine hint level from severity automatically
        severity_upper = severity.upper()
        if severity_upper == "CRITICAL":
            hint_level = 2
        elif severity_upper == "MAJOR":
            hint_level = 2
        elif severity_upper == "MINOR":
            hint_level = 3
        else:
            hint_level = 2
        
        # Query course materials for context (RAG)
        relevant_docs = ""
        if self.retriever:
            try:
                docs = self.retriever.retrieve(
                    query=f"{topic} {misconception}",
                    top_k=3
                )
                if docs:
                    relevant_docs = "\n".join([doc.page_content for doc in docs[:2]])
            except Exception as e:
                relevant_docs = ""
        
        # Create prompt for LLM that includes student work
        prompt = self._create_hint_generation_prompt(
            problem=problem,
            student_work=student_work,
            misconception=misconception,
            hint_level=hint_level,
            severity=severity,
            topic=topic,
            course_materials=relevant_docs
        )
        
        # Generate hint using LLM
        from fairlib.core.message import Message
        messages = [Message(role="user", content=prompt)]
        response = self.llm.invoke(messages)
        
        hint_text = response.content.strip()
        
        # Return in a format that signals completion
        return (
            f"COMPLETE HINT (Level {hint_level} based on {severity} severity):\n"
            f"{hint_text}\n\n"
            f"This hint is ready to present to the student. Use final_answer to deliver it."
        )

    def _create_hint_generation_prompt(
        self,
        problem: str,
        student_work: str,
        misconception: str,
        hint_level: int,
        severity: str,
        topic: str,
        course_materials: str
    ) -> str:
        hint_level_descriptions = {
            1: "General conceptual reminder - very broad guidance",
            2: "Specific concept pointer - focus on relevant concept",
            3: "Targeted Socratic question - guide toward error",
            4: "Directed guidance - specific about what to check"
        }
        
        return f"""You are a Socratic tutor creating a hint for a student.

    CONTEXT:
    Problem: {problem}
    Student's Work: {student_work}
    Identified Misconception: {misconception}
    Severity: {severity}
    Topic: {topic}

    COURSE MATERIALS (for context):
    {course_materials if course_materials else 'No additional materials'}

    YOUR TASK:
    Create a Level {hint_level} hint ({hint_level_descriptions.get(hint_level, 'guidance')}).

    CRITICAL REQUIREMENTS:
    1. ACKNOWLEDGE what the student did correctly in their work
    2. Reference their specific approach/notation
    3. Guide toward resolving their misconception
    4. Use a Socratic question when possible
    5. NEVER reveal the final answer
    6. NEVER complete the work for them

    FORMATTING RULES (CRITICAL):
    7. DO NOT use LaTeX notation at all (no backslashes: \\, \\times, \\(, \\), etc.)
    8. Instead of LaTeX, write formulas naturally:
    - Use: "p = m * v" or "p = m times v"
    - NOT: "\\( p = m \\times v \\)"
    9. For variables, just use plain letters: p, m, v, x, y
    10. This is MANDATORY because your output will be embedded in JSON

    HINT LEVEL GUIDANCE:
    - Level 1: "Remember the definition of [concept]"
    - Level 2: "Think about the relationship between [concepts]"
    - Level 3: "What happens when you [specific action]?"
    - Level 4: "Look at your [specific part]. Does it account for [consideration]?"

    Generate ONLY the hint text in plain English (no LaTeX, no meta-commentary):"""