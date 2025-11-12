# diagnostic_tools.py

from fairlib.core.interfaces.tools import AbstractTool
from fairlib.core.interfaces.llm import AbstractChatModel
from fairlib.core.message import Message
from fairlib.core.interfaces.memory import AbstractRetriever

class StudentWorkAnalyzerTool(AbstractTool):
    """
    Analyzes student work using LLM reasoning + course materials (RAG).
    """
    
    name = "student_work_analyzer"
    description = (
        "Analyzes student work to identify specific misconceptions."
        "Uses course materials as reference. Works for any subject domain."
        "Input format: 'PROBLEM: [text] ||| STUDENT_WORK: [text] ||| TOPIC: [text]'"
    )
    
    def __init__(self, llm: AbstractChatModel, retriever: AbstractRetriever):
        """
        Initialize with LLM and retriever for RAG.
        
        Args:
            llm: Language model for reasoning
            retriever: Retriever for querying course materials
        """
        self.llm = llm
        self.retriever = retriever
    
    def use(self, tool_input: str) -> str:
        """
        Analyze student work using LLM + course materials.
        
        Returns structured analysis that agents can parse.
        """
        try:
            # Parse input
            parts = tool_input.split("|||")
            if len(parts) < 3:
                return "ERROR: Invalid input format. Expected 'PROBLEM: ... ||| STUDENT_WORK: ... ||| TOPIC: ...'"
            
            problem = parts[0].replace("PROBLEM:", "").strip()
            student_work = parts[1].replace("STUDENT_WORK:", "").strip()
            topic = parts[2].replace("TOPIC:", "").strip()
            
            # Query course materials for relevant context
            kb_query = f"Common errors and misconceptions in {topic}: {problem}"
            relevant_docs = self.retriever.retrieve(kb_query, k=3)
            
            # Extract content from retrieved documents
            course_context = "\n\n".join([
                f"[Course Material {i+1}]: {doc.page_content[:500]}..." 
                for i, doc in enumerate(relevant_docs)
            ]) if relevant_docs else "No specific course materials found."
            
            # Create analysis prompt
            analysis_prompt = f"""You are an expert at diagnosing student misconceptions. Analyze the student's work to identify the SPECIFIC conceptual error.

PROBLEM: {problem}

STUDENT'S WORK: {student_work}

RELEVANT COURSE MATERIALS:
{course_context}

Analyze the student's work carefully:
1. What did the student do CORRECTLY? (Be specific and encouraging)
2. What is the SPECIFIC error they made? (Not just "wrong answer")
3. What is the ROOT CONCEPT they misunderstand?
4. What severity is this error? (Critical/Major/Minor)

Respond in this EXACT format:
CORRECT_ASPECTS: [What they did right - be specific, if nothing was done right, state that here]
ERROR_IDENTIFIED: [The specific mistake - be precise]
ROOT_MISCONCEPTION: [The underlying concept misunderstood]
SEVERITY: [Critical, Major, or Minor]
SUGGESTED_FOCUS: [What concept/skill to review]
EVIDENCE: [Quote from student work showing the error]"""

            # Get LLM analysis
            messages = [Message(role="user", content=analysis_prompt)]
            response = self.llm.invoke(messages)
            result = response.content.strip()
            
            # Parse severity for agent decision-making
            severity = self._extract_severity(result)
            
            return f"ANALYSIS COMPLETE - Severity: {severity}\n\n{result}"
            
        except Exception as e:
            return f"ERROR: Analysis failed. {str(e)}"
    
    def _extract_severity(self, llm_response: str) -> str:
        """Extract severity from LLM response with robust parsing"""
        response_upper = llm_response.upper()
        
        if "SEVERITY:" in response_upper:
            for line in llm_response.split("\n"):
                if "SEVERITY:" in line.upper():
                    if "CRITICAL" in line.upper():
                        return "Critical"
                    elif "MAJOR" in line.upper():
                        return "Major"
                    elif "MINOR" in line.upper():
                        return "Minor"
        
        # Fallback
        if "CRITICAL" in response_upper:
            return "Critical"
        elif "MINOR" in response_upper:
            return "Minor"
        else:
            return "Major"

class ConceptExplanationGeneratorTool(AbstractTool):
    """
    Retrieves and synthesizes concept explanations from course materials.
    Helps provide context-specific explanations.
    """
    
    name = "concept_explanation_generator"
    description = (
        "Retrieves concept explanations from course materials and synthesizes them. "
        "Input format: concept or topic name to explain"
    )
    
    def __init__(self, llm: AbstractChatModel, retriever: AbstractRetriever):
        self.llm = llm
        self.retriever = retriever
    
    def use(self, tool_input: str) -> str:
        """Generate concept explanation using course materials"""
        try:
            concept = tool_input.strip()
            
            # Query course materials
            kb_query = f"Explanation of {concept}"
            relevant_docs = self.retriever.retrieve(kb_query, k=3)
            
            if not relevant_docs:
                return f"No course materials found for concept: {concept}"
            
            # Synthesize from course materials
            materials = "\n\n".join([
                f"[Source {i+1}]: {doc.page_content}" 
                for i, doc in enumerate(relevant_docs)
            ])
            
            synthesis_prompt = f"""Based on the course materials provided, create a clear, concise explanation of: {concept}

COURSE MATERIALS:
{materials}

Create an explanation that:
1. Uses language from the course materials
2. Is clear and student-friendly
3. Highlights key points
4. Is 2-3 paragraphs maximum

Your explanation:"""

            messages = [Message(role="user", content=synthesis_prompt)]
            response = self.llm.invoke(messages)
            
            return f"CONCEPT: {concept}\n\n{response.content.strip()}"
            
        except Exception as e:
            return f"ERROR: Could not generate explanation. {str(e)}"