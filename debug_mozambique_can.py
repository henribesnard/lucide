"""Debug l'incohérence Mozambique CAN."""
import requests
import json

API_URL = "http://localhost:8001/match-analysis/analyze/extended"

print("="*80)
print("DEBUG: Mozambique - Incohérence Regular Time vs Phase de Groupes")
print("="*80)

payload = {
    "league": "Africa Cup of Nations",
    "league_type": "cup",
    "team_a": "Gabon",
    "team_b": "Mozambique",
}

response = requests.post(
    API_URL,
    json=payload,
    params={"num_last_matches": 30},
    timeout=120
)

if response.status_code != 200:
    print(f"Erreur: {response.status_code}")
    print(response.text)
    exit(1)

result = response.json()

# Extraire les features brutes
features = result.get("features", {})
mozambique_events_comp = features.get("team_b", {}).get("events_competition", {})

print("\n1. REGULAR TIME WINS (toute la compétition):")
regular_time = mozambique_events_comp.get("regular_time_wins", {})
print(f"   Total victoires: {regular_time.get('total_wins', 0)}")
print(f"   Victoires en temps réglementaire: {regular_time.get('wins_in_regular_time', 0)}")
print(f"   Victoires en prolongations/penalties: {regular_time.get('wins_in_extra_time', 0)}")
print(f"   Taux temps réglementaire: {regular_time.get('regular_time_win_rate', 0)*100:.1f}%")

print("\n2. BY PHASE (par phase de compétition):")
by_phase = mozambique_events_comp.get("by_phase", {})
for phase, stats in by_phase.items():
    print(f"   {phase}:")
    print(f"     - Total matchs: {stats.get('total_matches', 0)}")
    print(f"     - Victoires: {stats.get('wins', 0)}")
    print(f"     - Taux victoire: {stats.get('win_rate', 0)*100:.1f}%")

print("\n3. INSIGHTS GÉNÉRÉS:")
insights = result.get("insights", {}).get("items", [])
mozambique_insights = [i for i in insights if i.get("team") == "team_b"]
for insight in mozambique_insights:
    if insight.get("category") in ["competition_regular_time", "phase_weakness", "phase_dominance"]:
        print(f"   [{insight.get('category')}] {insight.get('text', '')}")

print("\n4. ANALYSE DU PROBLÈME:")
total_wins = regular_time.get('total_wins', 0)
wins_regular = regular_time.get('wins_in_regular_time', 0)
wins_extra = regular_time.get('wins_in_extra_time', 0)
group_wins = by_phase.get('group_stage', {}).get('wins', 0)

print(f"   Total victoires CAN: {total_wins}")
print(f"   Victoires temps réglementaire: {wins_regular}")
print(f"   Victoires prolongations/penalties: {wins_extra}")
print(f"   Victoires phase de groupes: {group_wins}")

if wins_extra > 0 and group_wins > 0:
    print("\n   ⚠️ INCOHÉRENCE DÉTECTÉE:")
    print(f"   - Il y a {wins_extra} victoire(s) en prolongations/penalties")
    print(f"   - Il y a {group_wins} victoire(s) en phase de groupes")
    print("   - MAIS en phase de groupes il n'y a PAS de prolongations!")
    print("\n   HYPOTHÈSE:")
    print("   - Les victoires en prolongations viennent de phases knockout (passées)")
    print("   - Les victoires en phase de groupes sont forcément en temps réglementaire")
    print(f"   - Donc au TOTAL: au moins {group_wins} victoire(s) en temps réglementaire")
    print(f"   - Le calcul 'wins_in_regular_time={wins_regular}' est probablement FAUX")
elif wins_extra == total_wins and group_wins > 0:
    print("\n   🔴 INCOHÉRENCE LOGIQUE CONFIRMÉE:")
    print(f"   - L'insight dit: TOUTES les victoires ({total_wins}) sont en prolongations")
    print(f"   - Mais il y a {group_wins} victoire(s) en phase de groupes")
    print("   - En phase de groupes, pas de prolongations → victoire = temps réglementaire")
    print("\n   CONCLUSION: L'insight 'regular_time' est FAUX ou incomplet")

print("\n" + "="*80)
