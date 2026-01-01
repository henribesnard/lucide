"""
Fixture resolution logic.

This module handles finding fixtures from various inputs:
- Team IDs
- Team names
- Match dates
- Current/next/recent matches
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from backend.api.football_api import FootballAPIClient
from backend.tools.football import execute_tool

logger = logging.getLogger(__name__)


class FixtureResolver:
    """
    Resolves fixtures from ambiguous inputs.

    Handles:
    - Finding fixture between two teams
    - Finding next/current match for a team
    - Extracting fixture details from API responses
    """

    def __init__(self, api_client: FootballAPIClient):
        self.api_client = api_client

    async def find_fixture_between_teams(
        self,
        team1_id: int,
        team2_id: int,
        prefer_next: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Find fixture between two teams.

        Args:
            team1_id: First team ID
            team2_id: Second team ID
            prefer_next: If True, prefer upcoming match; else recent match

        Returns:
            Fixture data or None if not found

        Examples:
            >>> resolver = FixtureResolver(api_client)
            >>> fixture = await resolver.find_fixture_between_teams(85, 33)
            >>> fixture['fixture']['id']
            1234567
        """
        logger.info(f"Finding fixture between teams {team1_id} and {team2_id}")

        # Try team1's next/recent matches
        result = await execute_tool(
            self.api_client,
            "fixtures_search",
            {"team_id": team1_id, "next": 1 if prefer_next else None, "last": 1 if not prefer_next else None},
        )

        fixtures = result.get("fixtures", []) if isinstance(result, dict) else []
        logger.info(f"Found {len(fixtures)} fixtures for team {team1_id}")

        # Check if any fixture involves team2
        for fx in fixtures:
            teams_block = fx.get("teams", {})
            home_id = (teams_block.get("home") or {}).get("id")
            away_id = (teams_block.get("away") or {}).get("id")

            if (home_id == team1_id and away_id == team2_id) or \
               (home_id == team2_id and away_id == team1_id):
                logger.info(f"Match found: fixture_id={fx.get('fixture', {}).get('id')}")
                return fx

        # Try team2's matches
        result = await execute_tool(
            self.api_client,
            "fixtures_search",
            {"team_id": team2_id, "next": 1 if prefer_next else None, "last": 1 if not prefer_next else None},
        )

        fixtures = result.get("fixtures", []) if isinstance(result, dict) else []
        logger.info(f"Found {len(fixtures)} fixtures for team {team2_id}")

        for fx in fixtures:
            teams_block = fx.get("teams", {})
            home_id = (teams_block.get("home") or {}).get("id")
            away_id = (teams_block.get("away") or {}).get("id")

            if (home_id == team1_id and away_id == team2_id) or \
               (home_id == team2_id and away_id == team1_id):
                logger.info(f"Match found on second attempt: fixture_id={fx.get('fixture', {}).get('id')}")
                return fx

        logger.warning(f"No fixture found between teams {team1_id} and {team2_id}")
        return None

    def extract_fixture_details(
        self,
        fixture_data: Dict[str, Any]
    ) -> Tuple[Optional[int], Optional[int], Optional[int], Optional[int], Optional[int]]:
        """
        Extract key details from fixture data.

        Args:
            fixture_data: Fixture object from API

        Returns:
            Tuple of (fixture_id, league_id, season, home_team_id, away_team_id)

        Examples:
            >>> details = resolver.extract_fixture_details(fixture)
            >>> fixture_id, league_id, season, home_id, away_id = details
        """
        fixture = fixture_data.get("fixture", {})
        league = fixture_data.get("league", {})
        teams = fixture_data.get("teams", {})

        fixture_id = fixture.get("id")
        league_id = league.get("id")
        season = league.get("season")
        home_team_id = (teams.get("home") or {}).get("id")
        away_team_id = (teams.get("away") or {}).get("id")

        return fixture_id, league_id, season, home_team_id, away_team_id

    def extract_team_ids_from_fixtures(
        self,
        fixtures: List[Dict[str, Any]]
    ) -> List[int]:
        """
        Extract all unique team IDs from a list of fixtures.

        Args:
            fixtures: List of fixture objects

        Returns:
            List of unique team IDs

        Examples:
            >>> team_ids = resolver.extract_team_ids_from_fixtures(fixtures)
            >>> len(team_ids)
            10  # 5 matches = 10 teams
        """
        team_ids = set()

        for fixture in fixtures:
            teams = fixture.get("teams", {})
            home_id = (teams.get("home") or {}).get("id")
            away_id = (teams.get("away") or {}).get("id")

            if home_id:
                team_ids.add(home_id)
            if away_id:
                team_ids.add(away_id)

        return list(team_ids)

    async def get_fixture_by_id(
        self,
        fixture_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get fixture details by ID.

        Args:
            fixture_id: Fixture ID

        Returns:
            Fixture data or None

        Examples:
            >>> fixture = await resolver.get_fixture_by_id(1234567)
            >>> fixture['teams']['home']['name']
            'Paris Saint Germain'
        """
        logger.info(f"Fetching fixture {fixture_id}")

        result = await execute_tool(
            self.api_client,
            "fixtures_search",
            {"fixture_id": fixture_id},
        )

        fixtures = result.get("fixtures", []) if isinstance(result, dict) else []

        if not fixtures:
            logger.warning(f"Fixture {fixture_id} not found")
            return None

        return fixtures[0]

    async def find_recent_fixture_for_team(
        self,
        team_id: int,
        limit: int = 1
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Find recent finished matches for a team.

        Args:
            team_id: Team ID
            limit: Number of matches to return

        Returns:
            List of fixtures or None

        Examples:
            >>> fixtures = await resolver.find_recent_fixture_for_team(85, limit=5)
            >>> len(fixtures)
            5
        """
        logger.info(f"Finding recent fixtures for team {team_id}")

        result = await execute_tool(
            self.api_client,
            "team_last_fixtures",
            {"team_id": team_id, "count": limit},
        )

        fixtures = result.get("fixtures", []) if isinstance(result, dict) else []

        if not fixtures:
            logger.warning(f"No recent fixtures found for team {team_id}")
            return None

        return fixtures

    async def find_next_fixture_for_team(
        self,
        team_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Find next scheduled match for a team.

        Args:
            team_id: Team ID

        Returns:
            Fixture data or None

        Examples:
            >>> fixture = await resolver.find_next_fixture_for_team(85)
            >>> fixture['fixture']['status']['short']
            'NS'  # Not Started
        """
        logger.info(f"Finding next fixture for team {team_id}")

        result = await execute_tool(
            self.api_client,
            "fixtures_search",
            {"team_id": team_id, "next": 1},
        )

        fixtures = result.get("fixtures", []) if isinstance(result, dict) else []

        if not fixtures:
            logger.warning(f"No upcoming fixture found for team {team_id}")
            return None

        return fixtures[0]
