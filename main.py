"""
Domain-Agnostic Tutor Driver with RAG

This driver sets up a tutoring system that works for ANY subject by:
1. Loading course materials into a vector store (RAG)
2. Creating LLM-powered tools that use course materials
3. Building agents that reason rather than pattern-match

Usage:
    python main.py --course_materials /path/to/materials --problems /path/to/problem_set

The system will:
- Load all documents from the course materials folder
- Create a vector store for retrieval
- Initialize domain-independent agents
- Start interactive tutoring session
"""

import argparse
import asyncio
import itertools
import json
import logging
import re
import sys
import threading
from pathlib import Path
from typing import List, Optional

try:
    import chromadb
except ImportError:
    print("chromadb not found. Run: pip install chromadb")
    sys.exit(1)

from fairlib import (
    Document,
    HuggingFaceAdapter,
    SummarizingMemory,
    ChromaDBVectorStore,
    SentenceTransformerEmbedder,
    SimpleRetriever,
)

from fairlib.utils.document_processor import DocumentProcessor

from agents.tutor_agent import TutorAgent
from config import TutorConfig
from tools.schemas import InteractionMode
from tools.sanitize import (
    wrap_untrusted,
    strip_mode_injection,
    UNTRUSTED_PREAMBLE,
    PREPROCESSOR_MODE_PREFIX,
)

logger = logging.getLogger(__name__)

# Patterns that indicate leaked internal reasoning
_LEAKED_PREFIXES_RE = re.compile(
    r"^\s*(?:Thought|Action|Observation|ACTION PLAN)\s*:",
    re.IGNORECASE,
)
_FRAMEWORK_FALLBACK_RE = re.compile(
    r"Agent stopped after reaching max steps\.?",
    re.IGNORECASE,
)
_FINAL_ANSWER_PREFIX_RE = re.compile(
    r"^\s*Final\s+Answer\s*:\s*",
    re.IGNORECASE,
)
_FINAL_ANSWER_ANYWHERE_RE = re.compile(
    r"Final\s+Answer\s*:\s*",
    re.IGNORECASE,
)
_TOOL_LINE_RE = re.compile(r"^\s*(?:\{|tool_)", re.IGNORECASE)

# Shared verb list for answer-confirmation patterns
_CONFIRMATION_VERBS = (
    r"found|determined|calculated|identified|got|solved|derived|computed|applied|shown"
    r"|rewrote|implemented|understood|recognized|demonstrated|verified|traced|wrote"
    r"|recalculated|recalculating|completed|established|proved|proven|obtained|arrived"
    r"|handled|handles|handling|covered|covers|managed|manages|addressed|mastered"
    r"|nailed|built|constructed|produced|created|written|figured"
)

# Matches the FULL sentence containing an answer confirmation.
# Captures from an optional leading praise word through to the next sentence
# boundary (period, exclamation, or question mark followed by space/end).
# This prevents leftover answer fragments after the match.
_ANSWER_CONFIRMATION_RE = re.compile(
    r"(?:(?:Great job|Correct|Excellent|Well done|Right|Fantastic|Fantastic job|"
    r"Brilliant|Perfect|Wonderful|Superb|Bravo|Nice work|Good work|Outstanding)"
    r"[!.]?\s*)?"
    r"You(?:'ve| have)?\s+(?:correctly|successfully|accurately|properly)\s+"
    rf"(?:{_CONFIRMATION_VERBS})\b"
    r"[^.!?\n]*[.!?]?",
    re.IGNORECASE,
)

# Matches direct answer statements that include a concrete value:
# "the answer is 42", "simplifies to 6x + 2", "is indeed x = 6",
# "as \( f'(x) = 6x + 2 \)", "giving us 12x^2 - 12x + 3"
_DIRECT_ANSWER_RE = re.compile(
    r"(?:the\s+(?:answer|result|solution|value|derivative|integral)|"
    r"your\s+(?:final\s+)?(?:answer|result|solution|value)\s+is|"
    r"(?:simplifies?|reduces?|equals?|evaluates?|gives?|giving)\s+(?:us\s+)?to|"
    r"is\s+indeed|"
    r"is\s+approximately|"
    r"as\s+\\?\(?\s*[a-zA-Z]'?\s*\\?\(?\s*[a-zA-Z]\s*\\?\)?\s*=)"
    r"[^.!?\n]*(?:\d|=)[^.!?\n]*[.!?]?",
    re.IGNORECASE,
)

