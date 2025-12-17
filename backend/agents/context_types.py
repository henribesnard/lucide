"""
Types pour le système de contexte structuré.
Permet de fournir un contexte hiérarchique aux agents autonomes.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List

class ZoneType(Enum):
    """Type de zone géographique."""
    NATIONAL = "national"        # Pays spécifique (France, England, etc.)
    CONTINENTAL = "continental"  # Continent (Europe, Africa, Asia, etc.)
    INTERNATIONAL = "international"  # Mondial (World)

@dataclass
class Zone:
    """
    Représente une zone géographique.

    Examples:
        >>> Zone(name="France", code="FR", zone_type=ZoneType.NATIONAL)
        >>> Zone(name="Europe", code=None, zone_type=ZoneType.CONTINENTAL)
    """
    name: str                    # "France", "Europe", "World"
    code: Optional[str] = None   # "FR", "GB" (null pour zones internationales)
    zone_type: ZoneType = ZoneType.NATIONAL

    @classmethod
    def from_country_code(cls, code: str, name: Optional[str] = None) -> "Zone":
        """
        Crée une zone depuis un code pays (FR, GB, etc.)

        Args:
            code: Code pays (FR, GB, ES, etc.)
            name: Nom du pays (optionnel, sinon utilise le code)

        Returns:
            Zone instance
        """
        return cls(
            name=name or code,
            code=code,
            zone_type=ZoneType.NATIONAL
        )

    @classmethod
    def from_international_name(cls, name: str) -> "Zone":
        """
        Crée une zone internationale (Europe, World, Africa, etc.)

        Args:
            name: Nom de la zone (Europe, World, Africa, etc.)

        Returns:
            Zone instance
        """
        zone_type = (
            ZoneType.INTERNATIONAL if name == "World"
            else ZoneType.CONTINENTAL
        )
        return cls(name=name, code=None, zone_type=zone_type)

@dataclass
class StructuredContext:
    """
    Contexte structuré fourni par le caller (UI, API, etc.).

    Permet de fournir un contexte hiérarchique pour résoudre les entités
    sans clarification utilisateur.

    Exemples d'usage:
        >>> # Question "Classement" avec contexte
        >>> context = StructuredContext(
        ...     zone=Zone.from_country_code("FR", "France"),
        ...     league="Ligue 1",
        ...     league_id=61
        ... )
        >>> # Le système peut maintenant répondre sans clarification

        >>> # Question "Stats match" avec fixture
        >>> context = StructuredContext(
        ...     zone=Zone.from_country_code("FR"),
        ...     league="Ligue 1",
        ...     fixture="PSG vs OM",
        ...     fixture_id=12345
        ... )
    """

    # Niveau 1: Zone (required)
    zone: Optional[Zone] = None

    # Niveau 2: League (optional)
    league: Optional[str] = None      # "Ligue 1", "Premier League"
    league_id: Optional[int] = None   # 61, 39

    # Niveau 3: Fixture (optional)
    fixture: Optional[str] = None     # "PSG vs OM"
    fixture_id: Optional[int] = None  # 12345

    # Métadonnées
    season: Optional[int] = None      # 2024, 2025

    def to_dict(self) -> dict:
        """
        Convert to dict for JSON serialization.

        Returns:
            Dict representation
        """
        return {
            "zone": {
                "name": self.zone.name,
                "code": self.zone.code,
                "type": self.zone.zone_type.value
            } if self.zone else None,
            "league": self.league,
            "league_id": self.league_id,
            "fixture": self.fixture,
            "fixture_id": self.fixture_id,
            "season": self.season
        }

    def __post_init__(self):
        """Auto-classification de la league si fournie."""
        # Import ici pour éviter circular imports
        if self.league and not hasattr(self, '_classification_checked'):
            from backend.agents.competition_classification import (
                get_competition_classification
            )

            classification = get_competition_classification(self.league)

            # Si c'est une compétition internationale, ajuster la zone automatiquement
            if classification and classification.is_international():
                zone_name = classification.get_display_zone()
                if self.zone is None:  # Seulement si pas déjà définie
                    self.zone = Zone.from_international_name(zone_name)

            self._classification_checked = True
