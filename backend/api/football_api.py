import httpx
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from backend.utils.status_mapping import is_valid_status

logger = logging.getLogger(__name__)


class FootballAPIError(Exception):
    """Custom error to surface API-Football issues with context."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class FootballAPIClient:
    """
    Client complet pour l'API Football v3
    Documentation: https://www.api-football.com/documentation-v3
    """

    def __init__(self, api_key: str, base_url: str = "https://v3.football.api-sports.io"):
        self.base_url = base_url
        self.headers = {
            # API-Football expects the x-apisports-key header (not x-rapidapi-key) per official docs.
            "x-apisports-key": api_key,
        }
        self.client = httpx.AsyncClient(timeout=30.0)
        # Small caches for low-churn referentials to reduce repeated calls
        self._cache_timezones: Optional[List[str]] = None
        self._cache_seasons: Optional[List[int]] = None
        self._cache_countries: Dict[str, List[Dict[str, Any]]] = {}
        self._cache_team_countries: Optional[List[Dict[str, Any]]] = None

    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Perform an HTTP request to API-Football and return the parsed payload."""
        params = params or {}
        try:
            url = f"{self.base_url}/{endpoint}"
            logger.info(f"API Request: {endpoint} with params: {params}")

            response = await self.client.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            try:
                data = response.json()
            except Exception as exc:
                logger.error("Invalid JSON payload from API-Football: %s", exc)
                raise FootballAPIError("Invalid JSON payload from API-Football", status_code=response.status_code) from exc

            if data.get("errors"):
                logger.error("API Error on %s: %s", endpoint, data["errors"])
                raise FootballAPIError(f"API Error: {data['errors']}", status_code=response.status_code)

            logger.info("API Response: %s results", len(data.get("response", [])))
            return data

        except httpx.TimeoutException as exc:
            logger.error("API-Football timeout on %s: %s", endpoint, exc)
            raise FootballAPIError("API-Football timeout reached", status_code=None) from exc
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text
            logger.error("HTTP status error on %s: %s - %s", endpoint, exc.response.status_code, detail)
            raise FootballAPIError(
                f"HTTP {exc.response.status_code} on {endpoint}: {detail}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.HTTPError as exc:
            logger.error("HTTP error on %s: %s", endpoint, exc)
            raise FootballAPIError("HTTP error while calling API-Football") from exc

    # ==========================================
    # TIMEZONE
    # ==========================================
    async def get_timezones(self) -> List[str]:
        """Return all available timezones."""
        if hasattr(self, "_cache_timezones") and self._cache_timezones is not None:
            return self._cache_timezones
        data = await self._make_request("timezone")
        self._cache_timezones = data.get("response", [])
        return self._cache_timezones

    # ==========================================
    # SEASONS
    # ==========================================
    async def get_seasons(self) -> List[int]:
        """Return all available seasons."""
        if hasattr(self, "_cache_seasons") and self._cache_seasons is not None:
            return self._cache_seasons
        data = await self._make_request("seasons")
        self._cache_seasons = data.get("response", [])
        return self._cache_seasons

    # ==========================================
    # COUNTRIES
    # ==========================================
    async def get_countries(
        self, name: Optional[str] = None, code: Optional[str] = None, search: Optional[str] = None
    ) -> List[Dict]:
        """Return the list of countries."""
        params = {}
        if name:
            params["name"] = name
        if code:
            params["code"] = code
        if search:
            params["search"] = search

        cache_key = f"{name or ''}|{code or ''}|{search or ''}"
        if hasattr(self, "_cache_countries") and cache_key in self._cache_countries:
            return self._cache_countries[cache_key]

        data = await self._make_request("countries", params)
        response = data.get("response", [])
        if hasattr(self, "_cache_countries"):
            self._cache_countries[cache_key] = response
        return response

    # ==========================================
    # LEAGUES
    # ==========================================

    async def get_leagues(
        self,
        league_id: Optional[int] = None,
        name: Optional[str] = None,
        country: Optional[str] = None,
        season: Optional[int] = None,
        team_id: Optional[int] = None,
        code: Optional[str] = None,
        type_: Optional[str] = None,
        current: Optional[bool] = None,
        search: Optional[str] = None,
        last: Optional[int] = None,
    ) -> List[Dict]:
        """
        Recupere les informations des ligues.

        Args:
            league_id: ID de la ligue
            name: Nom de la ligue
            country: Pays de la ligue
            season: Saison
            team_id: ID de l'equipe
            code: Code pays (ex: GB)
            type_: Type de competition (league/cup)
            current: Saison en cours uniquement
            search: Texte de recherche
            last: Dernieres ligues ajoutees (nb)
        """
        params = {}
        if league_id:
            params["id"] = league_id
        if name:
            params["name"] = name
        if country:
            params["country"] = country
        if season:
            params["season"] = season
        if team_id:
            params["team"] = team_id
        if code:
            params["code"] = code
        if type_:
            params["type"] = type_
        if current is not None:
            params["current"] = "true" if current else "false"
        if search:
            params["search"] = search
        if last:
            params["last"] = last

        data = await self._make_request("leagues", params)
        return data.get("response", [])


    # ==========================================
    # TEAMS
    # ==========================================

    async def get_teams(
        self,
        team_id: Optional[int] = None,
        name: Optional[str] = None,
        league_id: Optional[int] = None,
        season: Optional[int] = None,
        country: Optional[str] = None,
        code: Optional[str] = None,
        venue_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[Dict]:
        """
        Recupere les informations des equipes.

        Args:
            team_id: ID de l'equipe
            name: Nom de l'equipe
            league_id: ID de la ligue
            season: Saison
            country: Pays
            code: Code equipe (ex: PSG)
            venue_id: ID du stade
            search: Recherche textuelle
        """
        params = {}
        if team_id:
            params["id"] = team_id
        if name:
            params["name"] = name
        if league_id:
            params["league"] = league_id
        if season:
            params["season"] = season
        if country:
            params["country"] = country
        if code:
            params["code"] = code
        if venue_id:
            params["venue"] = venue_id
        if search:
            params["search"] = search

        data = await self._make_request("teams", params)
        return data.get("response", [])


    async def get_team_statistics(
        self,
        team_id: int,
        season: int,
        league_id: int,
        date: Optional[str] = None
    ) -> Dict:
        """
        Return detailed team statistics for a season and league.

        Args:
            team_id: ID of the team
            season: Saison
            league_id: ID de la ligue
            date: Specific date (YYYY-MM-DD)
        """
        params = {
            "team": team_id,
            "season": season,
            "league": league_id
        }
        if date:
            params["date"] = date

        data = await self._make_request("teams/statistics", params)
        return data.get("response", {})

    async def get_team_seasons(self, team_id: int) -> List[int]:
        """List available seasons for a team."""
        params = {"team": team_id}
        data = await self._make_request("teams/seasons", params)
        return data.get("response", [])

    async def get_team_countries(self) -> List[Dict]:
        """List countries that have teams available."""
        if hasattr(self, "_cache_team_countries") and self._cache_team_countries is not None:
            return self._cache_team_countries
        data = await self._make_request("teams/countries")
        self._cache_team_countries = data.get("response", [])
        return self._cache_team_countries

    # ==========================================
    # VENUES (STADES)
    # ==========================================
    async def get_venues(
        self,
        venue_id: Optional[int] = None,
        name: Optional[str] = None,
        city: Optional[str] = None,
        country: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict]:
        """
        Return venue information.

        Args:
            venue_id: ID du stade
            name: Nom du stade
            city: Ville
            country: Pays
            search: Recherche textuelle
        """
        params = {}
        if venue_id:
            params["id"] = venue_id
        if name:
            params["name"] = name
        if city:
            params["city"] = city
        if country:
            params["country"] = country
        if search:
            params["search"] = search

        data = await self._make_request("venues", params)
        return data.get("response", [])

    # ==========================================
    # STANDINGS (CLASSEMENTS)
    # ==========================================
    async def get_standings(
        self,
        season: int,
        league_id: Optional[int] = None,
        team_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Return standings.

        Args:
            season: Saison
            league_id: ID de la ligue
            team_id: ID of the team
        """
        params = {"season": season}
        if league_id:
            params["league"] = league_id
        if team_id:
            params["team"] = team_id

        data = await self._make_request("standings", params)
        return data.get("response", [])

    # ==========================================
    # FIXTURES (MATCHS)
    # ==========================================
    async def get_fixtures(
        self,
        fixture_id: Optional[int] = None,
        league_id: Optional[int] = None,
        season: Optional[int] = None,
        team_id: Optional[int] = None,
        date: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        round_: Optional[str] = None,
        status: Optional[str] = None,
        venue_id: Optional[int] = None,
        timezone: Optional[str] = None,
        live: Optional[str] = None,
        last: Optional[int] = None,
        next: Optional[int] = None
    ) -> List[Dict]:
        """
        Return fixtures (matches).

        Args:
            fixture_id: ID du match
            league_id: ID de la ligue
            season: Saison
            team_id: ID of the team
            date: Date (YYYY-MM-DD)
            from_date: Start date
            to_date: Date de fin
            round_: Round/Matchday
            status: Statut (TBD, NS, 1H, HT, 2H, ET, P, FT, AET, PEN, BT, SUSP, INT, PST, CANC, ABD, AWD, WO, LIVE)
            venue_id: ID du stade
            timezone: Timezone
            live: "all" pour tous les matchs en direct
            last: Last N fixtures for a team
            next: Next N fixtures for a team
        """
        params = {}
        if fixture_id:
            params["id"] = fixture_id
        if league_id:
            params["league"] = league_id
        if season:
            params["season"] = season
        if team_id:
            params["team"] = team_id
        if date:
            params["date"] = date
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        if round_:
            params["round"] = round_
        if status:
            status_value = status.upper()
            if not is_valid_status(status_value):
                raise FootballAPIError(f"Invalid match status code: {status}")
            params["status"] = status_value
        if venue_id:
            params["venue"] = venue_id
        if timezone:
            params["timezone"] = timezone
        if live:
            params["live"] = live
        if last:
            params["last"] = last
        if next:
            params["next"] = next

        data = await self._make_request("fixtures", params)
        return data.get("response", [])

    async def get_fixture_rounds(self, league_id: int, season: int, current: bool = False) -> List[str]:
        """
        Return rounds for a league.

        Args:
            league_id: ID de la ligue
            season: Saison
            current: True to return only the current round
        """
        params = {
            "league": league_id,
            "season": season
        }
        if current:
            params["current"] = "true"

        data = await self._make_request("fixtures/rounds", params)
        return data.get("response", [])

    async def get_head_to_head(
        self,
        team1_id: int,
        team2_id: int,
        last: Optional[int] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        league_id: Optional[int] = None,
        season: Optional[int] = None,
        status: Optional[str] = None,
        venue_id: Optional[int] = None,
        timezone: Optional[str] = None
    ) -> List[Dict]:
        """
        Return head-to-head fixtures between two teams (H2H).

        Args:
            team1_id: ID of the first team
            team2_id: ID of the second team
            last: Nombre de derniers matchs
            from_date: Start date
            to_date: Date de fin
            league_id: ID de la ligue
            season: Saison
            status: Statut
            venue_id: ID du stade
            timezone: Timezone
        """
        params = {"h2h": f"{team1_id}-{team2_id}"}
        if last:
            params["last"] = last
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        if league_id:
            params["league"] = league_id
        if season:
            params["season"] = season
        if status:
            status_value = status.upper()
            if not is_valid_status(status_value):
                raise FootballAPIError(f"Invalid match status code: {status}")
            params["status"] = status_value
        if venue_id:
            params["venue"] = venue_id
        if timezone:
            params["timezone"] = timezone

        data = await self._make_request("fixtures/headtohead", params)
        return data.get("response", [])

    async def get_fixture_statistics(self, fixture_id: int, team_id: Optional[int] = None) -> List[Dict]:
        """
        Return statistics for a fixture.

        Args:
            fixture_id: ID du match
            team_id: ID of the team (optional)
        """
        params = {"fixture": fixture_id}
        if team_id:
            params["team"] = team_id

        data = await self._make_request("fixtures/statistics", params)
        return data.get("response", [])

    async def get_fixture_events(
        self,
        fixture_id: int,
        team_id: Optional[int] = None,
        player_id: Optional[int] = None,
        type_: Optional[str] = None
    ) -> List[Dict]:
        """
        Return events for a fixture (goals, cards, etc.).

        Args:
            fixture_id: ID du match
            team_id: ID of the team
            player_id: ID du joueur
            type_: Event type (Goal, Card, subst, Var)
        """
        params = {"fixture": fixture_id}
        if team_id:
            params["team"] = team_id
        if player_id:
            params["player"] = player_id
        if type_:
            params["type"] = type_

        data = await self._make_request("fixtures/events", params)
        return data.get("response", [])

    async def get_fixture_lineups(self, fixture_id: int, team_id: Optional[int] = None) -> List[Dict]:
        """
        Return lineups for a fixture.

        Args:
            fixture_id: ID du match
            team_id: ID of the team (optional)
        """
        params = {"fixture": fixture_id}
        if team_id:
            params["team"] = team_id

        data = await self._make_request("fixtures/lineups", params)
        return data.get("response", [])

    async def get_fixture_player_statistics(self, fixture_id: int, team_id: Optional[int] = None) -> List[Dict]:
        """
        Return player statistics for a fixture.

        Args:
            fixture_id: ID du match
            team_id: ID of the team (optional)
        """
        params = {"fixture": fixture_id}
        if team_id:
            params["team"] = team_id

        data = await self._make_request("fixtures/players", params)
        return data.get("response", [])

    # ==========================================
    # INJURIES (BLESSURES)
    # ==========================================
    async def get_injuries(
        self,
        league_id: Optional[int] = None,
        season: Optional[int] = None,
        fixture_id: Optional[int] = None,
        team_id: Optional[int] = None,
        player_id: Optional[int] = None,
        date: Optional[str] = None,
        timezone: Optional[str] = None
    ) -> List[Dict]:
        """
        Return injuries.

        Args:
            league_id: ID de la ligue
            season: Saison
            fixture_id: ID du match
            team_id: ID of the team
            player_id: ID du joueur
            date: Date (YYYY-MM-DD)
            timezone: Timezone
        """
        params = {}
        if league_id:
            params["league"] = league_id
        if season:
            params["season"] = season
        if fixture_id:
            params["fixture"] = fixture_id
        if team_id:
            params["team"] = team_id
        if player_id:
            params["player"] = player_id
        if date:
            params["date"] = date
        if timezone:
            params["timezone"] = timezone

        data = await self._make_request("injuries", params)
        return data.get("response", [])

    # ==========================================
    # PREDICTIONS
    # ==========================================
    async def get_predictions(self, fixture_id: int) -> Dict:
        """
        Return predictions for a fixture.

        Args:
            fixture_id: ID du match
        """
        params = {"fixture": fixture_id}
        data = await self._make_request("predictions", params)
        response = data.get("response", [])
        return response[0] if response else {}

    # ==========================================
    # COTES (ODDS)
    # ==========================================
    async def get_odds(
        self,
        fixture_id: Optional[int] = None,
        league_id: Optional[int] = None,
        season: Optional[int] = None,
        date: Optional[str] = None,
        bookmaker_id: Optional[int] = None,
        bet_id: Optional[int] = None,
        timezone: Optional[str] = None
    ) -> List[Dict]:
        """
        Return odds from bookmakers.

        Args:
            fixture_id: ID du match
            league_id: ID de la ligue
            season: Saison
            date: Date (YYYY-MM-DD)
            bookmaker_id: ID du bookmaker
            bet_id: ID du type de pari
            timezone: Timezone
        """
        params = {}
        if fixture_id:
            params["fixture"] = fixture_id
        if league_id:
            params["league"] = league_id
        if season:
            params["season"] = season
        if date:
            params["date"] = date
        if bookmaker_id:
            params["bookmaker"] = bookmaker_id
        if bet_id:
            params["bet"] = bet_id
        if timezone:
            params["timezone"] = timezone

        data = await self._make_request("odds", params)
        return data.get("response", [])

    async def get_bookmakers(self, bookmaker_id: Optional[int] = None, search: Optional[str] = None) -> List[Dict]:
        """Return the list of bookmakers."""
        params = {}
        if bookmaker_id:
            params["id"] = bookmaker_id
        if search:
            params["search"] = search

        data = await self._make_request("odds/bookmakers", params)
        return data.get("response", [])

    async def get_bets(self, bet_id: Optional[int] = None, search: Optional[str] = None) -> List[Dict]:
        """Return the list of available bet types."""
        params = {}
        if bet_id:
            params["id"] = bet_id
        if search:
            params["search"] = search

        data = await self._make_request("odds/bets", params)
        return data.get("response", [])

    async def get_odds_mapping(self) -> List[Dict]:
        """Return odds mapping metadata."""
        data = await self._make_request("odds/mapping")
        return data.get("response", [])

    async def get_odds_live(self, fixture_id: Optional[int] = None, league_id: Optional[int] = None, bet_id: Optional[int] = None) -> List[Dict]:
        """Return live odds."""
        params = {}
        if fixture_id:
            params["fixture"] = fixture_id
        if league_id:
            params["league"] = league_id
        if bet_id:
            params["bet"] = bet_id

        data = await self._make_request("odds/live", params)
        return data.get("response", [])

    # ==========================================
    # PLAYERS (JOUEURS)
    # ==========================================
    async def get_players(
        self,
        player_id: Optional[int] = None,
        team_id: Optional[int] = None,
        league_id: Optional[int] = None,
        season: Optional[int] = None,
        search: Optional[str] = None,
        page: int = 1
    ) -> Dict:
        """
        Return player information and statistics.

        Args:
            player_id: ID du joueur
            team_id: ID of the team
            league_id: ID de la ligue
            season: Saison
            search: Recherche par nom
            page: Results page (25 results per page)
        """
        params = {"page": page}
        if player_id:
            params["id"] = player_id
        if team_id:
            params["team"] = team_id
        if league_id:
            params["league"] = league_id
        if season:
            params["season"] = season
        if search:
            params["search"] = search

        data = await self._make_request("players", params)
        return data


    async def get_player_profiles(
        self,
        player_id: Optional[int] = None,
        search: Optional[str] = None,
        page: int = 1,
    ) -> List[Dict]:
        """Recupere les profils joueurs (bio, poste, numero)."""
        params = {"page": page}
        if player_id:
            params["player"] = player_id
        if search:
            params["search"] = search

        data = await self._make_request("players/profiles", params)
        return data.get("response", [])

    async def get_players_squads(
        self,
        team_id: Optional[int] = None,
        player_id: Optional[int] = None,
    ) -> List[Dict]:
        """Recupere l'effectif d'une equipe ou les equipes d'un joueur."""
        params = {}
        if team_id:
            params["team"] = team_id
        if player_id:
            params["player"] = player_id

        data = await self._make_request("players/squads", params)
        return data.get("response", [])

    async def get_player_seasons(self, player_id: int) -> List[int]:
        """List available seasons for a player."""
        params = {"player": player_id}
        data = await self._make_request("players/seasons", params)
        return data.get("response", [])

    async def get_top_scorers(self, league_id: int, season: int) -> List[Dict]:
        """
        Return top scorers for a league.

        Args:
            league_id: ID de la ligue
            season: Saison
        """
        params = {
            "league": league_id,
            "season": season
        }
        data = await self._make_request("players/topscorers", params)
        return data.get("response", [])

    async def get_top_assists(self, league_id: int, season: int) -> List[Dict]:
        """
        Return top assists for a league.

        Args:
            league_id: ID de la ligue
            season: Saison
        """
        params = {
            "league": league_id,
            "season": season
        }
        data = await self._make_request("players/topassists", params)
        return data.get("response", [])

    async def get_top_yellow_cards(self, league_id: int, season: int) -> List[Dict]:
        """Return players with the most yellow cards."""
        params = {
            "league": league_id,
            "season": season
        }
        data = await self._make_request("players/topyellowcards", params)
        return data.get("response", [])

    async def get_top_red_cards(self, league_id: int, season: int) -> List[Dict]:
        """Return players with the most red cards."""
        params = {
            "league": league_id,
            "season": season
        }
        data = await self._make_request("players/topredcards", params)
        return data.get("response", [])

    # ==========================================
    # TRANSFERS
    # ==========================================
    async def get_transfers(self, player_id: Optional[int] = None, team_id: Optional[int] = None) -> List[Dict]:
        """
        Return transfer history.

        Args:
            player_id: ID du joueur
            team_id: ID of the team
        """
        params = {}
        if player_id:
            params["player"] = player_id
        if team_id:
            params["team"] = team_id

        data = await self._make_request("transfers", params)
        return data.get("response", [])

    # ==========================================
    # TROPHIES
    # ==========================================
    async def get_trophies(self, player_id: Optional[int] = None, coach_id: Optional[int] = None) -> List[Dict]:
        """
        Return trophies won.

        Args:
            player_id: ID du joueur
            coach_id: ID of the coach
        """
        params = {}
        if player_id:
            params["player"] = player_id
        if coach_id:
            params["coach"] = coach_id

        data = await self._make_request("trophies", params)
        return data.get("response", [])

    # ==========================================
    # SIDELINED (ABSENCES)
    # ==========================================
    async def get_sidelined(self, player_id: Optional[int] = None, coach_id: Optional[int] = None) -> List[Dict]:
        """
        Return sidelined history (injuries, suspensions).

        Args:
            player_id: ID du joueur
            coach_id: ID of the coach
        """
        params = {}
        if player_id:
            params["player"] = player_id
        if coach_id:
            params["coach"] = coach_id

        data = await self._make_request("sidelined", params)
        return data.get("response", [])

    # ==========================================
    # COACHES (ENTRAINEURS)
    # ==========================================
    async def get_coaches(
        self,
        coach_id: Optional[int] = None,
        team_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[Dict]:
        """
        Return coach information.

        Args:
            coach_id: ID of the coach
            team_id: ID of the team
            search: Recherche par nom
        """
        params = {}
        if coach_id:
            params["id"] = coach_id
        if team_id:
            params["team"] = team_id
        if search:
            params["search"] = search

        data = await self._make_request("coachs", params)
        return data.get("response", [])

    # ==========================================
    # UTILITY FUNCTIONS
    # ==========================================
    async def get_status(self) -> Dict:
        """Return API status and account information."""
        data = await self._make_request("status")
        return data

    async def close(self):
        """Ferme la connexion HTTP"""
        await self.client.aclose()

    # ==========================================
    # HELPER FUNCTIONS (pour faciliter l'usage)
    # ==========================================
    async def search_team(self, team_name: str) -> Optional[Dict]:
        """Search a team by name and return the first match."""
        teams = await self.get_teams(search=team_name)
        return teams[0] if teams else None

    async def search_player(self, player_name: str, season: Optional[int] = None) -> Optional[Dict]:
        """Recherche un joueur par nom"""
        data = await self.get_players(search=player_name, season=season)
        response = data.get("response", [])
        return response[0] if response else None

    async def get_live_fixtures(self) -> List[Dict]:
        """Return all live fixtures."""
        return await self.get_fixtures(live="all")

    async def get_fixtures_by_date(self, date: str) -> List[Dict]:
        """Return all fixtures for a given date (YYYY-MM-DD)."""
        return await self.get_fixtures(date=date)

    async def get_team_next_fixtures(self, team_id: int, n: int = 5) -> List[Dict]:
        """Return the next N fixtures for a team."""
        return await self.get_fixtures(team_id=team_id, next=n)

    async def get_team_last_fixtures(self, team_id: int, n: int = 5) -> List[Dict]:
        """Return the last N fixtures for a team."""
        return await self.get_fixtures(team_id=team_id, last=n)

    async def get_league_current_round(self, league_id: int, season: int) -> Optional[str]:
        """Return the current round for a league."""
        rounds = await self.get_fixture_rounds(league_id, season, current=True)
        return rounds[0] if rounds else None