# Matches complete step-by-step calculations that reveal intermediate + final values:
# "3×6 + 4×8 = 18 + 32 = 50", "2*3 + 4 = 10", "f'(x) = 6x + 2"
_COMPLETE_CALCULATION_RE = re.compile(
    r"\d+\s*[×x*·]\s*\d+(?:\s*[+\-]\s*\d+\s*[×x*·]\s*\d+)*\s*=\s*[^.!?\n]*=\s*\d+",
    re.IGNORECASE,
)

# Matches LaTeX-style answers: \( f'(x) = ... \) or \( g'(x) = ... \)
_LATEX_ANSWER_RE = re.compile(
    r"\\\(\s*[a-zA-Z]'?\s*\([a-zA-Z]\)\s*=\s*[^\\)]+\\\)",
    re.IGNORECASE,
)

# Matches praise followed by embedded value confirmation:
# "Great job on recalculating the top-right element correctly as 22!"
# "Excellent work identifying the base case as n == 0!"
_PRAISE_VALUE_RE = re.compile(
    r"(?:Great job|Excellent|Well done|Correct|Perfect|Brilliant|Wonderful|"
    r"Fantastic|Nice work|Good work|Outstanding|Superb|Bravo)"
    r"(?:\s+(?:work|job))?\s+"
    r"(?:on\s+)?"
    r"(?:[^.!?\n](?!correctly|accurately|properly|right))*"
    r"[^.!?\n]*"
    r"(?:correctly|accurately|properly|right)\s+"
    r"(?:as|to\s+be|that\s+it'?s?)\s+"
    r"[^.!?\n]*[.!?]?",
    re.IGNORECASE,
)

# Matches standalone praise at the START of a response that implicitly
# confirms a correct answer without explicitly stating it.
# E.g., "Excellent work! What was your reasoning..." or "Great job! Ready for..."
_PRAISE_CONFIRMATION_RE = re.compile(
    r"^(?:Exactly|Exactly\s+right|Excellent(?:\s+work)?|Great(?:\s+job)?|"
    r"Well\s+done|Correct|Right(?=\s*[!.])|Yes|Absolutely|Perfect|Brilliant|"
    r"Wonderful|Superb|Bravo|Outstanding|Fantastic(?:\s+job)?|Nice\s+work|"
    r"Good\s+work|Great\s+work|You'?re\s+(?:right|correct|absolutely\s+right)|"
    r"That'?s\s+(?:right|correct|exactly\s+right|it|exactly)|"
    r"Spot\s+on|Nailed\s+it|Bingo|"
    r"Great\s+(?:observations?|understanding|thinking|approach|reasoning|questions?)"
    r")(?:\s*[!.])+\s*",
    re.IGNORECASE,
)

# Neutral openers to replace praise confirmations
_NEUTRAL_OPENERS = (
    "Let's focus on one specific part of your work. ",
    "I'd like to ask about a particular step in your reasoning. ",
    "There's an important detail to consider here. ",
    "Let's examine the key step more closely. ",
    "I want to explore your reasoning on one point. ",
    "Let's check whether each step follows logically. ",
    "I have a question about how you got from one step to the next. ",
    "Let's look at the critical step in your solution. ",
)

# Matches truncated responses ending with ":" and no content after
_TRUNCATED_RESPONSE_RE = re.compile(r":\s*$")

