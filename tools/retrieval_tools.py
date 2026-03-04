"""RAG retrieval tool — pure computation, no LLM calls."""

import logging

from pydantic import ValidationError

from fairlib.core.interfaces.tools import AbstractTool
from fairlib.core.interfaces.memory import AbstractRetriever

from tools.schemas import RetrievalInput

logger = logging.getLogger(__name__)


class RetrieveCourseMaterialsTool(AbstractTool):
    """Retrieves relevant course material chunks from the knowledge base.

    This is a pure data-retrieval tool — it queries the vector store and
    returns document passages.  No LLM call is made.
    """

    name = "retrieve_course_materials"
    description = (
        "Retrieves relevant course material passages from the knowledge base. "
        'Input: JSON string with keys "query" (required) and optional "top_k" '
        "(default 3). Returns numbered document passages."
    )

    def __init__(self, retriever: AbstractRetriever):
        self.retriever = retriever

    def use(self, tool_input: str) -> str:
        try:
            inp = RetrievalInput.model_validate_json(tool_input)
        except (ValueError, ValidationError):
            return (
                'ERROR: Invalid JSON input. Expected: '
                '{"query": "...", "top_k": 3}'
            )

        if not inp.query.strip():
            return "ERROR: query must not be empty."

        try:
            docs = self.retriever.retrieve(inp.query, top_k=inp.top_k)
        except Exception:
            logger.warning("Retriever failed for query: %s", inp.query, exc_info=True)
            return "No course materials found (retriever unavailable)."

        if not docs:
            return "No course materials found for this query."

        lines = []
        for i, doc in enumerate(docs, 1):
            # Support both Document objects (.page_content) and plain strings
            content = getattr(doc, "page_content", str(doc))
            lines.append(f"[{i}] {content}")
        return "\n".join(lines)
