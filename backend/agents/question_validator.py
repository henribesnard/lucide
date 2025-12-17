"""
Question Validator for autonomous agents.

This module validates user questions, extracts entities,
and requests clarifications when information is missing.

Implemented in Phase 3.
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime, date
from backend.monitoring.autonomous_agents_metrics import logger
from backend.agents.context_types import StructuredContext, Zone, ZoneType


class QuestionType(Enum):
    """Types of questions the system can handle."""
    MATCH_LIVE_INFO = "match_live_info"
    MATCH_PREDICTION = "match_prediction"
    TEAM_COMPARISON = "team_comparison"
    TEAM_STATS = "team_stats"
    PLAYER_INFO = "player_info"
    LEAGUE_INFO = "league_info"
    H2H = "head_to_head"
    STANDINGS = "standings"
    UNKNOWN = "unknown"


class Language(Enum):
    """Supported languages."""
    FRENCH = "fr"
    ENGLISH = "en"
    UNKNOWN = "unknown"


@dataclass
class ValidationResult:
    """Result of question validation."""
    is_complete: bool
    question_type: Optional[QuestionType]
    extracted_entities: Dict[str, Any]
    missing_info: List[str]
    clarification_questions: List[str]
    confidence: float = 1.0
    detected_language: Language = Language.UNKNOWN


class QuestionValidator:
    """
    Validates questions and extracts required information.

    Features:
    - Entity extraction (teams, players, dates, leagues)
    - Question type classification
    - Required info checking
    - Clarification generation in French/English
    - Language detection
    """

    def __init__(self, llm_client=None):
        """
        Initialize the question validator.

        Args:
            llm_client: Optional LLM client for advanced extraction
        """
        self.llm = llm_client

        # Team name patterns (French and English)
        self.team_patterns = [
            # French teams
            r'\b(PSG|Paris|Paris SG|Paris Saint[- ]?Germain)\b',
            r'\b(OM|Marseille|Olympique Marseille)\b',
            r'\b(OL|Lyon|Olympique Lyonnais)\b',
            r'\b(Monaco|AS Monaco)\b',
            r'\b(Lille|LOSC)\b',
            r'\b(Nice|OGC Nice)\b',
            r'\b(Rennes|Stade Rennais)\b',
            r'\b(Lens|RC Lens)\b',
            r'\b(Saint[- ]?[ÉE]tienne|ASSE)\b',

            # English teams
            r'\b(Manchester United|Man Utd|Man United)\b',
            r'\b(Manchester City|Man City)\b',
            r'\b(Liverpool|Liverpool FC)\b',
            r'\b(Chelsea|Chelsea FC)\b',
            r'\b(Arsenal|Arsenal FC)\b',
            r'\b(Tottenham|Spurs|Tottenham Hotspur)\b',

            # Spanish teams
            r'\b(Real Madrid|Real|Madrid)\b',
            r'\b(Barcelona|Barça|Barca|FC Barcelona)\b',
            r'\b(Atletico Madrid|Atleti|Atl[ée]tico)\b',

            # German teams
            r'\b(Bayern Munich|Bayern|FC Bayern)\b',
            r'\b(Dortmund|BVB|Borussia Dortmund)\b',

            # Italian teams
            r'\b(Juventus|Juve)\b',
            r'\b(Inter Milan|Inter|Internazionale)\b',
            r'\b(AC Milan|Milan)\b',

            # Generic team pattern (any proper noun followed by "FC", "United", etc.)
            r'\b([A-Z][a-zà-ÿ]+(?:\s+[A-Z][a-zà-ÿ]+)*)\s+(?:FC|United|City|Athletic)\b',
        ]

        # Player name patterns
        self.player_patterns = [
            # Known players (can be extended)
            r'\b(Mbapp[ée]|Kylian Mbapp[ée])\b',
            r'\b(Neymar|Neymar Jr)\b',
            r'\b(Messi|Lionel Messi)\b',
            r'\b(Ronaldo|Cristiano Ronaldo)\b',
            r'\b(Benzema|Karim Benzema)\b',
            r'\b(Griezmann|Antoine Griezmann)\b',

            # Generic: Capitalized First Last (after common question words) - more restrictive
            r'(?:joueur|player)\s+([A-Z][a-zà-ÿ]+(?:\s+[A-Z][a-zà-ÿ]+)?)\b',
        ]

        # Date patterns
        self.date_patterns = [
            r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b',  # DD/MM/YYYY or DD-MM-YYYY
            r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b',  # YYYY-MM-DD
            r'\b(aujourd\'hui|today)\b',
            r'\b(demain|tomorrow)\b',
            r'\b(hier|yesterday)\b',
            r'\b(ce soir|tonight)\b',
            r'\b(cette semaine|this week)\b',
        ]

        # League patterns
        self.league_patterns = [
            r'\b(Ligue 1|L1)\b',
            r'\b(Ligue 2|L2)\b',
            r'\b(Premier League|EPL)\b',
            r'\b(La Liga|Liga)\b',
            r'\b(Serie A)\b',
            r'\b(Bundesliga)\b',
            r'\b(Champions League|UCL|Ligue des Champions)\b',
            r'\b(Europa League|UEL)\b',
            r'\b(Coupe de France)\b',
        ]

        # Question type keywords
        self.question_type_keywords = {
            QuestionType.MATCH_LIVE_INFO: [
                'score', 'match', 'résultat', 'result', 'live', 'en cours',
                'joue', 'playing', 'qui gagne', 'who is winning', 'buteur', 'scorer'
            ],
            QuestionType.MATCH_PREDICTION: [
                'prédiction', 'prediction', 'pronostic', 'forecast', 'va gagner',
                'will win', 'chances', 'probabilité', 'probability'
            ],
            QuestionType.TEAM_COMPARISON: [
                'comparaison', 'comparison', 'vs', 'contre', 'against', 'versus',
                'mieux', 'better', 'plus fort', 'stronger'
            ],
            QuestionType.TEAM_STATS: [
                'statistiques', 'statistics', 'stats', 'performance', 'bilan',
                'record', 'forme', 'form'
            ],
            QuestionType.PLAYER_INFO: [
                'joueur', 'player', 'buteur', 'scorer', 'passeur', 'assists',
                'carton', 'card', 'blessé', 'injured', 'buts', 'goals'
            ],
            QuestionType.LEAGUE_INFO: [
                'ligue', 'league', 'championnat', 'championship', 'compétition',
                'competition', 'tableau', 'table'
            ],
            QuestionType.H2H: [
                'historique', 'history', 'h2h', 'head to head', 'face à face',
                'confrontation', 'confrontations', 'matchs précédents', 'previous matches',
                'précédents', 'previous'
            ],
            QuestionType.STANDINGS: [
                'classement', 'standings', 'table', 'tableau', 'position',
                'rang', 'rank', 'ranking'
            ],
        }

        # Language detection keywords
        self.french_keywords = [
            'quel', 'quelle', 'qui', 'quand', 'où', 'comment', 'pourquoi',
            'le', 'la', 'les', 'un', 'une', 'des', 'est', 'sont', 'a', 'ont',
            'score', 'match', 'équipe', 'joueur', 'contre'
        ]

        self.english_keywords = [
            'what', 'which', 'who', 'when', 'where', 'how', 'why',
            'the', 'a', 'an', 'is', 'are', 'has', 'have',
            'score', 'match', 'team', 'player', 'against'
        ]

    async def validate(self, question: str, context: Optional[StructuredContext] = None) -> ValidationResult:
        """
        Validate a question and extract entities.

        Args:
            question: User's question
            context: Structured context (zone, league, fixture)

        Returns:
            ValidationResult with extracted entities and validation status
        """
        try:
            # Detect language
            language = self._detect_language(question)

            # Extract entities
            entities = self._extract_entities(question)

            # Merge context into entities (context has priority)
            if context:
                entities = self._merge_context_into_entities(context, entities)

            # Classify question type
            question_type, confidence = self._classify_question_type(question, entities)

            # Check completeness
            missing_info = self._check_completeness(question_type, entities, context)
            is_complete = len(missing_info) == 0

            # Generate clarification questions if needed
            clarification_questions = []
            if not is_complete:
                clarification_questions = self._generate_clarifications(
                    missing_info, question_type, language
                )

            logger.info(
                "question_validated",
                question=question,
                question_type=question_type.value if question_type else None,
                is_complete=is_complete,
                entities=entities,
                language=language.value
            )

            return ValidationResult(
                is_complete=is_complete,
                question_type=question_type,
                extracted_entities=entities,
                missing_info=missing_info,
                clarification_questions=clarification_questions,
                confidence=confidence,
                detected_language=language
            )

        except Exception as e:
            logger.error("question_validation_error", error=str(e), question=question)
            return ValidationResult(
                is_complete=False,
                question_type=QuestionType.UNKNOWN,
                extracted_entities={},
                missing_info=["error"],
                clarification_questions=["Je n'ai pas pu comprendre votre question. Pouvez-vous la reformuler ?"],
                confidence=0.0,
                detected_language=Language.UNKNOWN
            )

    def _detect_language(self, question: str) -> Language:
        """
        Detect the language of the question.

        Args:
            question: User's question

        Returns:
            Detected language
        """
        question_lower = question.lower()

        french_count = sum(1 for keyword in self.french_keywords if keyword in question_lower)
        english_count = sum(1 for keyword in self.english_keywords if keyword in question_lower)

        if french_count > english_count:
            return Language.FRENCH
        elif english_count > french_count:
            return Language.ENGLISH
        else:
            # Default to French if ambiguous
            return Language.FRENCH

    def _merge_context_into_entities(
        self,
        context: StructuredContext,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge provided context into extracted entities.

        **RULE: Context has PRIORITY over question entities**

        Args:
            context: Structured context from caller
            entities: Entities extracted from question text

        Returns:
            Merged entities dict
        """
        merged = entities.copy()

        # 1. Map zone
        if context.zone:
            merged['zone'] = context.zone.name
            merged['zone_code'] = context.zone.code
            merged['zone_type'] = context.zone.zone_type.value

        # 2. Map league (OVERRIDE question entities)
        if context.league:
            merged['leagues'] = [context.league]

        if context.league_id:
            merged['league_ids'] = [context.league_id]

        # 3. Map fixture (OVERRIDE question entities)
        if context.fixture:
            teams = self._parse_fixture_string(context.fixture)
            if teams:
                merged['teams'] = teams  # Override

        if context.fixture_id:
            merged['fixture_ids'] = [context.fixture_id]

        # 4. Map season
        if context.season:
            merged['season'] = context.season

        logger.info(
            "context_merged_into_entities",
            context_provided=context.to_dict(),
            entities_before=entities,
            entities_after=merged
        )

        return merged

    def _parse_fixture_string(self, fixture: str) -> Optional[List[str]]:
        """
        Parse a fixture string like "PSG vs OM" into team names.

        Args:
            fixture: String like "PSG vs OM", "Real Madrid - Barcelona"

        Returns:
            List of team names or None
        """
        # Try common separators
        separators = [' vs ', ' vs. ', ' - ', ' v ', ' contre ']

        fixture_lower = fixture.lower()
        for sep in separators:
            if sep in fixture_lower:
                # Find separator position in original string (preserve case)
                sep_index = fixture_lower.index(sep)
                home_team = fixture[:sep_index].strip()
                away_team = fixture[sep_index + len(sep):].strip()

                if home_team and away_team:
                    return [home_team, away_team]

        logger.warning("fixture_parse_failed", fixture=fixture)
        return None

    def _extract_entities(self, question: str) -> Dict[str, Any]:
        """
        Extract entities from the question.

        Args:
            question: User's question

        Returns:
            Dictionary of extracted entities
        """
        entities = {}

        # Extract teams
        teams = self._extract_teams(question)
        if teams:
            entities['teams'] = teams

        # Extract players
        players = self._extract_players(question)
        if players:
            entities['players'] = players

        # Extract dates
        dates = self._extract_dates(question)
        if dates:
            entities['dates'] = dates

        # Extract leagues
        leagues = self._extract_leagues(question)
        if leagues:
            entities['leagues'] = leagues

        return entities

    def _extract_teams(self, question: str) -> List[str]:
        """Extract team names from question."""
        teams = []
        for pattern in self.team_patterns:
            matches = re.finditer(pattern, question, re.IGNORECASE)
            for match in matches:
                team = match.group(0).strip()
                if team and team not in teams:
                    teams.append(team)

        return teams

    def _extract_players(self, question: str) -> List[str]:
        """Extract player names from question."""
        players = []
        for pattern in self.player_patterns:
            matches = re.finditer(pattern, question, re.IGNORECASE)
            for match in matches:
                # Get the full match or the first capturing group
                player = match.group(1) if match.lastindex else match.group(0)
                player = player.strip()
                if player and player not in players:
                    players.append(player)

        return players

    def _extract_dates(self, question: str) -> List[str]:
        """Extract dates from question."""
        dates = []
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, question, re.IGNORECASE)
            for match in matches:
                date_str = match.group(0).strip()

                # Normalize relative dates
                if date_str.lower() in ['aujourd\'hui', 'today']:
                    date_str = datetime.now().strftime("%Y-%m-%d")
                elif date_str.lower() in ['demain', 'tomorrow']:
                    from datetime import timedelta
                    date_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                elif date_str.lower() in ['hier', 'yesterday']:
                    from datetime import timedelta
                    date_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

                if date_str and date_str not in dates:
                    dates.append(date_str)

        return dates

    def _extract_leagues(self, question: str) -> List[str]:
        """Extract league names from question."""
        leagues = []
        for pattern in self.league_patterns:
            matches = re.finditer(pattern, question, re.IGNORECASE)
            for match in matches:
                league = match.group(0).strip()
                if league and league not in leagues:
                    leagues.append(league)

        return leagues

    def _classify_question_type(self, question: str, entities: Dict[str, Any]) -> tuple[Optional[QuestionType], float]:
        """
        Classify the type of question.

        Args:
            question: User's question
            entities: Extracted entities

        Returns:
            Tuple of (question_type, confidence)
        """
        question_lower = question.lower()

        # Count keyword matches for each question type
        type_scores = {}
        for q_type, keywords in self.question_type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in question_lower)
            if score > 0:
                type_scores[q_type] = score

        # No matches
        if not type_scores:
            return QuestionType.UNKNOWN, 0.0

        # Get type with highest score
        best_type = max(type_scores.items(), key=lambda x: x[1])
        question_type, score = best_type

        # Calculate confidence (simple heuristic)
        confidence = min(score / 3.0, 1.0)  # Cap at 1.0

        # Adjust based on entities
        if question_type == QuestionType.PLAYER_INFO and 'players' in entities:
            confidence = min(confidence + 0.2, 1.0)
        elif question_type in [QuestionType.TEAM_STATS, QuestionType.TEAM_COMPARISON] and 'teams' in entities:
            confidence = min(confidence + 0.2, 1.0)
        elif question_type == QuestionType.H2H and len(entities.get('teams', [])) >= 2:
            confidence = min(confidence + 0.3, 1.0)

        return question_type, confidence

    def _check_completeness(
        self,
        question_type: Optional[QuestionType],
        entities: Dict[str, Any],
        context: Optional[StructuredContext] = None
    ) -> List[str]:
        """
        Check if question has all required information.

        **IMPORTANT**: If context provides required info, don't mark as missing.

        Args:
            question_type: Classified question type
            entities: Extracted entities (already merged with context)
            context: Original context (to check what was provided)

        Returns:
            List of missing information
        """
        missing = []

        if question_type == QuestionType.UNKNOWN:
            missing.append("question_type")
            return missing

        # Required entities per question type
        requirements = {
            QuestionType.MATCH_LIVE_INFO: ['teams'],
            QuestionType.MATCH_PREDICTION: ['teams'],
            QuestionType.TEAM_COMPARISON: ['teams'],  # Should have 2 teams
            QuestionType.TEAM_STATS: ['teams'],
            QuestionType.PLAYER_INFO: ['players'],
            QuestionType.LEAGUE_INFO: ['leagues'],
            QuestionType.H2H: ['teams'],  # Should have 2 teams
            QuestionType.STANDINGS: ['leagues'],
        }

        required = requirements.get(question_type, [])

        for req in required:
            # Check in merged entities (which includes context)
            if req not in entities or not entities[req]:
                missing.append(req)

        # Special checks
        if question_type == QuestionType.H2H:
            if 'teams' in entities and len(entities['teams']) < 2:
                # Only add if context didn't provide a fixture
                if not (context and context.fixture):
                    missing.append('second_team')

        if question_type == QuestionType.TEAM_COMPARISON:
            if 'teams' in entities and len(entities['teams']) < 2:
                if not (context and context.fixture):
                    missing.append('second_team')

        return missing

    def _generate_clarifications(
        self,
        missing_info: List[str],
        question_type: Optional[QuestionType],
        language: Language
    ) -> List[str]:
        """
        Generate clarification questions for missing information.

        Args:
            missing_info: List of missing information
            question_type: Type of question
            language: Detected language

        Returns:
            List of clarification questions
        """
        clarifications = []

        # French clarifications
        french_templates = {
            'teams': "Quelle équipe vous intéresse ?",
            'second_team': "Quelle est la deuxième équipe ?",
            'players': "Quel joueur vous intéresse ?",
            'dates': "Pour quelle date souhaitez-vous cette information ?",
            'leagues': "Quelle ligue ou compétition vous intéresse ?",
            'question_type': "Que voulez-vous savoir exactement ?"
        }

        # English clarifications
        english_templates = {
            'teams': "Which team are you interested in?",
            'second_team': "What is the second team?",
            'players': "Which player are you interested in?",
            'dates': "For which date do you want this information?",
            'leagues': "Which league or competition are you interested in?",
            'question_type': "What exactly do you want to know?"
        }

        templates = french_templates if language == Language.FRENCH else english_templates

        for info in missing_info:
            clarification = templates.get(info)
            if clarification:
                clarifications.append(clarification)

        return clarifications
