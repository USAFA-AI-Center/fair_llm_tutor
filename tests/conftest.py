"""Shared test fixtures for fair_llm_tutor tests."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

# Add project root to path so we can import tutor modules
sys.path.insert(0, str(Path(__file__).parent.parent))
# Add fair_prompt_optimizer to path for integration tests
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "fair_prompt_optimizer"))


class MockMessage:
    """Minimal Message mock matching fairlib's Message interface."""

    def __init__(self, content: str, role: str = "assistant"):
        self.content = content
        self.role = role


class MockLLM:
    """Mock LLM that returns configurable responses."""

    def __init__(self, response_text: str = "Mock LLM response"):
        self.response_text = response_text
        self.call_count = 0
        self.last_messages = None

    def invoke(self, messages, **kwargs):
        self.call_count += 1
        self.last_messages = messages
        return MockMessage(self.response_text)

    async def ainvoke(self, messages, **kwargs):
        return self.invoke(messages, **kwargs)


class MockRetriever:
    """Mock retriever that returns configurable documents."""

    def __init__(self, documents=None):
        self.documents = documents or []
        self.last_query = None
        self.last_top_k = None

    def retrieve(self, query, top_k=3):
        self.last_query = query
        self.last_top_k = top_k
        return self.documents[:top_k]


@pytest.fixture
def mock_llm():
    """Returns a MockLLM with default response."""
    return MockLLM()


@pytest.fixture
def mock_retriever():
    """Returns a MockRetriever with no documents."""
    return MockRetriever()


@pytest.fixture
def mock_retriever_with_docs():
    """Returns a MockRetriever with sample documents."""
    return MockRetriever(documents=[
        "Document 1: Momentum is mass times velocity (p = mv).",
        "Document 2: The derivative of x^n is n*x^(n-1).",
        "Document 3: Force equals mass times acceleration (F = ma).",
    ])


def build_tool_input(**fields):
    """Build a |||−delimited tool input string from keyword arguments.

    Example:
        build_tool_input(PROBLEM="Find x", STUDENT_WORK="x=5", TOPIC="algebra")
        # Returns: "PROBLEM: Find x ||| STUDENT_WORK: x=5 ||| TOPIC: algebra"
    """
    return " ||| ".join(f"{key}: {value}" for key, value in fields.items())


def build_tutor_runner(mock_llm=None, mock_retriever=None):
    """Build a full HierarchicalAgentRunner with the tutor's real agents.

    Uses mock LLM/retriever so no actual inference is needed — only the
    agent structure, prompts, and tool registries matter for config tests.
    """
    from fairlib import WorkingMemory, HierarchicalAgentRunner

    # Import tutor agent classes (relative to fair_llm_tutor project root)
    from agents.safety_guard_agent import SafetyGuardAgent
    from agents.misconception_detector_agent import MisconceptionDetectorAgent
    from agents.hint_generator_agent import HintGeneratorAgent
    from agents.manager_agent import TutorManagerAgent

    llm = mock_llm or MockLLM()
    retriever = mock_retriever or MockRetriever()

    workers = {
        "SafetyGuard": SafetyGuardAgent.create(llm, WorkingMemory()),
        "MisconceptionDetector": MisconceptionDetectorAgent.create(
            llm, WorkingMemory(), retriever
        ),
        "HintGenerator": HintGeneratorAgent.create(
            llm, WorkingMemory(), retriever
        ),
    }

    manager = TutorManagerAgent.create(llm, WorkingMemory(), workers)
    return HierarchicalAgentRunner(manager, workers, max_steps=15)
