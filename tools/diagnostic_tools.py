# diagnostic_tools.py

import logging

from fairlib.core.interfaces.tools import AbstractTool
from fairlib.core.interfaces.llm import AbstractChatModel
from fairlib.core.message import Message
from fairlib.core.interfaces.memory import AbstractRetriever

from tools.schemas import DiagnosticInput

logger = logging.getLogger(__name__)

class StudentWorkAnalyzerTool(AbstractTool):
    """
    Analyzes student work using LLM reasoning + course materials (RAG).
    """

    name = "student_work_analyzer"
    description = (
        "Analyzes student work to identify specific misconceptions. "
        "Uses course materials as reference. Works for any subject domain. "
        'Input: JSON string with keys "problem", "student_work", "topic".'
    )

    def __init__(self, llm: AbstractChatModel, retriever: AbstractRetriever):
        self.llm = llm
        self.retriever = retriever

    def use(self, tool_input: str) -> str:
        """
        Analyze student work using LLM + course materials.

        Returns structured analysis that agents can parse.
        """
        try:
            try:
                inp = DiagnosticInput.model_validate_json(tool_input)
            except Exception:
                return (
                    'ERROR: Invalid JSON input. Expected: '
                    '{"problem": "...", "student_work": "...", "topic": "..."}'
                )

            if not inp.problem:
                return "ERROR: Missing required field: problem"
            if not inp.student_work:
                return "ERROR: Missing required field: student_work"
            if not inp.topic:
                return "ERROR: Missing required field: topic"

            # Query course materials for relevant context
            kb_query = f"Common errors and misconceptions in {inp.topic}: {inp.problem}"
            try:
                relevant_docs = self.retriever.retrieve(kb_query, top_k=3)
            except Exception:
                logger.warning("Failed to retrieve docs for diagnostic analysis", exc_info=True)
                relevant_docs = []

            # Extract content from retrieved documents
            course_context = "\n\n".join([
                f"[Course Material {i+1}]: {doc}..."
                for i, doc in enumerate(relevant_docs)
            ]) if relevant_docs else "No specific course materials found."

            analysis_prompt = f"""You are an expert at diagnosing student misconceptions. Analyze the student's work to identify the SPECIFIC conceptual error.

PROBLEM: {inp.problem}

STUDENT'S WORK: {inp.student_work}

RELEVANT COURSE MATERIALS:
{course_context}

Analyze the student's work carefully:
1. What did the student do CORRECTLY? (Be specific and encouraging)
2. What is the SPECIFIC error they made? (Not just "wrong answer")
3. What is the ROOT CONCEPT they misunderstand?
4. What severity is this error? (Critical/Major/Minor)

Respond in this EXACT format:
CORRECT_ASPECTS: [What they did right - be specific]
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
            logger.error(f"Diagnostic analysis failed: {e}", exc_info=True)
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
