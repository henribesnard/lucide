import logging
from typing import Any, Dict, List

from backend.agents.analysis_agent import AnalysisAgent
from backend.agents.intent_agent import IntentAgent
from backend.agents.response_agent import ResponseAgent
from backend.agents.tool_agent import ToolAgent
from backend.agents.types import AnalysisResult, IntentResult, ToolCallResult
from backend.api.football_api import FootballAPIClient
from backend.config import settings
from backend.llm.client import LLMClient

logger = logging.getLogger(__name__)


class LucidePipeline:
    """
    Orchestrates the full loop:
    intent/entity extraction -> tool calling -> structured analysis -> final answer.
    """

    def __init__(self, session_id: str | None = None):
        self.session_id = session_id
        self.llm = LLMClient(
            provider=settings.LLM_PROVIDER,
            api_key=settings.DEEPSEEK_API_KEY if settings.LLM_PROVIDER == "deepseek" else settings.OPENAI_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL if settings.LLM_PROVIDER == "deepseek" else None,
            model=settings.DEEPSEEK_MODEL if settings.LLM_PROVIDER == "deepseek" else settings.OPENAI_MODEL,
        )
        self.api_client = FootballAPIClient(
            api_key=settings.FOOTBALL_API_KEY,
            base_url=settings.FOOTBALL_API_BASE_URL,
        )
        self.intent_agent = IntentAgent(self.llm)
        self.tool_agent = ToolAgent(self.llm, self.api_client)
        self.analysis_agent = AnalysisAgent(self.llm)
        self.response_agent = ResponseAgent(self.llm)

    async def process(self, user_message: str) -> Dict[str, Any]:
        intent: IntentResult = await self.intent_agent.run(user_message)

        tool_results: List[ToolCallResult] = []
        assistant_notes = "Aucun appel de tool requis."
        if intent.needs_data:
            tool_results, assistant_notes = await self.tool_agent.run(user_message, intent)

        analysis: AnalysisResult = await self.analysis_agent.run(
            user_message=user_message,
            intent=intent,
            tool_results=tool_results,
            assistant_notes=assistant_notes,
        )
        final_answer = await self.response_agent.run(
            user_message=user_message,
            intent=intent,
            analysis=analysis,
        )

        return {
            "intent": intent,
            "tool_results": tool_results,
            "analysis": analysis,
            "answer": final_answer,
        }

    async def close(self):
        await self.api_client.close()
