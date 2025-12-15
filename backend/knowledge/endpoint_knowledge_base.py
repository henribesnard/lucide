"""
Endpoint Knowledge Base for API-Football.

This module will contain comprehensive metadata about all API-Football endpoints,
including their use cases, parameters, caching strategies, and enrichment capabilities.

To be implemented in Phase 1.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class DataFreshness(Enum):
    """Freshness level of the data returned by an endpoint."""
    STATIC = "static"           # Reference data (countries, leagues)
    SEASONAL = "seasonal"       # Season-bound data
    MATCH_BOUND = "match_bound" # Match-related data
    LIVE = "live"              # Real-time data


class CacheStrategy(Enum):
    """Caching strategy for endpoint data."""
    INDEFINITE = "indefinite"
    LONG_TTL = "long_ttl"      # 1 day
    SHORT_TTL = "short_ttl"    # 10 min
    NO_CACHE = "no_cache"
    MATCH_STATUS = "match_status"  # Adaptive based on match status


@dataclass
class EndpointMetadata:
    """Metadata about an API-Football endpoint."""
    name: str
    path: str
    description: str
    use_cases: List[str]
    required_params: List[str]
    optional_params: List[str]
    data_returned: List[str]
    is_enriched: bool = False
    enriched_data: List[str] = field(default_factory=list)
    freshness: DataFreshness = DataFreshness.MATCH_BOUND
    cache_strategy: CacheStrategy = CacheStrategy.SHORT_TTL
    can_replace: List[str] = field(default_factory=list)
    api_cost: int = 1


class EndpointKnowledgeBase:
    """
    Central knowledge base for API-Football endpoints.

    Contains comprehensive metadata for 50+ endpoints including:
    - Use cases and descriptions
    - Parameters (required and optional)
    - Data returned
    - Enrichment capabilities
    - Cache strategies
    """

    def __init__(self):
        self.endpoints: Dict[str, EndpointMetadata] = {}
        self._initialize_endpoints()

    def get_endpoint(self, name: str) -> Optional[EndpointMetadata]:
        """Get endpoint metadata by name."""
        return self.endpoints.get(name)

    def search_by_use_case(self, use_case: str) -> List[EndpointMetadata]:
        """
        Search endpoints by use case.

        Args:
            use_case: Use case description (e.g., "get match score", "team statistics")

        Returns:
            List of matching endpoints, sorted by relevance
        """
        use_case_lower = use_case.lower()
        matching_endpoints = []

        for endpoint in self.endpoints.values():
            # Check if use case matches any of the endpoint's use cases
            for endpoint_use_case in endpoint.use_cases:
                if use_case_lower in endpoint_use_case.lower():
                    matching_endpoints.append(endpoint)
                    break

        return matching_endpoints

    def get_all_endpoints(self) -> List[EndpointMetadata]:
        """Get all endpoints in the knowledge base."""
        return list(self.endpoints.values())

    def get_enriched_endpoints(self) -> List[EndpointMetadata]:
        """Get all enriched endpoints that can replace multiple calls."""
        return [ep for ep in self.endpoints.values() if ep.is_enriched]

    def calculate_cache_ttl(self, endpoint_name: str, match_status: Optional[str] = None) -> int:
        """
        Calculate appropriate cache TTL for an endpoint.

        Args:
            endpoint_name: Name of the endpoint
            match_status: Optional match status (NS, LIVE, FT, etc.)

        Returns:
            TTL in seconds
        """
        endpoint = self.get_endpoint(endpoint_name)
        if not endpoint:
            return 300  # Default 5 minutes

        # Override based on match status if applicable
        if match_status:
            if match_status in ['FT', 'AET', 'PEN', 'CANC', 'ABD', 'AWD', 'WO']:
                # Finished matches: cache indefinitely
                return -1  # -1 = indefinite
            elif match_status in ['LIVE', '1H', '2H', 'HT', 'ET', 'BT', 'P']:
                # Live matches: short TTL
                return 30  # 30 seconds
            elif match_status in ['NS', 'TBD', 'PST', 'SUSP', 'INT']:
                # Not started/postponed: medium TTL
                return 600  # 10 minutes

        # Use endpoint's cache strategy
        if endpoint.cache_strategy == CacheStrategy.INDEFINITE:
            return -1  # Indefinite
        elif endpoint.cache_strategy == CacheStrategy.LONG_TTL:
            return 86400  # 1 day
        elif endpoint.cache_strategy == CacheStrategy.SHORT_TTL:
            return 600  # 10 minutes
        elif endpoint.cache_strategy == CacheStrategy.NO_CACHE:
            return 0  # No cache
        elif endpoint.cache_strategy == CacheStrategy.MATCH_STATUS:
            # Default for match-bound data
            return 600  # 10 minutes

        return 300  # Default 5 minutes

    def _initialize_endpoints(self):
        """Initialize all API-Football endpoints with metadata."""
        # This will be populated with all 50+ endpoints
        self._add_fixtures_endpoints()
        self._add_prediction_endpoints()
        self._add_team_endpoints()
        self._add_player_endpoints()
        self._add_league_endpoints()
        self._add_standings_endpoints()
        self._add_search_endpoints()
        self._add_static_endpoints()
        self._add_odds_endpoints()
        self._add_transfer_endpoints()

    def _add_endpoint(self, endpoint: EndpointMetadata):
        """Add an endpoint to the knowledge base."""
        self.endpoints[endpoint.name] = endpoint

    def _add_fixtures_endpoints(self):
        """Add fixtures-related endpoints."""
        # Enriched endpoint - THE MOST IMPORTANT OPTIMIZATION
        self._add_endpoint(EndpointMetadata(
            name="fixtures_by_id",
            path="/fixtures",
            description="Get complete fixture details including events, lineups, statistics, and players",
            use_cases=[
                "Get match score",
                "Get match events (goals, cards, substitutions)",
                "Get lineups and formations",
                "Get match statistics (possession, shots, passes)",
                "Get player statistics for a match",
                "Get comprehensive match information"
            ],
            required_params=["id"],
            optional_params=["timezone"],
            data_returned=[
                "fixture", "league", "teams", "goals", "score",
                "events", "lineups", "statistics", "players"
            ],
            is_enriched=True,
            enriched_data=["events", "lineups", "statistics", "players"],
            freshness=DataFreshness.MATCH_BOUND,
            cache_strategy=CacheStrategy.MATCH_STATUS,
            can_replace=[
                "fixtures_basic",
                "fixtures_events",
                "fixtures_lineups",
                "fixtures_statistics",
                "fixtures_players"
            ],
            api_cost=1
        ))

        self._add_endpoint(EndpointMetadata(
            name="fixtures_live",
            path="/fixtures",
            description="Get all live fixtures with scores and basic events",
            use_cases=[
                "Get all live matches",
                "Get current scores of all ongoing matches",
                "Monitor live matches"
            ],
            required_params=["live"],
            optional_params=["league", "season", "timezone"],
            data_returned=["fixtures", "scores", "events", "elapsed_time"],
            is_enriched=False,
            freshness=DataFreshness.LIVE,
            cache_strategy=CacheStrategy.NO_CACHE,
            api_cost=1
        ))

        self._add_endpoint(EndpointMetadata(
            name="fixtures_search",
            path="/fixtures",
            description="Search fixtures by team, date, league, or round",
            use_cases=[
                "Find matches for a team",
                "Get team's last N matches",
                "Get team's next N matches",
                "Get matches on a specific date",
                "Get matches in a specific round"
            ],
            required_params=[],
            optional_params=[
                "id", "ids", "live", "date", "league", "season", "team",
                "last", "next", "from", "to", "round", "status", "timezone"
            ],
            data_returned=["fixtures", "teams", "league", "score"],
            is_enriched=False,
            freshness=DataFreshness.MATCH_BOUND,
            cache_strategy=CacheStrategy.SHORT_TTL,
            api_cost=1
        ))

        self._add_endpoint(EndpointMetadata(
            name="fixtures_headtohead",
            path="/fixtures/headtohead",
            description="Get head-to-head matches between two teams",
            use_cases=[
                "Get historical matches between two teams",
                "Analyze head-to-head statistics",
                "Compare team performances in direct matches"
            ],
            required_params=["h2h"],
            optional_params=["date", "league", "season", "last", "next", "from", "to", "status", "timezone"],
            data_returned=["fixtures", "scores", "teams"],
            is_enriched=False,
            freshness=DataFreshness.STATIC,
            cache_strategy=CacheStrategy.LONG_TTL,
            api_cost=1
        ))

        # Individual data endpoints (replaced by fixtures_by_id)
        self._add_endpoint(EndpointMetadata(
            name="fixtures_events",
            path="/fixtures/events",
            description="Get match events only (goals, cards, substitutions) - PREFER fixtures_by_id",
            use_cases=["Get match events separately"],
            required_params=["fixture"],
            optional_params=["team", "player", "type"],
            data_returned=["events"],
            is_enriched=False,
            freshness=DataFreshness.MATCH_BOUND,
            cache_strategy=CacheStrategy.MATCH_STATUS,
            api_cost=1
        ))

        self._add_endpoint(EndpointMetadata(
            name="fixtures_lineups",
            path="/fixtures/lineups",
            description="Get match lineups only - PREFER fixtures_by_id",
            use_cases=["Get match lineups separately"],
            required_params=["fixture"],
            optional_params=["team", "player"],
            data_returned=["lineups", "formations", "substitutes"],
            is_enriched=False,
            freshness=DataFreshness.MATCH_BOUND,
            cache_strategy=CacheStrategy.MATCH_STATUS,
            api_cost=1
        ))

        self._add_endpoint(EndpointMetadata(
            name="fixtures_statistics",
            path="/fixtures/statistics",
            description="Get match statistics only - PREFER fixtures_by_id",
            use_cases=["Get match statistics separately"],
            required_params=["fixture"],
            optional_params=["team"],
            data_returned=["statistics"],
            is_enriched=False,
            freshness=DataFreshness.MATCH_BOUND,
            cache_strategy=CacheStrategy.MATCH_STATUS,
            api_cost=1
        ))

        self._add_endpoint(EndpointMetadata(
            name="fixtures_players",
            path="/fixtures/players",
            description="Get player statistics for a match - PREFER fixtures_by_id",
            use_cases=["Get player statistics separately"],
            required_params=["fixture"],
            optional_params=["team"],
            data_returned=["player_statistics"],
            is_enriched=False,
            freshness=DataFreshness.MATCH_BOUND,
            cache_strategy=CacheStrategy.MATCH_STATUS,
            api_cost=1
        ))

    def _add_prediction_endpoints(self):
        """Add prediction-related endpoints."""
        # Enriched endpoint - CRITICAL OPTIMIZATION for upcoming matches
        self._add_endpoint(EndpointMetadata(
            name="predictions",
            path="/predictions",
            description="Get predictions with form, h2h, and comparisons included",
            use_cases=[
                "Get match predictions",
                "Analyze team form (last 5 games)",
                "Get head-to-head history",
                "Compare team statistics",
                "Get betting advice",
                "Analyze match probabilities"
            ],
            required_params=["fixture"],
            optional_params=[],
            data_returned=[
                "predictions", "winner", "goals", "advice", "percent",
                "last_5_home", "last_5_away", "league_stats_home", "league_stats_away",
                "h2h", "comparison"
            ],
            is_enriched=True,
            enriched_data=["last_5", "league_stats", "h2h", "comparison"],
            freshness=DataFreshness.MATCH_BOUND,
            cache_strategy=CacheStrategy.SHORT_TTL,
            can_replace=[
                "team_last_matches",
                "fixtures_headtohead",
                "team_statistics",
                "team_comparison"
            ],
            api_cost=1
        ))

    def _add_team_endpoints(self):
        """Add team-related endpoints."""
        self._add_endpoint(EndpointMetadata(
            name="teams_search",
            path="/teams",
            description="Search teams by name, league, country, or get team information",
            use_cases=[
                "Search team by name",
                "Get team details",
                "Find team ID",
                "Get team venue information"
            ],
            required_params=[],
            optional_params=["id", "name", "league", "season", "country", "code", "venue", "search"],
            data_returned=["team", "venue"],
            is_enriched=False,
            freshness=DataFreshness.STATIC,
            cache_strategy=CacheStrategy.INDEFINITE,
            api_cost=1
        ))

        self._add_endpoint(EndpointMetadata(
            name="team_statistics",
            path="/teams/statistics",
            description="Get complete team statistics for a season",
            use_cases=[
                "Get team season statistics",
                "Analyze team form",
                "Get win/draw/loss record",
                "Get goals scored/conceded",
                "Get home/away performance",
                "Get clean sheets statistics"
            ],
            required_params=["team", "season", "league"],
            optional_params=["date"],
            data_returned=[
                "form", "fixtures_played", "wins", "draws", "losses",
                "goals_for", "goals_against", "clean_sheet", "failed_to_score",
                "biggest_wins", "biggest_losses", "winning_streak"
            ],
            is_enriched=False,
            freshness=DataFreshness.SEASONAL,
            cache_strategy=CacheStrategy.SHORT_TTL,
            api_cost=1
        ))

        self._add_endpoint(EndpointMetadata(
            name="team_seasons",
            path="/teams/seasons",
            description="Get available seasons for a team",
            use_cases=["Get team's available seasons"],
            required_params=["team"],
            optional_params=[],
            data_returned=["seasons"],
            is_enriched=False,
            freshness=DataFreshness.STATIC,
            cache_strategy=CacheStrategy.LONG_TTL,
            api_cost=1
        ))

        self._add_endpoint(EndpointMetadata(
            name="team_countries",
            path="/teams/countries",
            description="Get available countries for teams",
            use_cases=["Get list of countries with teams"],
            required_params=[],
            optional_params=[],
            data_returned=["countries"],
            is_enriched=False,
            freshness=DataFreshness.STATIC,
            cache_strategy=CacheStrategy.INDEFINITE,
            api_cost=1
        ))

    def _add_player_endpoints(self):
        """Add player-related endpoints."""
        self._add_endpoint(EndpointMetadata(
            name="players_search",
            path="/players",
            description="Search players by name, team, league, or season",
            use_cases=[
                "Search player by name",
                "Find player ID",
                "Get player details",
                "Get players in a team",
                "Get players in a league"
            ],
            required_params=[],
            optional_params=["id", "team", "league", "season", "search", "page"],
            data_returned=["player", "statistics"],
            is_enriched=False,
            freshness=DataFreshness.STATIC,
            cache_strategy=CacheStrategy.LONG_TTL,
            api_cost=1
        ))

        self._add_endpoint(EndpointMetadata(
            name="players_seasons",
            path="/players/seasons",
            description="Get available seasons for a player",
            use_cases=[
                "Get player's career seasons",
                "Find which seasons player has data for"
            ],
            required_params=["player"],
            optional_params=[],
            data_returned=["seasons"],
            is_enriched=False,
            freshness=DataFreshness.STATIC,
            cache_strategy=CacheStrategy.LONG_TTL,
            api_cost=1
        ))

        self._add_endpoint(EndpointMetadata(
            name="players_statistics",
            path="/players",
            description="Get detailed player statistics for a season",
            use_cases=[
                "Get player season statistics",
                "Get player goals and assists",
                "Get player ratings and performance",
                "Get player appearances",
                "Analyze player form"
            ],
            required_params=["id", "season"],
            optional_params=["team", "league"],
            data_returned=[
                "player", "statistics", "games", "goals", "assists",
                "shots", "passes", "dribbles", "tackles", "rating"
            ],
            is_enriched=False,
            freshness=DataFreshness.SEASONAL,
            cache_strategy=CacheStrategy.SHORT_TTL,
            api_cost=1
        ))

        self._add_endpoint(EndpointMetadata(
            name="players_squads",
            path="/players/squads",
            description="Get team squad (all players in a team)",
            use_cases=[
                "Get all players in a team",
                "Get squad list",
                "Get team roster"
            ],
            required_params=["team"],
            optional_params=[],
            data_returned=["team", "players"],
            is_enriched=False,
            freshness=DataFreshness.SEASONAL,
            cache_strategy=CacheStrategy.SHORT_TTL,
            api_cost=1
        ))

        self._add_endpoint(EndpointMetadata(
            name="players_topscorers",
            path="/players/topscorers",
            description="Get top scorers in a league/season",
            use_cases=[
                "Get league top scorers",
                "Get highest goal scorers",
                "Get top 20 scorers"
            ],
            required_params=["league", "season"],
            optional_params=[],
            data_returned=["player", "statistics", "goals"],
            is_enriched=False,
            freshness=DataFreshness.SEASONAL,
            cache_strategy=CacheStrategy.SHORT_TTL,
            api_cost=1
        ))

        self._add_endpoint(EndpointMetadata(
            name="players_topassists",
            path="/players/topassists",
            description="Get top assist providers in a league/season",
            use_cases=[
                "Get league top assists",
                "Get most assists",
                "Get top 20 assist providers"
            ],
            required_params=["league", "season"],
            optional_params=[],
            data_returned=["player", "statistics", "assists"],
            is_enriched=False,
            freshness=DataFreshness.SEASONAL,
            cache_strategy=CacheStrategy.SHORT_TTL,
            api_cost=1
        ))

        self._add_endpoint(EndpointMetadata(
            name="players_topredcards",
            path="/players/topredcards",
            description="Get players with most red cards in a league/season",
            use_cases=[
                "Get most red cards",
                "Get disciplinary statistics"
            ],
            required_params=["league", "season"],
            optional_params=[],
            data_returned=["player", "statistics", "cards"],
            is_enriched=False,
            freshness=DataFreshness.SEASONAL,
            cache_strategy=CacheStrategy.SHORT_TTL,
            api_cost=1
        ))

        self._add_endpoint(EndpointMetadata(
            name="players_topyellowcards",
            path="/players/topyellowcards",
            description="Get players with most yellow cards in a league/season",
            use_cases=[
                "Get most yellow cards",
                "Get booking statistics"
            ],
            required_params=["league", "season"],
            optional_params=[],
            data_returned=["player", "statistics", "cards"],
            is_enriched=False,
            freshness=DataFreshness.SEASONAL,
            cache_strategy=CacheStrategy.SHORT_TTL,
            api_cost=1
        ))

    def _add_league_endpoints(self):
        """Add league-related endpoints."""
        self._add_endpoint(EndpointMetadata(
            name="leagues_search",
            path="/leagues",
            description="Search leagues by name, country, or get league details",
            use_cases=[
                "Search league by name",
                "Find league ID",
                "Get league details",
                "Get leagues by country",
                "Get current leagues"
            ],
            required_params=[],
            optional_params=["id", "name", "country", "code", "season", "team", "type", "current", "search"],
            data_returned=["league", "country", "seasons"],
            is_enriched=False,
            freshness=DataFreshness.STATIC,
            cache_strategy=CacheStrategy.LONG_TTL,
            api_cost=1
        ))

        self._add_endpoint(EndpointMetadata(
            name="leagues_seasons",
            path="/leagues/seasons",
            description="Get all available seasons",
            use_cases=[
                "Get available seasons",
                "Get list of all seasons"
            ],
            required_params=[],
            optional_params=[],
            data_returned=["seasons"],
            is_enriched=False,
            freshness=DataFreshness.STATIC,
            cache_strategy=CacheStrategy.INDEFINITE,
            api_cost=1
        ))

    def _add_standings_endpoints(self):
        """Add standings-related endpoints."""
        self._add_endpoint(EndpointMetadata(
            name="standings",
            path="/standings",
            description="Get league standings/table",
            use_cases=[
                "Get league table",
                "Get standings",
                "Get team rankings",
                "Get points table",
                "Get team position in league"
            ],
            required_params=["league", "season"],
            optional_params=["team"],
            data_returned=[
                "league", "standings", "rank", "team", "points",
                "goals_diff", "form", "played", "win", "draw", "lose"
            ],
            is_enriched=False,
            freshness=DataFreshness.SEASONAL,
            cache_strategy=CacheStrategy.SHORT_TTL,
            api_cost=1
        ))

    def _add_search_endpoints(self):
        """Add general search endpoints."""
        # Most search functionality is covered by specific endpoints
        # (teams_search, players_search, leagues_search)
        pass

    def _add_static_endpoints(self):
        """Add static data endpoints."""
        self._add_endpoint(EndpointMetadata(
            name="countries",
            path="/countries",
            description="Get all available countries",
            use_cases=[
                "Get list of countries",
                "Get country codes",
                "Find country information"
            ],
            required_params=[],
            optional_params=["name", "code", "search"],
            data_returned=["countries", "name", "code", "flag"],
            is_enriched=False,
            freshness=DataFreshness.STATIC,
            cache_strategy=CacheStrategy.INDEFINITE,
            api_cost=1
        ))

        self._add_endpoint(EndpointMetadata(
            name="timezones",
            path="/timezone",
            description="Get all available timezones",
            use_cases=[
                "Get list of timezones",
                "Get timezone information"
            ],
            required_params=[],
            optional_params=[],
            data_returned=["timezones"],
            is_enriched=False,
            freshness=DataFreshness.STATIC,
            cache_strategy=CacheStrategy.INDEFINITE,
            api_cost=1
        ))

        self._add_endpoint(EndpointMetadata(
            name="venues",
            path="/venues",
            description="Get stadium/venue information",
            use_cases=[
                "Get stadium details",
                "Search venue by name",
                "Get venue capacity and location"
            ],
            required_params=[],
            optional_params=["id", "name", "city", "country", "search"],
            data_returned=["venue", "name", "address", "city", "capacity", "surface", "image"],
            is_enriched=False,
            freshness=DataFreshness.STATIC,
            cache_strategy=CacheStrategy.INDEFINITE,
            api_cost=1
        ))

    def _add_odds_endpoints(self):
        """Add betting odds endpoints."""
        self._add_endpoint(EndpointMetadata(
            name="odds_live",
            path="/odds/live",
            description="Get live betting odds",
            use_cases=[
                "Get current odds for live matches",
                "Get live betting markets"
            ],
            required_params=[],
            optional_params=["fixture", "league", "bet"],
            data_returned=["fixture", "odds", "bookmakers", "bets", "values"],
            is_enriched=False,
            freshness=DataFreshness.LIVE,
            cache_strategy=CacheStrategy.NO_CACHE,
            api_cost=1
        ))

        self._add_endpoint(EndpointMetadata(
            name="odds_fixture",
            path="/odds",
            description="Get pre-match odds for a fixture",
            use_cases=[
                "Get match odds",
                "Get betting markets",
                "Compare bookmaker odds",
                "Get betting advice"
            ],
            required_params=["fixture"],
            optional_params=["league", "season", "date", "timezone", "page", "bookmaker", "bet"],
            data_returned=["fixture", "odds", "bookmakers", "bets", "values"],
            is_enriched=False,
            freshness=DataFreshness.MATCH_BOUND,
            cache_strategy=CacheStrategy.SHORT_TTL,
            api_cost=1
        ))

        self._add_endpoint(EndpointMetadata(
            name="odds_bookmakers",
            path="/odds/bookmakers",
            description="Get list of available bookmakers",
            use_cases=[
                "Get all bookmakers",
                "Get bookmaker IDs"
            ],
            required_params=[],
            optional_params=["id", "search"],
            data_returned=["bookmakers"],
            is_enriched=False,
            freshness=DataFreshness.STATIC,
            cache_strategy=CacheStrategy.INDEFINITE,
            api_cost=1
        ))

        self._add_endpoint(EndpointMetadata(
            name="odds_bets",
            path="/odds/bets",
            description="Get list of available bet types",
            use_cases=[
                "Get all bet types",
                "Get betting market IDs"
            ],
            required_params=[],
            optional_params=["id", "search"],
            data_returned=["bets"],
            is_enriched=False,
            freshness=DataFreshness.STATIC,
            cache_strategy=CacheStrategy.INDEFINITE,
            api_cost=1
        ))

    def _add_transfer_endpoints(self):
        """Add transfer and injury endpoints."""
        self._add_endpoint(EndpointMetadata(
            name="transfers",
            path="/transfers",
            description="Get player transfers",
            use_cases=[
                "Get player transfer history",
                "Get team transfers",
                "Get summer/winter transfers"
            ],
            required_params=[],
            optional_params=["player", "team"],
            data_returned=["player", "transfers", "date", "team_in", "team_out", "type"],
            is_enriched=False,
            freshness=DataFreshness.SEASONAL,
            cache_strategy=CacheStrategy.LONG_TTL,
            api_cost=1
        ))

        self._add_endpoint(EndpointMetadata(
            name="injuries",
            path="/injuries",
            description="Get player injuries",
            use_cases=[
                "Get injured players",
                "Get team injury list",
                "Get player injury history",
                "Check player availability"
            ],
            required_params=[],
            optional_params=["fixture", "league", "season", "team", "player", "date", "timezone"],
            data_returned=["player", "team", "fixture", "type", "reason"],
            is_enriched=False,
            freshness=DataFreshness.MATCH_BOUND,
            cache_strategy=CacheStrategy.SHORT_TTL,
            api_cost=1
        ))

        self._add_endpoint(EndpointMetadata(
            name="sidelined",
            path="/sidelined",
            description="Get sidelined players (injuries, suspensions, etc.)",
            use_cases=[
                "Get unavailable players",
                "Get suspended players",
                "Get complete unavailability list"
            ],
            required_params=[],
            optional_params=["player", "coach"],
            data_returned=["player", "type", "start", "end"],
            is_enriched=False,
            freshness=DataFreshness.MATCH_BOUND,
            cache_strategy=CacheStrategy.SHORT_TTL,
            api_cost=1
        ))
