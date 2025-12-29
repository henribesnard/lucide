"""
Migration script: JSON match contexts → PostgreSQL

This script migrates existing match analysis contexts from JSON files
to the PostgreSQL database.

Usage:
    python backend/scripts/migrate_json_to_db.py
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.db.database import SessionLocal
from backend.store.db_match_context_store import DBMatchContextStore
from backend.store.schemas import MatchContext


def migrate_json_contexts(json_dir: str = "./data/match_contexts"):
    """
    Migrate all JSON match contexts to database

    Args:
        json_dir: Directory containing JSON files
    """
    json_path = Path(json_dir)

    if not json_path.exists():
        print(f"❌ Directory not found: {json_dir}")
        return

    # Initialize DB store
    db_store = DBMatchContextStore(SessionLocal)

    # Get all JSON files
    json_files = list(json_path.glob("match_*.json"))

    if not json_files:
        print(f"⚠️  No match context files found in {json_dir}")
        return

    print(f"Found {len(json_files)} match context files to migrate\n")

    migrated = 0
    skipped = 0
    errors = 0

    for json_file in json_files:
        fixture_id = int(json_file.stem.replace("match_", ""))

        try:
            # Check if already in DB
            if db_store.has_context(fixture_id):
                print(f"⏭️  Skipped {json_file.name} (already in database)")
                skipped += 1
                continue

            # Load JSON
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Parse into MatchContext
            context = MatchContext(**data)

            # Save to DB
            db_store.save_context(context)

            print(f"✅ Migrated {json_file.name} → {context.home_team} vs {context.away_team}")
            migrated += 1

        except Exception as e:
            print(f"❌ Error migrating {json_file.name}: {str(e)}")
            errors += 1

    # Summary
    print(f"\n{'='*60}")
    print(f"Migration Summary:")
    print(f"  ✅ Migrated: {migrated}")
    print(f"  ⏭️  Skipped: {skipped}")
    print(f"  ❌ Errors: {errors}")
    print(f"  📊 Total: {len(json_files)}")
    print(f"{'='*60}")

    if errors == 0:
        print(f"\n🎉 Migration completed successfully!")
    else:
        print(f"\n⚠️  Migration completed with {errors} errors")


if __name__ == "__main__":
    print("="*60)
    print("JSON to PostgreSQL Migration Script")
    print("="*60)
    print()

    # Run migration
    migrate_json_contexts()
