"""
Script pour analyser tous les matchs programmés de la CAN.
Récupère les matchs à venir et lance l'analyse étendue sur chacun.
"""

import requests
import json
import os
import time
from datetime import datetime
from pathlib import Path

# Configuration
API_FOOTBALL_BASE_URL = "https://v3.football.api-sports.io"
BACKEND_API_URL = "http://localhost:8001"
CAN_LEAGUE_ID = 6
CURRENT_SEASON = 2025
OUTPUT_DIR = "can_analyses"

# Récupérer la clé API depuis .env
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("FOOTBALL_API_KEY")

if not API_KEY:
    print("ERREUR: FOOTBALL_API_KEY non trouvée dans .env")
    exit(1)


def get_upcoming_can_matches():
    """Récupère tous les matchs à venir de la CAN."""
    print("="*100)
    print("RÉCUPÉRATION DES MATCHS DE LA CAN 2025")
    print("="*100)

    headers = {
        "x-rapidapi-host": "v3.football.api-sports.io",
        "x-rapidapi-key": API_KEY
    }

    # Récupérer les fixtures de la saison en cours
    url = f"{API_FOOTBALL_BASE_URL}/fixtures"
    params = {
        "league": CAN_LEAGUE_ID,
        "season": CURRENT_SEASON
    }

    print(f"\nAppel API: {url}")
    print(f"Params: {params}")

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"ERREUR: Status code {response.status_code}")
        print(response.text)
        return []

    data = response.json()
    fixtures = data.get("response", [])

    print(f"\nTotal fixtures récupérées: {len(fixtures)}")

    # Filtrer les matchs à venir ou en cours
    upcoming_matches = []
    now = datetime.now()

    for fixture in fixtures:
        fixture_data = fixture.get("fixture", {})
        teams = fixture.get("teams", {})

        status = fixture_data.get("status", {}).get("short", "")
        fixture_date = fixture_data.get("date", "")

        # Inclure les matchs pas encore joués (NS = Not Started, TBD, PST, etc.)
        # ou en cours (1H, 2H, HT, etc.)
        if status in ["TBD", "NS", "1H", "HT", "2H", "ET", "BT", "P", "SUSP", "INT", "PST"]:
            match_info = {
                "fixture_id": fixture_data.get("id"),
                "date": fixture_date,
                "status": status,
                "team_home": teams.get("home", {}).get("name"),
                "team_home_id": teams.get("home", {}).get("id"),
                "team_away": teams.get("away", {}).get("name"),
                "team_away_id": teams.get("away", {}).get("id"),
                "round": fixture.get("league", {}).get("round", ""),
                "venue": fixture_data.get("venue", {}).get("name", ""),
            }
            upcoming_matches.append(match_info)

    print(f"\nMatchs à venir ou en cours: {len(upcoming_matches)}")

    # Trier par date
    upcoming_matches.sort(key=lambda x: x["date"])

    return upcoming_matches


def analyze_match(team_a, team_b, team_a_id, team_b_id):
    """Lance l'analyse étendue pour un match."""
    url = f"{BACKEND_API_URL}/match-analysis/analyze/extended"

    payload = {
        "league": str(CAN_LEAGUE_ID),
        "team_a": team_a,
        "team_b": team_b,
        "league_type": "cup"
    }

    params = {
        "num_last_matches": 30
    }

    print(f"\n  Appel API backend: {team_a} vs {team_b}")

    try:
        response = requests.post(
            url,
            json=payload,
            params=params,
            timeout=180
        )

        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"  [ERROR] Status {response.status_code}")
            print(f"  {response.text[:200]}")
            return None

    except requests.exceptions.Timeout:
        print(f"  [ERROR] TIMEOUT apres 180s")
        return None
    except Exception as e:
        print(f"  [ERROR] {e}")
        return None


