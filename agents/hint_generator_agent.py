# hint_generator_agent.py

from fairlib.modules.agent.simple_agent import SimpleAgent
from fairlib.core.interfaces.llm import AbstractChatModel
from fairlib.core.interfaces.memory import AbstractMemory
from fairlib.modules.planning.direct_planner import DirectToolPlanner
from fairlib.modules.action.executor import ToolExecutor
from fairlib.modules.action.tools.registry import ToolRegistry
from fairlib.core.interfaces.memory import AbstractRetriever

from tools.pedagogical_tools import SocraticHintGeneratorTool


class HintGeneratorAgent(SimpleAgent):
    """
    Generates Socratic hints using LLM + RAG + student work context.
    Uses DirectToolPlanner — zero LLM calls for planning since there's only one tool.

    Dual-mode operation:
    1. HINT mode: Generate hints for student work with misconceptions
    2. CONCEPT_EXPLANATION mode: Explain concepts when students ask questions
    """

    TOOL_NAME = "socratic_hint_generator"

    @classmethod
    def create(cls, llm: AbstractChatModel, memory: AbstractMemory,
               retriever: AbstractRetriever) -> "HintGeneratorAgent":
        tool_registry = ToolRegistry()

        tool_registry.register_tool(SocraticHintGeneratorTool(llm, retriever))

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
            "You generate Socratic hints AND concept explanations based on the mode specified."
        )

        return agent
