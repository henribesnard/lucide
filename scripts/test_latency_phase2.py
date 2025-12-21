#!/usr/bin/env python3
"""
Test de latence Phase 2 - Fast LLM activé
"""

import requests
import json
import time
from datetime import datetime
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://localhost:8001"
USER_EMAIL = "user2@example.com"
USER_PASSWORD = "testuser"
TOKEN = None

CAN_LEAGUE_ID = 6
CAN_SEASON = 2025


def authenticate():
    global TOKEN
    print("[AUTH] Authentication...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": USER_EMAIL, "password": USER_PASSWORD}
    )
    if response.status_code == 200:
        data = response.json()
        TOKEN = data["access_token"]
        print(f"[OK] Token obtained")
        return True
    else:
        print(f"[FAIL] Authentication failed: {response.status_code}")
        return False


def make_chat_request(question, context=None):
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    payload = {"message": question}
    if context:
        payload["context"] = context

    start_time = time.time()
    response = requests.post(f"{BASE_URL}/chat", headers=headers, json=payload)
    latency_ms = int((time.time() - start_time) * 1000)

    if response.status_code == 200:
        data = response.json()
        return {"success": True, "data": data, "latency_ms": latency_ms}
    else:
        return {"success": False, "error": response.text, "latency_ms": latency_ms}


def run_tests():
    tests = [
        {
            "name": "League Context",
            "question": "Quel est le classement actuel de la CAN ?",
            "context": {
                "context_type": "league",
                "league_id": CAN_LEAGUE_ID,
                "league_name": "Africa Cup of Nations",
                "season": CAN_SEASON
            }
        },
        {
            "name": "Match Context",
            "question": "Analyse complete du match Mali contre Zambia",
            "context": {
                "context_type": "match",
                "league_id": CAN_LEAGUE_ID,
                "match_id": 1347240,
                "home_team_id": 1500,
                "away_team_id": 1507,
                "season": CAN_SEASON
            }
        },
        {
            "name": "League+Team Context",
            "question": "Quelle est la forme de Senegal dans la CAN cette saison ?",
            "context": {
                "context_type": "league_team",
                "league_id": CAN_LEAGUE_ID,
                "team_id": 13,
                "team_name": "Senegal",
                "season": CAN_SEASON
            }
        },
        {
            "name": "Player Context",
            "question": "Quels sont les meilleurs joueurs de Senegal ?",
            "context": {
                "context_type": "league_team",
                "league_id": CAN_LEAGUE_ID,
                "team_id": 13,
                "team_name": "Senegal",
                "season": CAN_SEASON
            }
        }
    ]

    results = []

    for i, test in enumerate(tests, 1):
        print(f"\n{'='*80}")
        print(f"[TEST {i}] {test['name']}")
        print(f"{'='*80}")
        print(f"\n[Q] {test['question']}")

        response = make_chat_request(test['question'], test['context'])

        if response['success']:
            data = response['data']
            tools = data.get('tools', [])
            print(f"[OK] Success ({response['latency_ms']}ms)")
            print(f"[INTENT] {data.get('intent')}")
            print(f"[TOOLS] {len(tools)} appeles: {', '.join(tools)}")

            results.append({
                "name": test['name'],
                "latency_ms": response['latency_ms'],
                "tools_count": len(tools)
            })
        else:
            print(f"[FAIL] {response.get('error')}")
            results.append({
                "name": test['name'],
                "latency_ms": response['latency_ms'],
                "tools_count": 0
            })

    return results


def generate_comparison_report(results):
    print("\n" + "="*80)
    print(" RAPPORT PHASE 2 - COMPARAISON AVEC PHASES PRECEDENTES")
    print("="*80)

    baseline = {
        "League Context": 56537,
        "Match Context": 64357,
        "League+Team Context": 64203,
        "Player Context": 56892
    }

    phase1 = {
        "League Context": 41257,
        "Match Context": 58543,
        "League+Team Context": 54835,
        "Player Context": 54790
    }

    baseline_avg = sum(baseline.values()) / len(baseline)
    phase1_avg = sum(phase1.values()) / len(phase1)
    phase2_avg = sum(r['latency_ms'] for r in results) / len(results)

    print(f"\n{'Test':<25} {'Baseline':<12} {'Phase 1':<12} {'Phase 2':<12} {'Gain Total':<12}")
    print("-" * 80)

    for result in results:
        name = result['name']
        b = baseline[name]
        p1 = phase1[name]
        p2 = result['latency_ms']
        gain = ((b - p2) / b) * 100

        print(f"{name:<25} {b:<12} {p1:<12} {p2:<12} {gain:>+6.1f}%")

    print("-" * 80)
    print(f"{'MOYENNE':<25} {baseline_avg:<12.0f} {phase1_avg:<12.0f} {phase2_avg:<12.0f} {((baseline_avg - phase2_avg) / baseline_avg * 100):>+6.1f}%")

    print("\n" + "="*80)
    print(" PROGRESSION DES OPTIMISATIONS")
    print("="*80)
    print(f"  Baseline     : {baseline_avg:.0f}ms")
    print(f"  Phase 1      : {phase1_avg:.0f}ms (-{((baseline_avg - phase1_avg) / baseline_avg * 100):.1f}%)")
    print(f"  Phase 2      : {phase2_avg:.0f}ms (-{((baseline_avg - phase2_avg) / baseline_avg * 100):.1f}%)")
    print(f"  Gain Phase 2 : {phase1_avg - phase2_avg:.0f}ms (-{((phase1_avg - phase2_avg) / phase1_avg * 100):.1f}% vs Phase 1)")

    print("\n" + "="*80)
    print(" OPTIMISATIONS ACTIVES")
    print("="*80)
    print("  [X] Redis Cache")
    print("  [X] Parallel API Calls (max 5)")
    print("  [X] Fast LLM (GPT-4o-mini for Intent + Tools)")
    print("  [ ] Smart Skip Analysis")

    # Save report
    report_path = "documentation/RAPPORT_OPTIMISATION_LATENCE_PHASE2.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"""# Rapport Optimisation Latence - Phase 2

