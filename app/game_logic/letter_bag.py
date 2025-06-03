import random
import os
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Test mode configuration for endgame testing
TEST_MODE_ENDGAME = os.getenv("TEST_MODE_ENDGAME", "false").lower() == "true"

# Letter distribution with frequencies and points for each language
LETTER_DISTRIBUTION = {
    "de": {
        "frequency": {
            'A': 5, 'B': 2, 'C': 2, 'D': 4, 'E': 15, 'F': 2, 'G': 3, 'H': 4, 'I': 6,
            'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 9, 'O': 3, 'P': 1, 'Q': 1, 'R': 6,
            'S': 7, 'T': 6, 'U': 6, 'V': 1, 'W': 1, 'X': 1, 'Y': 1, 'Z': 1,
            'Ä': 1, 'Ö': 1, 'Ü': 1, '?': 2  # ? represents blank tiles
        },
        "points": {
            'A': 1, 'B': 3, 'C': 4, 'D': 1, 'E': 1, 'F': 4, 'G': 2, 'H': 2, 'I': 1,
            'J': 6, 'K': 4, 'L': 2, 'M': 3, 'N': 1, 'O': 2, 'P': 4, 'Q': 10, 'R': 1,
            'S': 1, 'T': 1, 'U': 1, 'V': 6, 'W': 3, 'X': 8, 'Y': 10, 'Z': 3,
            'Ä': 3, 'Ö': 3, 'Ü': 3, '?': 0  # Blanks are worth 0 points
        }
    },
    "en": {
        "frequency": {
            'A': 9, 'B': 2, 'C': 2, 'D': 4, 'E': 12, 'F': 2, 'G': 3, 'H': 2, 'I': 9,
            'J': 1, 'K': 1, 'L': 4, 'M': 2, 'N': 6, 'O': 8, 'P': 2, 'Q': 1, 'R': 6,
            'S': 4, 'T': 6, 'U': 4, 'V': 2, 'W': 2, 'X': 1, 'Y': 2, 'Z': 1, '?': 2
        },
        "points": {
            'A': 1, 'B': 3, 'C': 3, 'D': 2, 'E': 1, 'F': 4, 'G': 2, 'H': 4, 'I': 1,
            'J': 8, 'K': 5, 'L': 1, 'M': 3, 'N': 1, 'O': 1, 'P': 3, 'Q': 10, 'R': 1,
            'S': 1, 'T': 1, 'U': 1, 'V': 4, 'W': 4, 'X': 8, 'Y': 4, 'Z': 10, '?': 0
        }
    },
    "es": {  # Spanish
        "frequency": {
            'A': 12, 'B': 2, 'C': 4, 'D': 5, 'E': 12, 'F': 1, 'G': 2, 'H': 2, 'I': 6,
            'J': 1, 'L': 4, 'M': 2, 'N': 5, 'Ñ': 1, 'O': 9, 'P': 2, 'Q': 1, 'R': 5,
            'S': 6, 'T': 4, 'U': 5, 'V': 1, 'X': 1, 'Y': 1, 'Z': 1, '?': 2
        },
        "points": {
            'A': 1, 'B': 3, 'C': 3, 'D': 2, 'E': 1, 'F': 4, 'G': 2, 'H': 4, 'I': 1,
            'J': 8, 'L': 1, 'M': 3, 'N': 1, 'Ñ': 8, 'O': 1, 'P': 3, 'Q': 5, 'R': 1,
            'S': 1, 'T': 1, 'U': 1, 'V': 4, 'X': 8, 'Y': 4, 'Z': 10, '?': 0
        }
    },
    "fr": {  # French
        "frequency": {
            'A': 9, 'B': 2, 'C': 2, 'D': 3, 'E': 15, 'F': 2, 'G': 2, 'H': 2, 'I': 8,
            'J': 1, 'K': 1, 'L': 5, 'M': 3, 'N': 6, 'O': 6, 'P': 2, 'Q': 1, 'R': 6,
            'S': 6, 'T': 6, 'U': 6, 'V': 2, 'W': 1, 'X': 1, 'Y': 1, 'Z': 1, '?': 2
        },
        "points": {
            'A': 1, 'B': 3, 'C': 3, 'D': 2, 'E': 1, 'F': 4, 'G': 2, 'H': 4, 'I': 1,
            'J': 8, 'K': 10, 'L': 1, 'M': 2, 'N': 1, 'O': 1, 'P': 3, 'Q': 8, 'R': 1,
            'S': 1, 'T': 1, 'U': 1, 'V': 4, 'W': 10, 'X': 10, 'Y': 10, 'Z': 10, '?': 0
        }
    },
    "it": {  # Italian
        "frequency": {
            'A': 14, 'B': 3, 'C': 4, 'D': 3, 'E': 11, 'F': 2, 'G': 2, 'H': 2, 'I': 12,
            'L': 5, 'M': 5, 'N': 5, 'O': 15, 'P': 3, 'Q': 1, 'R': 4, 'S': 6, 'T': 4,
            'U': 5, 'V': 3, 'Z': 2, '?': 2
        },
        "points": {
            'A': 1, 'B': 5, 'C': 2, 'D': 5, 'E': 1, 'F': 5, 'G': 8, 'H': 8, 'I': 1,
            'L': 3, 'M': 4, 'N': 3, 'O': 1, 'P': 5, 'Q': 10, 'R': 2, 'S': 2, 'T': 2,
            'U': 5, 'V': 4, 'Z': 8, '?': 0
        }
    }
}

