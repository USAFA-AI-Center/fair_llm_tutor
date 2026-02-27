# misconception_detector_agent.py

from fairlib.modules.agent.simple_agent import SimpleAgent
from fairlib.core.interfaces.llm import AbstractChatModel
from fairlib.core.interfaces.memory import AbstractMemory
from fairlib.modules.planning.direct_planner import DirectToolPlanner
from fairlib.modules.action.executor import ToolExecutor
from fairlib.modules.action.tools.registry import ToolRegistry
from fairlib.core.interfaces.memory import AbstractRetriever

from tools.diagnostic_tools import StudentWorkAnalyzerTool


class MisconceptionDetectorAgent(SimpleAgent):
    """
    Diagnoses student errors using LLM + RAG.
    Uses DirectToolPlanner — zero LLM calls for planning since there's only one tool.
    """

    TOOL_NAME = "student_work_analyzer"

    @classmethod
    def create(cls, llm: AbstractChatModel, memory: AbstractMemory,
               retriever: AbstractRetriever) -> "MisconceptionDetectorAgent":
        """Create MisconceptionDetectorAgent with DirectToolPlanner"""

        tool_registry = ToolRegistry()
        tool_registry.register_tool(StudentWorkAnalyzerTool(llm, retriever))

        planner = DirectToolPlanner(tool_name=cls.TOOL_NAME)

        executor = ToolExecutor(tool_registry)

        agent = cls(
            llm=llm,
            planner=planner,
            tool_executor=executor,
            memory=memory,
            max_steps=3,
            stateless=True
        )

        agent.role_description = (
            "You analyze student work for errors OR explain concepts when students ask questions."
        )

        return agent
