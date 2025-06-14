#!/usr/bin/env python3

"""
Local test script to verify endgame test mode functionality.
"""

from app.game_logic.letter_bag import create_letter_bag, LetterBag, TEST_LETTER_DISTRIBUTION
from app.game_logic.game_state import GameState

def test_normal_vs_test_mode():
    """Compare normal mode vs test mode letter bags."""
    print("🧪 TESTING ENDGAME MODE FUNCTIONALITY")
    print("="*50)
    
    # Test normal mode
    print("\n📦 NORMAL MODE:")
    normal_bag = create_letter_bag("en", test_mode=False)
    print(f"Total tiles: {len(normal_bag)}")
    print(f"Sample letters: {sorted(normal_bag[:10])}")
    
    # Test endgame mode
    print("\n🧪 TEST MODE:")
    test_bag = create_letter_bag("en", test_mode=True)
    print(f"Total tiles: {len(test_bag)}")
    print(f"All letters: {sorted(test_bag)}")
    
    # Count distribution in test mode
    from collections import Counter
    distribution = Counter(test_bag)
    print(f"Distribution: {dict(distribution)}")
    
    # Verify it matches expected distribution
    expected = TEST_LETTER_DISTRIBUTION["en"]
    print(f"Expected:    {expected}")
    print(f"Match: {'✅' if distribution == expected else '❌'}")
    
    return distribution == expected

def test_game_state_creation():
    """Test GameState creation with test mode."""
    print("\n🎮 TESTING GAMESTATE WITH TEST MODE:")
    print("="*40)
    
    # Normal game state
    normal_game = GameState("en", test_mode=False)
    print(f"Normal game bag: {len(normal_game.letter_bag)} tiles")
    
    # Test mode game state  
    test_game = GameState("en", test_mode=True)
    print(f"Test game bag: {len(test_game.letter_bag)} tiles")
    
    return len(test_game.letter_bag) == 24

def test_letter_bag_class():
    """Test LetterBag class with test mode."""
    print("\n💼 TESTING LETTERBAG CLASS:")
    print("="*30)
    
    # Normal letter bag
    normal_bag = LetterBag("en", test_mode=False)
    print(f"Normal LetterBag: {normal_bag.remaining_count()} tiles")
    
    # Test mode letter bag
    test_bag = LetterBag("en", test_mode=True)
    print(f"Test LetterBag: {test_bag.remaining_count()} tiles")
    
    # Draw some letters
    drawn = test_bag.draw(7)
    print(f"Drew 7 letters: {drawn}")
    print(f"Remaining: {test_bag.remaining_count()} tiles")
    
    return test_bag.remaining_count() == 17  # 24 - 7 = 17

def main():
    """Run all tests."""
    print("🧪 ENDGAME TEST MODE VERIFICATION")
    print("="*60)
    
    results = []
    
    # Test letter bag creation
    results.append(test_normal_vs_test_mode())
    
    # Test GameState creation
    results.append(test_game_state_creation())
    
    # Test LetterBag class
    results.append(test_letter_bag_class())
    
    # Summary
    print(f"\n📊 TEST SUMMARY:")
    print(f"="*20)
    print(f"Distribution test: {'✅ PASS' if results[0] else '❌ FAIL'}")
    print(f"GameState test:    {'✅ PASS' if results[1] else '❌ FAIL'}")
    print(f"LetterBag test:    {'✅ PASS' if results[2] else '❌ FAIL'}")
    
    all_passed = all(results)
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print(f"\n🎯 READY FOR ENDGAME TESTING!")
        print(f"Use: TEST_MODE_ENDGAME=true to enable in production")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 