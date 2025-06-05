"""
Internationalization (i18n) utilities for WordBattle backend.

This module provides translation functions for all user-facing text
based on the user's language preference.
"""

from typing import Dict, Any, Optional
from enum import Enum

class SupportedLanguage(Enum):
    """Supported languages for the application."""
    ENGLISH = "en"
    GERMAN = "de"
    SPANISH = "es"
    FRENCH = "fr"
    ITALIAN = "it"

# Translation dictionaries for all supported languages
TRANSLATIONS = {
    # Error Messages
    "error.game_not_found": {
        "en": "Game not found",
        "de": "Spiel nicht gefunden",
        "es": "Juego no encontrado",
        "fr": "Jeu non trouvé",
        "it": "Gioco non trovato"
    },
    "error.player_not_found": {
        "en": "Player not found",
        "de": "Spieler nicht gefunden",
        "es": "Jugador no encontrado",
        "fr": "Joueur non trouvé",
        "it": "Giocatore non trovato"
    },
    "error.not_your_turn": {
        "en": "Not your turn",
        "de": "Sie sind nicht an der Reihe",
        "es": "No es tu turno",
        "fr": "Ce n'est pas votre tour",
        "it": "Non è il tuo turno"
    },
    "error.game_not_in_progress": {
        "en": "Game is not in progress",
        "de": "Spiel läuft nicht",
        "es": "El juego no está en progreso",
        "fr": "Le jeu n'est pas en cours",
        "it": "Il gioco non è in corso"
    },
    "error.game_full": {
        "en": "Game is full",
        "de": "Spiel ist voll",
        "es": "El juego está lleno",
        "fr": "Le jeu est complet",
        "it": "Il gioco è pieno"
    },
    "error.not_authorized": {
        "en": "Not authorized",
        "de": "Nicht autorisiert",
        "es": "No autorizado",
        "fr": "Non autorisé",
        "it": "Non autorizzato"
    },
    "error.invalid_language": {
        "en": "Invalid language. Supported languages: {languages}",
        "de": "Ungültige Sprache. Unterstützte Sprachen: {languages}",
        "es": "Idioma inválido. Idiomas soportados: {languages}",
        "fr": "Langue invalide. Langues supportées: {languages}",
        "it": "Lingua non valida. Lingue supportate: {languages}"
    },
    "error.max_players_invalid": {
        "en": "Max players must be between 2 and 4",
        "de": "Maximale Spielerzahl muss zwischen 2 und 4 liegen",
        "es": "El máximo de jugadores debe estar entre 2 y 4",
        "fr": "Le nombre maximum de joueurs doit être entre 2 et 4",
        "it": "Il numero massimo di giocatori deve essere tra 2 e 4"
    },
    "error.wordlist_not_available": {
        "en": "Wordlist for language '{language}' not available",
        "de": "Wörterliste für Sprache '{language}' nicht verfügbar",
        "es": "Lista de palabras para idioma '{language}' no disponible",
        "fr": "Liste de mots pour la langue '{language}' non disponible",
        "it": "Elenco parole per lingua '{language}' non disponibile"
    },
    "error.username_taken": {
        "en": "Username already taken",
        "de": "Benutzername bereits vergeben",
        "es": "Nombre de usuario ya en uso",
        "fr": "Nom d'utilisateur déjà pris",
        "it": "Nome utente già in uso"
    },
    "error.email_registered": {
        "en": "Email already registered",
        "de": "E-Mail bereits registriert",
        "es": "Email ya registrado",
        "fr": "Email déjà enregistré",
        "it": "Email già registrata"
    },
    "error.not_part_of_game": {
        "en": "You are not part of this game",
        "de": "Sie sind nicht Teil dieses Spiels",
        "es": "No eres parte de este juego",
        "fr": "Vous ne faites pas partie de ce jeu",
        "it": "Non fai parte di questo gioco"
    },
    "error.move_validation_failed": {
        "en": "Move validation failed: {message}",
        "de": "Zug-Validierung fehlgeschlagen: {message}",
        "es": "Validación de movimiento falló: {message}",
        "fr": "Validation du mouvement échouée: {message}",
        "it": "Validazione mossa fallita: {message}"
    },
    "error.invalid_verification_code": {
        "en": "Invalid verification code",
        "de": "Ungültiger Bestätigungscode",
        "es": "Código de verificación inválido",
        "fr": "Code de vérification invalide",
        "it": "Codice di verifica non valido"
    },
    "error.expired_verification_code": {
        "en": "Invalid or expired verification code",
        "de": "Ungültiger oder abgelaufener Bestätigungscode",
        "es": "Código de verificación inválido o expirado",
        "fr": "Code de vérification invalide ou expiré",
        "it": "Codice di verifica non valido o scaduto"
    },

    # Success Messages
    "success.language_updated": {
        "en": "Language updated successfully",
        "de": "Sprache erfolgreich aktualisiert",
        "es": "Idioma actualizado exitosamente",
        "fr": "Langue mise à jour avec succès",
        "it": "Lingua aggiornata con successo"
    },
    "success.game_created": {
        "en": "Game created successfully",
        "de": "Spiel erfolgreich erstellt",
        "es": "Juego creado exitosamente",
        "fr": "Jeu créé avec succès",
        "it": "Gioco creato con successo"
    },
    "success.game_joined": {
        "en": "Successfully joined game",
        "de": "Erfolgreich dem Spiel beigetreten",
        "es": "Se unió exitosamente al juego",
        "fr": "Rejoint le jeu avec succès",
        "it": "Iscritto al gioco con successo"
    },

    # Game Move Descriptions
    "move.played_words": {
        "en": "Played word(s): {words}",
        "de": "Gespielte Wörter: {words}",
        "es": "Palabras jugadas: {words}",
        "fr": "Mots joués: {words}",
        "it": "Parole giocate: {words}"
    },
    "move.placed_tiles": {
        "en": "Placed tiles",
        "de": "Steine platziert",
        "es": "Fichas colocadas",
        "fr": "Tuiles placées",
        "it": "Tessere piazzate"
    },
    "move.passed_turn": {
        "en": "Passed turn",
        "de": "Zug gepasst",
        "es": "Turno pasado",
        "fr": "Tour passé",
        "it": "Turno saltato"
    },
    "move.exchanged_letters": {
        "en": "Exchanged {count} letter(s)",
        "de": "{count} Buchstaben getauscht",
        "es": "Intercambió {count} letra(s)",
        "fr": "Échangé {count} lettre(s)",
        "it": "Scambiato {count} lettera/e"
    },
    "move.made_move": {
        "en": "Made a {move_type} move",
        "de": "{move_type}-Zug gemacht",
        "es": "Hizo un movimiento {move_type}",
        "fr": "A fait un mouvement {move_type}",
        "it": "Ha fatto una mossa {move_type}"
    },

    # Game Status Messages
    "status.waiting_for_players": {
        "en": "Waiting for players",
        "de": "Warten auf Spieler",
        "es": "Esperando jugadores",
        "fr": "En attente de joueurs",
        "it": "In attesa di giocatori"
    },
    "status.game_in_progress": {
        "en": "Game in progress",
        "de": "Spiel läuft",
        "es": "Juego en progreso",
        "fr": "Jeu en cours",
        "it": "Gioco in corso"
    },
    "status.game_completed": {
        "en": "Game completed",
        "de": "Spiel beendet",
        "es": "Juego completado",
        "fr": "Jeu terminé",
        "it": "Gioco completato"
    },

    # Test Mode Messages
    "test.test_move_success": {
        "en": "TEST MOVE SUCCESS: {message}",
        "de": "TEST-ZUG ERFOLGREICH: {message}",
        "es": "MOVIMIENTO DE PRUEBA EXITOSO: {message}",
        "fr": "MOUVEMENT TEST RÉUSSI: {message}",
        "it": "MOSSA TEST RIUSCITA: {message}"
    },
    "test.endgame_mode": {
        "en": "Creating game in test mode with {tile_count}-tile letter bag for endgame testing",
        "de": "Erstelle Spiel im Testmodus mit {tile_count}-Stein Buchstabenbeutel für Endspiel-Tests",
        "es": "Creando juego en modo prueba con bolsa de {tile_count} fichas para pruebas de final de juego",
        "fr": "Création d'un jeu en mode test avec sac de {tile_count} tuiles pour tester la fin de partie",
        "it": "Creazione gioco in modalità test con sacchetto da {tile_count} tessere per test fine partita"
    }
}

