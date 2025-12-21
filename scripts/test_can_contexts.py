#!/usr/bin/env python3
"""
Tests contextes V4 avec CAN (Africa Cup of Nations)
Matchs disponibles a partir du 22/12/2025
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8001"
USER_EMAIL = "user2@example.com"
USER_PASSWORD = "testuser"
TOKEN = None

# CAN = Africa Cup of Nations (league_id=6)
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


def get_can_fixtures():
    """Get CAN fixtures starting from 22/12/2025"""
    print("\n[DATA] Fetching CAN fixtures...")
    headers = {"Authorization": f"Bearer {TOKEN}"}

    # Try to get fixtures for CAN
    response = requests.get(
        f"{BASE_URL}/api/fixtures?league_id={CAN_LEAGUE_ID}&season={CAN_SEASON}&from_date=2025-12-22&to_date=2025-12-31",
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        fixtures = data.get('fixtures', [])
        if fixtures:
            print(f"[OK] Found {len(fixtures)} fixtures for CAN")
            return fixtures
        else:
            print("[WARN] No fixtures found, trying without date range...")
            # Try without date range
            response = requests.get(
                f"{BASE_URL}/api/fixtures?league_id={CAN_LEAGUE_ID}&season={CAN_SEASON}",
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                fixtures = data.get('fixtures', [])
                print(f"[INFO] Found {len(fixtures)} total fixtures for CAN")
                return fixtures

    print("[ERROR] Failed to get fixtures")
    return []


def get_can_teams():
    """Get CAN teams"""
    print("\n[DATA] Fetching CAN teams...")
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(
        f"{BASE_URL}/api/teams?league_id={CAN_LEAGUE_ID}&season={CAN_SEASON}",
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        teams = data.get('teams', [])
        print(f"[OK] Found {len(teams)} teams for CAN")
        return teams

    print("[ERROR] Failed to get teams")
    return []


def test_league_context():
    print("\n" + "="*80)
    print("[TEST 1] CONTEXTE LEAGUE - CAN")
    print("="*80)

    test = {
        "name": "Classement CAN 2025",
        "question": "Quel est le classement actuel de la CAN ?",
        "context": {
            "context_type": "league",
            "league_id": CAN_LEAGUE_ID,
            "league_name": "Africa Cup of Nations",
            "season": CAN_SEASON
        }
    }

    print(f"\n[Q] {test['question']}")
    response = make_chat_request(test['question'], test['context'])

    if response['success']:
        data = response['data']
        tools = data.get('tools', [])
        print(f"[OK] Success ({response['latency_ms']}ms)")
        print(f"[INTENT] {data.get('intent')}")
        print(f"[TOOLS] {len(tools)} appeles: {', '.join(tools)}")
        print(f"[RESPONSE] {data.get('response')[:200]}...")
        return {"test": test, "response": response, "tools": tools}
    else:
        print(f"[FAIL] {response.get('error')}")
        return {"test": test, "response": response, "tools": []}


def test_match_context(fixtures):
    print("\n" + "="*80)
    print("[TEST 2] CONTEXTE MATCH - CAN")
    print("="*80)

    if not fixtures:
        print("[SKIP] No fixtures available")
        return {"test": None, "response": None, "tools": []}

    # Take first fixture
    fixture = fixtures[0]
    fixture_info = fixture.get('fixture', {})
    teams = fixture.get('teams', {})

    match_id = fixture_info.get('id')
    home_team = teams.get('home', {})
    away_team = teams.get('away', {})

    test = {
        "name": f"Analyse {home_team.get('name')} vs {away_team.get('name')}",
        "question": f"Analyse complete du match {home_team.get('name')} contre {away_team.get('name')}",
        "context": {
            "context_type": "match",
            "league_id": CAN_LEAGUE_ID,
            "match_id": match_id,
            "home_team_id": home_team.get('id'),
            "away_team_id": away_team.get('id'),
            "season": CAN_SEASON
        }
    }

    print(f"\n[MATCH] {home_team.get('name')} vs {away_team.get('name')} (ID: {match_id})")
    print(f"[Q] {test['question']}")

    response = make_chat_request(test['question'], test['context'])

    if response['success']:
        data = response['data']
        tools = data.get('tools', [])
        print(f"[OK] Success ({response['latency_ms']}ms)")
        print(f"[INTENT] {data.get('intent')}")
        print(f"[TOOLS] {len(tools)} appeles: {', '.join(tools)}")
        print(f"[RESPONSE] {data.get('response')[:200]}...")
        return {"test": test, "response": response, "tools": tools}
    else:
        print(f"[FAIL] {response.get('error')}")
        return {"test": test, "response": response, "tools": []}


def test_league_team_context(teams):
    print("\n" + "="*80)
    print("[TEST 3] CONTEXTE LEAGUE + TEAM - CAN")
    print("="*80)

    if not teams:
        print("[SKIP] No teams available")
        return {"test": None, "response": None, "tools": []}

    # Take first team
    team = teams[0]

    test = {
        "name": f"Forme {team.get('name')} en CAN",
        "question": f"Quelle est la forme de {team.get('name')} dans la CAN cette saison ?",
        "context": {
            "context_type": "league_team",
            "league_id": CAN_LEAGUE_ID,
            "team_id": team.get('id'),
            "team_name": team.get('name'),
            "season": CAN_SEASON
        }
    }

    print(f"\n[TEAM] {team.get('name')} (ID: {team.get('id')})")
    print(f"[Q] {test['question']}")

    response = make_chat_request(test['question'], test['context'])

    if response['success']:
        data = response['data']
        tools = data.get('tools', [])
        print(f"[OK] Success ({response['latency_ms']}ms)")
        print(f"[INTENT] {data.get('intent')}")
        print(f"[TOOLS] {len(tools)} appeles: {', '.join(tools)}")
        print(f"[RESPONSE] {data.get('response')[:200]}...")
        return {"test": test, "response": response, "tools": tools}
    else:
        print(f"[FAIL] {response.get('error')}")
        return {"test": test, "response": response, "tools": []}


def test_player_team_context(teams):
    print("\n" + "="*80)
    print("[TEST 4] CONTEXTE PLAYER (Team Mode) - CAN")
    print("="*80)

    if not teams:
        print("[SKIP] No teams available")
        return {"test": None, "response": None, "tools": []}

    # Use first team and search for a player
    team = teams[0]

    test = {
        "name": f"Recherche joueur de {team.get('name')}",
        "question": f"Quels sont les meilleurs joueurs de {team.get('name')} ?",
        "context": {
            "context_type": "league_team",  # We use league_team because we don't have specific player_id yet
            "league_id": CAN_LEAGUE_ID,
            "team_id": team.get('id'),
            "team_name": team.get('name'),
            "season": CAN_SEASON
        }
    }

    print(f"\n[TEAM] {team.get('name')} (ID: {team.get('id')})")
    print(f"[Q] {test['question']}")

    response = make_chat_request(test['question'], test['context'])

    if response['success']:
        data = response['data']
        tools = data.get('tools', [])
        print(f"[OK] Success ({response['latency_ms']}ms)")
        print(f"[INTENT] {data.get('intent')}")
        print(f"[TOOLS] {len(tools)} appeles: {', '.join(tools)}")
        print(f"[RESPONSE] {data.get('response')[:200]}...")
        return {"test": test, "response": response, "tools": tools}
    else:
        print(f"[FAIL] {response.get('error')}")
        return {"test": test, "response": response, "tools": []}


def generate_report(results):
    """Generate markdown report"""
    print("\n" + "="*80)
    print("[REPORT] Generating report...")
    print("="*80)

    report_md = f"""# Tests Contextes V4 - CAN (Africa Cup of Nations)

