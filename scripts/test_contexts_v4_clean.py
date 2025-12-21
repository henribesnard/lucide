#!/usr/bin/env python3
"""
Script de test complet pour les contextes V4
Teste toutes les combinaisons de contexte avec des questions ralistes
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BASE_URL = "http://localhost:8001"
USER_EMAIL = "user2@example.com"
USER_PASSWORD = "testuser"

# Token global
TOKEN = None


class TestResult:
    def __init__(self, test_name: str, context_type: str):
        self.test_name = test_name
        self.context_type = context_type
        self.question = ""
        self.context = {}
        self.success = False
        self.latency_ms = 0
        self.response = ""
        self.intent = ""
        self.tools_called = []
        self.error = None
        self.session_id = None

    def to_dict(self):
        return {
            "test_name": self.test_name,
            "context_type": self.context_type,
            "question": self.question,
            "context": self.context,
            "success": self.success,
            "latency_ms": self.latency_ms,
            "response": self.response[:200] + "..." if len(self.response) > 200 else self.response,
            "intent": self.intent,
            "tools_called": self.tools_called,
            "error": str(self.error) if self.error else None,
            "session_id": self.session_id,
        }


def authenticate():
    """Authenticate and get token"""
    global TOKEN
    print("[AUTH] Authentication...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": USER_EMAIL, "password": USER_PASSWORD}
    )
    if response.status_code == 200:
        data = response.json()
        TOKEN = data["access_token"]
        print(f"[OK] Token obtained: {TOKEN[:50]}...")
        return True
    else:
        print(f"[FAIL] Authentication failed: {response.status_code}")
        return False


def make_chat_request(question: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make a chat request with optional context"""
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    payload = {"message": question}
    if context:
        payload["context"] = context

    start_time = time.time()
    response = requests.post(f"{BASE_URL}/chat", headers=headers, json=payload)
    latency_ms = int((time.time() - start_time) * 1000)

    if response.status_code == 200:
        data = response.json()
        return {
            "success": True,
            "data": data,
            "latency_ms": latency_ms
        }
    else:
        return {
            "success": False,
            "error": response.text,
            "latency_ms": latency_ms
        }


def test_league_context():
    """Test LEAGUE context with varied questions"""
    print("\n" + "="*80)
    print(" TEST 1: CONTEXTE LEAGUE")
    print("="*80)

    tests = [
        {
            "name": "Classement Ligue 1",
            "question": "Quel est le classement actuel ?",
            "context": {
                "context_type": "league",
                "league_id": 61,
                "league_name": "Ligue 1",
                "season": 2025
            }
        },
        {
            "name": "Meilleurs buteurs Premier League",
            "question": "Qui sont les meilleurs buteurs cette saison ?",
            "context": {
                "context_type": "league",
                "league_id": 39,
                "league_name": "Premier League",
                "season": 2025
            }
        },
        {
            "name": "Statistiques gnrales La Liga",
            "question": "Quelles sont les quipes en forme en ce moment ?",
            "context": {
                "context_type": "league",
                "league_id": 140,
                "league_name": "La Liga",
                "season": 2025
            }
        }
    ]

    results = []
    for test in tests:
        print(f"\n Test: {test['name']}")
        print(f"   Question: {test['question']}")

        result = TestResult(test['name'], "league")
        result.question = test['question']
        result.context = test['context']

        response = make_chat_request(test['question'], test['context'])
        result.latency_ms = response['latency_ms']
        result.success = response['success']

        if response['success']:
            data = response['data']
            result.response = data.get('response', '')
            result.intent = data.get('intent', '')
            result.session_id = data.get('session_id', '')

            # Extract tools called (correct field name is 'tools', not 'tool_results')
            if 'tools' in data:
                result.tools_called = data['tools']

            print(f"    Success ({result.latency_ms}ms)")
            print(f"   Intent: {result.intent}")
            print(f"   Tools: {', '.join(result.tools_called)}")
            print(f"   Response: {result.response[:150]}...")
        else:
            result.error = response.get('error')
            print(f"    Failed: {result.error}")

        results.append(result)
        time.sleep(1)  # Avoid rate limiting

    return results


