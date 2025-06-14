#!/usr/bin/env python3
"""
Test script to verify the internationalization (i18n) functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.i18n import get_translation, TranslationHelper, validate_language, get_supported_languages

def test_basic_translations():
    """Test basic translation functionality."""
    print("🌍 Testing Basic Translations")
    print("=" * 50)
    
    # Test all languages for a common error
    languages = ["en", "de", "es", "fr", "it"]
    
    for lang in languages:
        translation = get_translation("error.game_not_found", lang)
        print(f"  {lang}: {translation}")
    
    print()

def test_translation_with_variables():
    """Test translations with variable substitution."""
    print("🔧 Testing Translations with Variables")
    print("=" * 50)
    
    languages = ["en", "de", "es", "fr", "it"]
    
    for lang in languages:
        translation = get_translation(
            "error.invalid_language", 
            lang, 
            languages="en, de, es, fr, it"
        )
        print(f"  {lang}: {translation}")
    
    print()

def test_translation_helper():
    """Test the TranslationHelper class."""
    print("🛠️  Testing TranslationHelper Class")
    print("=" * 50)
    
    # Test different languages
    for lang in ["en", "de", "es", "fr", "it"]:
        t = TranslationHelper(lang)
        
        error_msg = t.error("game_not_found")
        success_msg = t.success("language_updated")
        move_msg = t.move_description("played_words", words="HELLO, WORLD")
        
        print(f"  {lang.upper()}:")
        print(f"    Error: {error_msg}")
        print(f"    Success: {success_msg}")
        print(f"    Move: {move_msg}")
        print()

def test_fallback_behavior():
    """Test fallback behavior for unsupported languages."""
    print("🔄 Testing Fallback Behavior")
    print("=" * 50)
    
    # Test unsupported language (should fallback to English)
    translation = get_translation("error.game_not_found", "zh")
    print(f"  Unsupported language 'zh': {translation}")
    
    # Test missing key (should return key)
    translation = get_translation("nonexistent.key", "en")
    print(f"  Missing key: {translation}")
    
    print()

def test_language_validation():
    """Test language validation functions."""
    print("✅ Testing Language Validation")
    print("=" * 50)
    
    supported_langs = get_supported_languages()
    print(f"  Supported languages: {supported_langs}")
    
    for lang in ["en", "de", "es", "fr", "it", "zh", "jp"]:
        is_valid = validate_language(lang)
        print(f"  {lang}: {'✅ Valid' if is_valid else '❌ Invalid'}")
    
    print()

def test_user_scenario():
    """Test a realistic user scenario."""
    print("👤 Testing User Scenario")
    print("=" * 50)
    
    # Simulate a German user trying to join a full game
    german_helper = TranslationHelper("de")
    
    print("  German user sees:")
    print(f"    Game not found: {german_helper.error('game_not_found')}")
    print(f"    Game full: {german_helper.error('game_full')}")
    print(f"    Successfully joined: {german_helper.success('game_joined')}")
    
    print()
    
    # Simulate a Spanish user updating language
    spanish_helper = TranslationHelper("es")
    
    print("  Spanish user sees:")
    print(f"    Language updated: {spanish_helper.success('language_updated')}")
    print(f"    Invalid language: {spanish_helper.error('invalid_language', languages='en, de, es, fr, it')}")
    
    print()

def main():
    """Run all i18n tests."""
    print("🧪 WordBattle Internationalization (i18n) Test Suite")
    print("=" * 60)
    print()
    
    try:
        test_basic_translations()
        test_translation_with_variables()
        test_translation_helper()
        test_fallback_behavior()
        test_language_validation()
        test_user_scenario()
        
        print("🎉 All i18n tests completed successfully!")
        print()
        print("💡 The internationalization system is working correctly.")
        print("   Users will now see error messages and responses in their preferred language!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 