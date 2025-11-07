"""
LLM-Powered Safety Tools
"""

from fairlib.core.interfaces.tools import AbstractTool
from fairlib.core.interfaces.llm import AbstractChatModel
from fairlib.core.message import Message

class AnswerRevelationAnalyzerTool(AbstractTool):
    """
    Uses LLM reasoning to determine if a response reveals an answer.
    Domain independent - works for any subject.
    
    Much more robust than regex patterns because:
    - Understands semantics and context
    - Can detect indirect revelation
    - Adapts to any domain
    - Handles novel cases
    """
    
    name = "answer_revelation_analyzer"
    description = (
        "Analyzes if a proposed tutor response reveals the answer to a problem. "
        "Uses LLM reasoning, not pattern matching. Works for any domain. "
        "Input format: 'PROBLEM: [text] ||| CORRECT_ANSWER: [text] ||| "
        "PROPOSED_RESPONSE: [text]'"
    )
    
    def __init__(self, llm: AbstractChatModel):
        """
        Initialize with an LLM for reasoning.
        
        Args:
            llm: The language model to use for analysis
        """
        self.llm = llm
    
    def use(self, tool_input: str) -> str:
        """
        Analyze if response reveals answer using LLM reasoning.
        
        Returns structured verdict that agents can parse.
        """
        try:
            # Parse input
            parts = tool_input.split("|||")
            if len(parts) < 3:
                return "ERROR: Invalid input format. Expected 'PROBLEM: ... ||| CORRECT_ANSWER: ... ||| PROPOSED_RESPONSE: ...'"
            
            problem = parts[0].replace("PROBLEM:", "").strip()
            correct_answer = parts[1].replace("CORRECT_ANSWER:", "").strip()
            proposed_response = parts[2].replace("PROPOSED_RESPONSE:", "").strip()
            
            # Create reasoning prompt for LLM
            analysis_prompt = f"""You are a safety validator for a tutoring system. Your job is to determine if a proposed response reveals the answer to a problem.

PROBLEM: {problem}

CORRECT ANSWER (for your reference only): {correct_answer}

PROPOSED RESPONSE TO VALIDATE: {proposed_response}

Analyze the proposed response carefully. Ask yourself:
1. Does it state the final answer directly or indirectly?
2. Does it complete calculations that give away the answer?
3. Does it provide the last step that leads immediately to the answer?
4. Would a student who reads this response know the answer without thinking?
5. Does it show worked-out steps that lead directly to the solution?

SAFE responses:
- Ask guiding questions (e.g., "What happens to the exponent?")
- Explain general concepts (e.g., "The power rule has two steps")
- Hint at approach (e.g., "Think about rate of change")
- Identify errors without correcting (e.g., "Check your exponent")
- Provide analogous examples

UNSAFE responses:
- State the answer (e.g., "The answer is 6x")
- Complete calculations (e.g., "3 x 2 = 6")
- Give the final step (e.g., "So the derivative is 6x")
- Show full solution path

You MUST respond in this EXACT format:
VERDICT: [SAFE or UNSAFE]
REASONING: [Your explanation in 1-2 sentences]
CONFIDENCE: [High, Medium, or Low]"""

            # Get LLM analysis
            messages = [Message(role="user", content=analysis_prompt)]
            response = self.llm.invoke(messages)
            result = response.content.strip()
            
            # Parse and validate LLM response
            verdict = self._extract_verdict(result)
            
            # Add structured prefix for agent parsing
            if verdict == "UNSAFE":
                return f"UNSAFE - Answer revelation detected.\n\n{result}"
            else:
                return f"SAFE - Response does not reveal answer.\n\n{result}"
                
        except Exception as e:
            return f"ERROR: Analysis failed. {str(e)}"
    
    def _extract_verdict(self, llm_response: str) -> str:
        """
        Extract verdict from LLM response with robust parsing.
        Handles stochastic LLM output.
        """
        # Try to find VERDICT line
        for line in llm_response.split("\n"):
            if "VERDICT:" in line.upper():
                if "UNSAFE" in line.upper():
                    return "UNSAFE"
                elif "SAFE" in line.upper():
                    return "SAFE"
        
        # Fallback: search entire response
        response_upper = llm_response.upper()
        if "UNSAFE" in response_upper:
            return "UNSAFE"
        
        # Default to SAFE if unclear (conservative for guiding questions)
        return "SAFE"


class SemanticAnswerMatcherTool(AbstractTool):
    """
    Uses LLM to check semantic similarity between response and answer.
    More sophisticated than string matching.
    """
    
    name = "semantic_answer_matcher"
    description = (
        "Uses LLM to determine if a response is semantically similar to the correct answer. "
        "Catches indirect or paraphrased answer revelation. "
        "Input format: 'CORRECT_ANSWER: [text] ||| PROPOSED_RESPONSE: [text]'"
    )
    
    def __init__(self, llm: AbstractChatModel):
        self.llm = llm
    
    def use(self, tool_input: str) -> str:
        """Check semantic similarity using LLM"""
        try:
            parts = tool_input.split("|||")
            if len(parts) < 2:
                return "ERROR: Invalid input format"
            
            correct_answer = parts[0].replace("CORRECT_ANSWER:", "").strip()
            proposed_response = parts[1].replace("PROPOSED_RESPONSE:", "").strip()
            
            prompt = f"""Compare these two texts for semantic similarity:

CORRECT ANSWER: {correct_answer}

PROPOSED RESPONSE: {proposed_response}

Does the proposed response contain or reveal the correct answer (directly or indirectly)?
Consider paraphrasing, equivalent expressions, and implicit revelation.

Respond in this format:
SIMILARITY: [High, Medium, or Low]
EXPLANATION: [Brief explanation]"""

            messages = [Message(role="user", content=prompt)]
            response = self.llm.invoke(messages)
            result = response.content.strip()
            
            # Parse similarity
            if "HIGH" in result.upper():
                return f"UNSAFE - High semantic similarity to answer.\n\n{result}"
            else:
                return f"SAFE - Low semantic similarity.\n\n{result}"
                
        except Exception as e:
            return f"ERROR: Analysis failed. {str(e)}"