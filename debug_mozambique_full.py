"""Debug complet Mozambique."""
import requests
import json

response = requests.post(
    "http://localhost:8001/match-analysis/analyze/extended",
    json={
        "league": "Africa Cup of Nations",
        "league_type": "cup",
        "team_a": "Gabon",
        "team_b": "Mozambique",
    },
    params={"num_last_matches": 30},
    timeout=120
)

result = response.json()

# Stats de compétition
stats_b = result["statistics"]["team_b"]
comp_stats = stats_b.get("competition_specific", {})

print("STATISTIQUES MOZAMBIQUE - COMPETITION:")
print(f"  Total matchs: {comp_stats.get('in_competition', {}).get('total_matches', 0)}")
print(f"  Victoires: {comp_stats.get('in_competition', {}).get('wins', 0)}")
print(f"  Win rate: {comp_stats.get('in_competition', {}).get('win_rate', 0)*100:.1f}%")

# Features
features_b = result["features"]["team_b"]

print("\nFEATURES EVENTS (toutes compétitions):")
events_global = features_b.get("events", {})
rt_global = events_global.get("regular_time_wins", {})
print(f"  Total wins: {rt_global.get('total_wins', 0)}")
print(f"  Wins regular: {rt_global.get('wins_in_regular_time', 0)}")
print(f"  Wins extra: {rt_global.get('wins_in_extra_time', 0)}")

print("\nFEATURES EVENTS COMPETITION:")
events_comp = features_b.get("events_competition", {})
rt_comp = events_comp.get("regular_time_wins", {})
print(f"  Total wins: {rt_comp.get('total_wins', 0)}")
print(f"  Wins regular: {rt_comp.get('wins_in_regular_time', 0)}")
print(f"  Wins extra: {rt_comp.get('wins_in_extra_time', 0)}")

print("\nFEATURES BY PHASE:")
by_phase = events_comp.get("by_phase", {})
print(f"  Phases détectées: {list(by_phase.keys())}")
for phase, stats in by_phase.items():
    print(f"  {phase}: {stats.get('wins', 0)}/{stats.get('total_matches', 0)} victoires")

# Sauvegarder le JSON complet pour inspection
with open("debug_mozambique_full.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print("\n✅ JSON complet sauvegardé dans debug_mozambique_full.json")
