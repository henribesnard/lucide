
import requests
import json
import time
import datetime
import statistics

BASE_URL = "http://localhost:8001"
LEAGUE_ID = 6  # Africa Cup of Nations (CAF)
FROM_DATE = "2025-12-22"
TO_DATE = "2026-01-31"  # Roughly end of competition
TEST_EMAIL = f"test_audit_{int(time.time())}@example.com"
TEST_PASSWORD = "password123"

def print_header(title):
    print(f"\n{'='*60}\n{title}\n{'='*60}")

def register_and_login():
    print(f"[*] Registering test user: {TEST_EMAIL}")
    try:
        # Register
        reg_payload = {"email": TEST_EMAIL, "password": TEST_PASSWORD, "first_name": "Test", "last_name": "Audit"}
        requests.post(f"{BASE_URL}/auth/register", json=reg_payload)
        
        # Login
        login_payload = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
        start = time.time()
        resp = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
        end = time.time()
        
        if resp.status_code != 200:
            print(f"[!] Login failed: {resp.text}")
            return None
            
        token = resp.json()["access_token"]
        print(f"[+] Authenticated (Latency: {end-start:.3f}s)")
        return token
    except Exception as e:
        print(f"[!] connection failed: {e}")
        return None

def get_can_fixtures(token):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}/api/fixtures?league_id={LEAGUE_ID}&from_date={FROM_DATE}&to_date={TO_DATE}"
    print(f"[*] Fetching CAN fixtures: {url}")
    
    start = time.time()
    resp = requests.get(url, headers=headers)
    end = time.time()
    
    if resp.status_code != 200:
        print(f"[!] Fetch fixtures failed: {resp.text}")
        return []
    
    data = resp.json()
    fixtures = data.get("fixtures", [])
    print(f"[+] Found {len(fixtures)} fixtures (Latency: {end-start:.3f}s)")
    return fixtures

def test_match_chat(token, match):
    headers = {"Authorization": f"Bearer {token}"}
    
    fixture = match["fixture"]
    teams = match["teams"]
    league = match["league"]
    
    match_title = f"{teams['home']['name']} vs {teams['away']['name']}"
    match_date = fixture["date"]
    
    questions = [
        f"Analyse le match {match_title}.",
        "Quels sont les enjeux ?",
        "Qui est favori ?"
    ]
    
    # Pick one question randomly or sequential
    question = questions[0]
    
    context = {
        "match_id": fixture["id"],
        "league_id": league["id"],
        "home_team_id": teams["home"]["id"],
        "away_team_id": teams["away"]["id"],
        "match_date": match_date,
        "league_name": league["name"],
        "league_country": "World" # CAN is international/world context
    }
    
    payload = {
        "message": question,
        "context": context
    }
    
    print(f"\n--- Testing Match: {match_title} ({match_date}) ---")
    print(f"Q: {question}")
    
    start = time.time()
    try:
        resp = requests.post(f"{BASE_URL}/chat", json=payload, headers=headers)
        end = time.time()
        
        latency = end - start
        
        if resp.status_code == 200:
            data = resp.json()
            response_text = data["response"]
            tools_used = data.get("tools", [])
            
            print(f"A: [Length: {len(response_text)} chars]")
            print(f"Tools Used: {tools_used}")
            print(f"Latency: {latency:.3f}s")
            
            return {
                "success": True,
                "match": match_title,
                "latency": latency,
                "tools": tools_used,
                "response_preview": response_text[:100] + "..."
            }
        else:
            print(f"[!] Chat failed: {resp.text}")
            return {"success": False, "match": match_title, "error": resp.status_code}
            
    except Exception as e:
        print(f"[!] Exception during chat: {e}")
        return {"success": False, "match": match_title, "error": str(e)}

def generate_report(results):
    print_header("RAPPORT DE VALIDATION - LUCIDE WORKFLOW (CAN)")
    
    if not results:
        print("Aucun résultat.")
        return

    latencies = [r["latency"] for r in results if r["success"]]
    avg_latency = statistics.mean(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0
    min_latency = min(latencies) if latencies else 0
    
    success_count = len([r for r in results if r["success"]])
    
    print(f"1. Capacité de réponse contextuelle")
    print(f"   - Matchs testés : {len(results)}")
    print(f"   - Succès : {success_count}/{len(results)}")
    print(f"   - Taux : {success_count/len(results)*100:.1f}%")
    
    print(f"\n2. Latence du Workflow")
    print(f"   - Moyenne : {avg_latency:.3f}s")
    print(f"   - Min : {min_latency:.3f}s")
    print(f"   - Max : {max_latency:.3f}s")
    
    print(f"\n3. Qualité des réponses (Echantillon)")
    for i, r in enumerate(results[:3]):
        if r["success"]:
            print(f"   - Match: {r['match']}")
            print(f"     Outils: {r['tools']}")
            print(f"     Aperçu: {r['response_preview']}")
            
    print(f"\n4. Endpoints API-Football utilisés")
    print(f"   - Basé sur les logs serveur (non visible ici), mais les outils indiquent l'utilisation de l'agent.")
    
    if success_count == len(results) and avg_latency < 10.0:
        print("\n✅ CONCLUSION: Workflow validé pour mise en production.")
    else:
        print("\n⚠️ CONCLUSION: Des optimisations sont nécessaires.")

def main():
    print_header("INITIALISATION DU TEST")
    token = register_and_login()
    if not token:
        return
        
    fixtures = get_can_fixtures(token)
    
    if not fixtures:
        print("Aucun match trouvé pour la CAN sur cette période.")
        print("Vérifiez que la ligue 6 et les dates sont correctes dans l'API Football.")
        # Fallback to current fixtures if empty just to test workflow? 
        # No, strict audit.
        return

    # Select a few spread out matches
    test_matches = fixtures[:3] # First 3
    
    results = []
    for match in test_matches:
        res = test_match_chat(token, match)
        results.append(res)
        time.sleep(1) # Pause between requests
        
    generate_report(results)
    
    with open("validation_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
