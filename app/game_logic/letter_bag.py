import random
from typing import List, Dict, Tuple

# Letter distribution with frequencies based on German language
LETTER_DISTRIBUTION = {
    'A': 5, 'B': 2, 'C': 2, 'D': 4, 'E': 15, 'F': 2, 'G': 3, 'H': 4, 'I': 6,
    'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 9, 'O': 3, 'P': 1, 'Q': 1, 'R': 6,
    'S': 7, 'T': 6, 'U': 6, 'V': 1, 'W': 1, 'X': 1, 'Y': 1, 'Z': 1,
    'Ä': 1, 'Ö': 1, 'Ü': 1, '?': 2  # ? represents blank tiles
}

# Letter point values
LETTER_POINTS = {
    'A': 1, 'B': 3, 'C': 4, 'D': 1, 'E': 1, 'F': 4, 'G': 2, 'H': 2, 'I': 1,
    'J': 6, 'K': 4, 'L': 2, 'M': 3, 'N': 1, 'O': 2, 'P': 4, 'Q': 10, 'R': 1,
    'S': 1, 'T': 1, 'U': 1, 'V': 6, 'W': 3, 'X': 8, 'Y': 10, 'Z': 3,
    'Ä': 3, 'Ö': 3, 'Ü': 3, '?': 0  # Blanks are worth 0 points
}

class LetterBag:
    """A class to manage the letter bag for the game."""
    
    def __init__(self):
        """Initialize the letter bag with the standard distribution."""
        self.letters = []
        for letter, count in LETTER_DISTRIBUTION.items():
            self.letters.extend([letter] * count)
        random.shuffle(self.letters)
    
    def draw(self, count: int) -> List[str]:
        """Draw a specified number of letters from the bag."""
        if count > len(self.letters):
            count = len(self.letters)  # Can't draw more than what's available
        
        drawn = []
        for _ in range(count):
            if self.letters:
                drawn.append(self.letters.pop())
        
        return drawn
    
    def return_letters(self, letters: List[str]) -> None:
        """Return letters to the bag and shuffle."""
        self.letters.extend(letters)
        random.shuffle(self.letters)
    
    def remaining(self) -> int:
        """Return the number of letters remaining in the bag."""
        return len(self.letters)
    
    def get_distribution(self) -> Dict[str, int]:
        """Return the current distribution of letters in the bag."""
        distribution = {}
        for letter in self.letters:
            distribution[letter] = distribution.get(letter, 0) + 1
        return distribution

def create_rack(letter_bag: LetterBag = None) -> str:
    """Create a new rack with 7 letters."""
    if letter_bag is None:
        # If no letter bag is provided, use the default distribution
        all_letters = []
        for letter, count in LETTER_DISTRIBUTION.items():
            all_letters.extend([letter] * count)
        return "".join(random.sample(all_letters, 7))
    
    # Draw from the provided letter bag
    drawn = letter_bag.draw(7)
    return "".join(drawn)

def exchange_letters(rack: str, letters_to_exchange: str, letter_bag: LetterBag = None) -> Tuple[str, List[str]]:
    """
    Exchange letters in a rack.
    
    Args:
        rack: The current rack
        letters_to_exchange: Letters to exchange
        letter_bag: Optional letter bag to draw from
        
    Returns:
        Tuple of (new_rack, new_letters)
    """
    # Remove the letters to exchange from the rack
    new_rack = rack
    for letter in letters_to_exchange:
        new_rack = new_rack.replace(letter, "", 1)
    
    if letter_bag:
        # Return the exchanged letters to the bag
        letter_bag.return_letters(list(letters_to_exchange))
        # Draw new letters
        new_letters = letter_bag.draw(len(letters_to_exchange))
    else:
        # If no letter bag is provided, just draw random letters
        all_letters = []
        for letter, count in LETTER_DISTRIBUTION.items():
            all_letters.extend([letter] * count)
        new_letters = random.sample(all_letters, len(letters_to_exchange))
    
    # Add the new letters to the rack
    new_rack += "".join(new_letters)
    
    return new_rack, new_letters