# Matches code blocks preceded by phrases that reveal a complete solution:
# "Here's your final function: ```", "the code: ```", "your complete code: ```"
_CODE_REVEAL_RE = re.compile(
    r"(?:(?:Here'?s|here\s+is)[^:]*:\s*```"
    r"|(?:your\s+(?:final|complete|finished|corrected)\s+\w+\s*:\s*```)"
    r"|(?:(?:the|your)\s+(?:function|code|solution|implementation)\s*:\s*```))"
    r"[\s\S]*?```",
    re.IGNORECASE,
)

_GRACEFUL_FALLBACK = (
    "Let me think about this differently. "
    "Could you try rephrasing your question or showing me your work step by step?"
)

# Extracts numeric values and simple expressions for context-aware sanitization.
# Used to determine whether the tutor is "revealing" a value the student already stated.
_NUMERIC_VALUE_RE = re.compile(r'-?\d+(?:\.\d+)?')

# Matches a sentence starting with "The student" followed by a verb/adverb.
# Applied per-sentence to avoid anchor-consumption issues.
_THIRD_PERSON_SENTENCE_RE = re.compile(
    r"^The\s+student(?:'s)?\s+(?:correctly|accurately|properly|successfully|"
    r"also|further|clearly|indeed|has|had|was|is|did|does|should|would|could|can|may|might|"
    r"demonstrated|showed|identified|recalled|explained|understood|applied|noted|mentioned|"
    r"recognized|grasped|calculated|computed|derived|obtained|arrived|wrote|provided|"
    r"submitted|presented|stated|described|observed|pointed|used|chose|selected|made|"
    r"work\b)",
    re.IGNORECASE,
)

# Matches standalone code blocks (```...```) that contain function definitions —
# full solutions the tutor should not provide.
_STANDALONE_CODE_BLOCK_RE = re.compile(
    r"```(?:python|javascript|java|c\+\+|cpp|go|rust|typescript)?\s*\n"
    r"(?:[^\n]*\n)*?"  # any lines
    r"[^\n]*(?:def |function |class |fn |func )[^\n]*\n"  # function definition
    r"(?:[^\n]*\n)*?"  # more lines
    r"```",
    re.IGNORECASE,
)

# Varied replacements — each asks a DIFFERENT type of question to avoid
# the "walk me through your steps" repetition loop.
_CONFIRMATION_REPLACEMENTS = (
    "Can you explain the reasoning behind your key step? What rule or principle did you apply there?",
    "How did you decide on that approach? What made you choose this method over alternatives?",
    "What would change in your answer if the input values were different? Try predicting the outcome.",
    "Can you identify the most important step in your work and explain why it's correct?",
    "What assumptions are you making here? Are there edge cases where your approach might not work?",
    "Try explaining your solution as if teaching it to a classmate — what's the core idea?",
    "What's the relationship between the given information and your result? How does each piece connect?",
    "Before we move on, what's the trickiest part of this problem, and how did you handle it?",
    "Can you trace through your work with a specific example to verify each step?",
)
_DIRECT_ANSWER_REPLACEMENTS = (
    "What rule or formula connects the information you were given to the result you need?",
    "Try breaking this into smaller pieces — what's the first thing you need to figure out?",
    "Think about what operation would get you from the given values to the unknown. What do you see?",
    "What information from the problem can you use as a starting point? Walk through it from there.",
)

_confirmation_cycle = itertools.cycle(_CONFIRMATION_REPLACEMENTS)
_direct_answer_cycle = itertools.cycle(_DIRECT_ANSWER_REPLACEMENTS)
_praise_cycle = itertools.cycle(_NEUTRAL_OPENERS)
_cycle_lock = threading.Lock()


def _get_confirmation_replacement() -> str:
    """Rotate through replacement phrases to avoid repetition."""
    with _cycle_lock:
        return next(_confirmation_cycle)


def _get_direct_answer_replacement() -> str:
    """Rotate through direct-answer replacement phrases."""
    with _cycle_lock:
        return next(_direct_answer_cycle)


def _get_praise_replacement() -> str:
    """Rotate through neutral openers to replace implicit praise confirmations."""
    with _cycle_lock:
        return next(_praise_cycle)


