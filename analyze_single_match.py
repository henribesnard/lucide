"""Analyse un seul match CAN."""
import requests
import time
from datetime import datetime

API_URL = "http://localhost:8001/match-analysis/analyze/extended"
OUTPUT_DIR = "can_analyses"

match = {
    "team_a": "Ivory Coast",
    "team_b": "Cameroon",
    "date": "2025-12-28T20:00:00+00:00",
    "round": "Group Stage - 2",
    "venue": "Stade de Marrakech"
}

print("="*80)
print(f"ANALYSE: {match['team_a']} vs {match['team_b']}")
print("="*80)
print("Attente de 60 secondes pour eviter le rate limit...")
time.sleep(60)

payload = {
    "league": "Africa Cup of Nations",
    "league_type": "cup",
    "team_a": match["team_a"],
    "team_b": match["team_b"],
}

try:
    response = requests.post(
        API_URL,
        json=payload,
        params={"num_last_matches": 30},
        timeout=120
    )

    if response.status_code == 200:
        result = response.json()
        stats = result.get("statistics", {})

        print(f"\n[OK] Succes")
        print(f"   {match['team_a']}: {stats.get('team_a', {}).get('total_matches', 0)} matchs")
        print(f"   {match['team_b']}: {stats.get('team_b', {}).get('total_matches', 0)} matchs")

        # Sauvegarder
        summary = result.get("summary", "")
        filename = f"{OUTPUT_DIR}/{match['date'].split('T')[0]}_{match['round'].replace(' ', '_').replace('-', '_')}_{match['team_a'].replace(' ', '_')}_vs_{match['team_b'].replace(' ', '_')}.md"

        header = f"""---
Match: {match['team_a']} vs {match['team_b']}
Date: {match['date']}
Round: {match['round']}
Venue: {match['venue']}
Status: NS
Generated: {datetime.utcnow().isoformat()}
---

"""
        with open(filename, "w", encoding="utf-8") as f:
            f.write(header)
            f.write(summary)

        print(f"\n[SAVED] {filename}")
    else:
        print(f"\n[ERROR] Erreur {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"\n[ERROR] Exception: {e}")
