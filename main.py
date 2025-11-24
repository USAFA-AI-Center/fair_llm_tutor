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
import sys
import argparse
from pathlib import Path
from typing import List
import torch

try:
    import chromadb
    CHROMADB_LOADED = True
except ImportError:
    print("chromadb not found. Run: pip install chromadb")
    CHROMADB_LOADED = False
    sys.exit(1)

from fairlib import (
    Document,
    HuggingFaceAdapter,
    WorkingMemory,
    ChromaDBVectorStore,
    SentenceTransformerEmbedder,
    SimpleRetriever,
    OpenAIAdapter
)

from fairlib.utils.document_processor import DocumentProcessor
from fairlib.modules.agent.multi_agent_runner import HierarchicalAgentRunner

# Import tutor specific agents
from agents.hint_generator_agent import HintGeneratorAgent
from agents.misconception_detector_agent import MisconceptionDetectorAgent
from agents.safety_guard_agent import SafetyGuardAgent
from agents.manager_agent import TutorManagerAgent


class TutorSession:
    """
    Main tutoring session.
    
    Loads course materials, creates RAG-enabled agents, and provides
    interactive tutoring interface.
    """
    
    def __init__(self, course_materials_path: str, problems_file: str = ""):
        """
        Initialize the tutor system.
        
        Args:
            course_materials_path: Path to folder containing course materials
            problems_file: Optional JSON file with problems to work on
        """

        print("Initializing Tutor System...")
        print("-" * 60)
        
        # Load course materials into RAG system
        print("\nLoading course materials...")
        self.retriever = self._setup_rag_system(course_materials_path)
        print("Course materials loaded into vector store")
        
        # Load problems if provided
        self.problems = None
        if problems_file and Path(problems_file).exists():
            with open(problems_file, 'r') as f:
                self.problems = json.load(f)
            print(f"Loaded {len(self.problems.get('problems', []))} problems")
        
        # Initialize LLM
        print("\nLoading language model...")
        self.llm = HuggingFaceAdapter(
            model_name="Qwen/Qwen2.5-14B-Instruct",
            quantized=False,
            stream=False,
            verbose=False,
            max_new_tokens=1000,
            auth_token="",

        )
        
        # Build agent team
        self.agents = self._build_agents()
        
        # Create runner
        self.runner = self._build_runner()
        
        print("\n" + "-" * 60)
        print("Domain-Agnostic Tutor initialized successfully!")
        print("-" * 60 + "\n")
    
    def _setup_rag_system(self, materials_path: str):
        """
        Set up RAG system by loading course materials into vector store.
        Follows the pattern from demo_rag_from_documents.py
        
        Returns:
            SimpleRetriever for querying course materials
        """
        materials_path_obj = Path(materials_path)
        
        # Initialize embedder and vector store
        embedder = SentenceTransformerEmbedder()
        vector_store = ChromaDBVectorStore(
            client=chromadb.Client(),
            collection_name="course_materials",
            embedder=embedder
        )
        
        if not materials_path_obj.exists():
            print(f"Course materials path not found: {materials_path}")
            print("Creating empty vector store...")
            return SimpleRetriever(vector_store)
        
        # Initialize DocumentProcessor
        print(f"  Processing files from: {materials_path}")
        doc_processor = DocumentProcessor({"files_directory": str(materials_path_obj)})
        
        # Process all files in directory
        all_documents: List[Document] = []
        if materials_path_obj.is_file():
            # Single file
            docs = doc_processor.process_file(str(materials_path_obj))
            if docs:
                all_documents.extend(docs)
                print(f"  Loaded: {materials_path_obj.name}")
        else:
            # Directory - process all files
            all_documents = doc_processor.load_documents_from_folder(str(materials_path_obj))
        
        print(f"  Total documents loaded: {len(all_documents)}")
        
        if not all_documents:
            print("  No documents loaded. Vector store will be empty.")
            return SimpleRetriever(vector_store)
        
        # Add documents to vector store
        # Extract text content from Document objects
        document_texts = [doc.page_content for doc in all_documents]
        print(f"  Adding {len(document_texts)} documents to vector store...")
        vector_store.add_documents(document_texts)
        
        # Create and return retriever
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
            max_steps=15
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
        
        print("\nAnalyzing your work...")
        print("-" * 60)
        
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
                print(f"\nError: {e}")
                import traceback
                traceback.print_exc()


async def main():
    parser = argparse.ArgumentParser()
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
    
    args = parser.parse_args()
    
    try:
        session = TutorSession(
            course_materials_path=args.course_materials,
            problems_file=args.problems
        )

        await session.interactive_loop()
        
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":    
    asyncio.run(main())