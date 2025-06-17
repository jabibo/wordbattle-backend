"""
Optimized Computer Player with Bubble Sort Word Elimination & Direct Access Object Model
======================================================================================

This implementation uses advanced performance optimizations:
1. BUBBLE SORT ELIMINATION: Fast rejection of impossible words before expensive operations
2. DIRECT ACCESS OBJECT MODEL: Pre-computed data structures for instant lookups
3. INDEXED WORD LOOKUP: Words organized by length, starting letters, and rack compatibility
4. STRATEGIC POSITION CACHING: Board analysis cached and reused
5. MINIMAL VALIDATION: Only validate promising candidates

Performance Target: <50ms per move vs current 2000ms+
"""

from typing import List, Dict, Any, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import time
import logging

logger = logging.getLogger(__name__)

@dataclass
class WordCandidate:
    """Optimized word candidate with pre-computed properties."""
    word: str
    length: int
    letter_set: Set[str]
    letter_count: Dict[str, int]
    first_letter: str
    last_letter: str
    score_potential: int  # Estimated max score for quick sorting

@dataclass 
class BoardPosition:
    """Strategic board position with placement potential."""
    row: int
    col: int
    horizontal_space: int
    vertical_space: int
    connectivity_score: int
    multiplier_potential: int

class OptimizedWordIndex:
    """Direct access object model for instant word lookups."""
    
    def __init__(self, wordlist: List[str]):
        """Build optimized indexes during service startup."""
        logger.info(f"🚀 Building optimized word index from {len(wordlist)} words...")
        start_time = time.time()
        
        # Core data structures for direct access
        self.words_by_length: Dict[int, List[WordCandidate]] = defaultdict(list)
        self.words_by_first_letter: Dict[str, List[WordCandidate]] = defaultdict(list)
        self.words_by_letter_set: Dict[frozenset, List[WordCandidate]] = defaultdict(list)
        self.rack_compatible_words: Dict[frozenset, List[WordCandidate]] = defaultdict(list)
        
        # Process each word into optimized candidate
        candidates = []
        for word_str in wordlist:
            word = word_str.upper().strip()
            if 2 <= len(word) <= 7:  # Only reasonable word lengths
                candidate = WordCandidate(
                    word=word,
                    length=len(word),
                    letter_set=set(word),
                    letter_count=self._count_letters(word),
                    first_letter=word[0],
                    last_letter=word[-1],
                    score_potential=self._estimate_score_potential(word)
                )
                candidates.append(candidate)
        
        # Build indexes for instant access
        for candidate in candidates:
            # Index by length for quick filtering
            self.words_by_length[candidate.length].append(candidate)
            
            # Index by first letter for placement optimization
            self.words_by_first_letter[candidate.first_letter].append(candidate)
            
            # Index by letter set for subset matching
            letter_set_key = frozenset(candidate.letter_set)
            self.words_by_letter_set[letter_set_key].append(candidate)
        
        # Sort all indexes by score potential (best words first)
        for length_list in self.words_by_length.values():
            length_list.sort(key=lambda w: w.score_potential, reverse=True)
            
        for letter_list in self.words_by_first_letter.values():
            letter_list.sort(key=lambda w: w.score_potential, reverse=True)
            
        for set_list in self.words_by_letter_set.values():
            set_list.sort(key=lambda w: w.score_potential, reverse=True)
        
        build_time = time.time() - start_time
        total_candidates = len(candidates)
        logger.info(f"✅ Optimized word index built in {build_time:.3f}s:")
        logger.info(f"   - {total_candidates} word candidates")
        logger.info(f"   - {len(self.words_by_length)} length buckets")
        logger.info(f"   - {len(self.words_by_first_letter)} first letter buckets")
        logger.info(f"   - {len(self.words_by_letter_set)} letter set buckets")
    
    def _count_letters(self, word: str) -> Dict[str, int]:
        """Count letter frequencies in word."""
        count = defaultdict(int)
        for letter in word:
            count[letter] += 1
        return dict(count)
    
    def _estimate_score_potential(self, word: str) -> int:
        """Estimate maximum possible score for word (rough heuristic)."""
        # Simple scoring based on letter values and length
        letter_values = {
            'A': 1, 'E': 1, 'I': 1, 'O': 1, 'U': 1, 'L': 1, 'N': 1, 'S': 1, 'T': 1, 'R': 1,
            'D': 2, 'G': 2, 'B': 3, 'C': 3, 'M': 3, 'P': 3, 'F': 4, 'H': 4, 'V': 4, 'W': 4, 'Y': 4,
            'K': 5, 'J': 8, 'X': 8, 'Q': 10, 'Z': 10
        }
        base_score = sum(letter_values.get(letter, 1) for letter in word)
        return base_score * len(word)  # Longer words get bonus
    
    def get_bubble_sorted_candidates(self, rack_letters: List[str], max_candidates: int = 20) -> List[WordCandidate]:
        """BUBBLE SORT ELIMINATION: Get best word candidates instantly."""
        rack_set = set(rack_letters)
        rack_counts = defaultdict(int)
        for letter in rack_letters:
            rack_counts[letter] += 1
        
        candidates = []
        
        # Fast elimination pass 1: Letter set compatibility
        for letter_set_key, word_list in self.words_by_letter_set.items():
            if letter_set_key.issubset(rack_set):
                candidates.extend(word_list[:5])  # Top 5 from each compatible set
                if len(candidates) >= max_candidates * 2:  # Collect extra for filtering
                    break
        
        # Fast elimination pass 2: Exact letter count validation
        valid_candidates = []
        for candidate in candidates:
            if self._can_make_word_fast(candidate, rack_counts):
                valid_candidates.append(candidate)
                if len(valid_candidates) >= max_candidates:
                    break
        
        # Already sorted by score potential
        return valid_candidates[:max_candidates]
    
    def _can_make_word_fast(self, candidate: WordCandidate, rack_counts: Dict[str, int]) -> bool:
        """Ultra-fast word validation using pre-computed letter counts."""
        word_counts = candidate.letter_count
        available_blanks = rack_counts.get('?', 0) + rack_counts.get('*', 0)
        
        for letter, needed in word_counts.items():
            available = rack_counts.get(letter, 0)
            if available < needed:
                # Need blanks to cover shortage
                shortage = needed - available
                if shortage > available_blanks:
                    return False
                available_blanks -= shortage
        
        return True

