from app.game_logic.letter_bag import create_letter_bag, create_rack, exchange_letters, draw_letters, return_letters, LetterBag

def test_letter_bag_initialization():
    """Test that letter bag is initialized with correct distribution."""
    bag = create_letter_bag()
    assert len(bag) > 0
    
    # Test German bag
    de_bag = create_letter_bag("de")
    assert len(de_bag) > 0
    
    # Test English bag
    en_bag = create_letter_bag("en")
    assert len(en_bag) > 0

def test_letter_bag_draw():
    """Test drawing letters from the bag."""
    bag = create_letter_bag()
    initial_size = len(bag)
    
    # Draw some letters
    drawn = draw_letters(bag, 7)
    assert len(drawn) == 7
    assert len(bag) == initial_size - 7
    
    # Draw more than available
    remaining = len(bag)
    drawn = draw_letters(bag, remaining + 10)
    assert len(drawn) == remaining
    assert len(bag) == 0

def test_letter_bag_return():
    """Test returning letters to the bag."""
    bag = create_letter_bag()
    initial_size = len(bag)
    
    # Draw and return letters
    drawn = draw_letters(bag, 7)
    return_letters(bag, drawn)
    assert len(bag) == initial_size

def test_create_rack():
    """Test creating a rack."""
    # Test with LetterBag class
    letter_bag = LetterBag()
    initial_size = letter_bag.remaining_count()
    
    # Create a rack
    rack = create_rack(letter_bag)
    assert len(rack) == 7
    assert letter_bag.remaining_count() == initial_size - 7
    
    # Create a rack with custom size
    rack = create_rack(letter_bag, size=5)
    assert len(rack) == 5
    assert letter_bag.remaining_count() == initial_size - 12  # 7 + 5 letters drawn
    
    # Test without letter bag (should use default distribution)
    rack = create_rack()
    assert len(rack) == 7

def test_exchange_letters():
    """Test exchanging letters."""
    letter_bag = LetterBag()
    initial_size = letter_bag.remaining_count()
    
    # Create a rack and exchange some letters
    rack = create_rack(letter_bag)
    letters_to_exchange = rack[:3]
    new_rack, new_letters = exchange_letters(rack, letters_to_exchange, letter_bag)
    
    assert len(new_rack) == 7
    assert len(new_letters) == 3
    assert letter_bag.remaining_count() == initial_size - 7  # Same size as before exchange
    
    # Test without letter bag
    rack = "ABCDEFG"
    letters_to_exchange = "ABC"
    new_rack, new_letters = exchange_letters(rack, letters_to_exchange)
    assert len(new_rack) == 7
    assert len(new_letters) == 3
    assert "A" not in new_rack[:4]  # First 4 letters should not contain exchanged letters
    assert "B" not in new_rack[:4]
    assert "C" not in new_rack[:4]