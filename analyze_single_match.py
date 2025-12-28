"""Analyze a single match."""
import requests
import json
from datetime import datetime

API_URL = "http://localhost:8001/match-analysis/analyze/extended"

payload = {
    "league": "6",
    "league_type": "cup",
    "team_a": "Mozambique",
    "team_b": "Cameroon",
}

print(f"Analyzing: {payload['team_a']} vs {payload['team_b']}")

response = requests.post(
    API_URL,
    json=payload,
    params={"num_last_matches": 30},
    timeout=300
)

if response.status_code == 200:
    result = response.json()
    summary = result.get("summary", "")

    # Save to file
    filename = "can_analyses/2025-12-31_Group_Stage___3_Mozambique_vs_Cameroon.md"

    # Add header
    header = """---
Match: Mozambique vs Cameroon
Date: 2025-12-31T19:00:00+00:00
Round: Group Stage - 3
Venue: Stade Adrar
Status: NS
Fixture ID: 1347274
Generated: {timestamp}
---

""".format(timestamp=datetime.utcnow().isoformat())

    with open(filename, "w", encoding="utf-8") as f:
        f.write(header)
        f.write(summary)

    print(f"[OK] Saved to: {filename}")
    print(f"Processing time: {result['metadata']['processing_time_seconds']}s")
else:
    print(f"[ERROR] {response.status_code}")
    print(response.text)