class OptimizedBoardAnalyzer:
    """Direct access board analysis with strategic position caching."""
    
    def __init__(self):
        self.cached_positions: Optional[List[BoardPosition]] = None
        self.last_board_hash: Optional[str] = None
    
    def get_strategic_positions(self, board: List[List]) -> List[BoardPosition]:
        """Get strategic positions with caching to avoid recomputation."""
        # Create simple board hash for cache validation
        board_hash = str(sum(1 for row in board for cell in row if cell is not None))
        
        # Return cached positions if board hasn't changed significantly
        if (self.cached_positions is not None and 
            self.last_board_hash == board_hash):
            return self.cached_positions[:10]  # Top 10 positions
        
        # Analyze board for strategic positions
        positions = []
        
        # Check if first move (empty board)
        if board_hash == "0":
            positions.append(BoardPosition(7, 7, 8, 8, 100, 50))  # Center with high priority
        else:
            # Find positions adjacent to existing tiles
            for row in range(15):
                for col in range(15):
                    if board[row][col] is not None:
                        # Check all 4 adjacent positions
                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            adj_row, adj_col = row + dr, col + dc
                            if (0 <= adj_row < 15 and 0 <= adj_col < 15 and 
                                board[adj_row][adj_col] is None):
                                
                                position = BoardPosition(
                                    row=adj_row,
                                    col=adj_col,
                                    horizontal_space=self._calculate_space(board, adj_row, adj_col, "horizontal"),
                                    vertical_space=self._calculate_space(board, adj_row, adj_col, "vertical"),
                                    connectivity_score=self._calculate_connectivity(board, adj_row, adj_col),
                                    multiplier_potential=self._calculate_multiplier_potential(adj_row, adj_col)
                                )
                                positions.append(position)
        
        # Sort by strategic value (connectivity + multiplier potential)
        positions.sort(key=lambda p: p.connectivity_score + p.multiplier_potential, reverse=True)
        
        # Cache results
        self.cached_positions = positions[:20]  # Cache top 20
        self.last_board_hash = board_hash
        
        return self.cached_positions[:10]  # Return top 10
    
    def _calculate_space(self, board: List[List], row: int, col: int, direction: str) -> int:
        """Calculate available space in direction."""
        if direction == "horizontal":
            space = 0
            for c in range(col, 15):
                if board[row][c] is None:
                    space += 1
                else:
                    break
            return space
        else:  # vertical
            space = 0
            for r in range(row, 15):
                if board[r][col] is None:
                    space += 1
                else:
                    break
            return space
    
    def _calculate_connectivity(self, board: List[List], row: int, col: int) -> int:
        """Calculate connectivity bonus for position."""
        connections = 0
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            adj_row, adj_col = row + dr, col + dc
            if (0 <= adj_row < 15 and 0 <= adj_col < 15 and 
                board[adj_row][adj_col] is not None):
                connections += 1
        return connections * 10  # 10 points per connection
    
    def _calculate_multiplier_potential(self, row: int, col: int) -> int:
        """Calculate multiplier potential for position."""
        # Simple multiplier map (basic implementation)
        if (row, col) == (7, 7):  # Center
            return 50
        if row in [0, 7, 14] or col in [0, 7, 14]:  # Word multiplier lines
            return 20
        if (row + col) % 2 == 0:  # Letter multiplier positions
            return 10
        return 5

