# diagnostic_tools.py

from fairlib.core.interfaces.tools import AbstractTool
from fairlib.core.interfaces.llm import AbstractChatModel
from fairlib.core.message import Message
from fairlib.core.interfaces.memory import AbstractRetriever
import re

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

    # TODO:: are there models that are tuned for this type of task?
    def _extract_units_from_work(self, student_work: str) -> list:
        """
        Extract and normalize units from student work.
        Handles various formats: kg*m/s, kg·m/s, kg m/s, etc.
        """
        units_found = []
        
        # Common unit patterns for physics/math
        unit_patterns = [
            # Momentum patterns
            r'(\d+(?:\.\d+)?)\s*kg\s*[·\*]?\s*m\s*/\s*s',  # kg*m/s variations
            r'(\d+(?:\.\d+)?)\s*kg\s*m\s*/\s*s',           # kg m/s
            r'(\d+(?:\.\d+)?)\s*kg·m/s',                   # kg·m/s
            r'(\d+(?:\.\d+)?)\s*kg\*m/s',                  # kg*m/s
            r'(\d+(?:\.\d+)?)\s*N\s*[·\*]?\s*s',           # N*s (also momentum)
            
            # Force patterns
            r'(\d+(?:\.\d+)?)\s*N(?![a-zA-Z])',            # Newtons
            r'(\d+(?:\.\d+)?)\s*kN(?![a-zA-Z])',           # kiloNewtons
            
            # Energy patterns
            r'(\d+(?:\.\d+)?)\s*J(?![a-zA-Z])',            # Joules
            r'(\d+(?:\.\d+)?)\s*kJ(?![a-zA-Z])',           # kiloJoules
            
            # Basic units
            r'(\d+(?:\.\d+)?)\s*kg(?![a-zA-Z])',           # kilograms
            r'(\d+(?:\.\d+)?)\s*m/s(?![a-zA-Z])',          # meters per second
            r'(\d+(?:\.\d+)?)\s*m(?![a-zA-Z])',            # meters
            r'(\d+(?:\.\d+)?)\s*s(?![a-zA-Z])',            # seconds
        ]
        
        for pattern in unit_patterns:
            matches = re.findall(pattern, student_work, re.IGNORECASE)
            if matches:
                # Store the full match with normalized format
                full_matches = re.finditer(pattern, student_work, re.IGNORECASE)
                for match in full_matches:
                    units_found.append(match.group(0))
        
        return units_found
    
    # TODO:: are there models that are tuned for this type of task?
    def _check_for_missing_units(self, student_work: str) -> bool:
        """
        Check if student provided numerical answer without units.
        """
        # Look for plain numbers that might be answers
        number_pattern = r'(?:answer|result|solution|=)\s*(\d+(?:\.\d+)?)(?!\s*[a-zA-Z·\*\/])'
        
        if re.search(number_pattern, student_work, re.IGNORECASE):
            # Found a number without units after answer indicator
            return True
        
        # Also check for standalone numbers that look like final answers
        if re.search(r'^\s*\d+(?:\.\d+)?\s*$', student_work.strip()):
            return True
        
        return False
    
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
            
            problem = ""
            student_work = ""
            topic = ""

            for part in parts:
                part = part.strip()
                if part.upper().startswith("PROBLEM:"):
                    problem = part.split(":", 1)[1].strip()
                elif part.upper().startswith("STUDENT_WORK:"):
                    student_work = part.split(":", 1)[1].strip()
                elif part.upper().startswith("TOPIC:"):
                    topic = part.split(":", 1)[1].strip()

            units_analysis = ""

            units_found = self._extract_units_from_work(student_work)
            missing_units = self._check_for_missing_units(student_work)
            
            if units_found:
                units_analysis = f"Units detected: {', '.join(units_found)}"
            elif missing_units:
                units_analysis = "WARNING: Numerical answer appears to be missing units!"
            else:
                units_analysis = "No clear numerical answer with units found."

            # Query course materials for relevant context
            kb_query = f"Common errors and misconceptions in {topic}: {problem}"
            relevant_docs = self.retriever.retrieve(kb_query, k=3)
            
            # Extract content from retrieved documents
            course_context = "\n\n".join([
                f"[Course Material {i+1}]: {doc}..." 
                for i, doc in enumerate(relevant_docs)
            ]) if relevant_docs else "No specific course materials found."
            
            # Create analysis prompt with unit awareness
            analysis_prompt = f"""You are an expert at diagnosing student misconceptions. Analyze the student's work to identify the SPECIFIC conceptual error.

PROBLEM: {problem}

STUDENT'S WORK: {student_work}

UNIT ANALYSIS: {units_analysis}

RELEVANT COURSE MATERIALS:
{course_context}

CRITICAL INSTRUCTIONS FOR UNIT CHECKING:
- If the problem requires units (physics, chemistry, engineering), check if student included them
- Recognize various unit formats: 50kg*m/s, 50 kg·m/s, 50kg m/s are all valid
- If student has correct value but missing units, this is a MINOR error
- If student has wrong units for the quantity, this is a MAJOR error

Analyze the student's work carefully:
1. What did the student do CORRECTLY? (Be specific and encouraging)
2. Are the UNITS correct and present if needed?
3. What is the SPECIFIC error they made? (Not just "wrong answer")
4. What is the ROOT CONCEPT they misunderstand?
5. What severity is this error? (Critical/Major/Minor)

Respond in this EXACT format:
CORRECT_ASPECTS: [What they did right - be specific]
UNITS_CHECK: [Present and correct / Missing / Wrong type / Not applicable]
ERROR_IDENTIFIED: [The specific mistake - be precise]
ROOT_MISCONCEPTION: [The underlying concept misunderstood]
SEVERITY: [Critical, Major, or Minor]
SUGGESTED_FOCUS: [What concept/skill to review]
EVIDENCE: [Quote from student work showing the error or success]
"""

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