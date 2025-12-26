"""
Router FastAPI pour le service d'analyse de match.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from backend.api.football_api import FootballAPIClient
from backend.config import settings
from .service import MatchAnalysisService
from .types import MatchAnalysisInput, MatchAnalysisResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/match-analysis", tags=["Match Analysis"])


# Dependency pour obtenir le service
def get_match_analysis_service() -> MatchAnalysisService:
    """Cree une instance du service d'analyse."""
    api_client = FootballAPIClient(
        api_key=settings.FOOTBALL_API_KEY,
        base_url=settings.FOOTBALL_API_BASE_URL,
        redis_url=settings.REDIS_URL,
        enable_cache=settings.ENABLE_REDIS_CACHE,
    )
    return MatchAnalysisService(api_client)


@router.post("/analyze", response_model=MatchAnalysisResult)
async def analyze_match(
    input_data: MatchAnalysisInput,
    service: MatchAnalysisService = Depends(get_match_analysis_service),
):
    """
    Analyse un match pour detecter des assets caches.

    Cette analyse implemente l'algorithme complet en 7 etapes:
    - Normalisation des identifiants
    - Definition du perimetre de donnees
    - Collecte des donnees via API-Football
    - Construction des features (equipe, contexte, H2H)
    - Generation des patterns candidats
    - Scoring et selection des assets caches
    - Formatage des insights

    Args:
        input_data: Parametres du match a analyser

    Returns:
        MatchAnalysisResult avec tous les insights detectes

    Raises:
        HTTPException 400: Si les parametres sont invalides
        HTTPException 404: Si league/team non trouvee
        HTTPException 500: Erreur interne
    """
    try:
        logger.info(f"Requete d'analyse: {input_data.team_a} vs {input_data.team_b}")
        result = await service.analyze_match(input_data)
        return result

    except ValueError as e:
        logger.error(f"Erreur de validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except Exception as e:
        logger.error(f"Erreur lors de l'analyse: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne lors de l'analyse",
        )


@router.post("/analyze/quick", response_model=MatchAnalysisResult)
async def analyze_match_quick(
    input_data: MatchAnalysisInput,
    service: MatchAnalysisService = Depends(get_match_analysis_service),
):
    """
    Analyse rapide d'un match (1 saison uniquement).

    Version allegee de l'analyse standard, plus rapide mais moins complete.

    Args:
        input_data: Parametres du match a analyser

    Returns:
        MatchAnalysisResult avec insights (historique limite)

    Raises:
        HTTPException 400: Si les parametres sont invalides
        HTTPException 500: Erreur interne
    """
    try:
        logger.info(f"Requete d'analyse rapide: {input_data.team_a} vs {input_data.team_b}")
        result = await service.analyze_match_quick(input_data)
        return result

    except ValueError as e:
        logger.error(f"Erreur de validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except Exception as e:
        logger.error(f"Erreur lors de l'analyse rapide: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne lors de l'analyse rapide",
        )


@router.post("/analyze/extended")
async def analyze_match_extended(
    input_data: MatchAnalysisInput,
    num_last_matches: int = 30,
    service: MatchAnalysisService = Depends(get_match_analysis_service),
):
    """
    Analyse etendue d'un match avec algorithme complet (toutes competitions).

    Cette analyse utilise le nouveau systeme avec:
    - 30 derniers matchs par equipe (toutes competitions confondues)
    - Events detailles (timeline, buts, cartons, etc.)
    - Statistiques match par match (possession, tirs, passes, etc.)
    - Lineups (compositions, remplacements)
    - Analyses statistiques avancees (pandas/scipy)
    - Detection de 39 types de patterns
    - Impact joueurs et synergies
    - Confrontations coaches

    Args:
        input_data: Parametres du match a analyser
        num_last_matches: Nombre de derniers matchs a analyser (defaut: 30)

    Returns:
        Dict avec:
        - match: Informations du match
        - statistics: Statistiques completes des 2 equipes + H2H
        - insights: Insights detectes (top 20) avec breakdown
        - metadata: Stats d'execution (API calls, temps, coverage)

    Raises:
        HTTPException 400: Si les parametres sont invalides
        HTTPException 404: Si league/team non trouvee
        HTTPException 500: Erreur interne

    Example:
        POST /match-analysis/analyze/extended
        {
            "league": "6",
            "team_a": "Morocco",
            "team_b": "Mali"
        }

        Response:
        {
            "success": true,
            "match": {...},
            "statistics": {...},
            "insights": {
                "total": 6,
                "items": [...],
                "breakdown": {...}
            },
            "metadata": {...}
        }
    """
    try:
        logger.info(f"Requete d'analyse etendue: {input_data.team_a} vs {input_data.team_b} ({num_last_matches} matchs)")
        result = await service.analyze_match_extended(input_data, num_last_matches)
        return result

    except ValueError as e:
        logger.error(f"Erreur de validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except Exception as e:
        logger.error(f"Erreur lors de l'analyse etendue: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne lors de l'analyse etendue",
        )


@router.get("/stats")
async def get_service_stats(
    service: MatchAnalysisService = Depends(get_match_analysis_service),
):
    """
    Retourne les statistiques du service.

    Returns:
        Dict avec statistiques (API calls, version, etc.)
    """
    return service.get_analysis_stats()


@router.get("/health")
async def health_check():
    """
    Verifie que le service est operationnel.

    Returns:
        Dict avec status healthy
    """
    return {
        "status": "healthy",
        "service": "match-analysis",
        "version": "1.0.0",
    }