class OptimizedComputerPlayer:
    """Minimal intelligence computer player - always passes (reactivated for testing)."""
    
    def __init__(self, difficulty: str = "medium"):
        self.difficulty = difficulty
        self.word_index: Optional[OptimizedWordIndex] = None
        self.board_analyzer = OptimizedBoardAnalyzer()
        
        # Performance thresholds by difficulty
        self.move_limits = {
            "easy": {"candidates": 5, "positions": 3, "attempts": 10},
            "medium": {"candidates": 10, "positions": 5, "attempts": 20},
            "hard": {"candidates": 20, "positions": 8, "attempts": 30}
        }
    
    def initialize_with_wordlist(self, wordlist: List[str]) -> None:
        """Initialize the optimized word index (called once during service startup)."""
        if self.word_index is None:
            self.word_index = OptimizedWordIndex(wordlist)
            # Store wordlist as set for fast dictionary validation
            self._wordlist_set = set(word.upper() for word in wordlist)
            logger.info(f"🚀 OptimizedComputerPlayer initialized with {len(wordlist)} words for validation")
    
    def _get_performance_wordlist(self, full_wordlist: List[str]) -> List[str]:
        """Get a performance-optimized subset of the wordlist for quick play."""
        # Convert to list if it's a set
        if not isinstance(full_wordlist, list):
            full_wordlist = list(full_wordlist)
        
        # Smart filtering for performance:
        # 1. Common word lengths (2-7 letters)
        # 2. No very rare words
        # 3. Priority to common letters
        common_letters = set('AEIOURSTLNDMHCBPFGWYVKJXQZ')
        
        performance_words = []
        for word in full_wordlist:
            word_upper = word.upper()
            # Filter criteria for performance
            if (2 <= len(word_upper) <= 7 and  # Good length range
                len(set(word_upper) & common_letters) >= len(word_upper) * 0.7):  # Mostly common letters
                performance_words.append(word_upper)
                
                # Limit to 25,000 words for quick initialization
                if len(performance_words) >= 25000:
                    break
        
        logger.info(f"🎯 Performance wordlist: {len(performance_words)} words from {len(full_wordlist)} total")
        return performance_words
    
    def make_move(self, game_state_data: Dict[str, Any], rack: str, wordlist: List[str]) -> Dict[str, Any]:
        """Make a move - MINIMAL INTELLIGENCE: Always pass."""
        rack_letters = list(rack.upper())
        board = game_state_data.get("board", [[None]*15 for _ in range(15)])
        
        logger.info(f"🤖 MinimalComputerPlayer: Always passing (minimal intelligence mode)")
        logger.info(f"   Rack: {rack_letters}")
        logger.info(f"   Board has tiles: {any(any(cell is not None for cell in row) for row in board)}")
        
        return {
            "type": "pass", 
            "message": "Computer passes (minimal intelligence mode - always passes)"
        }
    
    def _try_optimized_placement(self, board: List[List], candidate: WordCandidate, 
                                start_row: int, start_col: int, direction: str, 
                                rack_letters: List[str]) -> Optional[Dict[str, Any]]:
        """Try placing a word with validation for correctness."""
        word = candidate.word
        tiles = []
        rack_copy = rack_letters.copy()
        
        # CRITICAL: Validate word is in dictionary first!
        if not hasattr(self, '_wordlist_set'):
            logger.warning(f"⚠️ No wordlist available for validation, skipping word: {word}")
            return None
        
        # SPECIAL DETECTION: Only block known problematic patterns
        if word.upper() in ["ADSTAND", "ISTADSTAND", "ISTSTAND"]:
            logger.error(f"🚨 CRITICAL: Blocked known invalid word: '{word}'")
            return None
        
        if word.upper() not in self._wordlist_set:
            logger.error(f"🚫 INVALID WORD REJECTED: '{word}' is NOT in dictionary")
            # Log some similar words for debugging
            similar_words = [w for w in list(self._wordlist_set)[:100] if w.startswith(word[:3])][:5]
            logger.error(f"   Similar words in dictionary: {similar_words}")
            return None
        
        logger.debug(f"✅ MAIN WORD VALIDATED: '{word}' is in dictionary")
        
        # Fast connectivity check
        connected = False
        
        # Build tile placement
        for i, letter in enumerate(word):
            if direction == "horizontal":
                row, col = start_row, start_col + i
            else:
                row, col = start_row + i, start_col
            
            if board[row][col] is None:
                # Need to place this letter
                if letter in rack_copy:
                    rack_copy.remove(letter)
                elif '?' in rack_copy:  # Use blank
                    rack_copy.remove('?')
                elif '*' in rack_copy:  # Alternative blank format
                    rack_copy.remove('*')
                else:
                    logger.warning(f"⚠️ Cannot place '{word}': missing letter '{letter}' from rack")
                    return None  # Can't place this letter
                
                tiles.append({"row": row, "col": col, "letter": letter})
            else:
                # Letter must match existing tile
                cell = board[row][col]
                if isinstance(cell, dict):
                    existing_letter = cell.get("letter", cell.get("LETTER", str(cell))).upper()
                else:
                    existing_letter = str(cell).upper()
                
                if existing_letter != letter:
                    logger.warning(f"⚠️ Cannot place '{word}': letter mismatch at ({row},{col}), need '{letter}' but found '{existing_letter}'")
                    return None
                connected = True  # Connected to existing tile
        
        # Check connectivity (at least one tile connects to existing)
        if not connected and any(any(cell is not None for cell in row) for row in board):
            # Not first move and no connection
            logger.warning(f"⚠️ Cannot place '{word}': no connection to existing tiles")
            return None
        
        # Validate all cross-words formed (comprehensive validation)
        if not self._validate_all_cross_words(board, tiles, direction, start_row, start_col):
            logger.error(f"🚫 CROSS-WORD VALIDATION FAILED for main word '{word}'")
            return None
        
        logger.info(f"✅ VALID WORD ACCEPTED: '{word}' passed all validation checks")
        
        # Calculate simple score (basic implementation)
        score = len(word) * 2  # Simple scoring
        
        return {
            "word": word,
            "tiles": tiles,
            "score": score,
            "start_pos": (start_row, start_col),
            "direction": direction
        }
    
    def _validate_all_cross_words(self, board: List[List], tiles: List[Dict], 
                                 direction: str, start_row: int, start_col: int) -> bool:
        """Validate that all cross-words formed are in the dictionary."""
        if not hasattr(self, '_wordlist_set'):
            logger.warning("⚠️ No wordlist available for cross-word validation - skipping")
            return True  # Skip validation if no wordlist
        
        # Create temporary board with new tiles
        temp_board = [row[:] for row in board]
        for tile in tiles:
            temp_board[tile["row"]][tile["col"]] = tile["letter"]
        
        logger.debug(f"🔍 CROSS-WORD VALIDATION: Checking {len(tiles)} tiles in {direction} direction")
        
        # Check each placed tile for cross-words
        for tile in tiles:
            row, col = tile["row"], tile["col"]
            
            # Check horizontal cross-word (if main word is vertical)
            if direction == "vertical":
                word = self._extract_word_at_position(temp_board, row, col, "horizontal")
                if len(word) > 1:
                    if word.upper() not in self._wordlist_set:
                        logger.error(f"🚫 INVALID HORIZONTAL CROSS-WORD: '{word}' at ({row},{col}) NOT IN DICTIONARY")
                        return False
            
            # Check vertical cross-word (if main word is horizontal)  
            if direction == "horizontal":
                word = self._extract_word_at_position(temp_board, row, col, "vertical")
                if len(word) > 1:
                    if word.upper() not in self._wordlist_set:
                        logger.error(f"🚫 INVALID VERTICAL CROSS-WORD: '{word}' at ({row},{col}) NOT IN DICTIONARY")
                        return False
        
        logger.debug("✅ All cross-words validated successfully")
        return True
    
    def _extract_word_at_position(self, board: List[List], row: int, col: int, direction: str) -> str:
        """Extract the complete word at a position in the given direction."""
        logger.debug(f"🔍 Extracting {direction} word at ({row},{col})")
        
        if direction == "horizontal":
            # Find start of word
            start_col = col
            while start_col > 0 and board[row][start_col - 1] is not None:
                start_col -= 1
            
            # Extract word
            word = ""
            current_col = start_col
            while current_col < 15 and board[row][current_col] is not None:
                cell = board[row][current_col]
                if isinstance(cell, dict):
                    letter = cell.get("letter", str(cell)).upper()
                else:
                    letter = str(cell).upper()
                word += letter
                current_col += 1
            
            logger.debug(f"🔍 Extracted horizontal word: '{word}' from ({row},{start_col}) to ({row},{current_col-1})")
            return word
        
        else:  # vertical
            # Find start of word
            start_row = row
            while start_row > 0 and board[start_row - 1][col] is not None:
                start_row -= 1
            
            # Extract word
            word = ""
            current_row = start_row
            while current_row < 15 and board[current_row][col] is not None:
                cell = board[current_row][col]
                if isinstance(cell, dict):
                    letter = cell.get("letter", str(cell)).upper()
                else:
                    letter = str(cell).upper()
                word += letter
                current_row += 1
            
            logger.debug(f"🔍 Extracted vertical word: '{word}' from ({start_row},{col}) to ({current_row-1},{col})")
            return word


