"""Tests for tools.retrieval_tools — pure computation, no LLM needed."""

import json
import pytest
from tests.conftest import MockRetriever, FailingMockRetriever, build_json_input
from tools.retrieval_tools import RetrieveCourseMaterialsTool
from tools.schemas import RetrievalInput


class TestRetrieveCourseMaterials:
    def test_returns_numbered_documents(self):
        retriever = MockRetriever(documents=[
            "Momentum is mass times velocity.",
            "Force equals mass times acceleration.",
        ])
        tool = RetrieveCourseMaterialsTool(retriever)
        result = tool.use(build_json_input(RetrievalInput, query="momentum"))
        assert "[1] Momentum is mass times velocity." in result
        assert "[2] Force equals mass times acceleration." in result

    def test_respects_top_k(self):
        retriever = MockRetriever(documents=["doc1", "doc2", "doc3"])
        tool = RetrieveCourseMaterialsTool(retriever)
        result = tool.use(json.dumps({"query": "test", "top_k": 1}))
        assert "[1] doc1" in result
        assert "[2]" not in result
        assert retriever.last_top_k == 1

    def test_empty_results(self):
        retriever = MockRetriever(documents=[])
        tool = RetrieveCourseMaterialsTool(retriever)
        result = tool.use(json.dumps({"query": "obscure topic"}))
        assert "No course materials found" in result

    def test_retriever_failure_handled(self):
        retriever = FailingMockRetriever()
        tool = RetrieveCourseMaterialsTool(retriever)
        result = tool.use(json.dumps({"query": "anything"}))
        assert "No course materials found" in result
        assert "unavailable" in result

    def test_invalid_json_returns_error(self):
        retriever = MockRetriever()
        tool = RetrieveCourseMaterialsTool(retriever)
        result = tool.use("not valid json")
        assert "ERROR" in result

    def test_empty_query_returns_error(self):
        retriever = MockRetriever()
        tool = RetrieveCourseMaterialsTool(retriever)
        result = tool.use(json.dumps({"query": "  "}))
        assert "ERROR" in result

    def test_passes_query_to_retriever(self):
        retriever = MockRetriever(documents=["doc"])
        tool = RetrieveCourseMaterialsTool(retriever)
        tool.use(json.dumps({"query": "derivatives calculus"}))
        assert retriever.last_query == "derivatives calculus"

    def test_default_top_k_is_3(self):
        retriever = MockRetriever(documents=["a", "b", "c", "d"])
        tool = RetrieveCourseMaterialsTool(retriever)
        tool.use(json.dumps({"query": "test"}))
        assert retriever.last_top_k == 3

    def test_handles_document_objects(self):
        """Works with fairlib Document objects that have .page_content."""
        class FakeDoc:
            def __init__(self, content):
                self.page_content = content
        retriever = MockRetriever(documents=[FakeDoc("Real document content")])
        tool = RetrieveCourseMaterialsTool(retriever)
        result = tool.use(json.dumps({"query": "test"}))
        assert "Real document content" in result
