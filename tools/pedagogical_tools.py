# pedagogical_tools.py

from fairlib.core.interfaces.tools import AbstractTool
from fairlib.core.interfaces.llm import AbstractChatModel
from fairlib.core.interfaces.memory import AbstractRetriever


class HintLevelSelectorTool(AbstractTool):
    """
    Selects appropriate hint level based on misconception severity.
    """
    
    def __init__(self, llm: AbstractChatModel, max_level: int = 4):
        self.name = "hint_level_selector"
        self.description = (
            "Determines appropriate hint level (1-4) based on misconception severity. "
            "Input format: 'MISCONCEPTION: [text] ||| SEVERITY: [Critical/Major/Minor]'"
        )
        self.llm = llm
        self.max_level = max_level
    
    def use(self, tool_input: str) -> str:
        """Select hint level based on severity"""
        
        # Parse input
        parts = tool_input.split("|||")
        misconception = ""
        severity = "Minor"
        
        for part in parts:
            part = part.strip()
            if part.upper().startswith("MISCONCEPTION:"):
                misconception = part.split(":", 1)[1].strip()
            elif part.upper().startswith("SEVERITY:"):
                severity = part.split(":", 1)[1].strip()
        
        # Map severity to hint level
        severity_upper = severity.upper()
        if severity_upper == "CRITICAL":
            level = 2  # Conceptual guidance needed
        elif severity_upper == "MAJOR":
            level = 2  # Conceptual guidance needed
        elif severity_upper == "MINOR":
            level = 3  # Targeted question
        else:
            level = 2  # Default to conceptual
        
        # Ensure within bounds
        level = min(level, self.max_level)
        
        return (
            f"RECOMMENDED_LEVEL: {level}\n"
            f"REASONING: {severity} severity misconception. "
            f"Level {level} provides appropriate guidance without revealing answer."
        )


class SocraticHintGeneratorTool(AbstractTool):
    """
    Generates Socratic hints using LLM + RAG + STUDENT WORK context.
    """
    
    def __init__(self, llm: AbstractChatModel, retriever: AbstractRetriever, max_level: int = 4):
        self.name = "socratic_hint_generator"
        self.description = (
            "Generates Socratic hint using problem, student work, and misconception. "
            "Input format: 'PROBLEM: [text] ||| STUDENT_WORK: [their work] ||| "
            "MISCONCEPTION: [text] ||| HINT_LEVEL: [1-4] ||| TOPIC: [subject]'"
        )
        self.llm = llm
        self.retriever = retriever
        self.max_level = max_level
    
    def use(self, tool_input: str) -> str:
        """Generate hint with full context"""
        
        # Parse input
        parts = tool_input.split("|||")
        problem = ""
        student_work = ""
        misconception = ""
        hint_level = 2
        topic = ""
        
        # TODO:: may need more intelegent extraction here!
        for part in parts:
            part = part.strip()
            if part.upper().startswith("PROBLEM:"):
                problem = part.split(":", 1)[1].strip()
            elif part.upper().startswith("STUDENT_WORK:"):
                student_work = part.split(":", 1)[1].strip()
            elif part.upper().startswith("MISCONCEPTION:"):
                misconception = part.split(":", 1)[1].strip()
            elif part.upper().startswith("HINT_LEVEL:"):
                try:
                    hint_level = int(part.split(":", 1)[1].strip())
                    hint_level = min(hint_level, self.max_level)
                except:
                    hint_level = 2
            elif part.upper().startswith("TOPIC:"):
                topic = part.split(":", 1)[1].strip()
        
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
            except:
                relevant_docs = ""
        
        # Create prompt for LLM that includes student work
        prompt = self._create_hint_generation_prompt(
            problem=problem,
            student_work=student_work,
            misconception=misconception,
            hint_level=hint_level,
            topic=topic,
            course_materials=relevant_docs
        )
        
        # Generate hint using LLM
        from fairlib.core.message import Message
        messages = [Message(role="user", content=prompt)]
        response = self.llm.invoke(messages)
        
        hint_text = response.content.strip()
        
        return f"HINT_LEVEL_{hint_level} Generated:\n{hint_text}"
    
    def _create_hint_generation_prompt(
        self,
        problem: str,
        student_work: str,
        misconception: str,
        hint_level: int,
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

HINT LEVELS:
- Level 1: "Remember the definition of [concept]"
- Level 2: "Think about the relationship between [concepts]"
- Level 3: "What happens when you [specific action]?"
- Level 4: "Look at your [specific part]. Does it account for [consideration]?"

Generate ONLY the hint text (no meta-commentary):"""