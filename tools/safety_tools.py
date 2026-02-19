# safety_tools.py

import logging
import re

from fairlib.core.interfaces.tools import AbstractTool
from fairlib.core.interfaces.llm import AbstractChatModel
from fairlib.core.message import Message

logger = logging.getLogger(__name__)

class AnswerRevelationAnalyzerTool(AbstractTool):
    """
    Uses LLM reasoning to determine if a response reveals an answer.

    Will check coversation history, if the student has previously given the correct answer, a response with an
    answer will now be marked as SAFE.s
    """
    
    name = "answer_revelation_analyzer"
    description = (
        "Analyzes if a proposed tutor response reveals the answer to a problem. "
        "Uses LLM reasoning, not pattern matching. Works for any domain. "
        "Input format: 'PROBLEM: [text] ||| CORRECT_ANSWER: [text] ||| "
        "STUDENT_HISTORY: [list of previous submissions] ||| PROPOSED_RESPONSE: [text]'"
    )
    
    def __init__(self, llm: AbstractChatModel):
        """
        Initialize with an LLM for reasoning.
        
        Args:
            llm: The language model to use for analysis
        """
        self.llm = llm

    # TODO:: need this to be more intellegent, wont handle edge cases well
    def _extract_student_answers_from_history(self, history_str: str) -> list:
        """
        Extract answers the student has already provided.
        """
        student_answers = []
        
        # Parse history
        if not history_str or history_str == "[]":
            return []
        
        # Clean up the history string
        history_clean = history_str.strip("[]").replace("'", "").replace('"', '')
        
        # Split into individual submissions
        submissions = [s.strip() for s in history_clean.split(',') if s.strip()]
        
        for submission in submissions:
            # Domain-agnostic: detect any number with optional units (word after number)
            if re.search(r'\d+(?:\.\d+)?\s*[a-zA-Z/·\*]+', submission, re.IGNORECASE):
                student_answers.append(submission)
                continue

            # Check for answer-indicator keywords with numbers
            if re.search(r'(?:answer|got|calculated|result|equals|is)\s*[=:]?\s*\S+', submission, re.IGNORECASE):
                student_answers.append(submission)
                continue

            # Standalone numeric answer
            if re.search(r'^\s*-?\d+(?:\.\d+)?\s*$', submission.strip()):
                student_answers.append(submission)
        
        return student_answers
    
    # TODO:: need this to be more intellegent, wont handle edge cases well
    def _normalize_answer(self, answer: str) -> str:
        """
        Normalize an answer for comparison (handle unit format variations).
        """
        # Normalize units: kg*m/s, kg·m/s, kg m/s should all match
        normalized = answer.lower().strip()
        normalized = re.sub(r'\s+', '', normalized)  # Remove all spaces
        normalized = normalized.replace('*', '').replace('·', '').replace('×', '')
        return normalized
    
    def use(self, tool_input: str) -> str:
        """
        Analyze if response reveals answer using LLM reasoning.
        """
        try:
            # Parse input
            parts = tool_input.split("|||")
            problem = ""
            correct_answer = ""
            student_history = ""
            proposed_response = ""

            for part in parts:
                part_clean = part.strip()
                if part_clean.upper().startswith("PROBLEM:"):
                    problem = part_clean.split(":", 1)[1].strip()
                elif part_clean.upper().startswith("CORRECT_ANSWER:"):
                    correct_answer = part_clean.split(":", 1)[1].strip()
                elif part_clean.upper().startswith("STUDENT_HISTORY:"):
                    student_history = part_clean.split(":", 1)[1].strip()
                elif part_clean.upper().startswith("PROPOSED_RESPONSE:"):
                    proposed_response = part_clean.split(":", 1)[1].strip()

            student_answers = self._extract_student_answers_from_history(student_history)
            student_already_answered = False

            if student_answers and correct_answer:
                correct_normalized = self._normalize_answer(correct_answer)
                
                for student_ans in student_answers:
                    student_normalized = self._normalize_answer(student_ans)
                    if correct_normalized in student_normalized or student_normalized in correct_normalized:
                        student_already_answered = True
                        break
            
            # Create reasoning prompt for LLM with history context
            analysis_prompt = f"""You are a safety validator for a tutoring system. Your job is to determine if a proposed response reveals the answer to a problem.

IMPORTANT CONTEXT - STUDENT HISTORY:
{f"The student has already provided these answers: {student_answers}" if student_answers else "The student has not provided any answers yet."}
Student already stated the correct answer: {"YES" if student_already_answered else "NO"}

PROBLEM: {problem}

CORRECT ANSWER (for your reference only): {correct_answer}

PROPOSED RESPONSE TO VALIDATE: {proposed_response}

CRITICAL RULE:
If the student has ALREADY stated the correct answer in their history, then it is SAFE to:
- Confirm their answer is correct
- Reference the specific value they provided
- Celebrate their success
- Use phrases like "Yes, your answer is correct!"

Otherwise, analyze carefully:
1. Does it state the final answer directly or indirectly?
2. Does it complete calculations that give away the answer?
3. Does it provide the last step that leads immediately to the answer?
4. Would a student who reads this response know the answer without thinking?

SAFE responses when student has NOT answered:
- Ask guiding questions (e.g., "What happens to the exponent?")
- Explain general concepts (e.g., "The power rule has two steps")
- Hint at approach (e.g., "Think about units")
- Identify errors without correcting (e.g., "Check your calculation")

UNSAFE responses when student has NOT answered:
- State the answer (e.g., "The answer is George Washington")
- Complete calculations (e.g., "5 * 10 = 50")
- Give the final step (e.g., "So you get 1998")

You MUST respond in this EXACT format:
VERDICT: [SAFE or UNSAFE]
REASONING: [Your explanation in 1-2 sentences]
STUDENT_ALREADY_ANSWERED: [YES or NO]
CONFIDENCE: [High, Medium, or Low]"""

            # Get LLM analysis
            messages = [Message(role="user", content=analysis_prompt)]
            response = self.llm.invoke(messages)
            result = response.content.strip()
            
            # Parse and validate LLM response
            verdict = self._extract_verdict(result, student_already_answered)
            
            # Add structured prefix for agent parsing
            if verdict == "UNSAFE":
                return f"UNSAFE - Answer revelation detected.\n\n{result}"
            else:
                return f"SAFE - Response does not reveal answer.\n\n{result}"
                
        except Exception as e:
            logger.error(f"Safety analysis failed: {e}", exc_info=True)
            return f"ERROR: Analysis failed. {str(e)}"
    
    # TODO:: may need this to be improved as well, still weak parsing rules
    def _extract_verdict(self, llm_response: str, student_already_answered: bool) -> str:
        """
        Extract verdict from LLM response, considering student history.
        """
        for line in llm_response.split("\n"):
            if "VERDICT:" in line.upper():
                if "UNSAFE" in line.upper():
                    # Double-check: if student already answered, override to SAFE
                    if student_already_answered and "correct" in llm_response.lower():
                        return "SAFE"
                    return "UNSAFE"
                elif "SAFE" in line.upper():
                    return "SAFE"
        
        # If student already answered and response seems to confirm, it's SAFE
        if student_already_answered:
            confirm_phrases = ["correct", "right", "excellent", "perfect", "yes"]
            if any(phrase in llm_response.lower() for phrase in confirm_phrases):
                return "SAFE"
        
        # Fallback: search entire response
        response_upper = llm_response.upper()
        if "UNSAFE" in response_upper and not student_already_answered:
            return "UNSAFE"
        
        # Default to UNSAFE if unclear (conservative)
        return "UNSAFE"