#TODO:: Test with RAG against an entire textbook
#TODO:: make sure the overall prompting is not geared as much towards math, a lot of the prompting is specific to calculus

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
import sys
import argparse
from pathlib import Path
from typing import List

try:
    import chromadb
except ImportError:
    print("chromadb not found. Run: pip install chromadb")
    sys.exit(1)

from fairlib import (
    Document,
    HuggingFaceAdapter,
    WorkingMemory,
    ChromaDBVectorStore,
    SentenceTransformerEmbedder,
    SimpleRetriever,
)

from fairlib.utils.document_processor import DocumentProcessor
from fairlib.modules.agent.multi_agent_runner import HierarchicalAgentRunner

# Import tutor specific agents
from agents.hint_generator_agent import HintGeneratorAgent
from agents.misconception_detector_agent import MisconceptionDetectorAgent
from agents.safety_guard_agent import SafetyGuardAgent
from agents.manager_agent import TutorManagerAgent
from config import TutorConfig

logger = logging.getLogger(__name__)


class TutorSession:
    """
    Main tutoring session.

    Loads course materials, creates RAG-enabled agents, and provides
    interactive tutoring interface.
    """

    def __init__(self, course_materials_path: str, problems_file: str = "",
                 config: TutorConfig = None):
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
            stream=False,
            verbose=False,
            max_new_tokens=self.config.max_new_tokens,
            auth_token=self.config.auth_token,
        )

        # Build agent team
        self.agents = self._build_agents()

        # Create runner
        self.runner = self._build_runner()

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

    def _build_agents(self) -> dict:
        """Build all specialist agents with LLM+RAG tools"""
        agents = {}

        agents["SafetyGuard"] = SafetyGuardAgent.create(
            llm=self.llm,
            memory=WorkingMemory()
        )

        agents["MisconceptionDetector"] = MisconceptionDetectorAgent.create(
            llm=self.llm,
            memory=WorkingMemory(),
            retriever=self.retriever
        )

        agents["HintGenerator"] = HintGeneratorAgent.create(
            llm=self.llm,
            memory=WorkingMemory(),
            retriever=self.retriever
        )

        return agents

    def _build_runner(self) -> HierarchicalAgentRunner:
        """Build the hierarchical multi-agent runner"""
        manager_memory = WorkingMemory()

        manager = TutorManagerAgent.create(
            llm=self.llm,
            memory=manager_memory,
            workers=self.agents
        )

        return HierarchicalAgentRunner(
            manager_agent=manager,
            workers=self.agents,
            max_steps=self.config.runner_max_steps
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
        request = (
            f"PROBLEM: {problem_text}\n\n"
            f"STUDENT WORK: {student_work}\n\n"
            f"TOPIC: {topic}\n\n"
            f"Please analyze the student's work, identify any misconceptions, "
            f"and provide an appropriate hint or concept explanation. Remember: NEVER reveal the answer!"
        )

        # Prepend preprocessor mode hint if detected
        detected_mode = TutorManagerAgent.detect_mode(student_work)
        if detected_mode:
            prefix = f"PREPROCESSOR DETECTED MODE: {detected_mode}"
            if (detected_mode == "CONCEPT_EXPLANATION"
                    and TutorManagerAgent.has_answer_content(student_work)):
                prefix += (
                    "\nPREPROCESSOR WARNING: Answer-like content detected. "
                    "SafetyGuard REQUIRED."
                )
            request = f"{prefix}\n\n{request}"

        logger.info("Processing student work through multi-agent system...")

        response = await self.runner.arun(request)

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
                print(f"\nError processing your input. Please try again.")


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
        logger.fatal(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
