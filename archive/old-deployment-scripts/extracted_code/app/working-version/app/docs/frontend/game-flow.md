# Game Flow Documentation

## Overview

WordBattle implements a turn-based Scrabble-like word game with real-time multiplayer functionality. Players take turns placing letter tiles on a board to form words and score points.

## Game Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Player 1  │    │   Backend   │    │   Player 2  │
│   Flutter   │    │   FastAPI   │    │   Flutter   │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       │ 1. Create Game    │                   │
       ├──────────────────►│                   │
       │                   │ 2. Send Invite    │
       │                   ├──────────────────►│
       │                   │ 3. Accept Game    │
       │                   │◄──────────────────┤
       │ 4. Game Started   │                   │
       │◄──────────────────┤                   │
       │                   │ 5. Game Started   │
       │                   ├──────────────────►│
       │ 6. Make Move      │                   │
       ├──────────────────►│                   │
       │                   │ 7. Move Update    │
       │                   ├──────────────────►│
```

## Game States

```dart
enum GameState {
  waiting,      // Waiting for opponent
  active,       // Game in progress
  yourTurn,     // Player's turn to move
  theirTurn,    // Opponent's turn
  paused,       // Game paused
  completed,    // Game finished
  abandoned,    // Game abandoned by player
}
```

## Game Creation Flow

### 1. New Game Screen
```dart
class NewGameScreen extends StatefulWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('New Game')),
      body: Column(
        children: [
          // Opponent selection
          OpponentSelector(
            onFriendSelected: (friend) => _createGameWithFriend(friend),
            onRandomSelected: () => _createRandomGame(),
          ),
          
          // Game settings
          GameSettings(
            language: _selectedLanguage,
            timeLimit: _timeLimit,
            onLanguageChanged: (lang) => setState(() => _selectedLanguage = lang),
            onTimeLimitChanged: (time) => setState(() => _timeLimit = time),
          ),
          
          // Create button
          ElevatedButton(
            onPressed: _createGame,
            child: Text('Create Game'),
          ),
        ],
      ),
    );
  }
}
```

### 2. Game Creation API
```dart
Future<Game> createGame({
  String? opponentId,
  String language = 'en',
  int? timeLimit,
}) async {
  final response = await ApiClient.authenticatedRequest(
    'POST',
    '/games/create',
    body: {
      'opponent_id': opponentId,
      'language': language,
      'time_limit_minutes': timeLimit,
    },
  );
  
  if (response.statusCode == 201) {
    final gameData = jsonDecode(response.body);
    return Game.fromJson(gameData);
  } else {
    throw GameCreationException('Failed to create game');
  }
}
```

## Game Board Implementation

### Board Structure
```dart
class GameBoard {
  static const int size = 15;
  static const int centerPosition = 7;
  
  List<List<BoardCell>> cells = List.generate(
    size,
    (row) => List.generate(
      size,
      (col) => BoardCell(row: row, col: col),
    ),
  );
  
  // Special squares
  static const Map<String, List<Position>> specialSquares = {
    'triple_word': [
      Position(0, 0), Position(0, 7), Position(0, 14),
      Position(7, 0), Position(7, 14),
      Position(14, 0), Position(14, 7), Position(14, 14),
    ],
    'double_word': [
      Position(1, 1), Position(2, 2), Position(3, 3),
      // ... more positions
    ],
    'triple_letter': [
      Position(1, 5), Position(1, 9),
      Position(5, 1), Position(5, 5),
      // ... more positions
    ],
    'double_letter': [
      Position(0, 3), Position(0, 11),
      Position(2, 6), Position(2, 8),
      // ... more positions
    ],
  };
}
```

### Board Cell Widget
```dart
class BoardCellWidget extends StatelessWidget {
  final BoardCell cell;
  final bool isHighlighted;
  final VoidCallback? onTap;
  
  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: _getCellColor(),
          border: Border.all(color: Colors.grey),
        ),
        child: Stack(
          children: [
            // Special square indicator
            if (cell.isSpecial) _buildSpecialIndicator(),
            
            // Letter tile
            if (cell.tile != null) LetterTileWidget(tile: cell.tile!),
            
            // Highlight overlay
            if (isHighlighted) _buildHighlightOverlay(),
          ],
        ),
      ),
    );
  }
  
  Color _getCellColor() {
    if (cell.tile != null) return Colors.white;
    
    switch (cell.specialType) {
      case SpecialType.tripleWord:
        return Colors.red.shade300;
      case SpecialType.doubleWord:
        return Colors.pink.shade200;
      case SpecialType.tripleLetter:
        return Colors.blue.shade300;
      case SpecialType.doubleLetter:
        return Colors.lightBlue.shade200;
      default:
        return Colors.grey.shade100;
    }
  }
}
```

## Tile Management

### Letter Tile Model
```dart
class LetterTile {
  final String letter;
  final int points;
  final bool isBlank;
  final String? assignedLetter; // For blank tiles
  
