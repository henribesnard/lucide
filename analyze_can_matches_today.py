"""
Analyze CAN matches scheduled for a given date (default: today).
Generates one report per match in can_analyses/.
"""
import os
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

API_FOOTBALL_BASE_URL = "https://v3.football.api-sports.io"
BACKEND_API_URL = "http://localhost:8001"
CAN_LEAGUE_ID = 6
CURRENT_SEASON = 2025
OUTPUT_DIR = "can_analyses"
NUM_LAST_MATCHES = 30

STATUSES_INCLUDED = {
    "TBD", "NS", "1H", "HT", "2H", "ET", "BT", "P", "SUSP", "INT", "PST",
    "FT", "AET", "PEN"
}


def get_target_date() -> str:
    """Return target date (YYYY-MM-DD) from env or local date."""
    override = os.getenv("TARGET_DATE")
    if override:
        return override
    return datetime.now().strftime("%Y-%m-%d")


def get_matches_for_date(target_date: str, api_key: str):
    """Fetch CAN fixtures for a given date."""
    headers = {
        "x-rapidapi-host": "v3.football.api-sports.io",
        "x-rapidapi-key": api_key,
    }
    params = {
        "league": CAN_LEAGUE_ID,
        "season": CURRENT_SEASON,
        "date": target_date,
    }

    response = requests.get(
        f"{API_FOOTBALL_BASE_URL}/fixtures",
        headers=headers,
        params=params,
        timeout=30,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Fixtures API error {response.status_code}: {response.text[:200]}")

    fixtures = response.json().get("response", [])
    matches = []
    for fixture in fixtures:
        fixture_data = fixture.get("fixture", {}) or {}
        teams = fixture.get("teams", {}) or {}
        status = (fixture_data.get("status", {}) or {}).get("short", "")

        if status and status not in STATUSES_INCLUDED:
            continue

        matches.append({
            "fixture_id": fixture_data.get("id"),
            "date": fixture_data.get("date"),
            "status": status,
            "team_home": (teams.get("home") or {}).get("name"),
            "team_home_id": (teams.get("home") or {}).get("id"),
            "team_away": (teams.get("away") or {}).get("name"),
            "team_away_id": (teams.get("away") or {}).get("id"),
            "round": (fixture.get("league", {}) or {}).get("round", ""),
            "venue": (fixture_data.get("venue", {}) or {}).get("name", ""),
        })

    matches.sort(key=lambda item: item.get("date") or "")
    return matches


def analyze_match(match_info):
    """Call backend extended analysis."""
    url = f"{BACKEND_API_URL}/match-analysis/analyze/extended"
    payload = {
        "league": str(CAN_LEAGUE_ID),
        "league_type": "cup",
        "team_a": match_info["team_home"],
        "team_b": match_info["team_away"],
    }

    response = requests.post(
        url,
        json=payload,
        params={"num_last_matches": NUM_LAST_MATCHES},
        timeout=180,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Backend error {response.status_code}: {response.text[:200]}")
    return response.json()


def sanitize_name(value: str) -> str:
    """Sanitize string for filenames."""
    return value.replace(" ", "_").replace("/", "-")


def save_summary(match_info, analysis_data, output_dir: Path):
    """Write markdown report for a match."""
    summary = analysis_data.get("summary")
    if not summary:
        raise RuntimeError("No summary in analysis response.")

    team_a = sanitize_name(match_info["team_home"])
    team_b = sanitize_name(match_info["team_away"])
    match_date = match_info["date"][:10] if match_info.get("date") else "unknown-date"
    round_name = sanitize_name(match_info.get("round") or "unknown-round").replace("-", "_")
    filename = f"{match_date}_{round_name}_{team_a}_vs_{team_b}.md"
    filepath = output_dir / filename

    header = (
        "---\n"
        f"Match: {match_info['team_home']} vs {match_info['team_away']}\n"
        f"Date: {match_info.get('date')}\n"
        f"Round: {match_info.get('round')}\n"
        f"Venue: {match_info.get('venue')}\n"
        f"Status: {match_info.get('status')}\n"
        f"Fixture ID: {match_info.get('fixture_id')}\n"
        f"Generated: {datetime.now().isoformat()}\n"
        "---\n\n"
    )

    with open(filepath, "w", encoding="utf-8") as file_handle:
        file_handle.write(header)
        file_handle.write(summary)

    return filepath


def write_index(output_dir: Path, results: list, target_date: str):
    """Write a simple index markdown."""
    index_file = output_dir / "INDEX.md"
    with open(index_file, "w", encoding="utf-8") as file_handle:
        file_handle.write("# Analyses CAN 2025\n\n")
        file_handle.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file_handle.write(f"Target date: {target_date}\n\n")
        file_handle.write("## Matches\n\n")
        for result in results:
            if result["status"] == "success":
                filename = os.path.basename(result["file"])
                file_handle.write(f"- [{result['match']}](./{filename})\n")
            else:
                file_handle.write(f"- {result['match']} (error: {result['status']})\n")


def main():
    load_dotenv()
    api_key = os.getenv("FOOTBALL_API_KEY")
    if not api_key:
        raise RuntimeError("FOOTBALL_API_KEY not set in .env")

    target_date = get_target_date()
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(exist_ok=True)

    print("=" * 80)
    print(f"CAN MATCH ANALYSIS FOR {target_date}")
    print("=" * 80)

    matches = get_matches_for_date(target_date, api_key)
    if not matches:
        print("No CAN matches found for target date.")
        return

    print(f"Matches to analyze: {len(matches)}")

    results = []
    for index, match in enumerate(matches, 1):
        print(f"[{index}/{len(matches)}] {match['team_home']} vs {match['team_away']}")
        start_time = time.time()
        try:
            analysis_data = analyze_match(match)
            filepath = save_summary(match, analysis_data, output_dir)
            results.append({
                "match": f"{match['team_home']} vs {match['team_away']}",
                "status": "success",
                "file": str(filepath),
                "time": time.time() - start_time,
            })
            print(f"  Saved: {filepath}")
        except Exception as exc:
            results.append({
                "match": f"{match['team_home']} vs {match['team_away']}",
                "status": str(exc),
                "time": time.time() - start_time,
            })
            print(f"  Error: {exc}")

        if index < len(matches):
            time.sleep(2)

    write_index(output_dir, results, target_date)
    print("Done.")


if __name__ == "__main__":
    main()
