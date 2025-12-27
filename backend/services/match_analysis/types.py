"""Types et modeles pour le service d'analyse de match."""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# INPUT MODELS
# ============================================================================


class MatchAnalysisInput(BaseModel):
    """Parametres d'entree pour l'analyse de match."""

    league: str = Field(..., description="Nom ou ID de la league")
    league_type: Literal["league", "cup"] = Field(..., description="Type de competition")
    round: Optional[str] = Field(None, description="Round (ex: 'Group Stage - 2')")
    stadium: Optional[str] = Field(None, description="Nom du stade")
    referee: Optional[str] = Field(None, description="Nom de l'arbitre")
    team_a: str = Field(..., description="Nom ou ID de l'equipe A")
    team_b: str = Field(..., description="Nom ou ID de l'equipe B")
    coach_team_a: Optional[str] = Field(None, description="Coach de l'equipe A")
    coach_team_b: Optional[str] = Field(None, description="Coach de l'equipe B")
    season: Optional[int] = Field(None, description="Saison (ex: 2023)")
    num_seasons_history: int = Field(3, description="Nombre de saisons historiques a analyser", ge=1, le=10)


# ============================================================================
# DATA MODELS
# ============================================================================


class CoverageInfo(BaseModel):
    """Information sur la couverture des donnees."""

    events: bool = False
    lineups: bool = False
    statistics_fixtures: bool = False
    statistics_players: bool = False
    predictions: bool = False


class NormalizedIDs(BaseModel):
    """IDs normalises pour les entites."""

    league_id: int
    league_name: str
    league_type: str = "cup"  # "cup" ou "league"
    season: int
    team_a_id: int
    team_a_name: str
    team_b_id: int
    team_b_name: str
    venue_id: Optional[int] = None
    venue_name: Optional[str] = None
    coach_a_id: Optional[int] = None
    coach_b_id: Optional[int] = None
    coverage: CoverageInfo


# ============================================================================
# FEATURE MODELS
# ============================================================================


class TeamFeatures(BaseModel):
    """Features d'une equipe."""

    # Forme globale
    wins: int = 0
    draws: int = 0
    loses: int = 0
    win_rate: float = 0.0

    # Home/Away split
    home_wins: int = 0
    home_draws: int = 0
    home_loses: int = 0
    away_wins: int = 0
    away_draws: int = 0
    away_loses: int = 0

    # Buts
    goals_for: int = 0
    goals_against: int = 0
    goals_for_first_half: int = 0
    goals_for_second_half: int = 0
    goals_against_first_half: int = 0
    goals_against_second_half: int = 0

    # Buts par tranche de temps
    goals_for_0_15: int = 0
    goals_for_16_30: int = 0
    goals_for_31_45: int = 0
    goals_for_46_60: int = 0
    goals_for_61_75: int = 0
    goals_for_76_90: int = 0

    # Clean sheets
    clean_sheets: int = 0
    failed_to_score: int = 0

    # Formations tactiques (formation -> nb matchs)
    formations: Dict[str, int] = Field(default_factory=dict)
    win_rate_by_formation: Dict[str, float] = Field(default_factory=dict)

    # Penalties
    penalties_scored: int = 0
    penalties_missed: int = 0
    penalties_total: int = 0
    penalty_success_rate: float = 0.0

    # Series en cours
    current_win_streak: int = 0
    current_draw_streak: int = 0
    current_lose_streak: int = 0
    biggest_win_streak: int = 0

    # Style de jeu
    avg_possession: float = 0.0
    avg_shots: float = 0.0
    avg_shots_on_target: float = 0.0
    avg_corners: float = 0.0

    # Cartons
    yellow_cards: int = 0
    red_cards: int = 0
    yellow_cards_76_90: int = 0  # Exemple tranche de temps


class ContextFeatures(BaseModel):
    """Features de contexte (round, stadium, referee, coach)."""

    # Round-specific
    round_wins: int = 0
    round_draws: int = 0
    round_loses: int = 0
    round_win_rate: float = 0.0
    round_matches: int = 0

    # Stadium-specific
    stadium_wins: int = 0
    stadium_draws: int = 0
    stadium_loses: int = 0
    stadium_win_rate: float = 0.0
    stadium_matches: int = 0

    # Referee-specific
    referee_matches: int = 0
    referee_yellow_cards: int = 0
    referee_red_cards: int = 0
    referee_penalties: int = 0

    # Coach-specific
    coach_wins: int = 0
    coach_draws: int = 0
    coach_loses: int = 0
    coach_win_rate: float = 0.0
    coach_matches: int = 0


class H2HFeatures(BaseModel):
    """Features Head-to-Head."""

    total_matches: int = 0
    team_a_wins: int = 0
    draws: int = 0
    team_b_wins: int = 0
    team_a_win_rate: float = 0.0

    # H2H par contexte
    h2h_at_stadium_matches: int = 0
    h2h_at_stadium_wins: int = 0
    h2h_in_round_matches: int = 0
    h2h_in_round_wins: int = 0


class FeatureSet(BaseModel):
    """Ensemble complet de features pour une analyse."""

    team_a: TeamFeatures
    team_b: TeamFeatures
    team_a_context: ContextFeatures
    team_b_context: ContextFeatures
    h2h: H2HFeatures
    baseline_predictions: Optional[Dict[str, Any]] = None


# ============================================================================
# PATTERN MODELS
# ============================================================================


class Pattern(BaseModel):
    """Un pattern detecte."""

    pattern_type: str = Field(..., description="Type de pattern (round, stadium, formation, etc.)")
    condition: str = Field(..., description="Condition du pattern")
    team: str = Field(..., description="Equipe concernee (team_a ou team_b)")

    # Stats observees
    wins: int = 0
    draws: int = 0
    loses: int = 0
    matches: int = 0
    win_rate: float = 0.0

    # Stats baseline
    baseline_win_rate: float = 0.0
    baseline_matches: int = 0

    # Scoring
    delta_vs_baseline: float = 0.0  # En points de pourcentage
    sample_size_score: float = 0.0  # 0-1
    recency_score: float = 0.0  # 0-1
    confidence_score: float = 0.0  # 0-1

    # Metadata
    seasons_covered: List[int] = Field(default_factory=list)
    date_range: Optional[str] = None
    is_extreme: bool = False  # 0% ou 100%
    is_strong: bool = False  # >= 80%


# ============================================================================
# OUTPUT MODELS
# ============================================================================


class HiddenAsset(BaseModel):
    """Un asset cache detecte (insight final)."""

    pattern: Pattern
    insight_text: str = Field(..., description="Description textuelle de l'insight")
    confidence_level: Literal["low", "medium", "high"] = Field(..., description="Niveau de confiance")
    category: str = Field(..., description="Categorie (rare, strong, differential)")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MatchAnalysisResult(BaseModel):
    """Resultat complet de l'analyse."""

    # Input
    input: MatchAnalysisInput

    # IDs normalises
    normalized_ids: NormalizedIDs

    # Features extraites
    features: FeatureSet

    # Patterns detectes
    all_patterns: List[Pattern] = Field(default_factory=list)

    # Assets caches (insights finals)
    hidden_assets: List[HiddenAsset] = Field(default_factory=list)

    # Metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_api_calls: int = 0
    processing_time_seconds: float = 0.0
    warnings: List[str] = Field(default_factory=list)
