"""
Internationalization (i18n) utilities for multilingual support.
"""
from typing import Literal

Language = Literal["fr", "en"]

# Error messages in multiple languages
ERROR_MESSAGES = {
    "fr": {
        "not_authenticated": "Non authentifié",
        "invalid_credentials": "Identifiants invalides",
        "user_not_found": "Utilisateur non trouvé",
        "user_already_exists": "Un utilisateur avec cet email existe déjà",
        "invalid_token": "Token invalide ou expiré",
        "match_not_found": "Match non trouvé",
        "team_not_found": "Équipe non trouvée",
        "player_not_found": "Joueur non trouvé",
        "league_not_found": "Ligue non trouvée",
        "invalid_language": "Langue invalide. Utilisez 'fr' ou 'en'",
        "server_error": "Erreur serveur interne",
        "validation_error": "Erreur de validation des données",
        "api_error": "Erreur lors de l'appel à l'API externe",
        "permission_denied": "Permission refusée",
        "resource_not_found": "Ressource non trouvée",
        "bad_request": "Requête invalide",
    },
    "en": {
        "not_authenticated": "Not authenticated",
        "invalid_credentials": "Invalid credentials",
        "user_not_found": "User not found",
        "user_already_exists": "A user with this email already exists",
        "invalid_token": "Invalid or expired token",
        "match_not_found": "Match not found",
        "team_not_found": "Team not found",
        "player_not_found": "Player not found",
        "league_not_found": "League not found",
        "invalid_language": "Invalid language. Use 'fr' or 'en'",
        "server_error": "Internal server error",
        "validation_error": "Data validation error",
        "api_error": "Error calling external API",
        "permission_denied": "Permission denied",
        "resource_not_found": "Resource not found",
        "bad_request": "Bad request",
    }
}

# Success messages
SUCCESS_MESSAGES = {
    "fr": {
        "login_success": "Connexion réussie",
        "logout_success": "Déconnexion réussie",
        "registration_success": "Inscription réussie",
        "update_success": "Mise à jour réussie",
        "language_updated": "Langue mise à jour avec succès",
        "password_reset_sent": "Email de réinitialisation envoyé",
        "password_reset_success": "Mot de passe réinitialisé avec succès",
    },
    "en": {
        "login_success": "Login successful",
        "logout_success": "Logout successful",
        "registration_success": "Registration successful",
        "update_success": "Update successful",
        "language_updated": "Language updated successfully",
        "password_reset_sent": "Password reset email sent",
        "password_reset_success": "Password reset successful",
    }
}


def get_error_message(error_key: str, language: Language = "fr") -> str:
    """
    Get error message in the specified language.

    Args:
        error_key: The error message key
        language: Language code ('fr' or 'en')

    Returns:
        Translated error message
    """
    messages = ERROR_MESSAGES.get(language, ERROR_MESSAGES["fr"])
    return messages.get(error_key, messages["server_error"])


def get_success_message(message_key: str, language: Language = "fr") -> str:
    """
    Get success message in the specified language.

    Args:
        message_key: The success message key
        language: Language code ('fr' or 'en')

    Returns:
        Translated success message
    """
    messages = SUCCESS_MESSAGES.get(language, SUCCESS_MESSAGES["fr"])
    return messages.get(message_key, message_key)


def validate_language(language: str) -> Language:
    """
    Validate and normalize language code.

    Args:
        language: Language code to validate

    Returns:
        Validated language code

    Raises:
        ValueError: If language is invalid
    """
    language = language.lower().strip()
    if language not in ["fr", "en"]:
        raise ValueError(f"Invalid language: {language}. Must be 'fr' or 'en'")
    return language  # type: ignore