def get_translation(key: str, language: str = "en", **kwargs) -> str:
    """
    Get a translated string for the given key and language.
    
    Args:
        key: The translation key (e.g., 'error.game_not_found')
        language: The target language code (e.g., 'en', 'de', 'es', 'fr', 'it')
        **kwargs: Variables to format into the translation string
        
    Returns:
        The translated string with any formatting applied
        
    Example:
        get_translation('error.invalid_language', 'de', languages='en, de, es')
        # Returns: "Ungültige Sprache. Unterstützte Sprachen: en, de, es"
    """
    # Default to English if language not supported
    if language not in ["en", "de", "es", "fr", "it"]:
        language = "en"
    
    # Get the translation dictionary for this key
    translations = TRANSLATIONS.get(key, {})
    
    # Get the translation for the specified language, fallback to English
    translation = translations.get(language, translations.get("en", key))
    
    # Format the string with any provided variables
    try:
        return translation.format(**kwargs)
    except (KeyError, ValueError):
        # If formatting fails, return the unformatted string
        return translation

def get_supported_languages() -> Dict[str, str]:
    """
    Get a dictionary of supported language codes and their native names.
    
    Returns:
        Dictionary mapping language codes to native language names
    """
    return {
        "en": "English",
        "de": "Deutsch",
        "es": "Español", 
        "fr": "Français",
        "it": "Italiano"
    }

