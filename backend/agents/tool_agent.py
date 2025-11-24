import json
import logging
from typing import List, Tuple

from backend.api.football_api import FootballAPIClient
from backend.agents.types import IntentResult, ToolCallResult
from backend.llm.client import LLMClient
from backend.prompts import TOOL_SYSTEM_PROMPT
from backend.tools.football import TOOL_DEFINITIONS, execute_tool

logger = logging.getLogger(__name__)


class ToolAgent:
    """Handles DeepSeek function calling and executes the mapped tools."""

    def __init__(self, llm: LLMClient, api_client: FootballAPIClient, max_iterations: int = 3):
        self.llm = llm
        self.api_client = api_client
        self.max_iterations = max_iterations

    async def run(self, user_message: str, intent: IntentResult) -> Tuple[List[ToolCallResult], str]:
        league_mapping = (
            "Mapping ligues vers IDs: "
            "Ligue 1=61; Premier League=39; La Liga=140; Bundesliga=78; Serie A=135; "
            "Ligue des Champions=2; Europa League=3."
        )
        intent_guidance = {
            "classement_ligue": "Utilise le tool standings avec league_id et season (convertis le nom de ligue via le mapping).",
            "prochain_match_equipe": "Utilise search_team puis team_next_fixtures (count=1 par defaut).",
            "calendrier_matchs": (
                "Resous league -> league_id meme pour '1ere division <pays>'. "
                "Si date absente, prends aujourd'hui; season par defaut = saison en cours. "
                "Appelle fixtures_by_date avec league_id/date/season/status quand dispo."
            ),
            "analyse_rencontre": (
                "Resous les deux equipes via search_team. Si fixture_id absent, identifie la prochaine rencontre a venir "
                "(fixtures_by_date ou team_next_fixtures). Ensuite appelle predictions, head_to_head et odds_by_fixture."
            ),
            "stats_equipe_saison": (
                "Resous team -> team_id via search_team puis appelle team_statistics avec league_id + season (defaut saison actuelle)."
            ),
            "stats_joueur": (
                "Utilise search_player pour obtenir player_id; season par defaut = saison en cours. "
                "Le tool search_player suffit pour les stats globales."
            ),
            "top_performers": "Utilise top_scorers ou top_assists selon la demande.",
        }

        messages = [
            {"role": "system", "content": TOOL_SYSTEM_PROMPT},
            {
                "role": "system",
                "content": f"Intent cible: {intent.intent}. Entites: {intent.entities}. "
                "Si needs_data est False, reponds directement par une courte note sans tool.",
            },
            {"role": "system", "content": league_mapping},
            {
                "role": "system",
                "content": intent_guidance.get(
                    intent.intent,
                    "Choisis les tools les plus pertinents. Utilise le mapping des ligues quand une ligue est mentionnee.",
                ),
            },
            {"role": "user", "content": user_message},
        ]

        tool_results: List[ToolCallResult] = []
        assistant_notes = ""
        conversation = list(messages)

        for _ in range(self.max_iterations):
            try:
                response = await self.llm.chat_completion(
                    messages=conversation,
                    tools=TOOL_DEFINITIONS,
                    temperature=0.0,
                    max_tokens=600,
                )
            except Exception as exc:
                logger.error(f"Tool agent LLM call failed: {exc}", exc_info=True)
                assistant_notes = "Impossible d'appeler le modele pour les tools."
                break

            choice = response.choices[0]
            msg = choice.message
            finish_reason = choice.finish_reason

            if finish_reason == "stop":
                assistant_notes = msg.content or ""
                break

            if finish_reason == "tool_calls" and msg.tool_calls:
                # Record assistant intent for traceability
                conversation.append(
                    {
                        "role": "assistant",
                        "content": msg.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in msg.tool_calls
                        ],
                    }
                )

                for tool_call in msg.tool_calls:
                    try:
                        arguments = json.loads(tool_call.function.arguments or "{}")
                    except json.JSONDecodeError:
                        arguments = {}

                    logger.info(f"Executing tool {tool_call.function.name} with args {arguments}")
                    result = await execute_tool(self.api_client, tool_call.function.name, arguments)
                    tool_results.append(
                        ToolCallResult(
                            name=tool_call.function.name,
                            arguments=arguments,
                            output=result,
                            error=result.get("error") if isinstance(result, dict) else None,
                        )
                    )

                    conversation.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result, ensure_ascii=False),
                        }
                    )
                continue

            assistant_notes = msg.content or ""
            break

        return tool_results, assistant_notes