def test_match_context():
    """Test MATCH context"""
    print("\n" + "="*80)
    print(" TEST 2: CONTEXTE MATCH")
    print("="*80)

    # First, get a real match from Ligue 1
    print("\n Fetching real match data...")
    headers = {"Authorization": f"Bearer {TOKEN}"}
    fixtures_response = requests.get(
        f"{BASE_URL}/api/fixtures?league_id=61&season=2025",
        headers=headers
    )

    if fixtures_response.status_code != 200:
        print(f" Failed to get fixtures: {fixtures_response.status_code}")
        return []

    fixtures_data = fixtures_response.json()
    fixtures = fixtures_data.get('fixtures', [])

    if not fixtures:
        print("  No fixtures found for Ligue 1")
        return []

    # Take the first fixture
    fixture = fixtures[0]
    fixture_info = fixture.get('fixture', {})
    teams = fixture.get('teams', {})

    match_id = fixture_info.get('id')
    home_team = teams.get('home', {})
    away_team = teams.get('away', {})

    print(f" Match found: {home_team.get('name')} vs {away_team.get('name')} (ID: {match_id})")

    tests = [
        {
            "name": "Analyse match",
            "question": f"Analyse complte du match {home_team.get('name')} vs {away_team.get('name')}",
            "context": {
                "context_type": "match",
                "league_id": 61,
                "match_id": match_id,
                "home_team_id": home_team.get('id'),
                "away_team_id": away_team.get('id'),
                "season": 2025
            }
        },
        {
            "name": "Pronostic 1X2",
            "question": "Quel est ton pronostic pour ce match ?",
            "context": {
                "context_type": "match",
                "league_id": 61,
                "match_id": match_id,
                "home_team_id": home_team.get('id'),
                "away_team_id": away_team.get('id'),
                "season": 2025
            }
        },
        {
            "name": "Historique confrontations",
            "question": "Quel est l'historique des confrontations entre ces deux quipes ?",
            "context": {
                "context_type": "match",
                "league_id": 61,
                "match_id": match_id,
                "home_team_id": home_team.get('id'),
                "away_team_id": away_team.get('id'),
                "season": 2025
            }
        }
    ]

    results = []
    for test in tests:
        print(f"\n Test: {test['name']}")
        print(f"   Question: {test['question']}")

        result = TestResult(test['name'], "match")
        result.question = test['question']
        result.context = test['context']

        response = make_chat_request(test['question'], test['context'])
        result.latency_ms = response['latency_ms']
        result.success = response['success']

        if response['success']:
            data = response['data']
            result.response = data.get('response', '')
            result.intent = data.get('intent', '')
            result.session_id = data.get('session_id', '')

            if 'tool_results' in data:
                result.tools_called = [tr.get('name') for tr in data['tool_results']]

            print(f"    Success ({result.latency_ms}ms)")
            print(f"   Intent: {result.intent}")
            print(f"   Tools: {', '.join(result.tools_called)}")
            print(f"   Response: {result.response[:150]}...")
        else:
            result.error = response.get('error')
            print(f"    Failed: {result.error}")

        results.append(result)
        time.sleep(2)  # Longer delay for match tests (more API calls)

    return results


