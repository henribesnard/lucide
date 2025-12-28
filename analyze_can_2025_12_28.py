"""Analyse des matchs CAN du 28/12/2025 pour tester les stats de compétition."""
import requests
import json
import time
from datetime import datetime

API_URL = "http://localhost:8001/match-analysis/analyze/extended"
OUTPUT_DIR = "can_analyses"

# Matchs du 28/12/2025
matches_2025_12_28 = [
    {
        "team_a": "Gabon",
        "team_b": "Mozambique",
        "date": "2025-12-28T12:30:00+00:00",
        "round": "Group Stage - 2",
        "venue": "Stade Adrar"
    },
    {
        "team_a": "Equatorial Guinea",
        "team_b": "Sudan",
        "date": "2025-12-28T15:00:00+00:00",
        "round": "Group Stage - 2",
        "venue": "Stade Mohamed V"
    },
    {
        "team_a": "Algeria",
        "team_b": "Burkina Faso",
        "date": "2025-12-28T17:30:00+00:00",
        "round": "Group Stage - 2",
        "venue": "Stade Prince Moulay Hassan"
    },
    {
        "team_a": "Ivory Coast",
        "team_b": "Cameroon",
        "date": "2025-12-28T20:00:00+00:00",
        "round": "Group Stage - 2",
        "venue": "Stade de Marrakech"
    }
]

print("="*100)
print("ANALYSE DES MATCHS CAN DU 28/12/2025 - TEST STATS COMPETITION")
print("="*100)
print(f"\nNombre de matchs à analyser: {len(matches_2025_12_28)}")
print()

results = []

for i, match in enumerate(matches_2025_12_28, 1):
    print(f"[{i}/{len(matches_2025_12_28)}] {match['team_a']} vs {match['team_b']}")
    print(f"  Date: {match['date']}")
    print(f"  Round: {match['round']}")

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

            # Extraire les stats
            stats = result.get("statistics", {})
            team_a_stats = stats.get("team_a", {})
            team_b_stats = stats.get("team_b", {})

            # Stats de compétition
            team_a_comp = team_a_stats.get("competition_specific")
            team_b_comp = team_b_stats.get("competition_specific")

            print(f"  [OK] Succes")
            print(f"    {match['team_a']}: {team_a_stats.get('total_matches', 0)} matchs globaux")
            if team_a_comp:
                print(f"      > CAN: {team_a_comp.get('total_matches', 0)} matchs, {team_a_comp.get('win_rate', 0):.1f}% victoires")
            else:
                print(f"      > CAN: Pas de donnees")

            print(f"    {match['team_b']}: {team_b_stats.get('total_matches', 0)} matchs globaux")
            if team_b_comp:
                print(f"      > CAN: {team_b_comp.get('total_matches', 0)} matchs, {team_b_comp.get('win_rate', 0):.1f}% victoires")
            else:
                print(f"      > CAN: Pas de donnees")

            # Sauvegarder le resume
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

            print(f"  [SAVED] {filename}")

            results.append({
                "match": f"{match['team_a']} vs {match['team_b']}",
                "success": True,
                "team_a_comp_matches": team_a_comp.get('total_matches', 0) if team_a_comp else 0,
                "team_b_comp_matches": team_b_comp.get('total_matches', 0) if team_b_comp else 0,
            })

        else:
            print(f"  [ERROR] Erreur: {response.status_code}")
            print(f"    {response.text}")
            results.append({
                "match": f"{match['team_a']} vs {match['team_b']}",
                "success": False,
                "error": response.status_code
            })

    except Exception as e:
        print(f"  [ERROR] Exception: {e}")
        results.append({
            "match": f"{match['team_a']} vs {match['team_b']}",
            "success": False,
            "error": str(e)
        })

    print()
    if i < len(matches_2025_12_28):
        print("  Pause 2s...")
        time.sleep(2)

# Résumé final
print("="*100)
print("RÉSUMÉ")
print("="*100)

success_count = sum(1 for r in results if r.get("success"))
print(f"Succès: {success_count}/{len(matches_2025_12_28)}")
print()

print("Stats de compétition par équipe:")
for r in results:
    if r.get("success"):
        print(f"  {r['match']}:")
        print(f"    Team A: {r['team_a_comp_matches']} matchs CAN")
        print(f"    Team B: {r['team_b_comp_matches']} matchs CAN")

print()
print("[OK] Analyses sauvegardees dans:", OUTPUT_DIR)