# Short game distributions - only value-1 letters, total 24 tiles for quick endgame testing
SHORT_GAME_DISTRIBUTION = {
    "de": {
        # German value-1 letters: A, D, E, I, N, R, S, T, U - total 24
        'E': 4, 'A': 3, 'I': 3, 'N': 3, 'S': 3, 'R': 2, 'T': 2, 'U': 2, 'D': 2
    },
    "en": {
        # English value-1 letters: A, E, I, L, N, O, R, S, T, U - total 24
        'E': 4, 'A': 3, 'I': 3, 'O': 3, 'N': 2, 'R': 2, 'S': 2, 'T': 2, 'L': 2, 'U': 1
    },
    "es": {
        # Spanish value-1 letters: A, E, I, L, N, O, R, S, T, U - total 24
        'A': 4, 'E': 4, 'O': 3, 'I': 3, 'S': 2, 'R': 2, 'N': 2, 'T': 2, 'L': 1, 'U': 1
    },
    "fr": {
        # French value-1 letters: A, E, I, L, N, O, R, S, T, U - total 24
        'E': 4, 'A': 3, 'I': 3, 'O': 3, 'S': 2, 'T': 2, 'N': 2, 'R': 2, 'L': 2, 'U': 1
    },
    "it": {
        # Italian value-1 letters: A, E, I, O - total 24
        'A': 6, 'E': 6, 'I': 6, 'O': 6
    }
}

class LetterBag:
    """A class to manage the letter bag for the game."""
    
    def __init__(self, language: str = "en", short_game: bool = None):
        self.language = language
        # Use short_game parameter if provided, otherwise check environment variable for backward compatibility
        self.short_game = short_game if short_game is not None else TEST_MODE_ENDGAME
        self.letters = create_letter_bag(language, self.short_game)
    
    def draw(self, count: int) -> List[str]:
        """Draw letters from the bag."""
        return draw_letters(self.letters, count)
    
    def return_letters(self, letters: List[str]) -> None:
        """Return letters to the bag."""
        return_letters(self.letters, letters)
    
    def remaining_count(self) -> int:
        """Get the number of letters remaining in the bag."""
        return len(self.letters)

def create_letter_bag(language: str = "en", short_game: bool = None) -> List[str]:
    """Create a new letter bag with the correct distribution of letters."""
    # Use short_game parameter if provided, otherwise check environment variable for backward compatibility
    use_short_game = short_game if short_game is not None else TEST_MODE_ENDGAME
    
    if use_short_game:
        # Use reduced distribution with only value-1 letters for quick endgame testing
        letter_distribution = SHORT_GAME_DISTRIBUTION.get(language, SHORT_GAME_DISTRIBUTION["en"])
        logger.info(f"🧪 SHORT GAME: Using {language} letter bag with only value-1 letters ({sum(letter_distribution.values())} tiles total)")
    else:
        # Use normal distribution from LETTER_DISTRIBUTION
        if language in LETTER_DISTRIBUTION:
            letter_distribution = LETTER_DISTRIBUTION[language]["frequency"]
        else:
            # Default to English if language not found
            letter_distribution = LETTER_DISTRIBUTION["en"]["frequency"]
            logger.warning(f"⚠️  Language '{language}' not found, defaulting to English")
    
    # Create list with correct distribution
    letters = []
    for letter, count in letter_distribution.items():
        letters.extend([letter] * count)
    
    # Shuffle the letters
    random.shuffle(letters)
    return letters

def draw_letters(letter_bag: List[str], count: int) -> List[str]:
    """Draw a specified number of letters from the bag."""
    if count > len(letter_bag):
        count = len(letter_bag)
    drawn = []
    for _ in range(count):
        if letter_bag:
            drawn.append(letter_bag.pop())
    return drawn

def return_letters(letter_bag: List[str], letters: List[str]) -> None:
    """Return letters to the bag and shuffle."""
    letter_bag.extend(letters)
    random.shuffle(letter_bag)

def create_rack(letter_bag: Optional[LetterBag] = None, language: str = "en", size: int = 7) -> str:
    """Create a new rack with the specified number of letters."""
    if letter_bag is None:
        # If no letter bag is provided, use the default distribution
        all_letters = []
        distribution = LETTER_DISTRIBUTION[language]["frequency"]
        for letter, count in distribution.items():
            all_letters.extend([letter] * count)
        return "".join(random.sample(all_letters, min(size, len(all_letters))))
    
    # Draw from the provided letter bag
    if isinstance(letter_bag, LetterBag):
        drawn = letter_bag.draw(size)
    else:
        # Handle case where letter_bag is a List[str]
        drawn = draw_letters(letter_bag, size)
    return "".join(drawn)

def exchange_letters(rack: str, letters_to_exchange: str, letter_bag: Optional[LetterBag] = None, language: str = "en") -> Tuple[str, List[str]]:
    """
    Exchange letters in a rack.
    
    Args:
        rack: The current rack
        letters_to_exchange: Letters to exchange
        letter_bag: Optional letter bag to draw from
        language: Game language (default: "en")
        
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
        distribution = LETTER_DISTRIBUTION[language]["frequency"]
        for letter, count in distribution.items():
            all_letters.extend([letter] * count)
        new_letters = random.sample(all_letters, len(letters_to_exchange))
    
    # Add the new letters to the rack
    new_rack += "".join(new_letters)
    
    return new_rack, new_letters

def refill_rack(letter_bag: List[str], rack: str, target_size: int = 7) -> str:
    """Refill a rack to the target size."""
    needed = target_size - len(rack)
    if needed > 0:
        new_letters = draw_letters(letter_bag, needed)
        rack += "".join(new_letters)
    return rack