def test_league_team_context():
    """Test LEAGUE + TEAM context"""
    print("\n" + "="*80)
    print(" TEST 3: CONTEXTE LEAGUE + TEAM")
    print("="*80)

    tests = [
        {
            "name": "Forme PSG en Ligue 1",
            "question": "Quelle est la forme du PSG en Ligue 1 cette saison ?",
            "context": {
                "context_type": "league_team",
                "league_id": 61,
                "team_id": 85,  # PSG
                "team_name": "Paris Saint Germain",
                "season": 2025
            }
        },
        {
            "name": "Statistiques Man City Premier League",
            "question": "Quelles sont les statistiques de Manchester City en Premier League ?",
            "context": {
                "context_type": "league_team",
                "league_id": 39,
                "team_id": 50,  # Man City
                "team_name": "Manchester City",
                "season": 2025
            }
        }
    ]

    results = []
    for test in tests:
        print(f"\n Test: {test['name']}")
        print(f"   Question: {test['question']}")

        result = TestResult(test['name'], "league_team")
        result.question = test['question']
        result.context = test['context']

        response = make_chat_request(test['question'], test['context'])
        result.latency_ms = response['latency_ms']
        result.success = response['success']

        if response['success']:
            data = response['data']
            result.response = data.get('response', '')
            result.intent = data.get('intent', '')
            result.session_id = data.get('session_id', '')

            if 'tool_results' in data:
                result.tools_called = [tr.get('name') for tr in data['tool_results']]

            print(f"    Success ({result.latency_ms}ms)")
            print(f"   Intent: {result.intent}")
            print(f"   Tools: {', '.join(result.tools_called)}")
            print(f"   Response: {result.response[:150]}...")
        else:
            result.error = response.get('error')
            print(f"    Failed: {result.error}")

        results.append(result)
        time.sleep(1)

    return results


def test_player_match_context():
    """Test PLAYER (Match mode) context"""
    print("\n" + "="*80)
    print(" TEST 4: CONTEXTE PLAYER (Match Mode)")
    print("="*80)

    # Using known player IDs (Mbapp, etc.)
    tests = [
        {
            "name": "Performance Mbapp dans match",
            "question": "Comment a jou Mbapp dans ce match ?",
            "context": {
                "context_type": "player",
                "league_id": 61,
                "match_id": 1234567,  # Will fail if match doesn't exist, but tests the workflow
                "player_id": 278,  # Mbapp
                "team_id": 85,  # PSG
                "player_name": "Kylian Mbapp",
                "season": 2025
            }
        }
    ]

    results = []
    for test in tests:
        print(f"\n Test: {test['name']}")
        print(f"   Question: {test['question']}")
        print(f"     Note: May fail if match_id doesn't exist - testing workflow validation")

        result = TestResult(test['name'], "player_match")
        result.question = test['question']
        result.context = test['context']

        response = make_chat_request(test['question'], test['context'])
        result.latency_ms = response['latency_ms']
        result.success = response['success']

        if response['success']:
            data = response['data']
            result.response = data.get('response', '')
            result.intent = data.get('intent', '')
            result.session_id = data.get('session_id', '')

            if 'tool_results' in data:
                result.tools_called = [tr.get('name') for tr in data['tool_results']]

            print(f"    Success ({result.latency_ms}ms)")
            print(f"   Intent: {result.intent}")
            print(f"   Tools: {', '.join(result.tools_called)}")
        else:
            result.error = response.get('error')
            print(f"    Failed (expected if match doesn't exist): {result.error[:100]}")

        results.append(result)

    return results


def test_player_team_context():
    """Test PLAYER (Team mode) context"""
    print("\n" + "="*80)
    print(" TEST 5: CONTEXTE PLAYER (Team Mode)")
    print("="*80)

    tests = [
        {
            "name": "Statistiques Haaland saison",
            "question": "Quelles sont les statistiques de Haaland cette saison ?",
            "context": {
                "context_type": "player",
                "league_id": 39,
                "team_id": 50,  # Man City
                "player_id": 627,  # Haaland
                "player_name": "Erling Haaland",
                "season": 2025
            }
        },
        {
            "name": "Forme Mbapp saison",
            "question": "Quelle est la forme de Mbapp cette saison ?",
            "context": {
                "context_type": "player",
                "league_id": 61,
                "team_id": 85,  # PSG
                "player_id": 278,  # Mbapp
                "player_name": "Kylian Mbapp",
                "season": 2025
            }
        }
    ]

    results = []
    for test in tests:
        print(f"\n Test: {test['name']}")
        print(f"   Question: {test['question']}")

        result = TestResult(test['name'], "player_team")
        result.question = test['question']
        result.context = test['context']

        response = make_chat_request(test['question'], test['context'])
        result.latency_ms = response['latency_ms']
        result.success = response['success']

        if response['success']:
            data = response['data']
            result.response = data.get('response', '')
            result.intent = data.get('intent', '')
            result.session_id = data.get('session_id', '')

            if 'tool_results' in data:
                result.tools_called = [tr.get('name') for tr in data['tool_results']]

            print(f"    Success ({result.latency_ms}ms)")
            print(f"   Intent: {result.intent}")
            print(f"   Tools: {', '.join(result.tools_called)}")
            print(f"   Response: {result.response[:150]}...")
        else:
            result.error = response.get('error')
            print(f"    Failed: {result.error}")

        results.append(result)
        time.sleep(1)

    return results


