"""
LLM+RAG Powered Pedagogical Tools - Domain Independent

These tools generate hints and questions using:
- LLM reasoning for Socratic method
- Course materials for context
- Pedagogical best practices

Works for any domain because it adapts to teaching materials provided.
"""

from fairlib.core.interfaces.tools import AbstractTool
from fairlib.core.interfaces.llm import AbstractChatModel
from fairlib.core.message import Message
from fairlib.core.interfaces.memory import AbstractRetriever
import re


class SocraticHintGeneratorTool(AbstractTool):
    """
    Generates Socratic hints using LLM + course materials.
    """
    
    name = "socratic_hint_generator"
    description = (
        "Generates pedagogically appropriate hints using Socratic method. "
        "Queries course materials for context. Works for any subject domain. "
        "Input format: 'PROBLEM: [text] ||| MISCONCEPTION: [text] ||| "
        "HINT_LEVEL: [1-4] ||| TOPIC: [text]'"
    )

    HINT_LEVELS = {
        1: {
            "name": "STRATEGIC",
            "description": "Questions about problem type or overall approach",
            "guidance": "Ask 'What type of problem is this?' or 'What general strategy applies?'"
        },
        2: {
            "name": "CONCEPTUAL", 
            "description": "Questions about principles and concepts",
            "guidance": "Guide toward understanding the principle without revealing steps"
        },
        3: {
            "name": "PROCEDURAL",
            "description": "Questions about the process or next step",
            "guidance": "Hint at the next step without doing it for them"
        },
        4: {
            "name": "SPECIFIC",
            "description": "Questions about specific elements to check",
            "guidance": "Point to a specific part that needs attention"
        }
    }
    
    def __init__(self, llm: AbstractChatModel, retriever: AbstractRetriever, max_level: int = 4):
        """
        Initialize with LLM and retriever for RAG.
        
        Args:
            llm: Language model for generating hints
            retriever: Retriever for querying course/teaching materials
            max_level: Maximum hint level (default 4, NEVER allow 5)
        """
        self.llm = llm
        self.retriever = retriever
        self.max_level = min(max_level, 4)  # Hard cap at 4
    
    def use(self, tool_input: str) -> str:
        """Generate hint using LLM + course materials"""
        try:
            parts = tool_input.split("|||")
            if len(parts) < 4:
                return "ERROR: Invalid input format. Expected 'PROBLEM: ... ||| MISCONCEPTION: ... ||| HINT_LEVEL: ... ||| TOPIC: ...'"
            
            problem = parts[0].replace("PROBLEM:", "").strip()
            misconception = parts[1].replace("MISCONCEPTION:", "").strip()
            hint_level_str = parts[2].replace("HINT_LEVEL:", "").strip()
            topic = parts[3].replace("TOPIC:", "").strip()
            
            # Parse and validate hint level
            try:
                hint_level = int(hint_level_str)
                hint_level = max(1, min(self.max_level, hint_level))  # Clamp to valid range
            except ValueError:
                hint_level = 2  # Default to conceptual
            
            # Query course materials for teaching strategies
            kb_query = f"Teaching strategies and hints for {topic}: {misconception}"
            relevant_docs = self.retriever.retrieve(kb_query, k=3)
            
            teaching_context = "\n\n".join([
                f"[Teaching Resource {i+1}]: {doc.page_content[:400]}..."
                for i, doc in enumerate(relevant_docs)
            ]) if relevant_docs else "No specific teaching resources found - use general llm advice."
            
            level_info = self.HINT_LEVELS[hint_level]
            
            # Create hint generation prompt
            hint_prompt = f"""You are a Socratic tutor generating a hint to guide a student. Your hint should help them learn WITHOUT revealing the answer.

PROBLEM: {problem}

STUDENT'S MISCONCEPTION: {misconception}

HINT LEVEL: {hint_level} - {level_info['name']}
LEVEL DESCRIPTION: {level_info['description']}
GUIDANCE: {level_info['guidance']}

TEACHING MATERIALS FROM COURSE:
{teaching_context}

Generate a hint that:
1. Addresses the specific misconception identified
2. Uses Socratic questioning when possible (ask, don't tell)
3. Stays at Level {hint_level} - not more specific, not less
4. Guides toward understanding, not just the correct answer
5. References course materials if helpful
6. Is encouraging and supportive

CRITICAL RULES:
- NEVER state the final answer
- NEVER complete calculations for the student
- NEVER give the last step that leads to the solution
- Use questions that prompt thinking

Your hint (1-3 sentences):"""

            # Get LLM-generated hint
            messages = [Message(role="user", content=hint_prompt)]
            response = self.llm.invoke(messages)
            hint = response.content.strip()
            
            return f"HINT_LEVEL_{hint_level}: {hint}"
            
        except Exception as e:
            return f"ERROR: Hint generation failed. {str(e)}"


