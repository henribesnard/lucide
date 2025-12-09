"""
Classifier for match and league statuses.
"""

from typing import Optional
from datetime import datetime, timedelta
import logging

from backend.context.context_types import MatchStatus, LeagueStatus
from backend.utils.status_mapping import get_status_info

logger = logging.getLogger(__name__)


class StatusClassifier:
    """Classifies match and league statuses."""

    # API-Football status types mapping to our simplified statuses
    LIVE_TYPES = {"In Play"}
    FINISHED_TYPES = {"Finished"}
    UPCOMING_TYPES = {"Scheduled"}

    # Statuses that should be treated as finished
    FINISHED_STATUSES = {"FT", "AET", "PEN"}

    # Statuses that should be treated as live
    LIVE_STATUSES = {"1H", "HT", "2H", "ET", "BT", "P", "LIVE", "SUSP", "INT"}

    # Statuses that should be treated as upcoming
    UPCOMING_STATUSES = {"TBD", "NS"}

    @classmethod
    def classify_match_status(cls, status_code: Optional[str], match_date: Optional[str] = None) -> MatchStatus:
        """
        Classify a match status based on API-Football status code and optionally the match date.

        Args:
            status_code: The API-Football status short code (e.g., "FT", "1H", "NS")
            match_date: Optional match date in ISO format (YYYY-MM-DD)

        Returns:
            MatchStatus enum value (LIVE, FINISHED, or UPCOMING)
        """
        if not status_code:
            logger.warning("No status code provided, defaulting to UPCOMING")
            return MatchStatus.UPCOMING

        # Get status info from the mapping utility
        status_info = get_status_info(status_code)
        normalized_code = status_info.get("code", "").upper()
        status_type = status_info.get("type", "")

        # First check explicit status codes
        if normalized_code in cls.FINISHED_STATUSES:
            return MatchStatus.FINISHED

        if normalized_code in cls.LIVE_STATUSES:
            return MatchStatus.LIVE

        if normalized_code in cls.UPCOMING_STATUSES:
            return MatchStatus.UPCOMING

        # Then check status types
        if status_type in cls.LIVE_TYPES:
            return MatchStatus.LIVE

        if status_type in cls.FINISHED_TYPES:
            return MatchStatus.FINISHED

        if status_type in cls.UPCOMING_TYPES:
            return MatchStatus.UPCOMING

        # Handle special cases
        if status_type in {"Postponed", "Cancelled", "Abandoned", "Not Played"}:
            # These are treated as finished (won't be played or already not played)
            return MatchStatus.FINISHED

        # Fallback: use match date if available
        if match_date:
            try:
                match_dt = datetime.fromisoformat(match_date.replace("Z", "+00:00"))
                now = datetime.now(match_dt.tzinfo) if match_dt.tzinfo else datetime.now()

                # If match date is in the past (more than 4 hours ago), likely finished
                if match_dt < now - timedelta(hours=4):
                    return MatchStatus.FINISHED

                # If match date is within 4 hours (past or future), could be live
                if abs((match_dt - now).total_seconds()) < 4 * 3600:
                    return MatchStatus.LIVE

                # If match date is in the future, upcoming
                if match_dt > now:
                    return MatchStatus.UPCOMING
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse match date {match_date}: {e}")

        # Default to upcoming if we can't determine
        logger.warning(f"Could not classify status {normalized_code} (type: {status_type}), defaulting to UPCOMING")
        return MatchStatus.UPCOMING

    @classmethod
    def classify_league_status(
        cls,
        season: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> LeagueStatus:
        """
        Classify a league status based on season and dates.

        Args:
            season: The season year (e.g., 2024)
            start_date: Optional league start date in ISO format
            end_date: Optional league end date in ISO format

        Returns:
            LeagueStatus enum value (PAST, CURRENT, or UPCOMING)
        """
        now = datetime.now()
        current_year = now.year

        # Calculate current season (starts in August)
        current_season = current_year if now.month >= 8 else current_year - 1

        # If we have explicit dates, use them
        if start_date and end_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

                if end_dt < now:
                    return LeagueStatus.PAST
                elif start_dt <= now <= end_dt:
                    return LeagueStatus.CURRENT
                else:
                    return LeagueStatus.UPCOMING
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse league dates: {e}")

        # Fallback to season comparison
        if season < current_season:
            return LeagueStatus.PAST
        elif season == current_season:
            return LeagueStatus.CURRENT
        else:
            return LeagueStatus.UPCOMING

    @classmethod
    def is_today_match(cls, match_date: str) -> bool:
        """
        Check if a match is today's match (used to determine if past matches are from today).

        Args:
            match_date: Match date in ISO format

        Returns:
            True if the match is today, False otherwise
        """
        try:
            match_dt = datetime.fromisoformat(match_date.replace("Z", "+00:00"))
            now = datetime.now(match_dt.tzinfo) if match_dt.tzinfo else datetime.now()
            return match_dt.date() == now.date()
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse match date {match_date}: {e}")
            return False
