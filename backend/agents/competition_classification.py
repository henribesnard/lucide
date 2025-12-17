"""
Competition Classification - Classification détaillée des compétitions.

Fournit une classification multi-dimensionnelle pour les compétitions (internationales, continentales).
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict

class GeographicScope(Enum):
    """Portée géographique de la compétition."""
    GLOBAL = "global"        # Monde entier (FIFA)
    CONTINENTAL = "continental" # Continent entier (UEFA, CONMEBOL, etc.)
    REGIONAL = "regional"    # Sous-région
    NATIONAL = "national"    # Pays spécifique

class CompetitionTier(Enum):
    """Niveau de prestige."""
    ELITE = "elite"          # Top tier (UCL, Libertadores)
    SECONDARY = "secondary"  # Second tier (Europa League, Sudamericana)
    TERTIARY = "tertiary"    # Third tier (Conference League)
    DOMESTIC = "domestic"    # National leagues

class CompetitionFormat(Enum):
    """Format de la compétition."""
    LEAGUE = "league"        # Championnat (round-robin)
    CUP = "cup"              # Coupe (knockout)
    HYBRID = "hybrid"        # Mixte (groupes + knockout)

@dataclass
class CompetitionClassification:
    """Classification détaillée d'une compétition."""
    name: str
    geographic_scope: GeographicScope
    tier: CompetitionTier
    competition_format: CompetitionFormat
    confederation: str      # UEFA, FIFA, CONMEBOL, etc.
    country_code: Optional[str] = None # Pour les compétitions nationales

    def is_international(self) -> bool:
        """Vérifie si c'est une compétition internationale."""
        return self.geographic_scope in [GeographicScope.GLOBAL, GeographicScope.CONTINENTAL]

    def get_display_zone(self) -> str:
        """Retourne le nom de la zone d'affichage."""
        if self.geographic_scope == GeographicScope.GLOBAL:
            return "World"
        elif self.geographic_scope == GeographicScope.CONTINENTAL:
            # Map confederation to continent roughly
            confs = {
                "UEFA": "Europe",
                "CONMEBOL": "South-America",
                "CAF": "Africa",
                "AFC": "Asia",
                "CONCACAF": "North-America",
                "OFC": "Oceania"
            }
            return confs.get(self.confederation, "World")
        else:
            return "National" # Should use country name normally

# Registry des compétitions internationales majeures
# Note: Ce registry est utilisé par zone_resolver.py pour les compétitions sans "country" fixe
INTERNATIONAL_COMPETITIONS = {
    # EUROPE (UEFA)
    "UEFA Champions League": CompetitionClassification(
        "UEFA Champions League", GeographicScope.CONTINENTAL, CompetitionTier.ELITE, CompetitionFormat.HYBRID, "UEFA"
    ),
    "UEFA Europa League": CompetitionClassification(
        "UEFA Europa League", GeographicScope.CONTINENTAL, CompetitionTier.SECONDARY, CompetitionFormat.HYBRID, "UEFA"
    ),
    "UEFA Europa Conference League": CompetitionClassification(
        "UEFA Europa Conference League", GeographicScope.CONTINENTAL, CompetitionTier.TERTIARY, CompetitionFormat.HYBRID, "UEFA"
    ),
    "Euro Championship": CompetitionClassification(
        "Euro Championship", GeographicScope.CONTINENTAL, CompetitionTier.ELITE, CompetitionFormat.CUP, "UEFA"
    ),
    "UEFA Nations League": CompetitionClassification(
        "UEFA Nations League", GeographicScope.CONTINENTAL, CompetitionTier.SECONDARY, CompetitionFormat.LEAGUE, "UEFA"
    ),

    # SOUTH AMERICA (CONMEBOL)
    "Copa Libertadores": CompetitionClassification(
        "Copa Libertadores", GeographicScope.CONTINENTAL, CompetitionTier.ELITE, CompetitionFormat.HYBRID, "CONMEBOL"
    ),
    "Copa Sudamericana": CompetitionClassification(
        "Copa Sudamericana", GeographicScope.CONTINENTAL, CompetitionTier.SECONDARY, CompetitionFormat.HYBRID, "CONMEBOL"
    ),
    "Copa America": CompetitionClassification(
        "Copa America", GeographicScope.CONTINENTAL, CompetitionTier.ELITE, CompetitionFormat.CUP, "CONMEBOL"
    ),

    # GLOBAL (FIFA)
    "World Cup": CompetitionClassification(
        "World Cup", GeographicScope.GLOBAL, CompetitionTier.ELITE, CompetitionFormat.CUP, "FIFA"
    ),
    "FIFA Club World Cup": CompetitionClassification(
        "FIFA Club World Cup", GeographicScope.GLOBAL, CompetitionTier.ELITE, CompetitionFormat.CUP, "FIFA"
    ),

    # AFRICA (CAF)
    "CAF Champions League": CompetitionClassification(
        "CAF Champions League", GeographicScope.CONTINENTAL, CompetitionTier.ELITE, CompetitionFormat.HYBRID, "CAF"
    ),
    "Africa Cup of Nations": CompetitionClassification(
        "Africa Cup of Nations", GeographicScope.CONTINENTAL, CompetitionTier.ELITE, CompetitionFormat.CUP, "CAF"
    ),
}

def get_competition_classification(league_name: str) -> Optional[CompetitionClassification]:
    """Récupère la classification d'une compétition par son nom."""
    return INTERNATIONAL_COMPETITIONS.get(league_name)

def is_international_competition(league_name: str) -> bool:
    """Vérifie si une compétition est internationale."""
    comp = get_competition_classification(league_name)
    return comp is not None and comp.is_international()
