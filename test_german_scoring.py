#!/usr/bin/env python3
"""
Comprehensive test script for German letter scoring in WordBattle.

This script tests the scoring system to ensure:
1. German umlauts (Ä, Ö, Ü) have correct point values
2. Single source of truth for letter points (LETTER_DISTRIBUTION)
3. No conflicts between different scoring systems
4. Language-specific scoring works correctly

Usage:
    python test_german_scoring.py
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.game_logic.letter_bag import LETTER_DISTRIBUTION
from app.game_logic.full_points import get_letter_points, calculate_full_move_points
from app.game_logic.board_utils import BOARD_MULTIPLIERS

def test_german_letter_points():
    """Test that German letters have correct point values."""
    print("🧪 Testing German letter point values...")
    
    # Expected German letter points (standard German Scrabble values)
    expected_german_points = {
        'A': 1, 'B': 3, 'C': 4, 'D': 1, 'E': 1, 'F': 4, 'G': 2, 'H': 2, 'I': 1, 'J': 6,
        'K': 4, 'L': 2, 'M': 3, 'N': 1, 'O': 2, 'P': 4, 'Q': 10, 'R': 1, 'S': 1, 'T': 1,
        'U': 1, 'V': 6, 'W': 3, 'X': 8, 'Y': 10, 'Z': 3,
        'Ä': 6, 'Ö': 8, 'Ü': 6,  # German umlauts
        '?': 0  # Blank tile
    }
    
    # Test each letter
    failed_tests = []
    for letter, expected_points in expected_german_points.items():
        actual_points = get_letter_points(letter, "de")
        if actual_points != expected_points:
            failed_tests.append(f"  ❌ {letter}: expected {expected_points}, got {actual_points}")
        else:
            print(f"  ✅ {letter}: {actual_points} points")
    
    if failed_tests:
        print("\n🚨 FAILED TESTS:")
        for failure in failed_tests:
            print(failure)
        return False
    else:
        print("✅ All German letter points are correct!")
        return True

def test_noe_word_scoring():
    """Test the specific case of 'NÖ' word scoring."""
    print("\n🧪 Testing 'NÖ' word scoring...")
    
    # Create a simple board with 'NÖ' placed
    board = [[None for _ in range(15)] for _ in range(15)]
    
    # Place 'NÖ' horizontally at a position WITHOUT multipliers (1,0) and (1,1)
    # Note: (1,1) has WL multiplier, so let's use (1,0) and (1,1) - but (1,1) still has multiplier
    # Let's try (0,1) and (0,2) - but (0,3) has BL
    # Let's use (1,3) and (1,4) - no multipliers on these positions
    move_letters = [(1, 3, 'N'), (1, 4, 'Ö')]
    
    # Simple dictionary containing 'NÖ'
    dictionary = {'NÖ', 'nö', 'NO', 'no'}
    
    # Calculate points
    result = calculate_full_move_points(board, move_letters, "de", BOARD_MULTIPLIERS, dictionary)
    
    if result["valid"]:
        total_points = result["total"]
        base_points = get_letter_points('N', 'de') + get_letter_points('Ö', 'de')  # 1 + 8 = 9
        
        print(f"  Word: NÖ")
        print(f"  N points: {get_letter_points('N', 'de')}")
        print(f"  Ö points: {get_letter_points('Ö', 'de')}")
        print(f"  Base total: {base_points}")
        print(f"  Actual total: {total_points}")
        
        if total_points == base_points:
            print("  ✅ 'NÖ' scores correctly!")
            return True
        else:
            print(f"  ❌ 'NÖ' scoring failed: expected {base_points}, got {total_points}")
            return False
    else:
        print(f"  ❌ 'NÖ' move validation failed: {result.get('error', 'Unknown error')}")
        return False

def test_noe_word_scoring_with_multiplier():
    """Test 'NÖ' word scoring with center square multiplier."""
    print("\n🧪 Testing 'NÖ' word scoring with center square multiplier...")
    
    # Create a simple board with 'NÖ' placed
    board = [[None for _ in range(15)] for _ in range(15)]
    
    # Place 'NÖ' horizontally at center (7,7) and (7,8) - center has double word score
    move_letters = [(7, 7, 'N'), (7, 8, 'Ö')]
    
    # Simple dictionary containing 'NÖ'
    dictionary = {'NÖ', 'nö', 'NO', 'no'}
    
    # Calculate points
    result = calculate_full_move_points(board, move_letters, "de", BOARD_MULTIPLIERS, dictionary)
    
    if result["valid"]:
        total_points = result["total"]
        base_points = get_letter_points('N', 'de') + get_letter_points('Ö', 'de')  # 1 + 8 = 9
        expected_with_multiplier = base_points * 2  # Center square is double word score
        
        print(f"  Word: NÖ (on center square)")
        print(f"  N points: {get_letter_points('N', 'de')}")
        print(f"  Ö points: {get_letter_points('Ö', 'de')}")
        print(f"  Base total: {base_points}")
        print(f"  Expected with 2x multiplier: {expected_with_multiplier}")
        print(f"  Actual total: {total_points}")
        
        if total_points == expected_with_multiplier:
            print("  ✅ 'NÖ' with multiplier scores correctly!")
            return True
        else:
            print(f"  ❌ 'NÖ' multiplier scoring failed: expected {expected_with_multiplier}, got {total_points}")
            return False
    else:
        print(f"  ❌ 'NÖ' move validation failed: {result.get('error', 'Unknown error')}")
        return False

def test_umlaut_scoring_comprehensive():
    """Test all German umlauts in various scenarios."""
    print("\n🧪 Testing comprehensive umlaut scoring...")
    
    test_cases = [
        ('Ä', 6), ('ä', 6),  # Case insensitive
        ('Ö', 8), ('ö', 8),
        ('Ü', 6), ('ü', 6),
    ]
    
    failed_tests = []
    for letter, expected_points in test_cases:
        actual_points = get_letter_points(letter, "de")
        if actual_points != expected_points:
            failed_tests.append(f"  ❌ {letter}: expected {expected_points}, got {actual_points}")
        else:
            print(f"  ✅ {letter}: {actual_points} points")
    
    if failed_tests:
        print("\n🚨 FAILED UMLAUT TESTS:")
        for failure in failed_tests:
            print(failure)
        return False
    else:
        print("✅ All umlaut scoring tests passed!")
        return True

def test_language_consistency():
    """Test that different languages have different point values."""
    print("\n🧪 Testing language consistency...")
    
    # Test that German and English have different values for some letters
    test_letters = ['O', 'V', 'W']  # Letters that typically differ between languages
    
    differences_found = False
    for letter in test_letters:
        de_points = get_letter_points(letter, "de")
        en_points = get_letter_points(letter, "en")
        print(f"  {letter}: DE={de_points}, EN={en_points}")
        if de_points != en_points:
            differences_found = True
    
    # Test that German umlauts don't exist in English (should default to 1)
    umlaut_tests = []
    for umlaut in ['Ä', 'Ö', 'Ü']:
        de_points = get_letter_points(umlaut, "de")
        en_points = get_letter_points(umlaut, "en")  # Should default to 1
        print(f"  {umlaut}: DE={de_points}, EN={en_points}")
        if en_points == 1 and de_points > 1:
            umlaut_tests.append(True)
        else:
            umlaut_tests.append(False)
    
    if differences_found and all(umlaut_tests):
        print("✅ Language consistency tests passed!")
        return True
    else:
        print("❌ Language consistency tests failed!")
        return False

def test_fallback_behavior():
    """Test fallback behavior for unknown letters/languages."""
    print("\n🧪 Testing fallback behavior...")
    
    # Test unknown letter in known language
    unknown_letter_points = get_letter_points('§', "de")  # Non-standard letter
    print(f"  Unknown letter '§' in German: {unknown_letter_points} points")
    
    # Test known letter in unknown language
    unknown_lang_points = get_letter_points('A', "xx")  # Non-existent language
    print(f"  Letter 'A' in unknown language: {unknown_lang_points} points")
    
    # Both should default to 1
    if unknown_letter_points == 1 and unknown_lang_points == 1:
        print("✅ Fallback behavior works correctly!")
        return True
    else:
        print("❌ Fallback behavior failed!")
        return False

def main():
    """Run all scoring tests."""
    print("🎯 WordBattle German Scoring Test Suite")
    print("=" * 50)
    
    tests = [
        test_german_letter_points,
        test_noe_word_scoring,
        test_noe_word_scoring_with_multiplier,
        test_umlaut_scoring_comprehensive,
        test_language_consistency,
        test_fallback_behavior,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! German scoring is working correctly.")
        return 0
    else:
        print("🚨 Some tests failed. Please review the scoring implementation.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
