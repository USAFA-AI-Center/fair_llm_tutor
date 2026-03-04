"""Shared test fixtures for fair_llm_tutor tests."""

import sys
from pathlib import Path
import pytest

# Add project root to path so we can import tutor modules
sys.path.insert(0, str(Path(__file__).parent.parent))


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


class SequenceMockLLM(MockLLM):
    """Mock LLM that returns different responses per call.

    Enables testing multi-step ReAct loops where each call to the LLM
    should produce a different response (planning step 1, step 2, etc.)
    """

    def __init__(self, responses: list[str]):
        super().__init__(responses[0] if responses else "")
        self._responses = responses
        self._index = 0

    def invoke(self, messages, **kwargs):
        self.call_count += 1
        self.last_messages = messages
        response = self._responses[min(self._index, len(self._responses) - 1)]
        self._index += 1
        return MockMessage(response)

    async def ainvoke(self, messages, **kwargs):
        return self.invoke(messages, **kwargs)


class FailingMockLLM(MockLLM):
    """Mock LLM that raises an exception on invoke."""

    def __init__(self, error: Exception = None):
        super().__init__("")
        self._error = error or RuntimeError("LLM service unavailable")

    def invoke(self, messages, **kwargs):
        self.call_count += 1
        raise self._error

    async def ainvoke(self, messages, **kwargs):
        return self.invoke(messages, **kwargs)


class FailingMockRetriever:
    """Mock retriever that raises an exception on retrieve."""

    def __init__(self, error: Exception = None):
        self._error = error or RuntimeError("Retriever service unavailable")

    def retrieve(self, query, top_k=3):
        raise self._error


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


def build_json_input(model_class, **fields):
    """Build a JSON tool input string from a Pydantic model.

    Example:
        build_json_input(DiagnosticInput, problem="Find x", student_work="x=5", topic="algebra")
        # Returns: '{"problem":"Find x","student_work":"x=5","topic":"algebra"}'
    """
    return model_class(**fields).model_dump_json()


