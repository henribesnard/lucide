"""
Endpoint Planner for autonomous agents.

This module plans which API endpoints to call based on the user's question
and the knowledge base, optimizing for minimal API calls.

Implemented in Phase 4.
"""

import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from backend.knowledge.endpoint_knowledge_base import EndpointKnowledgeBase, EndpointMetadata
from backend.agents.question_validator import QuestionType
from backend.monitoring.autonomous_agents_metrics import logger


@dataclass
class EndpointCall:
    """Represents a planned endpoint call with dependencies."""

    call_id: str
    endpoint_name: str
    params: Dict[str, Any]
    depends_on: List[str] = field(default_factory=list)
    reason: str = ""
    is_optional: bool = False
    output_mapping: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'call_id': self.call_id,
            'endpoint_name': self.endpoint_name,
            'params': self.params,
            'depends_on': self.depends_on,
            'reason': self.reason,
            'is_optional': self.is_optional
        }


@dataclass
class ExecutionPlan:
    """
    Execution plan for answering a question.

    Contains the sequence of endpoint calls with dependency resolution.
    """

    question: str
    endpoints: List[EndpointCall] = field(default_factory=list)
    estimated_api_calls: int = 0
    reasoning: str = ""
    cached_data: Dict[str, Any] = field(default_factory=dict)
    optimizations_applied: List[str] = field(default_factory=list)
    estimated_duration_ms: int = 0

    def get_sequential_calls(self) -> List[List[EndpointCall]]:
        """
        Get calls organized by execution level for parallel execution.

        Returns:
            List of levels, each level contains calls that can be executed in parallel

        Example:
            [
                [call1, call2],  # Level 0: no dependencies, can run in parallel
                [call3],         # Level 1: depends on call1
                [call4, call5]   # Level 2: depend on call3, can run in parallel
            ]
        """
        if not self.endpoints:
            return []

        # Create call map
        call_map = {call.call_id: call for call in self.endpoints}

        # Calculate levels
        levels = []
        processed = set()

        while len(processed) < len(self.endpoints):
            current_level = []

            for call in self.endpoints:
                if call.call_id in processed:
                    continue

                # Check if all dependencies are satisfied
                if all(dep in processed for dep in call.depends_on):
                    current_level.append(call)

            if not current_level:
                # Cycle detected or error
                logger.error(
                    "dependency_cycle_detected",
                    processed=list(processed),
                    remaining=[c.call_id for c in self.endpoints if c.call_id not in processed]
                )
                break

            levels.append(current_level)
            processed.update(call.call_id for call in current_level)

        return levels

    def to_dict(self) -> Dict[str, Any]:
        return {
            'question': self.question,
            'endpoints': [e.to_dict() for e in self.endpoints],
            'estimated_api_calls': self.estimated_api_calls,
            'reasoning': self.reasoning,
            'optimizations': self.optimizations_applied,
            'estimated_duration_ms': self.estimated_duration_ms
        }


