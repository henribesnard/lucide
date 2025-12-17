"""
Zone Resolver - Résolution dynamique des zones pour toutes les compétitions.

Utilise une approche hybride :
1. Registry statique pour les compétitions internationales majeures
2. Lookup API pour toutes les autres compétitions (ligues nationales, coupes, etc.)
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
import structlog

from backend.agents.context_types import Zone, ZoneType
from backend.agents.competition_classification import (
    get_competition_classification,
    CompetitionClassification
)

logger = structlog.get_logger()


@dataclass
class ZoneResolutionResult:
    """Résultat de la résolution de zone."""
    zone: Zone
    source: str  # "registry" | "api_lookup" | "fallback"
    classification: Optional[CompetitionClassification] = None
    api_data: Optional[Dict[str, Any]] = None


class ZoneResolver:
    """
    Résout la zone pour n'importe quelle compétition.

    Stratégie de résolution :
    1. Chercher dans le registry statique (compétitions internationales)
    2. Si non trouvé, faire un lookup API via /leagues?id={league_id}
    3. Extraire country.code et country.name de la réponse
    4. Créer une Zone à partir de ces données

    Features:
    - Cache pour éviter trop d'appels API
    - Fallback sur league_name si league_id non fourni
    """

    def __init__(self, api_client=None):
        """
        Initialize zone resolver.

        Args:
            api_client: API-Football client (optionnel)
        """
        self.api_client = api_client
        self._cache: Dict[int, ZoneResolutionResult] = {}

    async def resolve_zone_for_league(
        self,
        league_name: Optional[str] = None,
        league_id: Optional[int] = None
    ) -> Optional[ZoneResolutionResult]:
        """
        Résout la zone pour une ligue donnée.

        Args:
            league_name: Nom de la ligue (e.g., "Ligue 1", "UEFA Champions League")
            league_id: ID API-Football de la ligue (e.g., 61 pour Ligue 1)

        Returns:
            ZoneResolutionResult ou None si échec

        Examples:
            >>> # Compétition internationale (depuis registry)
            >>> result = await resolver.resolve_zone_for_league(
            ...     league_name="UEFA Champions League"
            ... )
            >>> result.zone.name
            'Europe'
            >>> result.source
            'registry'

            >>> # Ligue nationale (lookup API)
            >>> result = await resolver.resolve_zone_for_league(
            ...     league_id=61  # Ligue 1
            ... )
            >>> result.zone.name
            'France'
            >>> result.zone.code
            'FR'
            >>> result.source
            'api_lookup'
        """

        # Strategy 1: Check static registry (international competitions)
        if league_name:
            classification = get_competition_classification(league_name)
            if classification:
                zone = self._zone_from_classification(classification)

                logger.info(
                    "zone_resolved_from_registry",
                    league_name=league_name,
                    zone=zone.name,
                    zone_type=zone.zone_type.value
                )

                return ZoneResolutionResult(
                    zone=zone,
                    source="registry",
                    classification=classification
                )

        # Strategy 2: API lookup (all other competitions)
        if league_id:
            # Check cache first
            if league_id in self._cache:
                logger.debug("zone_resolved_from_cache", league_id=league_id)
                return self._cache[league_id]

            # Fetch from API
            result = await self._lookup_zone_from_api(league_id)

            if result:
                # Cache result
                self._cache[league_id] = result
                return result

        # Strategy 3: Fallback - search by name if ID not available
        if league_name and self.api_client:
            result = await self._lookup_zone_by_name(league_name)
            if result:
                return result

        logger.warning(
            "zone_resolution_failed",
            league_name=league_name,
            league_id=league_id
        )
        return None

    async def _lookup_zone_from_api(
        self,
        league_id: int
    ) -> Optional[ZoneResolutionResult]:
        """
        Lookup zone depuis API-Football /leagues endpoint.

        Args:
            league_id: ID de la ligue

        Returns:
            ZoneResolutionResult ou None
        """
        if not self.api_client:
            logger.warning(
                "api_client_not_available",
                league_id=league_id,
                message="Cannot lookup zone without API client"
            )
            return None

        try:
            # Call API-Football /leagues?id={league_id}
            response = await self.api_client.get_league(league_id)

            if not response or 'response' not in response or not response['response']:
                logger.warning("api_league_not_found", league_id=league_id)
                return None

            league_data = response['response'][0]
            country_data = league_data.get('country', {})

            country_name = country_data.get('name')
            country_code = country_data.get('code')

            if not country_name:
                logger.warning(
                    "api_league_missing_country",
                    league_id=league_id,
                    league_data=league_data
                )
                return None

            # Determine zone type
            zone_type = self._determine_zone_type(country_name, country_code)

            zone = Zone(
                name=country_name,
                code=country_code,
                zone_type=zone_type
            )

            logger.info(
                "zone_resolved_from_api",
                league_id=league_id,
                league_name=league_data.get('league', {}).get('name'),
                zone=zone.name,
                zone_code=zone.code,
                zone_type=zone.zone_type.value
            )

            return ZoneResolutionResult(
                zone=zone,
                source="api_lookup",
                api_data=league_data
            )

        except Exception as e:
            logger.error(
                "api_lookup_error",
                league_id=league_id,
                error=str(e)
            )
            return None

    async def _lookup_zone_by_name(
        self,
        league_name: str
    ) -> Optional[ZoneResolutionResult]:
        """
        Lookup zone par nom de ligue (fallback).

        Args:
            league_name: Nom de la ligue

        Returns:
            ZoneResolutionResult ou None
        """
        try:
            # Call API-Football /leagues?search={league_name}
            response = await self.api_client.search_leagues(league_name)

            if not response or 'response' not in response or not response['response']:
                return None

            # Take first match
            league_data = response['response'][0]
            league_id = league_data.get('league', {}).get('id')

            if league_id:
                # Use ID-based lookup
                return await self._lookup_zone_from_api(league_id)

        except Exception as e:
            logger.error(
                "api_search_error",
                league_name=league_name,
                error=str(e)
            )

        return None

    def _zone_from_classification(
        self,
        classification: CompetitionClassification
    ) -> Zone:
        """
        Crée une Zone depuis une CompetitionClassification.

        Args:
            classification: Classification de la compétition

        Returns:
            Zone instance
        """
        zone_name = classification.get_display_zone()

        if classification.geographic_scope == classification.geographic_scope.NATIONAL:
            return Zone(
                name=zone_name,
                code=classification.country_code,
                zone_type=ZoneType.NATIONAL
            )
        elif classification.geographic_scope == classification.geographic_scope.GLOBAL:
            return Zone(
                name="World",
                code=None,
                zone_type=ZoneType.INTERNATIONAL
            )
        else:  # CONTINENTAL or REGIONAL
            return Zone(
                name=zone_name,
                code=None,
                zone_type=ZoneType.CONTINENTAL
            )

    def _determine_zone_type(
        self,
        country_name: str,
        country_code: Optional[str]
    ) -> ZoneType:
        """
        Détermine le type de zone basé sur le country de l'API.

        Args:
            country_name: Nom du pays/zone
            country_code: Code du pays (ou None)

        Returns:
            ZoneType

        Logic:
            - Si country_name in ["World"] → INTERNATIONAL
            - Si country_name in ["Europe", "Africa", "Asia", ...] → CONTINENTAL
            - Sinon → NATIONAL
        """
        # Zones internationales
        if country_name.lower() in ["world", "fifa"]:
            return ZoneType.INTERNATIONAL

        # Zones continentales (basé sur les noms utilisés par API-Football)
        continental_zones = [
            "europe", "uefa",
            "africa", "caf",
            "asia", "afc",
            "south-america", "south america", "conmebol",
            "north-america", "north america", "concacaf",
            "oceania", "ofc"
        ]

        if country_name.lower() in continental_zones:
            return ZoneType.CONTINENTAL

        # Par défaut : zone nationale
        return ZoneType.NATIONAL

    def clear_cache(self):
        """Clear le cache de résolution."""
        self._cache.clear()
        logger.info("zone_resolver_cache_cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """Retourne les stats du cache."""
        return {
            "cached_leagues": len(self._cache),
            "cache_size_bytes": sum(
                len(str(v)) for v in self._cache.values()
            )
        }