  LetterTile({
    required this.letter,
    required this.points,
    this.isBlank = false,
    this.assignedLetter,
  });
  
  String get displayLetter => isBlank ? (assignedLetter ?? '_') : letter;
  int get displayPoints => isBlank ? 0 : points;
}
```

### Tile Rack Widget
```dart
class TileRackWidget extends StatelessWidget {
  final List<LetterTile> tiles;
  final Function(LetterTile) onTileTapped;
  
  @override
  Widget build(BuildContext context) {
    return Container(
      height: 60,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        itemCount: tiles.length,
        itemBuilder: (context, index) {
          return Draggable<LetterTile>(
            data: tiles[index],
            child: TileWidget(tile: tiles[index]),
            feedback: TileWidget(
              tile: tiles[index],
              isDragging: true,
            ),
            childWhenDragging: TileWidget(
              tile: tiles[index],
              isPlaceholder: true,
            ),
          );
        },
      ),
    );
  }
}
```

## Move Validation

### Word Formation
```dart
class MoveValidator {
  static ValidationResult validateMove(
    GameBoard board,
    List<TilePlacement> placements,
  ) {
    // Check if tiles form valid words
    final words = _extractWords(board, placements);
    
    // Validate each word
    for (final word in words) {
      if (!DictionaryService.isValidWord(word.text)) {
        return ValidationResult.invalid('Invalid word: ${word.text}');
      }
    }
    
    // Check if move connects to existing tiles
    if (!_connectsToExistingTiles(board, placements)) {
      return ValidationResult.invalid('Move must connect to existing tiles');
    }
    
    // Check if tiles are placed in a line
    if (!_tilesInLine(placements)) {
      return ValidationResult.invalid('Tiles must be placed in a straight line');
    }
    
    return ValidationResult.valid(words);
  }
  
  static List<Word> _extractWords(
    GameBoard board,
    List<TilePlacement> placements,
  ) {
    final words = <Word>[];
    
    // Find horizontal words
    words.addAll(_findHorizontalWords(board, placements));
    
    // Find vertical words
    words.addAll(_findVerticalWords(board, placements));
    
    return words;
  }
}
```

### Scoring System
```dart
class ScoreCalculator {
  static int calculateMoveScore(
    GameBoard board,
    List<Word> words,
    List<TilePlacement> placements,
  ) {
    int totalScore = 0;
    int wordMultiplier = 1;
    
    for (final word in words) {
      int wordScore = 0;
      
      for (final position in word.positions) {
        final cell = board.getCell(position);
        int letterScore = cell.tile!.points;
        
        // Apply letter multipliers (only for new tiles)
        if (_isNewTile(position, placements)) {
          switch (cell.specialType) {
            case SpecialType.doubleLetter:
              letterScore *= 2;
              break;
            case SpecialType.tripleLetter:
              letterScore *= 3;
              break;
            case SpecialType.doubleWord:
              wordMultiplier *= 2;
              break;
            case SpecialType.tripleWord:
              wordMultiplier *= 3;
              break;
          }
        }
        
        wordScore += letterScore;
      }
      
      totalScore += wordScore * wordMultiplier;
    }
    
    // Bonus for using all 7 tiles
    if (placements.length == 7) {
      totalScore += 50;
    }
    
    return totalScore;
  }
}
```

## Real-time Updates

### WebSocket Integration
```dart
class GameWebSocket {
  late WebSocketChannel _channel;
  final String gameId;
  final Function(GameUpdate) onUpdate;
  
  GameWebSocket({
    required this.gameId,
    required this.onUpdate,
  });
  
  void connect() {
    _channel = WebSocketChannel.connect(
      Uri.parse('ws://localhost:8000/ws/game/$gameId'),
    );
    
    _channel.stream.listen(
      (data) {
        final update = GameUpdate.fromJson(jsonDecode(data));
        onUpdate(update);
      },
      onError: (error) => _handleConnectionError(error),
      onDone: () => _handleConnectionClosed(),
    );
  }
  
