"""
Data Collector - Collects all necessary data for match analysis

Follows the workflow from Structure_Analyse_Match_Lucide.md:
1. predictions
2. head_to_head history
3. h2h details (statistics, players, events, lineups)
4. complementary data (standings, team stats, injuries, top players)

Total: ~25 API calls per match
"""
import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime

from backend.api.football_api import FootballAPIClient

logger = logging.getLogger(__name__)


class DataCollector:
    """
    Collects all data necessary for match analysis

    Usage:
        collector = DataCollector(api_client)
        data = await collector.collect_match_data(fixture_id)
    """

    def __init__(self, api_client: FootballAPIClient):
        self.api = api_client
        self.api_calls_count = 0

    async def collect_match_data(self, fixture_id: int) -> Dict[str, Any]:
        """
        Collect all data for a match

        Args:
            fixture_id: ID of the fixture to analyze

        Returns:
            Dictionary with all collected data
        """
        logger.info(f"Starting data collection for fixture {fixture_id}")
        self.api_calls_count = 0

        # 1. Get fixture info
        fixture_info = await self._get_fixture_info(fixture_id)
        logger.info(
            f"Fixture: {fixture_info['teams']['home']['name']} vs {fixture_info['teams']['away']['name']} "
            f"({fixture_info['league']['name']})"
        )

        team1_id = fixture_info['teams']['home']['id']
        team2_id = fixture_info['teams']['away']['id']
        league_id = fixture_info['league']['id']
        season = fixture_info['league']['season']

        # 2. Predictions
        predictions = await self._safe_call(
            self.api.get_predictions(fixture_id),
            "predictions"
        )

        # 3. Head to Head history
        h2h_history = await self._safe_call(
            self.api.get_head_to_head(team1_id, team2_id, last=5, status="FT"),
            "h2h_history"
        )

        # 4. H2H details for 3 most recent matches
        h2h_details = await self._collect_h2h_details(h2h_history[:3] if h2h_history else [])

        # 5. Complementary data (collected in parallel)
        complementary = await self._collect_complementary_data(
            team1_id=team1_id,
            team2_id=team2_id,
            league_id=league_id,
            season=season
        )

        logger.info(f"Data collection complete: {self.api_calls_count} API calls")

        return {
            "fixture": fixture_info,
            "predictions": predictions,
            "h2h_history": h2h_history or [],
            "h2h_details": h2h_details,
            **complementary,
            "api_calls_count": self.api_calls_count,
            "collected_at": datetime.utcnow().isoformat()
        }

    async def _get_fixture_info(self, fixture_id: int) -> Dict[str, Any]:
        """Get basic fixture information"""
        fixtures = await self._safe_call(
            self.api.get_fixtures(fixture_id=fixture_id),
            "fixture_info"
        )

        if not fixtures:
            raise ValueError(f"Fixture {fixture_id} not found")

        return fixtures[0]

    async def _collect_h2h_details(self, h2h_matches: List[Dict]) -> List[Dict]:
        """
        Collect details for H2H matches

        For each match: statistics, players, events, lineups (4 calls per match)
        """
        if not h2h_matches:
            return []

        logger.info(f"Collecting details for {len(h2h_matches)} H2H matches")
        details = []

        for h2h_match in h2h_matches:
            fixture_id = h2h_match['fixture']['id']

            # Parallel calls for each H2H match
            stats, players, events, lineups = await asyncio.gather(
                self._safe_call(
                    self.api.get_fixture_statistics(fixture_id),
                    f"h2h_stats_{fixture_id}"
                ),
                self._safe_call(
                    self.api.get_fixture_player_statistics(fixture_id),
                    f"h2h_players_{fixture_id}"
                ),
                self._safe_call(
                    self.api.get_fixture_events(fixture_id),
                    f"h2h_events_{fixture_id}"
                ),
                self._safe_call(
                    self.api.get_fixture_lineups(fixture_id),
                    f"h2h_lineups_{fixture_id}"
                )
            )

            details.append({
                "fixture_id": fixture_id,
                "statistics": stats,
                "players": players,
                "events": events,
                "lineups": lineups
            })

        return details

    async def _collect_complementary_data(
        self,
        team1_id: int,
        team2_id: int,
        league_id: int,
        season: int
    ) -> Dict[str, Any]:
        """
        Collect complementary data in parallel

        Includes: standings, team stats, injuries, top players
        """
        logger.info("Collecting complementary data (parallel)")

        tasks = [
            self._safe_call(
                self.api.get_standings(season=season, league_id=league_id),
                "standings"
            ),
            self._safe_call(
                self.api.get_team_statistics(team1_id, season, league_id),
                "team1_stats"
            ),
            self._safe_call(
                self.api.get_team_statistics(team2_id, season, league_id),
                "team2_stats"
            ),
            self._safe_call(
                self.api.get_injuries(team_id=team1_id, league_id=league_id, season=season),
                "injuries_t1"
            ),
            self._safe_call(
                self.api.get_injuries(team_id=team2_id, league_id=league_id, season=season),
                "injuries_t2"
            ),
            self._safe_call(
                self.api.get_sidelined(team_id=team1_id),
                "sidelined_t1"
            ),
            self._safe_call(
                self.api.get_sidelined(team_id=team2_id),
                "sidelined_t2"
            ),
            self._safe_call(
                self.api.get_top_scorers(league_id, season),
                "top_scorers"
            ),
            self._safe_call(
                self.api.get_top_assists(league_id, season),
                "top_assists"
            ),
            self._safe_call(
                self.api.get_top_yellow_cards(league_id, season),
                "top_yellow"
            ),
            self._safe_call(
                self.api.get_top_red_cards(league_id, season),
                "top_red"
            ),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        (
            standings,
            team1_stats,
            team2_stats,
            injuries_t1,
            injuries_t2,
            sidelined_t1,
            sidelined_t2,
            top_scorers,
            top_assists,
            top_yellow,
            top_red
        ) = results

        # Merge injuries
        injuries = []
        if injuries_t1 and not isinstance(injuries_t1, Exception):
            injuries.extend(injuries_t1)
        if injuries_t2 and not isinstance(injuries_t2, Exception):
            injuries.extend(injuries_t2)

        sidelined = []
        if sidelined_t1 and not isinstance(sidelined_t1, Exception):
            sidelined.extend(sidelined_t1)
        if sidelined_t2 and not isinstance(sidelined_t2, Exception):
            sidelined.extend(sidelined_t2)

        return {
            "standings": standings if not isinstance(standings, Exception) else None,
            "team1_stats": team1_stats if not isinstance(team1_stats, Exception) else None,
            "team2_stats": team2_stats if not isinstance(team2_stats, Exception) else None,
            "injuries": injuries,
            "sidelined": sidelined,
            "top_scorers": top_scorers if not isinstance(top_scorers, Exception) else [],
            "top_assists": top_assists if not isinstance(top_assists, Exception) else [],
            "top_yellow": top_yellow if not isinstance(top_yellow, Exception) else [],
            "top_red": top_red if not isinstance(top_red, Exception) else []
        }

    async def _safe_call(self, coro, call_name: str):
        """
        Safe API call with error handling and rate limiting

        Args:
            coro: Coroutine to execute
            call_name: Name of the call (for logging)

        Returns:
            API response or None if error
        """
        try:
            # Small delay to avoid rate limiting (100ms)
            await asyncio.sleep(0.1)

            result = await coro
            self.api_calls_count += 1

            logger.debug(f"API call [{call_name}]: SUCCESS (total: {self.api_calls_count})")
            return result

        except Exception as e:
            self.api_calls_count += 1
            logger.warning(f"API call [{call_name}]: FAILED - {str(e)}")
            return None