def generate_report(all_results: List[TestResult]):
    """Generate comprehensive markdown report"""
    print("\n" + "="*80)
    print(" GENERATING REPORT")
    print("="*80)

    report_md = f"""# Tests Contextes V4 - Rapport Complet

**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Backend**: {BASE_URL}
**Utilisateur**: {USER_EMAIL}

---

##  Rsum Gnral

"""

    # Summary statistics
    total_tests = len(all_results)
    successful = sum(1 for r in all_results if r.success)
    failed = total_tests - successful
    avg_latency = sum(r.latency_ms for r in all_results) / total_tests if total_tests > 0 else 0

    report_md += f"""| Mtrique | Valeur |
|----------|--------|
| **Tests Totaux** | {total_tests} |
| ** Russis** | {successful} ({successful/total_tests*100:.1f}%) |
| ** chous** | {failed} ({failed/total_tests*100:.1f}%) |
| ** Latence Moyenne** | {avg_latency:.0f}ms |

---

"""

    # Group by context type
    by_context = {}
    for result in all_results:
        if result.context_type not in by_context:
            by_context[result.context_type] = []
        by_context[result.context_type].append(result)

    # Detail per context type
    for context_type, results in by_context.items():
        report_md += f"\n## {context_type.upper()} Context\n\n"

        for result in results:
            status_icon = "" if result.success else ""
            report_md += f"### {status_icon} {result.test_name}\n\n"
            report_md += f"**Question**: {result.question}\n\n"
            report_md += f"**Contexte**:\n```json\n{json.dumps(result.context, indent=2, ensure_ascii=False)}\n```\n\n"

            if result.success:
                report_md += f"**Intent**: `{result.intent}`\n\n"
                report_md += f"**Tools Appels** ({len(result.tools_called)}): `{', '.join(result.tools_called)}`\n\n"
                report_md += f"**Latence**: {result.latency_ms}ms\n\n"
                report_md += f"**Rponse**:\n> {result.response}\n\n"
            else:
                report_md += f"**Erreur**: {result.error}\n\n"

            report_md += "---\n\n"

    # Save report
    report_path = "documentation/RAPPORT_TESTS_CONTEXTES_V4.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_md)

    print(f" Report saved to: {report_path}")

    # Save JSON results
    json_path = "documentation/tests_contextes_v4_results.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump([r.to_dict() for r in all_results], f, indent=2, ensure_ascii=False)

    print(f" JSON results saved to: {json_path}")

    return report_path, json_path


def main():
    print("\n" + "="*80)
    print("  TESTS CONTEXTES V4 - LUCIDE BACKEND")
    print("="*80)

    if not authenticate():
        print(" Authentication failed. Exiting.")
        return

    all_results = []

    # Run all tests
    all_results.extend(test_league_context())
    all_results.extend(test_match_context())
    all_results.extend(test_league_team_context())
    all_results.extend(test_player_match_context())
    all_results.extend(test_player_team_context())

    # Generate report
    report_path, json_path = generate_report(all_results)

    print("\n" + "="*80)
    print(" ALL TESTS COMPLETED")
    print("="*80)
    print(f"\n Report: {report_path}")
    print(f" JSON: {json_path}")

    # Print summary
    successful = sum(1 for r in all_results if r.success)
    total = len(all_results)
    print(f"\n Success Rate: {successful}/{total} ({successful/total*100:.1f}%)")


if __name__ == "__main__":
    main()