  void sendMove(Move move) {
    _channel.sink.add(jsonEncode({
      'type': 'move',
      'data': move.toJson(),
    }));
  }
  
  void disconnect() {
    _channel.sink.close();
  }
}
```

### Game State Synchronization
```dart
class GameStateManager extends ChangeNotifier {
  Game? _currentGame;
  GameWebSocket? _webSocket;
  
  Game? get currentGame => _currentGame;
  
  void joinGame(String gameId) async {
    // Load game state from API
    _currentGame = await GameService.getGame(gameId);
    
    // Connect to WebSocket for real-time updates
    _webSocket = GameWebSocket(
      gameId: gameId,
      onUpdate: _handleGameUpdate,
    );
    _webSocket!.connect();
    
    notifyListeners();
  }
  
  void _handleGameUpdate(GameUpdate update) {
    switch (update.type) {
      case UpdateType.move:
        _currentGame = _currentGame!.applyMove(update.move!);
        break;
      case UpdateType.turnChange:
        _currentGame = _currentGame!.copyWith(
          currentPlayer: update.currentPlayer,
        );
        break;
      case UpdateType.gameEnd:
        _currentGame = _currentGame!.copyWith(
          state: GameState.completed,
          winner: update.winner,
        );
        break;
    }
    
    notifyListeners();
  }
  
  Future<void> makeMove(List<TilePlacement> placements) async {
    // Validate move locally first
    final validation = MoveValidator.validateMove(
      _currentGame!.board,
      placements,
    );
    
    if (!validation.isValid) {
      throw MoveValidationException(validation.error!);
    }
    
    // Send move to server
    final move = Move(
      placements: placements,
      words: validation.words!,
      score: ScoreCalculator.calculateMoveScore(
        _currentGame!.board,
        validation.words!,
        placements,
      ),
    );
    
    _webSocket!.sendMove(move);
  }
}
```

## Game UI Components

### Game Screen Layout
```dart
class GameScreen extends StatefulWidget {
  final String gameId;
  
  @override
  _GameScreenState createState() => _GameScreenState();
}

class _GameScreenState extends State<GameScreen> {
  late GameStateManager _gameManager;
  List<TilePlacement> _pendingPlacements = [];
  
  @override
  void initState() {
    super.initState();
    _gameManager = Provider.of<GameStateManager>(context, listen: false);
    _gameManager.joinGame(widget.gameId);
  }
  
  @override
  Widget build(BuildContext context) {
    return Consumer<GameStateManager>(
      builder: (context, gameManager, child) {
        final game = gameManager.currentGame;
        if (game == null) return LoadingScreen();
        
        return Scaffold(
          appBar: GameAppBar(game: game),
          body: Column(
            children: [
              // Score display
              ScoreDisplay(
                playerScore: game.playerScore,
                opponentScore: game.opponentScore,
              ),
              
              // Game board
              Expanded(
                child: GameBoardWidget(
                  board: game.board,
                  onCellTapped: _handleCellTapped,
                  pendingPlacements: _pendingPlacements,
                ),
              ),
              
              // Tile rack
              TileRackWidget(
                tiles: game.playerTiles,
                onTileTapped: _handleTileTapped,
              ),
              
              // Action buttons
              GameActionButtons(
                canPlay: _pendingPlacements.isNotEmpty,
                onPlay: _submitMove,
                onPass: _passMove,
                onShuffle: _shuffleTiles,
                onUndo: _undoLastPlacement,
              ),
            ],
          ),
        );
      },
    );
  }
  
  void _handleCellTapped(Position position) {
    // Handle tile placement logic
  }
  
  void _submitMove() async {
    try {
      await _gameManager.makeMove(_pendingPlacements);
      setState(() {
        _pendingPlacements.clear();
      });
    } catch (e) {
      _showError(e.toString());
    }
  }
}
```

### Drag and Drop Implementation
```dart
class GameBoardWidget extends StatefulWidget {
  final GameBoard board;
  final Function(Position) onCellTapped;
  final List<TilePlacement> pendingPlacements;
  
  @override
  _GameBoardWidgetState createState() => _GameBoardWidgetState();
}