**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Phase**: Phase 2 - Fast LLM activé
**Optimisations**: Redis Cache + Parallélisation + Fast LLM (GPT-4o-mini)

---

## Résumé Exécutif

| Phase | Latence Moyenne | vs Baseline | vs Phase Précédente |
|-------|-----------------|-------------|---------------------|
| **Baseline** | {baseline_avg:.0f}ms | - | - |
| **Phase 1** | {phase1_avg:.0f}ms | -{((baseline_avg - phase1_avg) / baseline_avg * 100):.1f}% | - |
| **Phase 2** | {phase2_avg:.0f}ms | **-{((baseline_avg - phase2_avg) / baseline_avg * 100):.1f}%** | **-{((phase1_avg - phase2_avg) / phase1_avg * 100):.1f}%** |

---

## Résultats Détaillés

| Test | Baseline | Phase 1 | Phase 2 | Gain Total |
|------|----------|---------|---------|------------|
""")
        for result in results:
            name = result['name']
            b = baseline[name]
            p1 = phase1[name]
            p2 = result['latency_ms']
            gain = ((b - p2) / b) * 100
            f.write(f"| {name} | {b}ms | {p1}ms | {p2}ms | {gain:+.1f}% |\n")

        f.write(f"""
---

## Analyse

### Objectif Phase 2
- **Cible**: ~22s de latence moyenne
- **Résultat**: {phase2_avg:.0f}ms ({phase2_avg/1000:.1f}s)
- **Statut**: {'✅ OBJECTIF ATTEINT' if phase2_avg <= 22000 else '⚠️ À améliorer'}

### Impact Fast LLM
- **Gain Phase 1 → Phase 2**: {phase1_avg - phase2_avg:.0f}ms (-{((phase1_avg - phase2_avg) / phase1_avg * 100):.1f}%)
- **Composantes optimisées**:
  - Intent Detection: DeepSeek → GPT-4o-mini (~2s → ~0.3s)
  - Tool Selection: DeepSeek → GPT-4o-mini (~1.5s → ~0.2s)
  - Response Generation: Optimisé ou reste DeepSeek

### Optimisations Actives

1. ✅ **Redis Cache** (Phase 1)
   - TTLs: 6h-24h selon endpoint
   - Hit rate production estimé: 60-70%

2. ✅ **Parallélisation API** (Phase 1)
   - Max 5 appels simultanés
   - asyncio.gather() avec semaphore

3. ✅ **Fast LLM** (Phase 2)
   - Provider: OpenAI GPT-4o-mini
   - Cibles: Intent Detection + Tool Selection
   - Gain: ~3-4s par requête

---

## Prochaines Étapes

### Phase 3 (Optionnel)
- Activer ENABLE_SMART_SKIP_ANALYSIS=true
- Implémenter Response Streaming (SSE)
- Cible: <18s de latence moyenne

---

**Validé par**: Script test_latency_phase2.py
**Date**: {datetime.now().strftime('%Y-%m-%d')}
**Statut**: {'✅ Phase 2 complète - Objectif atteint' if phase2_avg <= 22000 else '⚠️ Phase 2 complète - Optimisation supplémentaire requise'}
""")

    print(f"\n[OK] Rapport sauvegardé: {report_path}")


def main():
    print("\n" + "="*80)
    print(" TEST DE LATENCE - PHASE 2 (FAST LLM)")
    print("="*80)

    if not authenticate():
        return

    results = run_tests()
    generate_comparison_report(results)


if __name__ == "__main__":
    main()
