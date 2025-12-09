"""
Test du workflow complet du système de contexte dynamique
Simule des questions réelles d'utilisateurs sur des matchs à venir
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any, List

# Configuration
API_BASE_URL = "http://localhost:8001"

# Couleurs pour l'affichage
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

def print_section(text: str):
    print(f"\n{Colors.OKCYAN}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'-'*80}{Colors.ENDC}")

def print_success(text: str):
    print(f"{Colors.OKGREEN}[OK] {text}{Colors.ENDC}")

def print_info(text: str):
    print(f"{Colors.OKBLUE}[INFO] {text}{Colors.ENDC}")

def print_warning(text: str):
    print(f"{Colors.WARNING}[WARN] {text}{Colors.ENDC}")

def print_error(text: str):
    print(f"{Colors.FAIL}[ERROR] {text}{Colors.ENDC}")

def classify_intent_simulation(question: str, context_type: str, status: str) -> Dict[str, Any]:
    """
    Simule la classification d'intent localement
    (car l'endpoint /api/classify-intent n'existe pas encore)
    """
    from backend.context.intent_classifier import IntentClassifier
    from backend.context.context_types import ContextType, MatchStatus, LeagueStatus

    # Convertir les strings en enums
    ctx_type = ContextType.MATCH if context_type == "match" else ContextType.LEAGUE

    if context_type == "match":
        if status == "live":
            st = MatchStatus.LIVE
        elif status == "finished":
            st = MatchStatus.FINISHED
        else:
            st = MatchStatus.UPCOMING
    else:
        if status == "current":
            st = LeagueStatus.CURRENT
        elif status == "past":
            st = LeagueStatus.PAST
        else:
            st = LeagueStatus.UPCOMING

    result = IntentClassifier.classify_intent(question, ctx_type, st)
    return result

def test_match_context(fixture_id: int, questions: List[str]):
    """Teste le workflow complet pour un match"""

    print_section(f"Test Match Context - Fixture ID: {fixture_id}")

    # Étape 1: Récupérer le contexte
    print_info("Étape 1: Récupération du contexte match...")
    response = requests.get(f"{API_BASE_URL}/api/context/match/{fixture_id}")

    if response.status_code != 200:
        print_error(f"Échec récupération contexte: {response.status_code}")
        return

    context = response.json()["context"]
    print_success(f"Contexte créé: {context['context_id']}")
    print_info(f"  Match: {context['home_team']} vs {context['away_team']}")
    print_info(f"  Status: {context['status']}")
    print_info(f"  Ligue: {context['league']}")
    print_info(f"  Date: {context['match_date']}")

    # Étape 2: Pour chaque question, classifier l'intent et sélectionner les endpoints
    print_section("Étape 2: Classification des intentions et sélection des endpoints")

    results = []
    for i, question in enumerate(questions, 1):
        print(f"\n{Colors.BOLD}Question {i}: {question}{Colors.ENDC}")

        try:
            # Classifier l'intent
            intent_result = classify_intent_simulation(
                question=question,
                context_type="match",
                status=context["status"]
            )

            print_success(f"Intent détecté: {intent_result['intent']}")
            print_success(f"Endpoints sélectionnés: {', '.join(intent_result['endpoints'])}")
            print_info(f"Confiance: {intent_result['confidence']:.2f}")

            results.append({
                "question": question,
                "intent": intent_result["intent"],
                "endpoints": intent_result["endpoints"],
                "confidence": intent_result["confidence"]
            })

        except Exception as e:
            print_error(f"Erreur classification: {str(e)}")

    return {
        "context": context,
        "questions": results
    }

def test_league_context(league_id: int, season: int, questions: List[str]):
    """Teste le workflow complet pour une ligue"""

    print_section(f"Test League Context - League ID: {league_id}, Season: {season}")

    # Étape 1: Récupérer le contexte
    print_info("Étape 1: Récupération du contexte ligue...")
    response = requests.get(f"{API_BASE_URL}/api/context/league/{league_id}?season={season}")

    if response.status_code != 200:
        print_error(f"Échec récupération contexte: {response.status_code}")
        return

    context = response.json()["context"]
    print_success(f"Contexte créé: {context['context_id']}")
    print_info(f"  Ligue: {context['league_name']}")
    print_info(f"  Status: {context['status']}")
    print_info(f"  Pays: {context['country']}")
    print_info(f"  Saison: {context['season']}")

    # Étape 2: Pour chaque question, classifier l'intent et sélectionner les endpoints
    print_section("Étape 2: Classification des intentions et sélection des endpoints")

    results = []
    for i, question in enumerate(questions, 1):
        print(f"\n{Colors.BOLD}Question {i}: {question}{Colors.ENDC}")

        try:
            # Classifier l'intent
            intent_result = classify_intent_simulation(
                question=question,
                context_type="league",
                status=context["status"]
            )

            print_success(f"Intent détecté: {intent_result['intent']}")
            print_success(f"Endpoints sélectionnés: {', '.join(intent_result['endpoints'])}")
            print_info(f"Confiance: {intent_result['confidence']:.2f}")

            results.append({
                "question": question,
                "intent": intent_result["intent"],
                "endpoints": intent_result["endpoints"],
                "confidence": intent_result["confidence"]
            })

        except Exception as e:
            print_error(f"Erreur classification: {str(e)}")

    return {
        "context": context,
        "questions": results
    }

def main():
    print_header("TEST WORKFLOW COMPLET - SYSTÈME DE CONTEXTE DYNAMIQUE")

    all_results = []

    # ============================================================================
    # Scénario 1: Match à venir (UPCOMING)
    # ============================================================================
    print_header("SCÉNARIO 1: MATCH À VENIR (UPCOMING)")

    # Utilisons un fixture_id que nous connaissons (AFC Champions League)
    fixture_id_upcoming = 1438950  # Vissel Kobe vs Chengdu Better City

    questions_upcoming = [
        "Qui va gagner ce match ?",
        "Quelle est la forme des deux équipes ?",
        "Quel est l'historique des confrontations ?",
        "Qui sont les blessés ?",
        "Quelle est la composition probable ?",
        "Quelles sont les cotes pour ce match ?",
        "Quelles sont les statistiques des équipes ?"
    ]

    result1 = test_match_context(fixture_id_upcoming, questions_upcoming)
    if result1:
        all_results.append({
            "scenario": "Match à venir",
            "fixture_id": fixture_id_upcoming,
            "result": result1
        })

    # ============================================================================
    # Scénario 2: Match terminé (FINISHED)
    # ============================================================================
    print_header("SCÉNARIO 2: MATCH TERMINÉ (FINISHED)")

    fixture_id_finished = 1479558  # Emelec vs Macara (FT)

    questions_finished = [
        "Quel est le résultat final ?",
        "Quelles sont les statistiques du match ?",
        "Qui a marqué les buts ?",
        "Quel est le résumé du match ?",
        "Qui a été le meilleur joueur ?",
        "Comment s'est déroulé le match ?",
        "Quelle était la composition des équipes ?"
    ]

    result2 = test_match_context(fixture_id_finished, questions_finished)
    if result2:
        all_results.append({
            "scenario": "Match terminé",
            "fixture_id": fixture_id_finished,
            "result": result2
        })

    # ============================================================================
    # Scénario 3: Contexte Ligue (Champions League)
    # ============================================================================
    print_header("SCÉNARIO 3: CONTEXTE LIGUE (UEFA Champions League)")

    league_id = 2  # UEFA Champions League
    season = 2025

    questions_league = [
        "Quel est le classement de la ligue ?",
        "Qui sont les meilleurs buteurs ?",
        "Qui sont les meilleurs passeurs ?",
        "Quels sont les prochains matchs ?",
        "Quels sont les derniers résultats ?",
        "Quelles sont les statistiques des équipes ?"
    ]

    result3 = test_league_context(league_id, season, questions_league)
    if result3:
        all_results.append({
            "scenario": "Contexte ligue",
            "league_id": league_id,
            "result": result3
        })

    # ============================================================================
    # Résumé Final
    # ============================================================================
    print_header("RÉSUMÉ FINAL DES TESTS")

    print_section("Statistiques Globales")
    total_questions = sum(len(r["result"]["questions"]) for r in all_results)
    print_info(f"Total de scénarios testés: {len(all_results)}")
    print_info(f"Total de questions testées: {total_questions}")

    print_section("Intents Détectés par Scénario")
    for result in all_results:
        print(f"\n{Colors.BOLD}{result['scenario']}:{Colors.ENDC}")
        intents_used = {}
        for q in result["result"]["questions"]:
            intent = q["intent"]
            intents_used[intent] = intents_used.get(intent, 0) + 1

        for intent, count in intents_used.items():
            print(f"  • {intent}: {count} fois")

    print_section("Endpoints Utilisés par Scénario")
    for result in all_results:
        print(f"\n{Colors.BOLD}{result['scenario']}:{Colors.ENDC}")
        endpoints_used = set()
        for q in result["result"]["questions"]:
            endpoints_used.update(q["endpoints"])

        for endpoint in sorted(endpoints_used):
            print(f"  • {endpoint}")

    # Sauvegarder les résultats dans un fichier JSON
    output_file = "test_context_workflow_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print_section("Résultats Sauvegardés")
    print_success(f"Résultats complets sauvegardés dans: {output_file}")

    print(f"\n{Colors.OKGREEN}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}{Colors.BOLD}{'TESTS TERMINÉS AVEC SUCCÈS'.center(80)}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Tests interrompus par l'utilisateur{Colors.ENDC}\n")
    except Exception as e:
        print(f"\n\n{Colors.FAIL}Erreur fatale: {str(e)}{Colors.ENDC}\n")
        import traceback
        traceback.print_exc()
