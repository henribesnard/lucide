"""
Autonomous Pipeline - Orchestration complète des agents autonomes.

Ce module intègre tous les agents autonomes (QuestionValidator, EndpointPlanner, APIOrchestrator)
pour fournir une interface simple d'utilisation.

Usage:
    pipeline = AutonomousPipeline(api_client, cache_manager, knowledge_base)
    response = await pipeline.process_question("Statistiques de PSG ?")
"""

import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import structlog
from backend.agents.context_types import StructuredContext

from backend.agents.question_validator import QuestionValidator, QuestionType, ValidationResult
from backend.agents.endpoint_planner import EndpointPlanner, ExecutionPlan
from backend.agents.api_orchestrator import APIOrchestrator, ExecutionResult, SimpleCircuitBreaker
from backend.knowledge.endpoint_knowledge_base import EndpointKnowledgeBase

logger = structlog.get_logger()


@dataclass
class PipelineResult:
    """Résultat complet du traitement d'une question."""

    # Question
    original_question: str
    provided_context: Optional[StructuredContext] = None

    # Validation
    validation_result: Optional[ValidationResult] = None
    needs_clarification: bool = False
    clarification_questions: List[str] = field(default_factory=list)

    # Planning
    execution_plan: Optional[ExecutionPlan] = None

    # Execution
    execution_result: Optional[ExecutionResult] = None

    # Data collectée
    collected_data: Dict[str, Any] = field(default_factory=dict)

    # Metrics
    total_time_ms: int = 0
    validation_time_ms: int = 0
    planning_time_ms: int = 0
    execution_time_ms: int = 0

    # Success
    success: bool = False
    errors: List[str] = field(default_factory=list)

    # Cache metrics
    cache_hit_rate: float = 0.0
    total_api_calls: int = 0
    total_cache_hits: int = 0