def validate_language(language: str) -> bool:
    """
    Check if a language code is supported.
    
    Args:
        language: The language code to validate
        
    Returns:
        True if the language is supported, False otherwise
    """
    return language in ["en", "de", "es", "fr", "it"]

class TranslationHelper:
    """
    Helper class for managing translations in the context of a specific user language.
    """
    
    def __init__(self, language: str = "en"):
        """
        Initialize the translation helper with a specific language.
        
        Args:
            language: The language code for this helper instance
        """
        self.language = language if validate_language(language) else "en"
    
    def t(self, key: str, **kwargs) -> str:
        """
        Translate a key using the helper's language.
        
        Args:
            key: The translation key
            **kwargs: Variables to format into the translation
            
        Returns:
            The translated string
        """
        return get_translation(key, self.language, **kwargs)
    
    def error(self, key: str, **kwargs) -> str:
        """
        Get an error message translation.
        
        Args:
            key: The error key (without 'error.' prefix)
            **kwargs: Variables to format into the translation
            
        Returns:
            The translated error message
        """
        return self.t(f"error.{key}", **kwargs)
    
    def success(self, key: str, **kwargs) -> str:
        """
        Get a success message translation.
        
        Args:
            key: The success key (without 'success.' prefix)
            **kwargs: Variables to format into the translation
            
        Returns:
            The translated success message
        """
        return self.t(f"success.{key}", **kwargs)
    
    def move_description(self, key: str, **kwargs) -> str:
        """
        Get a move description translation.
        
        Args:
            key: The move key (without 'move.' prefix)
            **kwargs: Variables to format into the translation
            
        Returns:
            The translated move description
        """
        return self.t(f"move.{key}", **kwargs) 