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

import asyncio
import json
import logging
import re
import sys
import argparse
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
    WorkingMemory,
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
)

# Matches phrases that implicitly confirm correctness by declaring student work
# is complete/perfect/final, e.g. "your function should work perfectly",
# "Here's your final code:", "Your final implementation:"
_IMPLICIT_CONFIRMATION_RE = re.compile(
    r"(?:your\s+(?:function|code|solution|implementation|program|answer|formula|equation)"
    r"\s+(?:should|will|does)\s+(?:work|run|execute|compute)\s+"
    r"(?:perfectly|correctly|fine|now|as expected))"
    r"|(?:(?:here'?s|here\s+is)\s+your\s+(?:final|complete|finished|corrected|working)"
    r"\s+(?:code|solution|implementation|function|program|answer|version))"
    r"|(?:your\s+(?:final|complete|corrected|finished|working)"
    r"\s+(?:code|solution|implementation|function|program|answer|version)\s+(?:is|looks|would\s+be))",
    re.IGNORECASE,
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
    r"(?:simplifies?|reduces?|equals?|evaluates?|gives?|giving)\s+(?:us\s+)?to|"
    r"is\s+indeed|"
    r"as\s+\\?\(?\s*[a-zA-Z]'?\s*\\?\(?\s*[a-zA-Z]\s*\\?\)?\s*=)"
    r"[^.!?\n]*(?:\d|=)[^.!?\n]*[.!?]?",
    re.IGNORECASE,
)

# Matches LaTeX-style answers: \( f'(x) = ... \) or \( g'(x) = ... \)
_LATEX_ANSWER_RE = re.compile(
    r"\\\(\s*[a-zA-Z]'?\s*\([a-zA-Z]\)\s*=\s*[^\\)]+\\\)",
    re.IGNORECASE,
)

# Matches standalone praise at the START of a response that implicitly
# confirms a correct answer without explicitly stating it.
# E.g., "Excellent work! What was your reasoning..." or "Great job! Ready for..."
_PRAISE_CONFIRMATION_RE = re.compile(
    r"^(?:Excellent(?:\s+work)?|Great(?:\s+job)?|Well\s+done|Correct|"
    r"Perfect|Brilliant|Wonderful|Superb|Bravo|Outstanding|Fantastic"
    r"(?:\s+job)?|Nice\s+work|Good\s+work|Great\s+work|"
    r"Great\s+(?:observation|understanding|thinking|approach|reasoning|questions)"
    r")(?:\s*[!.])+\s*",
    re.IGNORECASE,
)

# Neutral openers to replace praise confirmations
_NEUTRAL_OPENERS = [
    "Let's take a closer look. ",
    "Interesting approach. ",
    "I see your thinking. ",
    "Let's work through this together. ",
    "Good effort so far. ",
]

# Matches truncated responses ending with ":" and no content after
_TRUNCATED_RESPONSE_RE = re.compile(r":\s*$")

_GRACEFUL_FALLBACK = (
    "Let me think about this differently. "
    "Could you try rephrasing your question or showing me your work step by step?"
)

# Varied replacements — each asks a DIFFERENT type of question to avoid
# the "walk me through your steps" repetition loop.
_CONFIRMATION_REPLACEMENTS = [
    "What rule or concept did you apply here?",
    "What would happen if the input were different — say, twice as large?",
    "Can you think of a case where this approach might not work?",
    "How does this connect to what we discussed earlier?",
    "What's the key insight that makes this work?",
    "Could you solve this a different way? What trade-offs would there be?",
    "What part of this was trickiest for you, and why?",
]
_DIRECT_ANSWER_REPLACEMENTS = [
    "Let's think about this differently. What concept applies here?",
    "Before we continue, what's the key relationship in this problem?",
    "Interesting — what would change if we modified the problem slightly?",
]

_confirmation_counter = 0
_direct_answer_counter = 0
_praise_counter = 0