# Global instance for service-level caching
_optimized_computer_player: Optional[OptimizedComputerPlayer] = None
_computer_player_status = {
    "initialized": False,
    "ready": False,
    "error": None,
    "fallback_available": True,
    "initialization_time": None,
    "last_check": None
}

def get_computer_player_health() -> Dict[str, Any]:
    """Get comprehensive health status of the computer player system."""
    global _computer_player_status
    
    # Update last check timestamp
    _computer_player_status["last_check"] = time.time()
    
    # Only OptimizedComputerPlayer is available now - no fallbacks
    standard_available = False
    
    # Test if optimized computer player is working
    optimized_available = False
    optimized_error = None
    
    if _optimized_computer_player is not None:
        try:
            # Quick test of optimized player
            if _optimized_computer_player.word_index is not None:
                optimized_available = True
        except Exception as e:
            optimized_error = str(e)
            logger.warning(f"⚠️ OptimizedComputerPlayer health check failed: {e}")
    
    # Overall readiness assessment
    overall_ready = optimized_available or standard_available
    
    status = {
        "overall_ready": overall_ready,
        "optimized_computer_player": {
            "available": optimized_available,
            "initialized": _computer_player_status["initialized"],
            "error": optimized_error or _computer_player_status["error"]
        },
        "standard_computer_player": {
            "available": standard_available
        },
        "recommendation": "optimized" if optimized_available else ("standard" if standard_available else "unavailable"),
        "initialization_time": _computer_player_status["initialization_time"],
        "last_health_check": _computer_player_status["last_check"]
    }
    
    return status

