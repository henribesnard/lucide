import httpx
from typing import Dict, List, Optional, Any
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

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

    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Effectue une requête à l'API et retourne la réponse"""
        try:
            url = f"{self.base_url}/{endpoint}"
            logger.info(f"API Request: {endpoint} with params: {params}")

            response = await self.client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("errors") and len(data["errors"]) > 0:
                logger.error(f"API Error: {data['errors']}")
                raise Exception(f"API Error: {data['errors']}")

            logger.info(f"API Response: {len(data.get('response', []))} results")
            return data

        except httpx.HTTPError as e:
            logger.error(f"HTTP Error: {e}")
            raise

    # ==========================================
    # TIMEZONE
    # ==========================================
    async def get_timezones(self) -> List[str]:
        """Récupère la liste de tous les timezones disponibles"""
        data = await self._make_request("timezone")
        return data.get("response", [])

    # ==========================================
    # SEASONS
    # ==========================================
    async def get_seasons(self) -> List[int]:
        """Récupère la liste de toutes les saisons disponibles"""
        data = await self._make_request("seasons")
        return data.get("response", [])

    # ==========================================
    # COUNTRIES
    # ==========================================
    async def get_countries(self, name: Optional[str] = None, code: Optional[str] = None) -> List[Dict]:
        """
        Récupère la liste des pays

        Args:
            name: Nom du pays (ex: "France")
            code: Code du pays (ex: "FR")
        """
        params = {}
        if name:
            params["name"] = name
        if code:
            params["code"] = code

        data = await self._make_request("countries", params)
        return data.get("response", [])

    # ==========================================
    # LEAGUES
    # ==========================================
    async def get_leagues(
        self,
        league_id: Optional[int] = None,
        name: Optional[str] = None,
        country: Optional[str] = None,
        season: Optional[int] = None,
        team_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Récupère les informations des ligues

        Args:
            league_id: ID de la ligue
            name: Nom de la ligue
            country: Pays de la ligue
            season: Saison
            team_id: ID de l'équipe
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
        search: Optional[str] = None
    ) -> List[Dict]:
        """
        Récupère les informations des équipes

        Args:
            team_id: ID de l'équipe
            name: Nom de l'équipe
            league_id: ID de la ligue
            season: Saison
            country: Pays
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
        Récupère les statistiques détaillées d'une équipe

        Args:
            team_id: ID de l'équipe
            season: Saison
            league_id: ID de la ligue
            date: Date spécifique (YYYY-MM-DD)
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
        """Récupère les saisons disponibles pour une équipe"""
        params = {"team": team_id}
        data = await self._make_request("teams/seasons", params)
        return data.get("response", [])

    async def get_team_countries(self) -> List[Dict]:
        """Récupère la liste des pays avec des équipes disponibles"""
        data = await self._make_request("teams/countries")
        return data.get("response", [])

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
        Récupère les informations des stades

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
        Récupère les classements

        Args:
            season: Saison
            league_id: ID de la ligue
            team_id: ID de l'équipe
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
        Récupère les matchs (fixtures)

        Args:
            fixture_id: ID du match
            league_id: ID de la ligue
            season: Saison
            team_id: ID de l'équipe
            date: Date (YYYY-MM-DD)
            from_date: Date de début
            to_date: Date de fin
            round_: Tour/Journée
            status: Statut (TBD, NS, 1H, HT, 2H, ET, P, FT, AET, PEN, BT, SUSP, INT, PST, CANC, ABD, AWD, WO, LIVE)
            venue_id: ID du stade
            timezone: Timezone
            live: "all" pour tous les matchs en direct
            last: N derniers matchs d'une équipe
            next: N prochains matchs d'une équipe
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
            params["status"] = status
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
        Récupère les journées/tours d'une ligue

        Args:
            league_id: ID de la ligue
            season: Saison
            current: True pour obtenir seulement la journée actuelle
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
        Récupère l'historique des confrontations directes (H2H)

        Args:
            team1_id: ID de l'équipe 1
            team2_id: ID de l'équipe 2
            last: Nombre de derniers matchs
            from_date: Date de début
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
            params["status"] = status
        if venue_id:
            params["venue"] = venue_id
        if timezone:
            params["timezone"] = timezone

        data = await self._make_request("fixtures/headtohead", params)
        return data.get("response", [])

    async def get_fixture_statistics(self, fixture_id: int, team_id: Optional[int] = None) -> List[Dict]:
        """
        Récupère les statistiques d'un match

        Args:
            fixture_id: ID du match
            team_id: ID de l'équipe (optionnel)
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
        Récupère les événements d'un match (buts, cartons, etc.)

        Args:
            fixture_id: ID du match
            team_id: ID de l'équipe
            player_id: ID du joueur
            type_: Type d'événement (Goal, Card, subst, Var)
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
        Récupère les compositions d'équipe pour un match

        Args:
            fixture_id: ID du match
            team_id: ID de l'équipe (optionnel)
        """
        params = {"fixture": fixture_id}
        if team_id:
            params["team"] = team_id

        data = await self._make_request("fixtures/lineups", params)
        return data.get("response", [])

    async def get_fixture_player_statistics(self, fixture_id: int, team_id: Optional[int] = None) -> List[Dict]:
        """
        Récupère les statistiques des joueurs pour un match

        Args:
            fixture_id: ID du match
            team_id: ID de l'équipe (optionnel)
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
        Récupère la liste des blessures

        Args:
            league_id: ID de la ligue
            season: Saison
            fixture_id: ID du match
            team_id: ID de l'équipe
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
        Récupère les prédictions pour un match

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
        Récupère les cotes des bookmakers

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
        """Récupère la liste des bookmakers"""
        params = {}
        if bookmaker_id:
            params["id"] = bookmaker_id
        if search:
            params["search"] = search

        data = await self._make_request("odds/bookmakers", params)
        return data.get("response", [])

    async def get_bets(self, bet_id: Optional[int] = None, search: Optional[str] = None) -> List[Dict]:
        """Récupère la liste des types de paris disponibles"""
        params = {}
        if bet_id:
            params["id"] = bet_id
        if search:
            params["search"] = search

        data = await self._make_request("odds/bets", params)
        return data.get("response", [])

    async def get_odds_mapping(self) -> List[Dict]:
        """Récupère le mapping des cotes"""
        data = await self._make_request("odds/mapping")
        return data.get("response", [])

    async def get_odds_live(self, fixture_id: Optional[int] = None, league_id: Optional[int] = None, bet_id: Optional[int] = None) -> List[Dict]:
        """Récupère les cotes en direct"""
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
        Récupère les informations et statistiques des joueurs

        Args:
            player_id: ID du joueur
            team_id: ID de l'équipe
            league_id: ID de la ligue
            season: Saison
            search: Recherche par nom
            page: Page de résultats (25 résultats par page)
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

    async def get_player_seasons(self, player_id: int) -> List[int]:
        """Récupère les saisons disponibles pour un joueur"""
        params = {"player": player_id}
        data = await self._make_request("players/seasons", params)
        return data.get("response", [])

    async def get_top_scorers(self, league_id: int, season: int) -> List[Dict]:
        """
        Récupère les meilleurs buteurs d'une ligue

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
        Récupère les meilleurs passeurs d'une ligue

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
        """Récupère les joueurs avec le plus de cartons jaunes"""
        params = {
            "league": league_id,
            "season": season
        }
        data = await self._make_request("players/topyellowcards", params)
        return data.get("response", [])

    async def get_top_red_cards(self, league_id: int, season: int) -> List[Dict]:
        """Récupère les joueurs avec le plus de cartons rouges"""
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
        Récupère l'historique des transferts

        Args:
            player_id: ID du joueur
            team_id: ID de l'équipe
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
        Récupère les trophées gagnés

        Args:
            player_id: ID du joueur
            coach_id: ID de l'entraîneur
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
        Récupère l'historique des absences (blessures, suspensions)

        Args:
            player_id: ID du joueur
            coach_id: ID de l'entraîneur
        """
        params = {}
        if player_id:
            params["player"] = player_id
        if coach_id:
            params["coach"] = coach_id

        data = await self._make_request("sidelined", params)
        return data.get("response", [])

    # ==========================================
    # COACHES (ENTRAÎNEURS)
    # ==========================================
    async def get_coaches(
        self,
        coach_id: Optional[int] = None,
        team_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[Dict]:
        """
        Récupère les informations des entraîneurs

        Args:
            coach_id: ID de l'entraîneur
            team_id: ID de l'équipe
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
        """Récupère le statut de l'API et les informations du compte"""
        data = await self._make_request("status")
        return data

    async def close(self):
        """Ferme la connexion HTTP"""
        await self.client.aclose()

    # ==========================================
    # HELPER FUNCTIONS (pour faciliter l'usage)
    # ==========================================
    async def search_team(self, team_name: str) -> Optional[Dict]:
        """Recherche une équipe par nom et retourne la première correspondance"""
        teams = await self.get_teams(search=team_name)
        return teams[0] if teams else None

    async def search_player(self, player_name: str, season: Optional[int] = None) -> Optional[Dict]:
        """Recherche un joueur par nom"""
        data = await self.get_players(search=player_name, season=season)
        response = data.get("response", [])
        return response[0] if response else None

    async def get_live_fixtures(self) -> List[Dict]:
        """Récupère tous les matchs en direct"""
        return await self.get_fixtures(live="all")

    async def get_fixtures_by_date(self, date: str) -> List[Dict]:
        """Récupère tous les matchs d'une date donnée (YYYY-MM-DD)"""
        return await self.get_fixtures(date=date)

    async def get_team_next_fixtures(self, team_id: int, n: int = 5) -> List[Dict]:
        """Récupère les N prochains matchs d'une équipe"""
        return await self.get_fixtures(team_id=team_id, next=n)

    async def get_team_last_fixtures(self, team_id: int, n: int = 5) -> List[Dict]:
        """Récupère les N derniers matchs d'une équipe"""
        return await self.get_fixtures(team_id=team_id, last=n)

    async def get_league_current_round(self, league_id: int, season: int) -> Optional[str]:
        """Récupère la journée actuelle d'une ligue"""
        rounds = await self.get_fixture_rounds(league_id, season, current=True)
        return rounds[0] if rounds else None