class AutonomousPipeline:
    """
    Pipeline complet pour traiter les questions utilisateur de manière autonome.

    Le pipeline suit ce flow:
    1. Question → QuestionValidator (validation + extraction d'entités)
    2. Entities → EndpointPlanner (planification endpoints)
    3. Plan → APIOrchestrator (exécution avec retry/cache/circuit breaker)
    4. Data → Response (à implémenter: analyse et génération de réponse)

    Features:
    - Validation automatique des questions
    - Planification intelligente des endpoints
    - Exécution parallèle avec cache
    - Gestion d'erreurs robuste
    - Métriques détaillées
    - Logging structuré
    """

    def __init__(
        self,
        api_client=None,
        cache_manager=None,
        knowledge_base: Optional[EndpointKnowledgeBase] = None,
        circuit_breaker: Optional[SimpleCircuitBreaker] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialise le pipeline autonome.

        Args:
            api_client: Client API pour appels API-Football
            cache_manager: Gestionnaire de cache (IntelligentCacheManager)
            knowledge_base: Base de connaissance des endpoints
            circuit_breaker: Circuit breaker pour résilience
            max_retries: Nombre max de retries par appel
            retry_delay: Délai entre retries (secondes)
        """
        # Initialize knowledge base
        self.knowledge_base = knowledge_base or EndpointKnowledgeBase()

        # Initialize agents
        self.validator = QuestionValidator()
        self.planner = EndpointPlanner(self.knowledge_base)
        self.orchestrator = APIOrchestrator(
            cache_manager=cache_manager,
            api_client=api_client,
            circuit_breaker=circuit_breaker,
            max_retries=max_retries,
            retry_delay=retry_delay
        )

        logger.info(
            "autonomous_pipeline_initialized",
            max_retries=max_retries,
            has_cache=cache_manager is not None,
            has_api_client=api_client is not None
        )

    async def process_question(
        self,
        question: str,
        context: Optional[StructuredContext] = None,
        user_id: Optional[str] = None,
        skip_execution: bool = False
    ) -> PipelineResult:
        """
        Traite une question utilisateur de manière autonome.

        Args:
            question: Question de l'utilisateur
            context: Contexte structuré (zone, league, fixture)
            user_id: ID utilisateur (pour cache multi-utilisateurs)
            skip_execution: Si True, ne fait que validation + planning (pas d'appels API)

        Returns:
            PipelineResult avec toutes les données collectées
        """
        start_time = time.time()

        logger.info(
            "pipeline_start",
            question=question,
            has_context=context is not None,
            user_id=user_id,
            skip_execution=skip_execution
        )

        result = PipelineResult(
            original_question=question,
            provided_context=context
        )

        try:
            # 1. VALIDATION
            validation_start = time.time()
            validation_result = await self.validator.validate(question, context=context)
            validation_time = time.time() - validation_start

            result.validation_result = validation_result
            result.validation_time_ms = int(validation_time * 1000)

            logger.info(
                "pipeline_validation_complete",
                question_type=validation_result.question_type.value if validation_result.question_type else None,
                is_complete=validation_result.is_complete,
                entities_count=sum(len(v) if isinstance(v, list) else 1 for v in validation_result.extracted_entities.values()),
                duration_ms=result.validation_time_ms
            )

            # Check if clarification needed
            if not validation_result.is_complete:
                result.needs_clarification = True
                result.clarification_questions = validation_result.clarification_questions
                result.success = False
                result.errors.append("Question incomplete - clarification needed")

                logger.warning(
                    "pipeline_needs_clarification",
                    missing_info=validation_result.missing_info,
                    clarification_count=len(validation_result.clarification_questions)
                )

                result.total_time_ms = int((time.time() - start_time) * 1000)
                return result

            # 2. PLANNING
            planning_start = time.time()
            execution_plan = await self.planner.plan(
                question,
                validation_result.extracted_entities,
                validation_result.question_type
            )
            planning_time = time.time() - planning_start

            result.execution_plan = execution_plan
            result.planning_time_ms = int(planning_time * 1000)

            logger.info(
                "pipeline_planning_complete",
                endpoints_count=len(execution_plan.endpoints),
                estimated_api_calls=execution_plan.estimated_api_calls,
                estimated_duration_ms=execution_plan.estimated_duration_ms,
                optimizations_count=len(execution_plan.optimizations_applied),
                duration_ms=result.planning_time_ms
            )

            # Stop here if skip_execution
            if skip_execution:
                result.success = True
                result.total_time_ms = int((time.time() - start_time) * 1000)

                logger.info(
                    "pipeline_complete_without_execution",
                    total_time_ms=result.total_time_ms
                )

                return result

            # 3. EXECUTION
            execution_start = time.time()
            execution_result = await self.orchestrator.execute(execution_plan)
            execution_time = time.time() - execution_start

            result.execution_result = execution_result
            result.execution_time_ms = int(execution_time * 1000)
            result.collected_data = execution_result.collected_data
            result.total_api_calls = execution_result.total_api_calls
            result.total_cache_hits = execution_result.total_cache_hits

            # Calculate cache hit rate
            total_calls = result.total_api_calls + result.total_cache_hits
            if total_calls > 0:
                result.cache_hit_rate = result.total_cache_hits / total_calls

            # Success if execution succeeded
            result.success = execution_result.success
            result.errors = execution_result.errors

            logger.info(
                "pipeline_execution_complete",
                success=execution_result.success,
                api_calls=execution_result.total_api_calls,
                cache_hits=execution_result.total_cache_hits,
                cache_hit_rate=f"{result.cache_hit_rate:.1%}",
                errors_count=len(execution_result.errors),
                duration_ms=result.execution_time_ms
            )

        except Exception as e:
            result.success = False
            result.errors.append(f"Pipeline error: {str(e)}")

            logger.error(
                "pipeline_error",
                error=str(e),
                question=question
            )

        # Total time
        result.total_time_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "pipeline_complete",
            success=result.success,
            total_time_ms=result.total_time_ms,
            validation_ms=result.validation_time_ms,
            planning_ms=result.planning_time_ms,
            execution_ms=result.execution_time_ms,
            cache_hit_rate=f"{result.cache_hit_rate:.1%}"
        )

        return result

    async def process_batch(
        self,
        questions: List[str],
        user_id: Optional[str] = None
    ) -> List[PipelineResult]:
        """
        Traite un batch de questions en parallèle.

        Args:
            questions: Liste de questions
            user_id: ID utilisateur

        Returns:
            Liste de PipelineResult
        """
        import asyncio

        logger.info("pipeline_batch_start", questions_count=len(questions))

        # Process all questions in parallel
        tasks = [
            self.process_question(q, user_id=user_id)
            for q in questions
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to failed results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_result = PipelineResult(
                    original_question=questions[i],
                    success=False,
                    errors=[f"Batch processing error: {str(result)}"]
                )
                final_results.append(failed_result)
            else:
                final_results.append(result)

        success_count = sum(1 for r in final_results if r.success)

        logger.info(
            "pipeline_batch_complete",
            questions_count=len(questions),
            success_count=success_count,
            failure_count=len(questions) - success_count
        )

        return final_results

    def get_metrics(self) -> Dict[str, Any]:
        """
        Récupère les métriques du circuit breaker.

        Returns:
            Dict avec métriques
        """
        cb = self.orchestrator.circuit_breaker

        return {
            "circuit_breaker": {
                "state": cb.state,
                "failures": cb.failures,
                "threshold": cb.failure_threshold,
                "is_open": cb.is_open()
            }
        }

    async def validate_only(self, question: str) -> ValidationResult:
        """
        Valide une question sans exécution (utile pour tester).

        Args:
            question: Question à valider

        Returns:
            ValidationResult
        """
        return await self.validator.validate(question)

    async def plan_only(
        self,
        question: str,
        entities: Optional[Dict[str, Any]] = None,
        question_type: Optional[QuestionType] = None
    ) -> ExecutionPlan:
        """
        Planifie les endpoints sans exécution (utile pour tester).

        Args:
            question: Question
            entities: Entités extraites (si None, fait validation d'abord)
            question_type: Type de question (si None, fait validation d'abord)

        Returns:
            ExecutionPlan
        """
        if entities is None or question_type is None:
            validation_result = await self.validator.validate(question)
            entities = validation_result.extracted_entities
            question_type = validation_result.question_type

        return await self.planner.plan(question, entities, question_type)