def _get_confirmation_replacement() -> str:
    """Rotate through replacement phrases to avoid repetition."""
    global _confirmation_counter
    text = _CONFIRMATION_REPLACEMENTS[
        _confirmation_counter % len(_CONFIRMATION_REPLACEMENTS)
    ]
    _confirmation_counter += 1
    return text


def _get_direct_answer_replacement() -> str:
    """Rotate through direct-answer replacement phrases."""
    global _direct_answer_counter
    text = _DIRECT_ANSWER_REPLACEMENTS[
        _direct_answer_counter % len(_DIRECT_ANSWER_REPLACEMENTS)
    ]
    _direct_answer_counter += 1
    return text


def _get_praise_replacement() -> str:
    """Rotate through neutral openers to replace implicit praise confirmations."""
    global _praise_counter
    text = _NEUTRAL_OPENERS[_praise_counter % len(_NEUTRAL_OPENERS)]
    _praise_counter += 1
    return text


def _strip_sentences_with_answers(text: str) -> str:
    """Remove full sentences that contain answer-confirming content.

    Operates at the sentence level: splits on sentence boundaries, removes
    sentences that match answer patterns, and reassembles. This prevents
    leftover answer fragments that sentence-unaware regex sub would leave.
    """
    # Split into sentences (period/excl/question followed by space or end)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    clean = []
    replaced = False
    for sent in sentences:
        if _ANSWER_CONFIRMATION_RE.search(sent):
            if not replaced:
                clean.append(_get_confirmation_replacement())
                replaced = True
            continue
        if _DIRECT_ANSWER_RE.search(sent):
            if not replaced:
                clean.append(_get_direct_answer_replacement())
                replaced = True
            continue
        if _IMPLICIT_CONFIRMATION_RE.search(sent):
            # "your function should work perfectly", "Here's your final code", etc.
            if not replaced:
                clean.append(_get_confirmation_replacement())
                replaced = True
            continue
        if _LATEX_ANSWER_RE.search(sent):
            affirm_words = re.search(
                r'\b(?:correctly|right|exactly|yes|correct)\b', sent, re.IGNORECASE
            )
            if affirm_words:
                if not replaced:
                    clean.append(_get_confirmation_replacement())
                    replaced = True
                continue
        clean.append(sent)

    return " ".join(clean).strip()


def sanitize_tutor_response(response: str | None) -> str:
    """Strip leaked internal reasoning from tutor responses before displaying.

    Defence-in-depth: catches leaked Thought/Action/Observation chains,
    framework error messages, and 'Final Answer:' prefixes that should
    never reach the student.
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
    # direct answer statements, or implicit confirmations like "your code works
    # perfectly". Sentence-level removal prevents leftover answer fragments.
    if (_ANSWER_CONFIRMATION_RE.search(text) or _DIRECT_ANSWER_RE.search(text)
            or _LATEX_ANSWER_RE.search(text)
            or _IMPLICIT_CONFIRMATION_RE.search(text)):
        text = _strip_sentences_with_answers(text)

    # Strip complete code solutions — the tutor sometimes dumps full code blocks
    # that reveal the answer. Remove code blocks that follow confirmatory phrasing.
    if re.search(r"(?:Here'?s|here\s+is)[^:]*:\s*```", text, re.IGNORECASE):
        text = re.sub(
            r"(?:Here'?s|here\s+is)[^:]*:\s*```[\s\S]*?```",
            lambda _: _get_confirmation_replacement(),
            text,
            flags=re.IGNORECASE,
        )

    # Strip standalone praise at start of response that implicitly confirms
    # correctness (e.g., "Excellent work! Walk me through...").
    # This must run AFTER sentence-level filtering above.
    if _PRAISE_CONFIRMATION_RE.match(text):
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

        # Defence-in-depth: sanitize any leaked internal reasoning
        response = sanitize_tutor_response(response)

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
