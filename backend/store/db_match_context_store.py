"""
Database-backed Match Context Store - Replaces JSON file storage

This module provides PostgreSQL-backed storage for match analysis contexts,
replacing the previous JSON file-based system.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.db.models import MatchAnalysis
from backend.store.schemas import MatchContext, MatchMetadata, BetAnalysisData

logger = logging.getLogger(__name__)


class DBMatchContextStore:
    """PostgreSQL-backed match context storage"""

    def __init__(self, db_session_factory):
        """
        Initialize the database store

        Args:
            db_session_factory: Function that returns a DB session (e.g., SessionLocal)
        """
        self.get_session = db_session_factory

    def has_context(self, fixture_id: int) -> bool:
        """
        Check if match context exists in database

        Args:
            fixture_id: ID of the fixture

        Returns:
            True if context exists, False otherwise
        """
        with self.get_session() as session:
            exists = session.query(
                session.query(MatchAnalysis)
                .filter(MatchAnalysis.fixture_id == fixture_id)
                .exists()
            ).scalar()

            logger.debug(f"Context check for fixture {fixture_id}: {exists}")
            return exists

    def get_context(self, fixture_id: int) -> Optional[MatchContext]:
        """
        Retrieve match context from database

        Updates access metadata automatically

        Args:
            fixture_id: ID of the fixture

        Returns:
            MatchContext if found, None otherwise
        """
        with self.get_session() as session:
            analysis = session.query(MatchAnalysis).filter(
                MatchAnalysis.fixture_id == fixture_id
            ).first()

            if not analysis:
                logger.warning(f"Context not found for fixture {fixture_id}")
                return None

            # Convert DB model to Pydantic MatchContext
            context = self._db_to_context(analysis)

            # Update access metadata
            analysis.last_accessed = datetime.utcnow()
            analysis.access_count += 1
            session.commit()

            logger.info(
                f"Context loaded for fixture {fixture_id} "
                f"(access count: {analysis.access_count})"
            )

            return context

    def save_context(self, context: MatchContext):
        """
        Save or update match context in database

        Args:
            context: MatchContext to save
        """
        with self.get_session() as session:
            # Check if exists
            existing = session.query(MatchAnalysis).filter(
                MatchAnalysis.fixture_id == context.fixture_id
            ).first()

            if existing:
                # Update existing
                self._update_analysis(existing, context)
                logger.info(f"Context updated for fixture {context.fixture_id}")
            else:
                # Create new
                new_analysis = self._context_to_db(context)
                session.add(new_analysis)
                logger.info(f"Context created for fixture {context.fixture_id}")

            session.commit()

    def delete_context(self, fixture_id: int) -> bool:
        """
        Delete match context from database

        Args:
            fixture_id: ID of the fixture

        Returns:
            True if deleted, False if not found
        """
        with self.get_session() as session:
            deleted = session.query(MatchAnalysis).filter(
                MatchAnalysis.fixture_id == fixture_id
            ).delete()

            session.commit()

            if deleted:
                logger.info(f"Context deleted for fixture {fixture_id}")
                return True
            else:
                logger.warning(f"Cannot delete: context not found for fixture {fixture_id}")
                return False

    def list_all_contexts(self) -> List[int]:
        """
        List all fixture IDs with stored contexts

        Returns:
            List of fixture IDs
        """
        with self.get_session() as session:
            fixture_ids = session.query(MatchAnalysis.fixture_id).all()
            return [fid[0] for fid in fixture_ids]

    def get_contexts_by_status(self, status: str) -> List[int]:
        """
        Get all fixture IDs with specific status

        Args:
            status: Match status code (e.g., 'NS', 'FT', '1H')

        Returns:
            List of fixture IDs
        """
        with self.get_session() as session:
            fixture_ids = session.query(MatchAnalysis.fixture_id).filter(
                MatchAnalysis.match_status == status
            ).all()
            return [fid[0] for fid in fixture_ids]

    def get_contexts_summary(self) -> List[dict]:
        """
        Get summary of all stored contexts

        Returns:
            List of context summaries (fixture_id, teams, date, access_count)
        """
        with self.get_session() as session:
            analyses = session.query(MatchAnalysis).all()

            summaries = []
            for analysis in analyses:
                summaries.append({
                    "fixture_id": analysis.fixture_id,
                    "home_team": analysis.home_team,
                    "away_team": analysis.away_team,
                    "league": analysis.league,
                    "date": analysis.match_date.isoformat(),
                    "status": analysis.match_status,
                    "access_count": analysis.access_count,
                    "created_at": analysis.created_at.isoformat()
                })

            return summaries

    def cleanup_old_contexts(self, days: int = 30) -> int:
        """
        Remove contexts older than X days

        Args:
            days: Number of days to keep

        Returns:
            Number of deleted contexts
        """
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        with self.get_session() as session:
            deleted_count = session.query(MatchAnalysis).filter(
                MatchAnalysis.created_at < cutoff_date
            ).delete()

            session.commit()

            logger.info(f"Cleanup: deleted {deleted_count} contexts older than {days} days")
            return deleted_count

    # Helper methods

    def _db_to_context(self, analysis: MatchAnalysis) -> MatchContext:
        """
        Convert DB model to Pydantic MatchContext

        Args:
            analysis: SQLAlchemy MatchAnalysis object

        Returns:
            MatchContext object
        """
        # Reconstruct BetAnalysisData objects from JSON
        analyses = {}
        for bet_type, data in analysis.analyses_data.items():
            analyses[bet_type] = BetAnalysisData(**data)

        return MatchContext(
            fixture_id=analysis.fixture_id,
            home_team=analysis.home_team,
            away_team=analysis.away_team,
            league=analysis.league,
            season=analysis.season,
            date=analysis.match_date,
            status=analysis.match_status,
            raw_data={},  # Not stored in DB (per user request)
            analyses=analyses,
            metadata=MatchMetadata(
                version=analysis.version,
                context_created_at=analysis.created_at,
                last_accessed=analysis.last_accessed,
                access_count=analysis.access_count,
                api_calls_count=analysis.api_calls_count
            )
        )

    def _context_to_db(self, context: MatchContext) -> MatchAnalysis:
        """
        Convert Pydantic MatchContext to DB model

        Args:
            context: MatchContext object

        Returns:
            SQLAlchemy MatchAnalysis object
        """
        # Serialize analyses to JSON
        analyses_data = {}
        for bet_type, analysis in context.analyses.items():
            analyses_data[bet_type] = analysis.dict()

        return MatchAnalysis(
            fixture_id=context.fixture_id,
            home_team=context.home_team,
            away_team=context.away_team,
            league=context.league,
            season=context.season,
            match_date=context.date,
            match_status=context.status,
            analyses_data=analyses_data,
            api_calls_count=context.metadata.api_calls_count,
            version=context.metadata.version,
            created_at=context.metadata.context_created_at,
            last_accessed=context.metadata.last_accessed,
            access_count=context.metadata.access_count
        )

    def _update_analysis(self, db_analysis: MatchAnalysis, context: MatchContext):
        """
        Update existing DB record with new context data

        Args:
            db_analysis: Existing SQLAlchemy MatchAnalysis object
            context: New MatchContext data
        """
        db_analysis.home_team = context.home_team
        db_analysis.away_team = context.away_team
        db_analysis.league = context.league
        db_analysis.season = context.season
        db_analysis.match_date = context.date
        db_analysis.match_status = context.status
        db_analysis.analyses_data = {
            bt: analysis.dict() for bt, analysis in context.analyses.items()
        }
        db_analysis.api_calls_count = context.metadata.api_calls_count
        db_analysis.access_count = context.metadata.access_count
