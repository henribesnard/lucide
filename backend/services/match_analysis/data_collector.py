"""
Collecteur de donnees pour l'analyse de match (VERSION ELARGIE).
Collecte les donnees TOUTES COMPETITIONS confondues.
Implemente les Etapes 0-2 de l'algorithme elargi.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from difflib import SequenceMatcher
from backend.api.football_api import FootballAPIClient
from .types import MatchAnalysisInput, NormalizedIDs, CoverageInfo
import asyncio

logger = logging.getLogger(__name__)


class DataCollector:
    """
    Collecte et normalise les donnees (VERSION ELARGIE).
    Collecte les 30 derniers matchs toutes competitions + events + stats + lineups.
    """

    def __init__(self, api_client: FootballAPIClient):
        self.api = api_client
        self.api_call_count = 0

    # ========================================================================
    # ETAPE 0: NORMALISER LES IDENTIFIANTS
    # ========================================================================

    async def normalize_identifiers(
        self, input_data: MatchAnalysisInput
    ) -> NormalizedIDs:
        """Etape 0: Resoudre les IDs et valider la couverture."""
        logger.info("=== ETAPE 0: Normalisation des identifiants ===")

        # 1) Resoudre league ID et season
        league_id, league_name, season = await self._resolve_league(
            input_data.league, input_data.season
        )

        # 2) Valider la couverture
        coverage = await self._validate_coverage(league_id, season)

        # 3) Resoudre team IDs
        team_a_id, team_a_name = await self._resolve_team(input_data.team_a)
        team_b_id, team_b_name = await self._resolve_team(input_data.team_b)

        # 4) Resoudre venue ID (optionnel)
        venue_id, venue_name = None, None
        if input_data.stadium:
            venue_id, venue_name = await self._resolve_venue(input_data.stadium)

        # 5) Resoudre coach IDs (optionnel)
        coach_a_id, coach_b_id = None, None
        if input_data.coach_team_a:
            coach_a_id = await self._resolve_coach(input_data.coach_team_a, team_a_id)
        if input_data.coach_team_b:
            coach_b_id = await self._resolve_coach(input_data.coach_team_b, team_b_id)

        # 6) Récupérer le type de league (cup ou league)
        league_type = await self.api.get_league_type(league_id, season)
        league_type = league_type.lower() if league_type in ["Cup", "League"] else "cup"
        logger.info(f"League type: {league_type}")

        normalized = NormalizedIDs(
            league_id=league_id,
            league_name=league_name,
            league_type=league_type,
            season=season,
            team_a_id=team_a_id,
            team_a_name=team_a_name,
            team_b_id=team_b_id,
            team_b_name=team_b_name,
            venue_id=venue_id,
            venue_name=venue_name,
            coach_a_id=coach_a_id,
            coach_b_id=coach_b_id,
            coverage=coverage,
        )

        logger.info(f"Normalisation terminee: {normalized}")
        return normalized

    async def _resolve_league(
        self, league_input: str, season: Optional[int]
    ) -> Tuple[int, str, int]:
        """
        Resout l'ID de la league et la saison avec recherche intelligente.

        Si le nom est ambigu, utilise la similarité de chaînes pour trouver
        la meilleure correspondance parmi les résultats.
        """
        if league_input.isdigit():
            league_id = int(league_input)
            data = await self.api.get_leagues(league_id=league_id)
            self.api_call_count += 1
        else:
            data = await self.api.get_leagues(search=league_input)
            self.api_call_count += 1

        if not data:
            raise ValueError(f"League non trouvee: {league_input}")

        # Si un seul résultat, le retourner directement
        if len(data) == 1:
            league_info = data[0]
        else:
            # Plusieurs résultats : trouver la meilleure correspondance
            logger.info(f"Recherche league '{league_input}': {len(data)} resultats trouves")

            best_match = None
            best_score = 0.0
            league_input_lower = league_input.lower()

            for league_data in data:
                league_name = league_data["league"]["name"]
                league_name_lower = league_name.lower()

                # Calculer le score de similarité
                score = SequenceMatcher(None, league_input_lower, league_name_lower).ratio()

                # Bonus si le nom recherché est contenu dans le nom de la league
                if league_input_lower in league_name_lower:
                    score += 0.3

                # Bonus si les noms commencent de la même manière
                if league_name_lower.startswith(league_input_lower[:3]):
                    score += 0.2

                logger.debug(f"  - {league_name} (ID: {league_data['league']['id']}): score={score:.2f}")

                if score > best_score:
                    best_score = score
                    best_match = league_data

            if not best_match:
                best_match = data[0]
                logger.warning(f"Aucun bon match trouve pour league, utilisation du premier: {best_match['league']['name']}")
            else:
                logger.info(f"Meilleur match league: {best_match['league']['name']} (ID: {best_match['league']['id']}, score={best_score:.2f})")

            league_info = best_match

        league_id = league_info["league"]["id"]
        league_name = league_info["league"]["name"]

        if season is None:
            seasons = league_info.get("seasons", [])
            current_season = next(
                (s for s in seasons if s.get("current", False)), None
            )
            if current_season:
                season = current_season["year"]
            else:
                season = max(s["year"] for s in seasons)

        return league_id, league_name, season

    async def _validate_coverage(
        self, league_id: int, season: int
    ) -> CoverageInfo:
        """Valide la couverture des donnees."""
        data = await self.api.get_leagues(league_id=league_id)
        self.api_call_count += 1

        if not data:
            raise ValueError(f"League non trouvee: {league_id}")

        league_info = data[0]
        seasons = league_info.get("seasons", [])
        season_info = next((s for s in seasons if s["year"] == season), None)

        if not season_info:
            raise ValueError(f"Saison {season} non disponible pour league {league_id}")

        coverage_data = season_info.get("coverage", {})
        fixtures_coverage = coverage_data.get("fixtures", {})

        coverage = CoverageInfo(
            events=fixtures_coverage.get("events", False),
            lineups=fixtures_coverage.get("lineups", False),
            statistics_fixtures=fixtures_coverage.get("statistics_fixtures", False),
            statistics_players=fixtures_coverage.get("statistics_players", False),
            predictions=coverage_data.get("predictions", False),
        )

        logger.info(f"Coverage validee: {coverage}")
        return coverage

    async def _resolve_team(self, team_input: str) -> Tuple[int, str]:
        """
        Resout l'ID d'une team avec recherche intelligente.

        Si le nom est ambigu, utilise la similarité de chaînes pour trouver
        la meilleure correspondance parmi les résultats.
        """
        if team_input.isdigit():
            team_id = int(team_input)
            data = await self.api.get_teams(team_id=team_id)
            self.api_call_count += 1
        else:
            data = await self.api.get_teams(search=team_input)
            self.api_call_count += 1

        if not data:
            raise ValueError(f"Team non trouvee: {team_input}")

        # Si un seul résultat, le retourner directement
        if len(data) == 1:
            team_info = data[0]
            logger.info(f"Team trouvee: {team_info['team']['name']} (ID: {team_info['team']['id']})")
            return team_info["team"]["id"], team_info["team"]["name"]

        # Plusieurs résultats : trouver la meilleure correspondance
        logger.info(f"Recherche '{team_input}': {len(data)} resultats trouves")

        best_match = None
        best_score = 0.0
        team_input_lower = team_input.lower()

        for team_data in data:
            team_name = team_data["team"]["name"]
            team_name_lower = team_name.lower()

            # Calculer le score de similarité
            score = SequenceMatcher(None, team_input_lower, team_name_lower).ratio()

            # Bonus si le nom recherché est contenu dans le nom de l'équipe
            if team_input_lower in team_name_lower:
                score += 0.3

            # Bonus si les noms commencent de la même manière
            if team_name_lower.startswith(team_input_lower[:3]):
                score += 0.2

            logger.debug(f"  - {team_name} (ID: {team_data['team']['id']}): score={score:.2f}")

            if score > best_score:
                best_score = score
                best_match = team_data

        if not best_match:
            # Fallback sur le premier résultat si aucun match
            best_match = data[0]
            logger.warning(f"Aucun bon match trouve, utilisation du premier: {best_match['team']['name']}")
        else:
            logger.info(f"Meilleur match: {best_match['team']['name']} (ID: {best_match['team']['id']}, score={best_score:.2f})")

        return best_match["team"]["id"], best_match["team"]["name"]

    async def _resolve_venue(self, venue_input: str) -> Tuple[Optional[int], Optional[str]]:
        """Resout l'ID d'un venue."""
        try:
            data = await self.api.get_venues(search=venue_input)
            self.api_call_count += 1

            if data:
                venue_info = data[0]
                return venue_info["id"], venue_info["name"]
        except Exception as e:
            logger.warning(f"Impossible de resoudre venue {venue_input}: {e}")

        return None, None

    async def _resolve_coach(self, coach_input: str, team_id: int) -> Optional[int]:
        """Resout l'ID d'un coach."""
        try:
            logger.warning(f"Resolution coach non implementee: {coach_input}")
        except Exception as e:
            logger.warning(f"Impossible de resoudre coach {coach_input}: {e}")
        return None

    # ========================================================================
    # ETAPE 1: DEFINIR LE PERIMETRE (ELARGI)
    # ========================================================================

    async def define_data_scope_extended(
        self,
        normalized: NormalizedIDs,
        num_last_matches: int = 30
    ) -> Dict[str, Any]:
        """
        Etape 1 ELARGIE: Definit le perimetre toutes competitions.

        Args:
            num_last_matches: Nombre de derniers matchs a collecter (toutes comps)

        Returns:
            Dict avec le perimetre elargi
        """
        logger.info("=== ETAPE 1: Definition du perimetre (ELARGI) ===")

        return {
            "num_last_matches": num_last_matches,
            "team_a_id": normalized.team_a_id,
            "team_b_id": normalized.team_b_id,
            "league_id": normalized.league_id,
            "season": normalized.season,
        }

    # ========================================================================
    # ETAPE 2: COLLECTER LES DONNEES (ENRICHI)
    # ========================================================================

    async def collect_data_extended(
        self,
        normalized: NormalizedIDs,
        scope: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Etape 2 ENRICHIE: Collecte TOUTES les donnees (toutes comps + details).

        Returns:
            Dict contenant:
            - team_a_all_matches: 30 derniers matchs team A (toutes comps)
            - team_b_all_matches: 30 derniers matchs team B (toutes comps)
            - h2h_matches: H2H toutes comps
            - events_by_fixture: Dict {fixture_id: events}
            - stats_by_fixture: Dict {fixture_id: stats}
            - lineups_by_fixture: Dict {fixture_id: lineups}
            - injuries_team_a/b: Blessures actuelles
            - sidelined_team_a/b: Suspensions
        """
        logger.info("=== ETAPE 2: Collecte des donnees (ENRICHIE) ===")

        num_matches = scope["num_last_matches"]

        # Collecter les derniers matchs de chaque equipe (TOUTES COMPS)
        logger.info(f"Collecte des {num_matches} derniers matchs (toutes competitions)...")

        team_a_fixtures_all = await self._get_team_last_matches(
            normalized.team_a_id, num_matches
        )
        team_b_fixtures_all = await self._get_team_last_matches(
            normalized.team_b_id, num_matches
        )

        # NOUVEAU: Collecter les matchs dans la league (TOUTES saisons disponibles)
        logger.info(f"Collecte matchs historiques dans {normalized.league_name} (toutes éditions)...")

        team_a_fixtures_league = await self._get_team_league_matches(
            normalized.team_a_id, normalized.league_id
        )
        team_b_fixtures_league = await self._get_team_league_matches(
            normalized.team_b_id, normalized.league_id
        )

        # H2H
        h2h_fixtures = await self._get_h2h_fixtures(
            normalized.team_a_id, normalized.team_b_id
        )

        # Combiner tous les fixture IDs pour collecte detaillee
        # Inclut: matchs generaux + matchs league + h2h
        all_fixture_ids = set()
        for fixture in team_a_fixtures_all + team_b_fixtures_all + team_a_fixtures_league + team_b_fixtures_league + h2h_fixtures:
            all_fixture_ids.add(fixture["fixture"]["id"])

        logger.info(f"Total de {len(all_fixture_ids)} matchs uniques a analyser")

        # Collecter details pour chaque match (en parallele)
        logger.info("Collecte events/stats/lineups pour chaque match...")

        events_by_fixture = {}
        stats_by_fixture = {}
        lineups_by_fixture = {}

        # Paralleliser les appels (groupes de 10)
        fixture_id_list = list(all_fixture_ids)
        batch_size = 10

        for i in range(0, len(fixture_id_list), batch_size):
            batch = fixture_id_list[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(fixture_id_list) + batch_size - 1) // batch_size

            logger.info(f"Traitement batch {batch_num}/{total_batches} ({len(batch)} matchs)...")

            # Creer les tasks pour ce batch
            tasks = []
            for fixture_id in batch:
                tasks.append(self._collect_match_details(
                    fixture_id,
                    normalized.coverage
                ))

            # Executer en parallele
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Stocker les resultats
            for fixture_id, result in zip(batch, results):
                if isinstance(result, Exception):
                    logger.warning(f"Erreur collecte match {fixture_id}: {result}")
                    continue

                events_by_fixture[fixture_id] = result.get("events", [])
                stats_by_fixture[fixture_id] = result.get("stats", [])
                lineups_by_fixture[fixture_id] = result.get("lineups", [])

            # Throttling: Pause de 2 secondes entre chaque batch (sauf le dernier)
            if i + batch_size < len(fixture_id_list):
                logger.debug(f"Pause de 2s avant le prochain batch (rate limiting)...")
                await asyncio.sleep(2)

        # Blessures et suspensions actuelles
        injuries_a = await self._get_injuries(normalized.team_a_id)
        injuries_b = await self._get_injuries(normalized.team_b_id)
        sidelined_a = await self._get_sidelined(normalized.team_a_id)
        sidelined_b = await self._get_sidelined(normalized.team_b_id)

        logger.info(
            f"Collecte terminee: {len(team_a_fixtures_all)} matchs team A (all), "
            f"{len(team_a_fixtures_league)} matchs team A (league), "
            f"{len(team_b_fixtures_all)} matchs team B (all), "
            f"{len(team_b_fixtures_league)} matchs team B (league), "
            f"{len(h2h_fixtures)} H2H, "
            f"{len(events_by_fixture)} matchs avec events"
        )

        return {
            # Matchs generaux (toutes competitions)
            "team_a_all_matches": team_a_fixtures_all,
            "team_b_all_matches": team_b_fixtures_all,
            # NOUVEAU: Matchs dans la league specifique
            "team_a_league_matches": team_a_fixtures_league,
            "team_b_league_matches": team_b_fixtures_league,
            # H2H et details
            "h2h_matches": h2h_fixtures,
            "events_by_fixture": events_by_fixture,
            "stats_by_fixture": stats_by_fixture,
            "lineups_by_fixture": lineups_by_fixture,
            "injuries_team_a": injuries_a,
            "injuries_team_b": injuries_b,
            "sidelined_team_a": sidelined_a,
            "sidelined_team_b": sidelined_b,
        }

    async def _get_team_last_matches(
        self, team_id: int, last: int
    ) -> List[Dict[str, Any]]:
        """Recupere les N derniers matchs d'une team (TOUTES COMPETITIONS)."""
        try:
            data = await self.api.get_fixtures(team_id=team_id, last=last)
            self.api_call_count += 1
            return data if data else []
        except Exception as e:
            logger.error(f"Erreur get_team_last_matches: {e}")
            return []

    async def _get_team_league_matches(
        self, team_id: int, league_id: int
    ) -> List[Dict[str, Any]]:
        """
        Recupere les matchs d'une team dans une league sur TOUTES les saisons disponibles.

        Ex: Tous les matchs de Benin en CAN (toutes éditions historiques)

        1. Récupère toutes les saisons disponibles pour la league via /leagues?id=X
        2. Pour chaque saison, récupère les matchs de l'équipe via /fixtures?team=X&league=Y&season=Z

        Cela permet d'analyser la forme historique complète de l'équipe dans cette compétition
        et de détecter des patterns comme "ne gagne jamais en temps régulier à la CAN".
        """
        all_matches = []

        try:
            # 1) Récupérer toutes les saisons disponibles pour cette league
            logger.info(f"Récupération des saisons disponibles pour league {league_id}...")
            league_info = await self.api.get_leagues(league_id=league_id)
            self.api_call_count += 1

            if not league_info or len(league_info) == 0:
                logger.warning(f"Aucune info trouvée pour league {league_id}")
                return []

            seasons = league_info[0].get("seasons", [])
            available_seasons = [s["year"] for s in seasons]

            logger.info(f"League {league_id}: {len(available_seasons)} saisons disponibles")

            # 2) Pour chaque saison, récupérer les matchs de l'équipe
            logger.info(f"Collecte matchs pour team {team_id} dans league {league_id}...")

            for season in available_seasons:
                if season < 2015:  # Limiter aux données récentes (depuis 2015)
                    continue

                try:
                    data = await self.api.get_fixtures(
                        team_id=team_id,
                        league_id=league_id,
                        season=season
                    )
                    self.api_call_count += 1

                    if data:
                        all_matches.extend(data)
                        logger.info(f"  Saison {season}: {len(data)} matchs")

                except Exception as e:
                    logger.debug(f"  Saison {season}: aucun match - {e}")
                    continue

            logger.info(f"Team {team_id} dans league {league_id}: {len(all_matches)} matchs au total")

            return all_matches

        except Exception as e:
            logger.error(f"Erreur get_team_league_matches: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    async def _get_h2h_fixtures(
        self, team_a_id: int, team_b_id: int
    ) -> List[Dict[str, Any]]:
        """Recupere l'historique H2H."""
        try:
            data = await self.api.get_head_to_head(team_a_id, team_b_id, last=20)
            self.api_call_count += 1
            return data if data else []
        except Exception as e:
            logger.error(f"Erreur get_h2h_fixtures: {e}")
            return []

    async def _collect_match_details(
        self,
        fixture_id: int,
        coverage: CoverageInfo
    ) -> Dict[str, Any]:
        """
        Collecte tous les details d'un match (events, stats, lineups).

        Returns:
            Dict avec events, stats, lineups
        """
        result = {
            "events": [],
            "stats": [],
            "lineups": [],
        }

        try:
            # Events (si couverture)
            if coverage.events:
                events = await self.api.get_fixture_events(fixture_id)
                self.api_call_count += 1
                result["events"] = events if events else []

            # Stats (si couverture)
            if coverage.statistics_fixtures:
                stats = await self.api.get_fixture_statistics(fixture_id)
                self.api_call_count += 1
                result["stats"] = stats if stats else []

            # Lineups (si couverture)
            if coverage.lineups:
                lineups = await self.api.get_fixture_lineups(fixture_id)
                self.api_call_count += 1
                result["lineups"] = lineups if lineups else []

        except Exception as e:
            logger.warning(f"Erreur collecte details match {fixture_id}: {e}")

        return result

    async def _get_injuries(self, team_id: int) -> List[Dict[str, Any]]:
        """Recupere les blessures actuelles."""
        try:
            data = await self.api.get_injuries(team_id=team_id)
            self.api_call_count += 1
            return data if data else []
        except Exception as e:
            logger.warning(f"Erreur get_injuries: {e}")
            return []

    async def _get_sidelined(self, team_id: int) -> List[Dict[str, Any]]:
        """Recupere les suspensions."""
        try:
            data = await self.api.get_sidelined(team_id=team_id)
            self.api_call_count += 1
            return data if data else []
        except Exception as e:
            logger.warning(f"Erreur get_sidelined: {e}")
            return []