class EndpointPlanner:
    """
    Plans which endpoints to call to answer a question.

    Features:
    - Endpoint selection using knowledge base
    - Redundancy filtering (cache-aware)
    - Optimization with enriched endpoints
    - Dependency resolution
    - Parallel execution planning
    """

    def __init__(
        self,
        knowledge_base: EndpointKnowledgeBase,
        cache_manager=None,
        llm_client=None
    ):
        """
        Initialize the endpoint planner.

        Args:
            knowledge_base: EndpointKnowledgeBase instance
            cache_manager: Optional cache manager for optimization
            llm_client: Optional LLM client for advanced planning
        """
        self.kb = knowledge_base
        self.cache = cache_manager
        self.llm = llm_client

        # Question type to endpoints mapping
        self.question_type_endpoints = {
            QuestionType.MATCH_LIVE_INFO: [
                'teams_search', 'fixtures_search', 'fixtures_events'
            ],
            QuestionType.MATCH_PREDICTION: [
                'teams_search', 'predictions', 'fixtures_headtohead', 'team_statistics'
            ],
            QuestionType.TEAM_COMPARISON: [
                'teams_search', 'team_statistics', 'fixtures_headtohead', 'standings'
            ],
            QuestionType.TEAM_STATS: [
                'teams_search', 'team_statistics', 'standings'
            ],
            QuestionType.PLAYER_INFO: [
                'players_search', 'players_statistics'
            ],
            QuestionType.LEAGUE_INFO: [
                'leagues_search', 'standings'
            ],
            QuestionType.H2H: [
                'teams_search', 'fixtures_headtohead', 'fixtures_search'
            ],
            QuestionType.STANDINGS: [
                'standings', 'leagues_search'
            ],
        }

    async def plan(
        self,
        question: str,
        entities: Dict[str, Any],
        question_type: Optional[QuestionType] = None,
        context_id: Optional[str] = None
    ) -> ExecutionPlan:
        """
        Create an optimized execution plan for the question.

        Args:
            question: User's question
            entities: Extracted entities from QuestionValidator
            question_type: Type of question (from QuestionValidator)
            context_id: Optional context ID for cache lookup

        Returns:
            ExecutionPlan with optimized endpoint calls
        """
        logger.info(
            "planning_endpoints",
            question=question,
            question_type=question_type.value if question_type else None,
            entities=entities
        )

        # 1. Identify candidate endpoints
        candidate_endpoints = self._identify_candidate_endpoints(
            question_type,
            entities
        )
        logger.info("candidate_endpoints", count=len(candidate_endpoints))

        # 2. Optimize with enriched endpoints
        optimizations = []
        optimized_endpoints = self._optimize_with_enriched_endpoints(
            candidate_endpoints,
            optimizations
        )
        logger.info("after_enriched_optimization", count=len(optimized_endpoints))

        # 3. Resolve dependencies and create calls
        execution_calls = self._resolve_dependencies(
            optimized_endpoints,
            entities
        )
        logger.info("execution_calls_created", count=len(execution_calls))

        # 4. Calculate estimated cost
        estimated_cost = len([c for c in execution_calls if not c.is_optional])
        estimated_duration = self._estimate_duration(execution_calls)

        # 5. Generate reasoning
        reasoning = self._generate_reasoning(
            question_type,
            execution_calls,
            optimizations
        )

        plan = ExecutionPlan(
            question=question,
            endpoints=execution_calls,
            estimated_api_calls=estimated_cost,
            reasoning=reasoning,
            optimizations_applied=optimizations,
            estimated_duration_ms=estimated_duration
        )

        logger.info(
            "plan_created",
            api_calls=estimated_cost,
            levels=len(plan.get_sequential_calls()),
            optimizations=len(optimizations)
        )

        return plan

    def _identify_candidate_endpoints(
        self,
        question_type: Optional[QuestionType],
        entities: Dict[str, Any]
    ) -> List[str]:
        """
        Identify candidate endpoints based on question type and entities.

        Args:
            question_type: Type of question
            entities: Extracted entities

        Returns:
            List of endpoint names
        """
        candidates = set()

        # Add endpoints based on question type
        if question_type and question_type in self.question_type_endpoints:
            candidates.update(self.question_type_endpoints[question_type])

        # Add endpoints based on entities
        if 'teams' in entities:
            candidates.add('teams_search')

            if len(entities['teams']) >= 2:
                # Multiple teams → probably need H2H
                candidates.add('fixtures_headtohead')

        if 'players' in entities:
            candidates.add('players_search')

        if 'leagues' in entities:
            candidates.add('leagues_search')
            # If league specified, might want standings
            candidates.add('standings')

        if 'dates' in entities:
            # Date specified → fixtures by date
            candidates.add('fixtures_search')

        return list(candidates)

    def _optimize_with_enriched_endpoints(
        self,
        candidate_endpoints: List[str],
        optimizations: List[str]
    ) -> List[str]:
        """
        Optimize by replacing multiple endpoints with enriched ones.

        Args:
            candidate_endpoints: List of candidate endpoint names
            optimizations: List to append optimization descriptions

        Returns:
            Optimized list of endpoint names
        """
        optimized = set(candidate_endpoints)

        # Check each endpoint for enriched alternatives
        for endpoint_name in candidate_endpoints:
            endpoint = self.kb.get_endpoint(endpoint_name)

            if not endpoint or not endpoint.can_replace:
                continue

            # Check if this enriched endpoint can replace multiple others
            replaceable = [ep for ep in endpoint.can_replace if ep in optimized]

            if len(replaceable) >= 2:
                # This enriched endpoint can replace multiple
                optimized.add(endpoint_name)
                for ep in replaceable:
                    optimized.discard(ep)

                optimizations.append(
                    f"Used {endpoint_name} (enriched) instead of {len(replaceable)} endpoints"
                )
                logger.info(
                    "enriched_optimization",
                    enriched=endpoint_name,
                    replaced=replaceable
                )

        return list(optimized)

    def _resolve_dependencies(
        self,
        endpoint_names: List[str],
        entities: Dict[str, Any]
    ) -> List[EndpointCall]:
        """
        Resolve dependencies and create ordered endpoint calls.

        Args:
            endpoint_names: List of endpoint names to call
            entities: Extracted entities

        Returns:
            List of EndpointCall with dependencies resolved
        """
        calls = []
        call_counter = 0

        # Track which calls provide which data
        providers = {}  # data_type -> call_id

        # Process in two passes: search endpoints first, then others
        # This ensures dependencies are resolved correctly
        search_endpoints = [e for e in endpoint_names if e in ['teams_search', 'players_search', 'leagues_search']]
        other_endpoints = [e for e in endpoint_names if e not in search_endpoints]
        ordered_endpoints = search_endpoints + other_endpoints

        for endpoint_name in ordered_endpoints:
            endpoint = self.kb.get_endpoint(endpoint_name)
            if not endpoint:
                continue

            call_id = f"call_{call_counter}"
            call_counter += 1

            params = {}
            depends_on = []
            reason = f"Get {endpoint.description}"

            # Determine parameters and dependencies
            if endpoint_name == 'teams_search':
                if 'teams' in entities and len(entities['teams']) > 0:
                    # Create one call per team
                    for i, team in enumerate(entities['teams'][:2]):  # Max 2 teams
                        team_call_id = f"call_{call_counter}"
                        call_counter += 1

                        calls.append(EndpointCall(
                            call_id=team_call_id,
                            endpoint_name='teams_search',
                            params={'name': team},
                            reason=f"Resolve team '{team}' to ID",
                            output_mapping={'team_id': f'teams.{i}.id'}
                        ))

                        providers[f'team_id_{i}'] = team_call_id
                continue  # Skip adding generic call (whether teams found or not)

            elif endpoint_name == 'team_statistics':
                # Depends on teams_search
                if 'team_id_0' in providers:
                    depends_on.append(providers['team_id_0'])
                    params['team'] = '<from_teams_search>'
                    params['season'] = 2025  # Default current season
                    params['league'] = 61  # Default Ligue 1

            elif endpoint_name == 'fixtures_headtohead':
                # Depends on both teams
                if 'team_id_0' in providers and 'team_id_1' in providers:
                    depends_on.extend([providers['team_id_0'], providers['team_id_1']])
                    params['h2h'] = '<from_teams_search_0>-<from_teams_search_1>'

            elif endpoint_name == 'fixtures_search':
                # May depend on teams_search
                if 'team_id_0' in providers:
                    depends_on.append(providers['team_id_0'])
                    params['team'] = '<from_teams_search>'

                if 'dates' in entities and len(entities['dates']) > 0:
                    params['date'] = entities['dates'][0]

            elif endpoint_name == 'standings':
                if 'leagues' in entities:
                    # Try to resolve league name to ID
                    params['league'] = 61  # Default Ligue 1
                    params['season'] = 2025

            elif endpoint_name == 'players_search':
                if 'players' in entities and len(entities['players']) > 0:
                    params['search'] = entities['players'][0]
                    providers['player'] = call_id

            elif endpoint_name == 'players_statistics':
                # Depends on players_search
                if 'player' in providers:
                    depends_on.append(providers['player'])
                    params['id'] = '<from_players_search>'
                    params['season'] = 2025

            # Add call (if not skipped by continue)
            call = EndpointCall(
                call_id=call_id,
                endpoint_name=endpoint_name,
                params=params,
                depends_on=depends_on,
                reason=reason
            )
            calls.append(call)

        return calls

    def _estimate_duration(self, calls: List[EndpointCall]) -> int:
        """
        Estimate total execution duration in milliseconds.

        Args:
            calls: List of endpoint calls

        Returns:
            Estimated duration in milliseconds
        """
        # Assume average API call takes 500ms
        # But calls in same level can run in parallel
        plan = ExecutionPlan(question="", endpoints=calls)
        levels = plan.get_sequential_calls()

        # Duration = sum of max duration per level
        total_duration = 0
        for level in levels:
            # Max duration in this level (all parallel)
            level_duration = max(500 for _ in level) if level else 0
            total_duration += level_duration

        return total_duration

    def _generate_reasoning(
        self,
        question_type: Optional[QuestionType],
        calls: List[EndpointCall],
        optimizations: List[str]
    ) -> str:
        """
        Generate human-readable reasoning for the plan.

        Args:
            question_type: Type of question
            calls: List of endpoint calls
            optimizations: List of optimizations applied

        Returns:
            Reasoning string
        """
        reasoning_parts = []

        # Question type
        if question_type:
            reasoning_parts.append(f"Question type: {question_type.value}")

        # Number of calls
        reasoning_parts.append(f"Total API calls: {len(calls)}")

        # Parallel execution
        plan = ExecutionPlan(question="", endpoints=calls)
        levels = plan.get_sequential_calls()
        if len(levels) > 1:
            reasoning_parts.append(f"Execution levels: {len(levels)} (parallel execution enabled)")

        # Optimizations
        if optimizations:
            reasoning_parts.append(f"Optimizations: {len(optimizations)}")
            for opt in optimizations:
                reasoning_parts.append(f"  - {opt}")

        # Endpoint sequence
        reasoning_parts.append("Endpoint sequence:")
        for i, level in enumerate(levels):
            if len(level) == 1:
                reasoning_parts.append(f"  Level {i}: {level[0].endpoint_name}")
            else:
                reasoning_parts.append(f"  Level {i} (parallel): {', '.join(c.endpoint_name for c in level)}")

        return "\n".join(reasoning_parts)