def save_summary(match_info, analysis_data, output_dir):
    """Sauvegarde le résumé d'analyse dans un fichier .md."""
    if not analysis_data or "summary" not in analysis_data:
        print(f"  [WARNING] Pas de resume disponible")
        return None

    # Créer le nom de fichier
    team_a = match_info["team_home"].replace(" ", "_").replace("/", "-")
    team_b = match_info["team_away"].replace(" ", "_").replace("/", "-")
    match_date = match_info["date"][:10]  # YYYY-MM-DD
    round_name = match_info["round"].replace(" ", "_").replace("-", "_")

    filename = f"{match_date}_{round_name}_{team_a}_vs_{team_b}.md"
    filepath = os.path.join(output_dir, filename)

    # Ajouter des métadonnées en haut du fichier
    header = f"""---
Match: {match_info["team_home"]} vs {match_info["team_away"]}
Date: {match_info["date"]}
Round: {match_info["round"]}
Venue: {match_info["venue"]}
Status: {match_info["status"]}
Fixture ID: {match_info["fixture_id"]}
Generated: {datetime.now().isoformat()}
---

"""

    full_content = header + analysis_data["summary"]

    # Sauvegarder
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_content)

    print(f"  [OK] Sauvegarde: {filename}")
    return filepath


def main():
    """Fonction principale."""
    print("\n" + "="*100)
    print("ANALYSE AUTOMATIQUE DES MATCHS DE LA CAN 2025")
    print("="*100)

    # Créer le dossier de sortie
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(exist_ok=True)
    print(f"\nDossier de sortie: {output_dir.absolute()}")

    # Récupérer les matchs
    matches = get_upcoming_can_matches()

    if not matches:
        print("\n[ERROR] Aucun match a venir trouve")
        return

    print("\n" + "="*100)
    print(f"MATCHS À ANALYSER: {len(matches)}")
    print("="*100)

    for i, match in enumerate(matches, 1):
        print(f"\n[{i}/{len(matches)}] {match['round']}")
        print(f"  Date: {match['date']}")
        print(f"  Match: {match['team_home']} vs {match['team_away']}")
        print(f"  Venue: {match['venue']}")
        print(f"  Status: {match['status']}")

    # Information sur le traitement
    print("\n" + "="*100)
    print(f"LANCEMENT DE {len(matches)} ANALYSES")
    print(f"Temps estime: {len(matches) * 15 / 60:.1f} minutes")
    print("="*100)

    # Lancer les analyses
    print("\n" + "="*100)
    print("LANCEMENT DES ANALYSES")
    print("="*100)

    results = []
    successful = 0
    failed = 0

    for i, match in enumerate(matches, 1):
        print(f"\n[{i}/{len(matches)}] Analyse: {match['team_home']} vs {match['team_away']}")

        # Lancer l'analyse
        start_time = time.time()
        analysis_data = analyze_match(
            match["team_home"],
            match["team_away"],
            match["team_home_id"],
            match["team_away_id"]
        )
        elapsed = time.time() - start_time

        if analysis_data:
            # Sauvegarder le résumé
            filepath = save_summary(match, analysis_data, output_dir)
            if filepath:
                successful += 1
                results.append({
                    "match": f"{match['team_home']} vs {match['team_away']}",
                    "status": "success",
                    "file": filepath,
                    "time": elapsed
                })
            else:
                failed += 1
                results.append({
                    "match": f"{match['team_home']} vs {match['team_away']}",
                    "status": "no_summary",
                    "time": elapsed
                })
        else:
            failed += 1
            results.append({
                "match": f"{match['team_home']} vs {match['team_away']}",
                "status": "failed",
                "time": elapsed
            })

        print(f"  Temps: {elapsed:.1f}s")

        # Pause entre les analyses pour éviter de surcharger
        if i < len(matches):
            print("  Pause de 2s...")
            time.sleep(2)

    # Résumé final
    print("\n" + "="*100)
    print("RESUME FINAL")
    print("="*100)
    print(f"\nTotal matchs: {len(matches)}")
    print(f"[OK] Succes: {successful}")
    print(f"[ERROR] Echecs: {failed}")
    print(f"\nFichiers generes dans: {output_dir.absolute()}")

    # Créer un index
    index_file = output_dir / "INDEX.md"
    with open(index_file, "w", encoding="utf-8") as f:
        f.write("# Analyses CAN 2025\n\n")
        f.write(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Total matchs analysés: {successful}/{len(matches)}\n\n")
        f.write("## Matchs analysés\n\n")

        for result in results:
            if result["status"] == "success":
                filename = os.path.basename(result["file"])
                f.write(f"- [{result['match']}](./{filename}) ✅\n")
            else:
                f.write(f"- {result['match']} ❌ ({result['status']})\n")

    print(f"\nIndex cree: {index_file}")
    print("\n" + "="*100)
    print("TERMINE !")
    print("="*100)


if __name__ == "__main__":
    main()
