from app.game_logic.letter_bag import LetterBag, create_rack, exchange_letters, LETTER_DISTRIBUTION

def test_letter_bag_initialization():
    """Test that the letter bag is initialized correctly."""
    bag = LetterBag()
    
    # Check that the bag has the correct number of letters
    total_letters = sum(LETTER_DISTRIBUTION.values())
    assert bag.remaining() == total_letters
    
    # Check that the distribution is correct
    distribution = bag.get_distribution()
    for letter, count in LETTER_DISTRIBUTION.items():
        assert distribution.get(letter, 0) == count

def test_letter_bag_draw():
    """Test drawing letters from the bag."""
    bag = LetterBag()
    initial_count = bag.remaining()
    
    # Draw some letters
    drawn = bag.draw(7)
    
    # Check that the correct number of letters was drawn
    assert len(drawn) == 7
    assert bag.remaining() == initial_count - 7
    
    # Draw more than remaining
    bag = LetterBag()
    total = bag.remaining()
    drawn = bag.draw(total + 10)
    assert len(drawn) == total
    assert bag.remaining() == 0

def test_letter_bag_return():
    """Test returning letters to the bag."""
    bag = LetterBag()
    initial_count = bag.remaining()
    
    # Draw some letters
    drawn = bag.draw(7)
    assert bag.remaining() == initial_count - 7
    
    # Return the letters
    bag.return_letters(drawn)
    assert bag.remaining() == initial_count

def test_create_rack():
    """Test creating a rack."""
    # Test with default distribution
    rack = create_rack()
    assert len(rack) == 7
    
    # Test with letter bag
    bag = LetterBag()
    initial_count = bag.remaining()
    rack = create_rack(bag)
    assert len(rack) == 7
    assert bag.remaining() == initial_count - 7

def test_exchange_letters():
    """Test exchanging letters."""
    # Test with default distribution
    rack = "ABCDEFG"
    new_rack, new_letters = exchange_letters(rack, "ABC")
    assert len(new_rack) == 7
    assert "D" in new_rack
    assert "E" in new_rack
    assert "F" in new_rack
    assert "G" in new_rack
    assert len(new_letters) == 3
    
    # Test with letter bag
    bag = LetterBag()
    initial_count = bag.remaining()
    rack = "ABCDEFG"
    new_rack, new_letters = exchange_letters(rack, "ABC", bag)
    assert len(new_rack) == 7
    assert "D" in new_rack
    assert "E" in new_rack
    assert "F" in new_rack
    assert "G" in new_rack
    assert len(new_letters) == 3
    assert bag.remaining() == initial_count  # Should be the same since we returned and drew the same number