def _extract_student_values(student_work: str) -> set[str]:
    """Extract numeric values from student work for context-aware filtering.

    Returns a set of number strings found in the student's input. Used to
    determine whether the tutor is revealing NEW information or just
    referencing values the student already stated.
    """
    if not student_work:
        return set()
    return set(_NUMERIC_VALUE_RE.findall(student_work))


def _sentence_reveals_new_values(sentence: str, student_values: set[str]) -> bool:
    """Check if a sentence introduces numeric values not in the student's work.

    If the student already stated all the values mentioned in the sentence,
    the tutor is acknowledging — not revealing. Only strip sentences that
    introduce genuinely new values.
    """
    if not student_values:
        # No student context available — assume revelation (conservative)
        return True
    sent_values = set(_NUMERIC_VALUE_RE.findall(sentence))
    if not sent_values:
        # No numeric values in the sentence — it's a qualitative confirmation
        # (e.g., "Great job!"). These are handled by praise filters, not here.
        return True
    # New values = values in the tutor's sentence but NOT in the student's work
    new_values = sent_values - student_values
    return len(new_values) > 0


def _strip_sentences_with_answers(
    text: str,
    student_work: str = "",
    check_third_person: bool = False,
) -> str:
    """Remove full sentences that contain answer-confirming or third-person content.

    Context-aware: if the student already stated the values being confirmed,
    the sentence is kept (it's acknowledgment, not revelation). Only sentences
    that introduce NEW values are stripped.

    Third-person references are always stripped regardless of context (voice issue).
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    clean = []
    replaced = False
    student_values = _extract_student_values(student_work)

    for sent in sentences:
        # Third-person references are always a voice problem — strip regardless
        if check_third_person and _THIRD_PERSON_SENTENCE_RE.search(sent):
            if not replaced:
                clean.append(_get_confirmation_replacement())
                replaced = True
            continue

        # Check answer-confirming patterns, but only strip if revealing NEW values
        is_confirming = False
        replacement_fn = _get_confirmation_replacement

        if _ANSWER_CONFIRMATION_RE.search(sent):
            is_confirming = True
        elif _DIRECT_ANSWER_RE.search(sent):
            is_confirming = True
            replacement_fn = _get_direct_answer_replacement
        elif _LATEX_ANSWER_RE.search(sent):
            affirm_words = re.search(
                r'\b(?:correctly|right|exactly|yes|correct)\b', sent, re.IGNORECASE
            )
            if affirm_words:
                is_confirming = True
        elif _PRAISE_VALUE_RE.search(sent):
            is_confirming = True
        elif _COMPLETE_CALCULATION_RE.search(sent):
            is_confirming = True

        if is_confirming:
            # Context-aware: keep if student already stated these values
            if not _sentence_reveals_new_values(sent, student_values):
                clean.append(sent)
                continue
            # Genuinely revealing new values — strip
            if not replaced:
                clean.append(replacement_fn())
                replaced = True
            continue

        clean.append(sent)

    return " ".join(clean).strip()


def sanitize_tutor_response(response: str | None, student_work: str = "") -> str:
    """Strip leaked internal reasoning from tutor responses before displaying.

    Defence-in-depth: catches leaked Thought/Action/Observation chains,
    framework error messages, and 'Final Answer:' prefixes that should
    never reach the student.

    Context-aware: when ``student_work`` is provided, answer-confirmation
    filters only strip sentences that introduce values the student has NOT
    already stated.  This prevents the sanitizer from destroying helpful
    acknowledgments of correct student work.
    """
    if not response:
        return _GRACEFUL_FALLBACK

    # Replace framework max-steps message with a graceful fallback
    # Use search instead of match to catch it embedded in longer responses
    if _FRAMEWORK_FALLBACK_RE.search(response.strip()):
        return _GRACEFUL_FALLBACK

    text = response

    # If the response starts with internal reasoning, try to extract
    # useful content after the last "Final Answer:" occurrence first
    if _LEAKED_PREFIXES_RE.match(text):
        fa_match = _FINAL_ANSWER_ANYWHERE_RE.search(text)
        if fa_match:
            text = text[fa_match.end():].strip()
        else:
            # No final answer found — strip lines that look like
            # internal reasoning or tool calls
            lines = text.split("\n")
            clean_lines = [
                line for line in lines
                if not _LEAKED_PREFIXES_RE.match(line)
                and not _TOOL_LINE_RE.match(line)
            ]
            text = "\n".join(clean_lines).strip()
    elif _FINAL_ANSWER_PREFIX_RE.match(text):
        # Strip "Final Answer:" prefix (benign but unprofessional)
        text = _FINAL_ANSWER_PREFIX_RE.sub("", text, count=1).strip()

    if not text or len(text) < 10:
        return _GRACEFUL_FALLBACK

    # Defence-in-depth: strip full sentences containing answer confirmations,
    # direct answer statements, or third-person references.
    # Context-aware: sentences referencing values already in student_work are kept.
    has_answer_patterns = (
        _ANSWER_CONFIRMATION_RE.search(text) or _DIRECT_ANSWER_RE.search(text)
        or _LATEX_ANSWER_RE.search(text)
        or _PRAISE_VALUE_RE.search(text)
        or _COMPLETE_CALCULATION_RE.search(text)
    )
    has_third_person = _THIRD_PERSON_SENTENCE_RE.search(text)
    if has_answer_patterns or has_third_person:
        text = _strip_sentences_with_answers(
            text,
            student_work=student_work,
            check_third_person=bool(has_third_person),
        )

    # Strip complete code solutions — the tutor sometimes dumps full code blocks
    # that reveal the answer. Remove code blocks that follow confirmatory phrasing
    # or present "your final function/code/solution".
    if _CODE_REVEAL_RE.search(text):
        text = _CODE_REVEAL_RE.sub(
            lambda _: _get_confirmation_replacement(),
            text,
        )

    # Strip standalone code blocks containing function definitions — even without
    # confirmatory phrasing, dumping a full implementation reveals the answer.
    if _STANDALONE_CODE_BLOCK_RE.search(text):
        text = _STANDALONE_CODE_BLOCK_RE.sub(
            "Instead of providing code, let me ask: what's the key logic you need to implement? "
            "Think about the steps your function should follow.",
            text,
        )

    # Strip standalone praise at start of response ONLY when we have no
    # evidence the student stated correct values.  If the student's work
    # contains numeric values that appear in the tutor's response, the
    # praise is likely warranted acknowledgment — keep it.
    if _PRAISE_CONFIRMATION_RE.match(text):
        student_values = _extract_student_values(student_work)
        tutor_values = set(_NUMERIC_VALUE_RE.findall(text))
        # If no student context or the tutor isn't referencing student values,
        # strip the praise opener
        if not student_values or not (tutor_values & student_values):
            text = _PRAISE_CONFIRMATION_RE.sub(_get_praise_replacement(), text, count=1)

    # Catch truncated responses ending with ":" and no content
    if _TRUNCATED_RESPONSE_RE.search(text) and len(text) < 80:
        text += " What do you think the next step would be?"

    if not text or len(text) < 10:
        return _GRACEFUL_FALLBACK

    return text


class TutorSession:
    """
    Main tutoring session.

    Loads course materials, creates RAG-enabled agents, and provides
    interactive tutoring interface.
    """

    def __init__(self, course_materials_path: str, problems_file: str = "",
                 config: Optional[TutorConfig] = None):
        """
        Initialize the tutor system.

        Args:
            course_materials_path: Path to folder containing course materials
            problems_file: Optional JSON file with problems to work on
            config: Optional TutorConfig; defaults to TutorConfig.from_env()
        """
        self.config = config or TutorConfig.from_env()
        warnings = self.config.validate()
        if warnings:
            logger.warning(f"Config has {len(warnings)} warning(s)")

        logger.info("Initializing Tutor System...")

        # Load course materials into RAG system
        logger.info("Loading course materials...")
        self.retriever = self._setup_rag_system(course_materials_path)
        logger.info("Course materials loaded into vector store")

        # Load problems if provided
        self.problems = None
        if problems_file and Path(problems_file).exists():
            with open(problems_file, 'r') as f:
                self.problems = json.load(f)
            logger.info(f"Loaded {len(self.problems.get('problems', []))} problems")

        # Initialize LLM
        logger.info(f"Loading language model: {self.config.model_name}")
        self.llm = HuggingFaceAdapter(
            model_name=self.config.model_name,
            quantized=self.config.quantized,
            stream=self.config.stream,
            verbose=self.config.verbose,
            max_new_tokens=self.config.max_new_tokens,
            auth_token=self.config.auth_token,
        )

        # Build single tutor agent
        self.agent = self._build_agent()

        logger.info("Domain-Agnostic Tutor initialized successfully!")

    def _setup_rag_system(self, materials_path: str):
        """
        Set up RAG system by loading course materials into vector store.

        Returns:
            SimpleRetriever for querying course materials
        """
        materials_path_obj = Path(materials_path)

        # Initialize embedder and vector store
        embedder = SentenceTransformerEmbedder()

        if self.config.chromadb_persist_path:
            client = chromadb.PersistentClient(path=self.config.chromadb_persist_path)
            logger.info(f"Using persistent ChromaDB at: {self.config.chromadb_persist_path}")
        else:
            client = chromadb.Client()
            logger.info("Using ephemeral ChromaDB (data will not persist between sessions)")

        vector_store = ChromaDBVectorStore(
            client=client,
            collection_name=self.config.collection_name,
            embedder=embedder
        )

        if not materials_path_obj.exists():
            logger.warning(f"Course materials path not found: {materials_path}")
            return SimpleRetriever(vector_store)

        # Initialize DocumentProcessor
        logger.info(f"Processing files from: {materials_path}")
        doc_processor = DocumentProcessor({"files_directory": str(materials_path_obj)})

        # Process all files in directory
        all_documents: List[Document] = []
        if materials_path_obj.is_file():
            docs = doc_processor.process_file(str(materials_path_obj))
            if docs:
                all_documents.extend(docs)
                logger.info(f"Loaded: {materials_path_obj.name}")
        else:
            all_documents = doc_processor.load_documents_from_folder(str(materials_path_obj))

        logger.info(f"Total documents loaded: {len(all_documents)}")

        if not all_documents:
            logger.warning("No documents loaded. Vector store will be empty.")
            return SimpleRetriever(vector_store)

        # Add documents to vector store
        document_texts = [doc.page_content for doc in all_documents]
        logger.info(f"Adding {len(document_texts)} documents to vector store...")
        vector_store.add_documents(document_texts)

        return SimpleRetriever(vector_store)

    def _build_agent(self) -> TutorAgent:
        """Build the single tutor agent with SummarizingMemory for long sessions."""
        return TutorAgent.create(
            llm=self.llm,
            memory=SummarizingMemory(
                llm=self.llm,
                max_history_length=30,
                messages_to_keep_at_end=8,
            ),
            retriever=self.retriever,
            max_steps=self.config.max_steps,
            escalation_threshold=self.config.escalation_threshold,
        )

    async def process_student_work(self, problem_text: str, student_work: str, topic: str) -> str:
        """
        Process student work through the multi-agent system.

        Args:
            problem_text: The original problem statement
            student_work: The student's answer or work
            topic: The topic/domain (for RAG context)

        Returns:
            Tutor's response
        """
        # Strip mode-detection injection attempts before any processing
        sanitized_work = strip_mode_injection(student_work)

        # Wrap student input in untrusted tags
        tagged_work = wrap_untrusted(sanitized_work)

        request = (
            f"PROBLEM: {problem_text}\n\n"
            f"{UNTRUSTED_PREAMBLE}\n"
            f"STUDENT WORK: {tagged_work}\n\n"
            f"TOPIC: {topic}\n\n"
            f"Please analyze the student's work, identify any misconceptions, "
            f"and provide an appropriate hint or concept explanation. Remember: NEVER reveal the answer!"
        )

        # Prepend preprocessor mode hint if detected
        detected_mode = TutorAgent.detect_mode(sanitized_work)
        if detected_mode:
            prefix = f"{PREPROCESSOR_MODE_PREFIX} {detected_mode.value}"
            prefix += "\nSafety check REQUIRED."
            request = f"{prefix}\n\n{request}"

        # Warn if concept question contains answer-like content
        if detected_mode == InteractionMode.CONCEPT_EXPLANATION and TutorAgent.has_answer_content(sanitized_work):
            request += (
                "\n\nWARNING: Student input may contain answer-like content. "
                "Do NOT confirm any specific values."
            )

        logger.info("Processing student work through agent...")

        response = await self.agent.arun(request)

        logger.info("tutor_response_raw: %s", response)

        # Defence-in-depth: sanitize any leaked internal reasoning.
        # Pass student_work for context-aware filtering — confirmations of
        # values the student already stated are kept, not stripped.
        response = sanitize_tutor_response(response, student_work=student_work)

        logger.info("tutor_response: %s", response)

        return response

    async def interactive_loop(self):
        print("\n" + "*" * 30)
        print("\nWelcome to the FAIR_LLM Tutor!")
        print("\nCommands:")
        print("  'help' - Show available commands")
        print("  'topic [name]' - Set the current topic")
        print("  'problem [text]' - Set the current problem")
        print("  'quit' or 'exit' - End session")
        print("\n" + "*" * 30)

        current_topic = "general"
        current_problem = None

        while True:
            try:
                user_input = input("\nYou: ").strip()

                if not user_input:
                    continue

                if len(user_input) > self.config.max_input_length:
                    print(
                        f"\nInput too long ({len(user_input)} chars). "
                        f"Please keep it under {self.config.max_input_length} characters."
                    )
                    continue

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\nExiting tutor session...")
                    break

                if user_input.lower() == 'help':
                    print("\nAvailable commands:")
                    print("  topic [name] - Set current topic (e.g., 'topic calculus')")
                    print("  problem [text] - Set current problem to work on")
                    print("  [your work] - Submit your work for feedback")
                    print("  quit/exit - End session")
                    continue

                if user_input.lower().startswith('topic'):
                    current_topic = user_input[5:].strip()
                    print(f"Topic set to: {current_topic}")
                    continue

                if user_input.lower().startswith('problem'):
                    current_problem = user_input[7:].strip()
                    print(f"Problem set: {current_problem}")
                    print("Now submit your work!")
                    continue

                if not current_problem:
                    print("Please set a problem first using: problem [text]")
                    continue

                response = await self.process_student_work(
                    problem_text=current_problem,
                    student_work=user_input,
                    topic=current_topic
                )

                print("\n" + "-" * 60)
                print("TUTOR RESPONSE")
                print("-" * 60)
                print(f"\n{response}\n")
                print("-" * 60)

            except KeyboardInterrupt:
                print("\n\nSession interrupted. Exiting...")
                break
            except Exception as e:
                logger.error(f"Error during tutoring: {e}", exc_info=True)
                print("\nError processing your input. Please try again.")


async def main():
    parser = argparse.ArgumentParser(description="FAIR_LLM Tutor - Domain-Agnostic Tutoring System")
    parser.add_argument(
        "--course_materials",
        type=str,
        default="course_materials",
        help="Path to course materials folder"
    )
    parser.add_argument(
        "--problems",
        type=str,
        default=None,
        help="Path to problems JSON file (optional)"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to YAML config file (optional)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    try:
        config = None
        if args.config:
            config = TutorConfig.from_yaml(args.config)

        session = TutorSession(
            course_materials_path=args.course_materials,
            problems_file=args.problems,
            config=config,
        )

        await session.interactive_loop()

    except Exception as e:
        logger.critical("Fatal error: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
