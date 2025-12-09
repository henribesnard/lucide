"""
Utility helpers to normalize and validate match status codes.
Data is sourced from the repository-level status.csv (SHORT;LONG;TYPE;DESCRIPTION).
Falls back to a baked-in table if the CSV is missing.
"""
from __future__ import annotations

import csv
import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Conservative fallback in case the CSV cannot be read at runtime.
_DEFAULT_STATUS_TABLE: Dict[str, Dict[str, str]] = {
    "TBD": {
        "long": "Time To Be Defined",
        "type": "Scheduled",
        "description": "Scheduled but date and time are not known",
    },
    "NS": {"long": "Not Started", "type": "Scheduled", "description": ""},
    "1H": {"long": "First Half", "type": "In Play", "description": "First half in play"},
    "HT": {"long": "Halftime", "type": "In Play", "description": "Finished in the regular time"},
    "2H": {"long": "Second Half", "type": "In Play", "description": "Second half in play"},
    "ET": {"long": "Extra Time", "type": "In Play", "description": "Extra time in play"},
    "BT": {"long": "Break Time", "type": "In Play", "description": "Break during extra time"},
    "P": {"long": "Penalty In Progress", "type": "In Play", "description": "Penalty played after extra time"},
    "SUSP": {
        "long": "Match Suspended",
        "type": "In Play",
        "description": "Suspended by referee's decision, may be rescheduled another day",
    },
    "INT": {
        "long": "Match Interrupted",
        "type": "In Play",
        "description": "Interrupted by referee's decision, should resume in a few minutes",
    },
    "FT": {"long": "Match Finished", "type": "Finished", "description": "Finished in the regular time"},
    "AET": {
        "long": "Match Finished",
        "type": "Finished",
        "description": "Finished after extra time without going to the penalty shootout",
    },
    "PEN": {
        "long": "Match Finished",
        "type": "Finished",
        "description": "Finished after the penalty shootout",
    },
    "PST": {
        "long": "Match Postponed",
        "type": "Postponed",
        "description": "Postponed to another day, once the new date and time is known the status will change to Not Started",
    },
    "CANC": {"long": "Match Cancelled", "type": "Cancelled", "description": "Cancelled, match will not be played"},
    "ABD": {
        "long": "Match Abandoned",
        "type": "Abandoned",
        "description": "Abandoned for various reasons (Bad Weather, Safety, Floodlights, Playing Staff Or Referees), Can be rescheduled or not, it depends on the competition",
    },
    "AWD": {"long": "Technical Loss", "type": "Not Played", "description": ""},
    "WO": {"long": "WalkOver", "type": "Not Played", "description": "Victory by forfeit or absence of competitor"},
    "LIVE": {
        "long": "In Progress",
        "type": "In Play",
        "description": "Used in very rare cases. Indicates a fixture in progress without half-time or elapsed time available",
    },
}


@lru_cache()
def load_status_table() -> Dict[str, Dict[str, str]]:
    """
    Load the status table from status.csv located at the repository root.
    Returns an upper-cased dict keyed by short code.
    """
    project_root = Path(__file__).resolve().parents[2]
    csv_path = project_root / "status.csv"
    table: Dict[str, Dict[str, str]] = {}

    if not csv_path.exists():
        logger.warning("status.csv not found at %s, falling back to default status table", csv_path)
        return _DEFAULT_STATUS_TABLE

    try:
        with csv_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                code = (row.get("SHORT") or row.get("code") or row.get("short") or "").strip()
                if not code:
                    continue
                code = code.upper()
                table[code] = {
                    "long": (row.get("LONG") or row.get("long") or row.get("label") or "").strip(),
                    "type": (row.get("TYPE") or row.get("type") or "").strip(),
                    "description": (row.get("DESCRIPTION") or row.get("description") or "").strip(),
                }
    except Exception as exc:
        logger.error("Failed to read status.csv: %s", exc)
        return _DEFAULT_STATUS_TABLE

    return table or _DEFAULT_STATUS_TABLE


def is_valid_status(code: Optional[str]) -> bool:
    if not code:
        return False
    return code.strip().upper() in load_status_table()


def get_status_info(code: Optional[str]) -> Dict[str, Optional[str]]:
    """
    Normalize a status code to a compact dict.
    Always uppercases the code and returns a label/type/description when known.
    """
    if not code:
        return {"code": None, "label": None, "type": None, "description": None}
    normalized = code.strip().upper()
    table = load_status_table()
    info = table.get(normalized) or _DEFAULT_STATUS_TABLE.get(normalized)
    if not info:
        return {"code": normalized, "label": normalized, "type": "Unknown", "description": ""}
    return {
        "code": normalized,
        "label": info.get("long") or normalized,
        "type": info.get("type"),
        "description": info.get("description") or "",
    }


def list_status_codes() -> Dict[str, Dict[str, str]]:
    """Expose the loaded table (useful for tests and debugging)."""
    return load_status_table()