class _GameBoardWidgetState extends State<GameBoardWidget> {
  @override
  Widget build(BuildContext context) {
    return InteractiveViewer(
      minScale: 0.5,
      maxScale: 2.0,
      child: GridView.builder(
        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: GameBoard.size,
        ),
        itemCount: GameBoard.size * GameBoard.size,
        itemBuilder: (context, index) {
          final row = index ~/ GameBoard.size;
          final col = index % GameBoard.size;
          final position = Position(row, col);
          final cell = widget.board.getCell(position);
          
          return DragTarget<LetterTile>(
            onAccept: (tile) => _placeTile(tile, position),
            onWillAccept: (tile) => _canPlaceTile(position),
            builder: (context, candidateData, rejectedData) {
              return BoardCellWidget(
                cell: cell,
                isHighlighted: candidateData.isNotEmpty,
                onTap: () => widget.onCellTapped(position),
              );
            },
          );
        },
      ),
    );
  }
  
  void _placeTile(LetterTile tile, Position position) {
    // Add to pending placements
    setState(() {
      widget.pendingPlacements.add(
        TilePlacement(tile: tile, position: position),
      );
    });
  }
  
  bool _canPlaceTile(Position position) {
    final cell = widget.board.getCell(position);
    return cell.tile == null && 
           !_hasPendingPlacement(position);
  }
}
```

## Game End Handling

### End Game Detection
```dart
class GameEndDetector {
  static bool isGameEnded(Game game) {
    // Game ends when:
    // 1. All tiles used and tile bag empty
    // 2. Both players pass consecutively
    // 3. Player resigns
    // 4. Time limit exceeded
    
    return game.tilesRemaining == 0 ||
           game.consecutivePasses >= 2 ||
           game.hasResignation ||
           game.isTimeExpired;
  }
  
  static GameResult calculateResult(Game game) {
    int player1Score = game.player1Score;
    int player2Score = game.player2Score;
    
    // Subtract remaining tile values from final score
    if (game.tilesRemaining == 0) {
      final remainingTiles1 = game.player1Tiles;
      final remainingTiles2 = game.player2Tiles;
      
      player1Score -= _calculateTileValue(remainingTiles1);
      player2Score -= _calculateTileValue(remainingTiles2);
      
      // Add opponent's remaining tiles to winner's score
      if (remainingTiles1.isEmpty) {
        player1Score += _calculateTileValue(remainingTiles2);
      } else if (remainingTiles2.isEmpty) {
        player2Score += _calculateTileValue(remainingTiles1);
      }
    }
    
    return GameResult(
      player1Score: player1Score,
      player2Score: player2Score,
      winner: player1Score > player2Score ? game.player1 : game.player2,
      endReason: _determineEndReason(game),
    );
  }
}
```

### Results Screen
```dart
class GameResultsScreen extends StatelessWidget {
  final GameResult result;
  final Game game;
  
  @override
  Widget build(BuildContext context) {
    final isWinner = result.winner.id == game.currentUserId;
    
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Win/lose animation
            AnimatedContainer(
              duration: Duration(seconds: 1),
              child: isWinner 
                ? WinAnimation() 
                : LoseAnimation(),
            ),
            
            // Final scores
            ScoreCard(
              playerScore: result.player1Score,
              opponentScore: result.player2Score,
              isWinner: isWinner,
            ),
            
            // Game statistics
            GameStatsCard(
              duration: game.duration,
              totalMoves: game.moves.length,
              bestWord: _findBestWord(game.moves),
              bestScore: _findBestScore(game.moves),
            ),
            
            // Action buttons
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                ElevatedButton(
                  onPressed: () => _playAgain(),
                  child: Text('Play Again'),
                ),
                ElevatedButton(
                  onPressed: () => _shareResult(),
                  child: Text('Share'),
                ),
              ],
            ),
            
            TextButton(
              onPressed: () => Navigator.of(context).popUntil(
                ModalRoute.withName('/home'),
              ),
              child: Text('Back to Games'),
            ),
          ],
        ),
      ),
    );
  }
}
```

## Performance Optimization

### Board Rendering
- Use `RepaintBoundary` for individual cells
- Implement efficient tile animations
- Cache board state for quick redraws

### Memory Management
- Dispose WebSocket connections properly
- Clear game state when leaving
- Optimize image loading for tiles

### Network Optimization
- Batch multiple tile placements
- Compress game state updates
- Implement offline mode for single-player

## Testing Strategy

### Unit Tests
- Move validation logic
- Score calculation
- Game state transitions
- Tile placement rules

### Widget Tests
- Board interaction
- Tile drag and drop
- UI state updates
- Animation behavior

### Integration Tests
- Full game flow
- WebSocket communication
- Real-time synchronization
- Error handling scenarios 