class HintLevelSelectorTool(AbstractTool):
    """
    Determines appropriate hint level based on misconception severity.
    Uses LLM reasoning to adapt to different error types.
    """
    
    name = "hint_level_selector"
    description = (
        "Selects appropriate hint level (1-4) based on misconception type and severity. "
        "Uses reasoning to determine optimal pedagogical approach. "
        "Input format: 'MISCONCEPTION: [text] ||| SEVERITY: [Critical/Major/Minor]'"
    )
    
    def __init__(self, llm: AbstractChatModel, max_level: int = 4):
        self.llm = llm
        self.max_level = min(max_level, 4)
    
    def use(self, tool_input: str) -> str:
        """Determine appropriate hint level using LLM reasoning"""
        try:
            parts = tool_input.split("|||")
            if len(parts) < 2:
                return "ERROR: Invalid input format. Expected 'MISCONCEPTION: ... ||| SEVERITY: ...'"
            
            misconception = parts[0].replace("MISCONCEPTION:", "").strip()
            severity = parts[1].replace("SEVERITY:", "").strip()
            
            # Create reasoning prompt
            prompt = f"""You are a pedagogical expert determining the appropriate hint level for a student.

STUDENT'S MISCONCEPTION: {misconception}
ERROR SEVERITY: {severity}

Hint Levels:
1. STRATEGIC - Questions about problem type/approach (most broad)
2. CONCEPTUAL - Questions about principles/concepts
3. PROCEDURAL - Questions about process/next step
4. SPECIFIC - Questions about specific elements (most narrow)

Based on the misconception and severity, what hint level is most appropriate?

Consider:
- Critical errors often need conceptual review (Level 2)
- Major rule/principle errors need conceptual hints (Level 2)
- Major procedural errors need procedural hints (Level 3)
- Minor errors can use specific hints (Level 4)

Respond in this format:
RECOMMENDED_LEVEL: [1, 2, 3, or 4]
REASONING: [Brief explanation of why this level is appropriate]"""

            messages = [Message(role="user", content=prompt)]
            response = self.llm.invoke(messages)
            result = response.content.strip()
            
            # Extract level
            level = self._extract_level(result)
            
            return f"RECOMMENDED_LEVEL: {level}\n\n{result}"
            
        except Exception as e:
            # Fallback to safe default
            return f"RECOMMENDED_LEVEL: 2\n\nERROR: Could not determine level. Defaulting to conceptual (Level 2). {str(e)}"
    
    def _extract_level(self, llm_response: str) -> int:
        """Extract recommended level from LLM response"""
        # Look for explicit level recommendation
        for line in llm_response.split("\n"):
            if "RECOMMENDED_LEVEL:" in line.upper():
                # Extract number
                numbers = re.findall(r'\d', line)
                if numbers:
                    level = int(numbers[0])
                    return max(1, min(self.max_level, level))
        
        # Fallback: search for level numbers in response
        for i in range(1, 5):
            if f"Level {i}" in llm_response or f"level {i}" in llm_response:
                return i
        
        # Default to conceptual if unclear
        return 2