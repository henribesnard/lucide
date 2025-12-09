"""
Match Context Store - Persistent storage for match analysis contexts

Principle: A match is analyzed once, then the complete context is stored.
All subsequent questions use the cached context (0 API calls).
"""
import json
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from backend.store.schemas import MatchContext, MatchMetadata

logger = logging.getLogger(__name__)


class MatchContextStore:
    """
    Persistent storage for match contexts

    Features:
    - JSON-based storage (easy debugging, portable)
    - Automatic metadata tracking (access count, timestamps)
    - Thread-safe operations
    """

    def __init__(self, storage_path: str = "./data/match_contexts"):
        """
        Initialize the store

        Args:
            storage_path: Directory where match contexts are stored
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"MatchContextStore initialized at {self.storage_path}")

    def has_context(self, fixture_id: int) -> bool:
        """
        Check if a match context exists

        Args:
            fixture_id: ID of the fixture

        Returns:
            True if context exists, False otherwise
        """
        context_file = self._get_context_file(fixture_id)
        exists = context_file.exists()

        logger.debug(f"Context check for fixture {fixture_id}: {exists}")
        return exists

    def get_context(self, fixture_id: int) -> Optional[MatchContext]:
        """
        Retrieve a match context

        Args:
            fixture_id: ID of the fixture

        Returns:
            MatchContext if found, None otherwise
        """
        context_file = self._get_context_file(fixture_id)

        if not context_file.exists():
            logger.warning(f"Context not found for fixture {fixture_id}")
            return None

        try:
            with open(context_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Parse into Pydantic model
            context = MatchContext(**data)

            # Update access metadata
            context.metadata.last_accessed = datetime.utcnow()
            context.metadata.access_count += 1

            # Save updated metadata
            self._save_context_data(fixture_id, context)

            logger.info(
                f"Context loaded for fixture {fixture_id} "
                f"(access count: {context.metadata.access_count})"
            )

            return context

        except Exception as e:
            logger.error(f"Error loading context for fixture {fixture_id}: {e}", exc_info=True)
            return None

    def save_context(self, context: MatchContext):
        """
        Save a match context

        Args:
            context: MatchContext to save
        """
        try:
            self._save_context_data(context.fixture_id, context)

            logger.info(
                f"Context saved for fixture {context.fixture_id} "
                f"({context.home_team} vs {context.away_team})"
            )

        except Exception as e:
            logger.error(
                f"Error saving context for fixture {context.fixture_id}: {e}",
                exc_info=True
            )
            raise

    def delete_context(self, fixture_id: int) -> bool:
        """
        Delete a match context

        Args:
            fixture_id: ID of the fixture

        Returns:
            True if deleted, False if not found
        """
        context_file = self._get_context_file(fixture_id)

        if not context_file.exists():
            logger.warning(f"Cannot delete: context not found for fixture {fixture_id}")
            return False

        try:
            context_file.unlink()
            logger.info(f"Context deleted for fixture {fixture_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting context for fixture {fixture_id}: {e}", exc_info=True)
            return False

    def list_all_contexts(self) -> List[int]:
        """
        List all stored match contexts

        Returns:
            List of fixture IDs
        """
        fixture_ids = [
            int(f.stem.replace("match_", ""))
            for f in self.storage_path.glob("match_*.json")
        ]

        logger.debug(f"Found {len(fixture_ids)} stored contexts")
        return sorted(fixture_ids)

    def get_contexts_summary(self) -> List[dict]:
        """
        Get summary of all stored contexts

        Returns:
            List of context summaries (fixture_id, teams, date, access_count)
        """
        summaries = []

        for fixture_id in self.list_all_contexts():
            context = self.get_context(fixture_id)
            if context:
                summaries.append({
                    "fixture_id": context.fixture_id,
                    "home_team": context.home_team,
                    "away_team": context.away_team,
                    "league": context.league,
                    "date": context.date.isoformat(),
                    "status": context.status,
                    "access_count": context.metadata.access_count,
                    "created_at": context.metadata.context_created_at.isoformat()
                })

        return summaries

    def cleanup_old_contexts(self, days: int = 30):
        """
        Remove contexts older than X days

        Args:
            days: Number of days to keep
        """
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted_count = 0

        for fixture_id in self.list_all_contexts():
            context = self.get_context(fixture_id)

            if context and context.metadata.context_created_at < cutoff_date:
                if self.delete_context(fixture_id):
                    deleted_count += 1

        logger.info(f"Cleanup: deleted {deleted_count} contexts older than {days} days")
        return deleted_count

    def _get_context_file(self, fixture_id: int) -> Path:
        """Get the file path for a fixture context"""
        return self.storage_path / f"match_{fixture_id}.json"

    def _save_context_data(self, fixture_id: int, context: MatchContext):
        """Save context data to file"""
        context_file = self._get_context_file(fixture_id)

        # Convert to dict for JSON serialization
        data = context.dict()

        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