**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Competition**: Africa Cup of Nations (CAN)
**League ID**: {CAN_LEAGUE_ID}
**Season**: {CAN_SEASON}

---

## Résumé

"""

    # Calculate statistics
    total_tests = len(results)
    successful = sum(1 for r in results if r['response'] and r['response'].get('success'))
    total_tools = sum(len(r.get('tools', [])) for r in results)
    avg_latency = sum(r['response']['latency_ms'] for r in results if r['response']) / max(successful, 1)

    report_md += f"""| Métrique | Valeur |
|----------|--------|
| **Tests** | {successful}/{total_tests} réussis |
| **Tools Appelés** | {total_tools} au total |
| **Latence Moyenne** | {avg_latency:.0f}ms |

---

"""

    # Detail each test
    for i, result in enumerate(results, 1):
        test = result.get('test')
        response = result.get('response')
        tools = result.get('tools', [])

        if not test or not response:
            report_md += f"## Test {i}: [SKIPPED]\n\n"
            continue

        report_md += f"""## Test {i}: {test['name']}

**Question**: {test['question']}

**Context**:
```json
{json.dumps(test['context'], indent=2, ensure_ascii=False)}
```

"""

        if response.get('success'):
            data = response['data']
            report_md += f"""**Résultat**: SUCCESS
**Latence**: {response['latency_ms']}ms
**Intent**: `{data.get('intent')}`
**Tools Appelés** ({len(tools)}): `{', '.join(tools) if tools else 'Aucun'}`

**Réponse**:
> {data.get('response')}

---

"""
        else:
            report_md += f"""**Résultat**: FAILED
**Erreur**: {response.get('error')}

---

"""

    # Save report
    report_path = "documentation/RAPPORT_TESTS_CAN_V4.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_md)

    print(f"[OK] Report saved: {report_path}")

    # Save JSON
    json_path = "documentation/tests_can_v4_results.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    print(f"[OK] JSON saved: {json_path}")

    return report_path


def main():
    print("\n" + "="*80)
    print(" TESTS CONTEXTES V4 - CAN (Africa Cup of Nations)")
    print("="*80)

    if not authenticate():
        return

    # Get data
    fixtures = get_can_fixtures()
    teams = get_can_teams()

    results = []

    # Run tests
    results.append(test_league_context())

    if fixtures:
        results.append(test_match_context(fixtures))
    else:
        print("\n[WARN] Skipping MATCH tests - no fixtures available")

    if teams:
        results.append(test_league_team_context(teams))
        results.append(test_player_team_context(teams))
    else:
        print("\n[WARN] Skipping TEAM tests - no teams available")

    # Generate report
    report_path = generate_report(results)

    print("\n" + "="*80)
    print(" TESTS COMPLETED")
    print("="*80)
    print(f"\n[REPORT] {report_path}")

    # Print summary
    total_tools = sum(len(r.get('tools', [])) for r in results)
    print(f"\n[SUMMARY] Total tools called: {total_tools}")


if __name__ == "__main__":
    main()
