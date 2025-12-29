import logging
import time
from typing import Any, Dict, List, Callable, Optional

from backend.agents.analysis_agent import AnalysisAgent
from backend.agents.intent_agent import IntentAgent
from backend.agents.response_agent import ResponseAgent
from backend.agents.tool_agent import ToolAgent
from backend.agents.context_agent import ContextAgent
from backend.agents.causal_agent import CausalAgent
from backend.agents.types import AnalysisResult, IntentResult, ToolCallResult
from backend.api.football_api import FootballAPIClient
from backend.config import settings
from backend.llm.client import LLMClient
from backend.core.data_collector import DataCollector

logger = logging.getLogger(__name__)


class LucidePipeline:
    """
    Orchestrates the full loop:
    intent/entity extraction -> tool calling (with context caching) -> structured analysis -> final answer.

    Key feature: Match analysis with intelligent caching
    - First access: 25 API calls to collect all data + run 8 analyzers
    - Subsequent accesses: 0 API calls (loads from cache)
    """

    def __init__(
        self,
        session_id: str | None = None,
        storage_path: str = "./data/match_contexts",
        user_id: str | None = None,
    ):
        self.session_id = session_id
        self.user_id = user_id
        if settings.ENABLE_MULTI_LLM:
            # Slow LLM (DeepSeek) - par défaut, économique
            slow_provider = settings.SLOW_LLM_PROVIDER
            slow_api_key = (
                settings.SLOW_LLM_API_KEY
                or (settings.OPENAI_API_KEY if slow_provider == "openai" else settings.DEEPSEEK_API_KEY)
            )
            self.slow_llm = LLMClient(
                provider=slow_provider,
                api_key=slow_api_key,
                base_url=settings.DEEPSEEK_BASE_URL if slow_provider == "deepseek" else None,
                model=settings.SLOW_LLM_MODEL,
            )

            # Medium LLM (GPT-4o-mini) - équilibré
            medium_provider = settings.MEDIUM_LLM_PROVIDER
            medium_api_key = (
                settings.MEDIUM_LLM_API_KEY
                or (settings.OPENAI_API_KEY if medium_provider == "openai" else settings.DEEPSEEK_API_KEY)
            )
            self.medium_llm = LLMClient(
                provider=medium_provider,
                api_key=medium_api_key,
                base_url=settings.DEEPSEEK_BASE_URL if medium_provider == "deepseek" else None,
                model=settings.MEDIUM_LLM_MODEL,
            )

            # Fast LLM (GPT-4o) - premium, rapide
            fast_provider = settings.FAST_LLM_PROVIDER
            fast_api_key = (
                settings.FAST_LLM_API_KEY
                or (settings.OPENAI_API_KEY if fast_provider == "openai" else settings.DEEPSEEK_API_KEY)
            )
            self.fast_llm = LLMClient(
                provider=fast_provider,
                api_key=fast_api_key,
                base_url=settings.DEEPSEEK_BASE_URL if fast_provider == "deepseek" else None,
                model=settings.FAST_LLM_MODEL,
            )

            # Use Medium for intent/tools, Fast for analysis/response by default
            llm_for_intent = self.medium_llm
            llm_for_tools = self.medium_llm
            llm_for_analysis = self.fast_llm
            llm_for_response = self.fast_llm
        else:
            self.llm = LLMClient(
                provider=settings.LLM_PROVIDER,
                api_key=settings.DEEPSEEK_API_KEY if settings.LLM_PROVIDER == "deepseek" else settings.OPENAI_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL if settings.LLM_PROVIDER == "deepseek" else None,
                model=settings.DEEPSEEK_MODEL if settings.LLM_PROVIDER == "deepseek" else settings.OPENAI_MODEL,
            )
            llm_for_intent = self.llm
            llm_for_tools = self.llm
            llm_for_analysis = self.llm
            llm_for_response = self.llm
        self.api_client = FootballAPIClient(
            api_key=settings.FOOTBALL_API_KEY,
            base_url=settings.FOOTBALL_API_BASE_URL,
        )

        # Initialize context management components
        self.data_collector = DataCollector(self.api_client)
        self.context_agent = ContextAgent(self.data_collector, storage_path=storage_path)

        # Initialize agents
        self.intent_agent = IntentAgent(llm_for_intent)
        self.tool_agent = ToolAgent(llm_for_tools, self.api_client, context_agent=self.context_agent)
        self.analysis_agent = AnalysisAgent(llm_for_analysis)
        self.response_agent = ResponseAgent(llm_for_response)
        self.causal_agent = CausalAgent(context_agent=self.context_agent)

    def _get_llm_for_model_type(self, model_type: str = "slow"):
        """
        Retourne le LLM approprié selon le model_type.
        - "slow" : DeepSeek (par défaut, économique)
        - "medium" : GPT-4o-mini (équilibré)
        - "fast" : GPT-4o (premium, rapide)
        """
        if not settings.ENABLE_MULTI_LLM:
            # Si ENABLE_MULTI_LLM est désactivé, utiliser le LLM unique
            return self.llm

        if model_type == "slow":
            return self.slow_llm
        elif model_type == "medium":
            return self.medium_llm
        else:  # "fast"
            return self.fast_llm

    def _needs_analysis(
        self,
        intent: IntentResult,
        context: Dict[str, Any] | None,
        tool_results: List[ToolCallResult],
    ) -> bool:
        if not settings.ENABLE_SMART_SKIP_ANALYSIS:
            return True
        if not context or context.get("context_type") != "league":
            return True
        simple_intents = {
            "classement_ligue",
            "top_performers",
            "top_cartons",
            "calendrier_ligue_saison",
            "journees_competition",
            "matchs_live_filtre",
            "prochains_ou_derniers_matchs",
            "referentiel_ligues",
        }
        if intent.intent not in simple_intents:
            return True
        if len(tool_results) > 3:
            return True
        return False


    async def process(
        self,
        user_message: str,
        context: Dict[str, Any] = None,
        user_id: str = None,
        model_type: str = "slow",
        language: str = "fr",
        status_callback: Optional[Callable[[str, str], None]] = None
    ) -> Dict[str, Any]:
        # Log and validate context (frontend may already inject text into user_message).
        if context:
            context_type = context.get("context_type")
            if not context_type:
                if "player_id" in context:
                    context_type = "player"
                elif "team_id" in context and "league_id" in context:
                    context_type = "league_team"
                elif "team_id" in context:
                    context_type = "team"
                elif "match_id" in context or "fixture_id" in context:
                    context_type = "match"
                elif "league_id" in context:
                    context_type = "league"

            logger.info(
                "Processing with context payload",
                extra={
                    "context_type": context_type,
                    "context_keys": list(context.keys()),
                    "session_id": self.session_id,
                    "user_id": user_id or self.user_id
                }
            )

            required_keys = []
            validation_errors = []

            # V4 Context Validation
            if context_type == "match":
                if "match_id" not in context and "fixture_id" not in context:
                    required_keys.append("match_id/fixture_id")
                if "league_id" not in context:
                    required_keys.append("league_id")
            elif context_type == "league":
                required_keys = ["league_id"]
            elif context_type == "team":
                required_keys = ["team_id"]
            elif context_type == "league_team":
                required_keys = ["league_id", "team_id"]
            elif context_type == "player":
                # Player requires player_id + (match_id OR team_id)
                if "player_id" not in context:
                    required_keys.append("player_id")
                has_match = "match_id" in context or "fixture_id" in context
                has_team = "team_id" in context
                if not has_match and not has_team:
                    validation_errors.append("player context requires either match_id or team_id")

                # Log player mode
                if has_match:
                    logger.info("Player context: MATCH mode (player in specific match)")
                elif has_team:
                    logger.info("Player context: TEAM mode (player in team/season)")

            if required_keys:
                missing = [k for k in required_keys if k not in context]
                if missing:
                    logger.warning(f"Missing required context keys: {missing}")

            if validation_errors:
                logger.error(f"Context validation errors: {validation_errors}")

        start_total = time.perf_counter()

        # Step 1: Intent detection
        if status_callback:
            status_callback("intent", "🔍 Analyse de votre question...")
        intent_start = time.perf_counter()
        intent: IntentResult = await self.intent_agent.run(user_message, context=context)
        intent_latency = time.perf_counter() - intent_start

        # Enrichir les entities avec le contexte si disponible
        if context:
            # Inject fixture_id/match_id into entities if not already present
            if "fixture_id" in context and "fixture_id" not in intent.entities:
                intent.entities["fixture_id"] = context["fixture_id"]
            elif "match_id" in context and "fixture_id" not in intent.entities:
                intent.entities["fixture_id"] = context["match_id"]

            # Inject league_id if not already present
            if "league_id" in context and "league_id" not in intent.entities:
                intent.entities["league_id"] = context["league_id"]

            # Inject team_id if not already present
            if "team_id" in context and "team_id" not in intent.entities:
                intent.entities["team_id"] = context["team_id"]

            # Inject player_id if not already present
            if "player_id" in context and "player_id" not in intent.entities:
                intent.entities["player_id"] = context["player_id"]

            # Inject season if not already present
            if "season" in context and "season" not in intent.entities:
                intent.entities["season"] = context["season"]

            logger.info(f"Intent detected: {intent.intent} (needs_data={intent.needs_data}, confidence={intent.confidence})")
            logger.info(f"Entities after context enrichment: {intent.entities}")

        tool_results: List[ToolCallResult] = []
        assistant_notes = "Aucun appel de tool requis."
        if intent.needs_data:
            # Step 2: Tool execution
            if status_callback:
                status_callback("tools", "🛠️ Collecte des données football...")
            tool_start = time.perf_counter()
            tool_results, assistant_notes = await self.tool_agent.run(
                user_message,
                intent,
                context=context
            )
            tool_latency = time.perf_counter() - tool_start
        else:
            tool_latency = 0.0
        # Best-effort check for critical data in match analysis
        if intent.intent in {"analyse_rencontre", "match_analysis", "stats_final", "stats_live"}:
            required_tools = {
                "fixtures_search",
                "team_last_fixtures",
                "standings",
                "team_statistics",
                "head_to_head",
            }
            available = {tr.name for tr in tool_results}
            missing = required_tools - available
            if missing:
                logger.warning(f"analyse_rencontre: missing critical data from tools: {sorted(missing)}")

        # Override LLM based on model_type parameter
        selected_llm = self._get_llm_for_model_type(model_type)
        analysis_agent = AnalysisAgent(selected_llm)
        response_agent = ResponseAgent(selected_llm)
        causal_summary = ""
        causal_payload: Dict[str, Any] = {}

        if settings.ENABLE_CAUSAL_AI and self.causal_agent.should_run(user_message, intent, tool_results):
            # Step 3: Causal analysis
            if status_callback:
                status_callback("causal", "🧠 Analyse causale en cours...")
            try:
                causal_result = await self.causal_agent.run(
                    question=user_message,
                    intent=intent,
                    tool_results=tool_results,
                    llm_client=selected_llm,
                    language=language,
                    context=context,
                )
                if causal_result:
                    causal_summary = causal_result.llm_analysis
                    causal_payload = causal_result.to_payload()
            except Exception as exc:
                logger.warning("Causal analysis failed: %s", exc)

        logger.info(f"Using model_type='{model_type}' for analysis and response")

        analysis_latency = 0.0
        if self._needs_analysis(intent, context, tool_results):
            # Step 4: Analysis
            if status_callback:
                status_callback("analysis", "📊 Analyse des données...")
            analysis_start = time.perf_counter()
            analysis = await analysis_agent.run(
                user_message=user_message,
                intent=intent,
                tool_results=tool_results,
                assistant_notes=assistant_notes,
                context=context,
            )
            analysis_latency = time.perf_counter() - analysis_start
        else:
            analysis = AnalysisResult(
                brief="Donnees recuperees directement depuis les tools.",
                data_points=[f"Tools utilises: {[tr.name for tr in tool_results]}"],
                gaps=[],
                safety_notes=[],
            )
            logger.info("Skipped analysis for intent %s (context=%s)", intent.intent, context.get("context_type") if context else "none")
        analysis.causal_summary = causal_summary
        analysis.causal_payload = causal_payload

        # Step 5: Response generation
        if status_callback:
            status_callback("response", "✍️ Génération de la réponse...")
        response_start = time.perf_counter()
        final_answer = await response_agent.run(
            user_message=user_message,
            intent=intent,
            analysis=analysis,
            context=context,
            language=language,
        )
        response_latency = time.perf_counter() - response_start
        total_latency = time.perf_counter() - start_total

        logger.info(
            "pipeline_timing intent=%.2fs tools=%.2fs analysis=%.2fs response=%.2fs total=%.2fs",
            intent_latency,
            tool_latency,
            analysis_latency,
            response_latency,
            total_latency,
        )

        return {
            "intent": intent,
            "tool_results": tool_results,
            "analysis": analysis,
            "answer": final_answer,
        }

    async def close(self):
        await self.api_client.close()
