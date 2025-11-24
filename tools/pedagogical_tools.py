# pedagogical_tools.py

from fairlib.core.interfaces.tools import AbstractTool
from fairlib.core.interfaces.llm import AbstractChatModel
from fairlib.core.interfaces.memory import AbstractRetriever
from fairlib.core.message import Message

class SocraticHintGeneratorTool(AbstractTool):
    """
    Generates Socratic hints using LLM + RAG + STUDENT WORK context.
    """
    
    def __init__(self, llm: AbstractChatModel, retriever: AbstractRetriever):
        self.name = "socratic_hint_generator"
        self.description = (
            "Generates Socratic hints OR concept explanations based on MODE. "
            "For hints: 'MODE: HINT ||| PROBLEM: [text] ||| STUDENT_WORK: [work] ||| "
            "MISCONCEPTION: [text] ||| SEVERITY: [level] ||| TOPIC: [subject]' "
            "For concepts: 'MODE: CONCEPT_EXPLANATION ||| CONCEPT: [what to explain] ||| "
            "QUESTION: [student question] ||| TOPIC: [subject]'"
        )
        self.llm = llm
        self.retriever = retriever
    
    def use(self, tool_input: str) -> str:
        """Generate hint with full context"""
        
        # Parse input
        parts = tool_input.split("|||")
        mode = "HINT"  # Default

        problem = ""
        student_work = ""
        misconception = ""
        severity = "Minor"
        topic = ""
        concept = ""
        question = ""
        
        for part in parts:
            part = part.strip()
            if part.upper().startswith("MODE:"):
                mode_value = part.split(":", 1)[1].strip().upper()
                if "CONCEPT" in mode_value:
                    mode = "CONCEPT_EXPLANATION"
                else:
                    mode = "HINT"
            elif part.upper().startswith("PROBLEM:"):
                problem = part.split(":", 1)[1].strip()
            elif part.upper().startswith("STUDENT_WORK:"):
                student_work = part.split(":", 1)[1].strip()
            elif part.upper().startswith("MISCONCEPTION:"):
                misconception = part.split(":", 1)[1].strip()
            elif part.upper().startswith("SEVERITY:"):
                severity = part.split(":", 1)[1].strip()
            elif part.upper().startswith("TOPIC:"):
                topic = part.split(":", 1)[1].strip()
            elif part.upper().startswith("CONCEPT:"):
                concept = part.split(":", 1)[1].strip()
            elif part.upper().startswith("QUESTION:"):
                question = part.split(":", 1)[1].strip()

        if mode == "CONCEPT_EXPLANATION":
            return self._generate_concept_explanation(concept, question, topic)
        else:
            return self._generate_socratic_hint(
                problem, student_work, misconception, severity, topic
            )
        
    def _generate_concept_explanation(self, concept: str, question: str, topic: str) -> str:
        """
        Generate concept explanations for student questions.
        """
        
        # Query course materials for concept
        relevant_docs = ""
        if self.retriever:
            try:
                docs = self.retriever.retrieve(
                    query=f"{topic} {concept} explanation definition",
                    top_k=3
                )
                if docs:
                    relevant_docs = "\n".join([
                        f"[Material {i+1}]: {str(doc)[:200]}..." 
                        for i, doc in enumerate(docs)
                    ])
            except Exception:
                relevant_docs = ""
        
        prompt = f"""You are a helpful tutor providing a clear concept explanation.

STUDENT QUESTION: {question}
CONCEPT TO EXPLAIN: {concept}
SUBJECT AREA: {topic}

COURSE MATERIALS:
{relevant_docs if relevant_docs else 'No specific materials available.'}

Provide a clear, educational explanation that:
1. Defines the concept clearly
2. Gives relevant examples
3. Connects to what the student might already know
4. Uses simple, accessible language
5. Is 2-3 paragraphs maximum

IMPORTANT: Do NOT solve specific problems or give direct answers to homework.
Focus on conceptual understanding.
"""

        messages = [Message(role="user", content=prompt)]
        response = self.llm.invoke(messages)
        
        explanation = response.content.strip()
        
        return (
            f"CONCEPT EXPLANATION for '{concept}':\n\n"
            f"{explanation}\n\n"
            "This explanation is ready to present to the student. Use final_answer to deliver it."
        )
    
    def _generate_socratic_hint(
        self, 
        problem: str, 
        student_work: str, 
        misconception: str, 
        severity: str, 
        topic: str
    ) -> str:
        """
        Generate Socratic hints for student work.
        """

        if "none" in misconception.lower() or "correct" in misconception.lower():
            return self._generate_success_response(problem, student_work, topic)
        
        # Determine hint level from severity
        severity_upper = severity.upper()
        if severity_upper == "CRITICAL":
            hint_level = 2
        elif severity_upper == "MAJOR":
            hint_level = 2
        elif severity_upper == "MINOR":
            hint_level = 3
        else:
            hint_level = 2
        
        # Query course materials for context
        relevant_docs = ""
        if self.retriever:
            try:
                docs = self.retriever.retrieve(
                    query=f"{topic} {misconception}",
                    top_k=3
                )
                if docs:
                    relevant_docs = "\n".join([str(doc)[:200] for doc in docs[:2]])
            except Exception:
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
        messages = [Message(role="user", content=prompt)]
        response = self.llm.invoke(messages)
        
        hint_text = response.content.strip()
        
        return (
            f"COMPLETE HINT (Level {hint_level} based on {severity} severity):\n"
            f"{hint_text}\n\n"
            f"This hint is ready to present to the student. Use final_answer to deliver it."
        )
    
    def _generate_success_response(self, problem: str, student_work: str, topic: str) -> str:
        """Generate response when student got the answer correct"""
        
        prompt = f"""The student has correctly solved this problem. Generate an encouraging response.

PROBLEM: {problem}
STUDENT'S CORRECT WORK: {student_work}
TOPIC: {topic}

Create a response that:
1. Confirms they are correct
2. Praises specific aspects of their work
3. Optionally asks a follow-up question to deepen understanding
4. Is encouraging and supportive
"""

        messages = [Message(role="user", content=prompt)]
        response = self.llm.invoke(messages)
        
        return (
            f"SUCCESS RESPONSE:\n"
            f"{response.content.strip()}\n\n"
            "This response is ready to present to the student. Use final_answer to deliver it."
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

        latex_warning = """
CRITICAL JSON SAFETY RULES - VIOLATION WILL BREAK THE SYSTEM:
================================================
YOUR OUTPUT WILL BE EMBEDDED IN JSON. FOLLOW THESE RULES OR THE SYSTEM WILL CRASH:

1. ABSOLUTELY NO LATEX NOTATION - NONE AT ALL:
   NEVER write: \(x\) or \(2x + 5 = 15\)
   INSTEAD write: x or 2x + 5 = 15
   
   NEVER write: \\times, \\cdot, \\frac, \\sqrt
   INSTEAD write: *, ·, /, sqrt()

2. NO BACKSLASHES EXCEPT FOR QUOTES:
   NEVER: Any \symbol or \command
   ONLY EXCEPTION: \' for quotes in contractions

3. WRITE ALL MATH IN PLAIN TEXT:
   WRONG: "isolate \(x\) in the equation \(2x + 5 = 15\)"
   RIGHT: "isolate x in the equation 2x + 5 = 15"
   
   WRONG: "calculate \(p = m \\times v\)"
   RIGHT: "calculate p = m * v" or "calculate p = m * v"

4. EXAMPLES OF SAFE MATHEMATICAL EXPRESSIONS:
   - "x = 5"
   - "2x + 5 = 15"
   - "p = m * v"
   - "Force equals mass times acceleration (F = ma)"
   - "The derivative of x^2 is 2x"
   - "sqrt(16) = 4"

IF YOU USE ANY LATEX NOTATION, THE SYSTEM WILL CRASH AND THE STUDENT WILL SEE AN ERROR.
================================================
"""
        
        return f"""{latex_warning}
        
    You are a Socratic tutor creating a hint for a student.

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

    HINT LEVEL GUIDANCE:
    - Level 1: "Remember the definition of [concept]"
    - Level 2: "Think about the relationship between [concepts]"
    - Level 3: "What happens when you [specific action]?"
    - Level 4: "Look at your [specific part]. Does it account for [consideration]?"

    Generate ONLY the hint text in plain English (no LaTeX, no meta-commentary)."""