def is_computer_player_ready() -> bool:
    """Quick check if any computer player is ready for games."""
    health = get_computer_player_health()
    return health["overall_ready"]

def get_optimized_computer_player(difficulty: str = "medium") -> OptimizedComputerPlayer:
    """Get or create optimized computer player with service-level caching."""
    global _optimized_computer_player, _computer_player_status
    
    try:
        if _optimized_computer_player is None:
            _optimized_computer_player = OptimizedComputerPlayer(difficulty)
            _computer_player_status["initialized"] = True
            logger.info("🚀 Created global OptimizedComputerPlayer instance")
        
        return _optimized_computer_player
    except Exception as e:
        _computer_player_status["error"] = str(e)
        logger.error(f"❌ Failed to create OptimizedComputerPlayer: {e}")
        raise

def initialize_optimized_computer_player(wordlist: List[str]) -> None:
    """Initialize optimized computer player during service startup."""
    global _computer_player_status
    
    start_time = time.time()
    
    try:
        player = get_optimized_computer_player()
        
        # Use performance wordlist for quick startup
        performance_wordlist = player._get_performance_wordlist(wordlist)
        player.initialize_with_wordlist(performance_wordlist)
        
        initialization_time = time.time() - start_time
        _computer_player_status.update({
            "ready": True,
            "error": None,
            "initialization_time": initialization_time
        })
        
        logger.info(f"🚀 OptimizedComputerPlayer initialized for service in {initialization_time:.2f}s with {len(performance_wordlist)} words")
    except Exception as e:
        _computer_player_status.update({
            "ready": False,
            "error": str(e),
            "initialization_time": None
        })
        logger.error(f"❌ Failed to initialize OptimizedComputerPlayer: {e}")
        logger.info("🔄 Computer player will work with lazy initialization")
        # Don't raise - allow lazy initialization 