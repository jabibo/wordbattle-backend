#!/bin/bash
# Organize existing tests into new structure

echo "📦 Organizing tests into new structure..."

# Unit tests - Game Logic
mv test_game_logic.py unit/game_logic/ 2>/dev/null && echo "  ✓ test_game_logic.py → unit/game_logic/"
mv test_letter_bag.py unit/game_logic/ 2>/dev/null && echo "  ✓ test_letter_bag.py → unit/game_logic/"
mv test_round_control.py unit/game_logic/ 2>/dev/null && echo "  ✓ test_round_control.py → unit/game_logic/"
mv test_rack.py unit/game_logic/ 2>/dev/null && echo "  ✓ test_rack.py → unit/game_logic/"
mv test_rack_management.py unit/game_logic/ 2>/dev/null && echo "  ✓ test_rack_management.py → unit/game_logic/"
mv test_score_persistence.py unit/game_logic/ 2>/dev/null && echo "  ✓ test_score_persistence.py → unit/game_logic/"
mv test_move_score.py unit/game_logic/ 2>/dev/null && echo "  ✓ test_move_score.py → unit/game_logic/"

# Unit tests - Models
mv test_player_model.py unit/models/ 2>/dev/null && echo "  ✓ test_player_model.py → unit/models/"

# Unit tests - Utils
mv test_utils.py unit/utils/ 2>/dev/null && echo "  ✓ test_utils.py → unit/utils/"
mv test_error_handling.py unit/utils/ 2>/dev/null && echo "  ✓ test_error_handling.py → unit/utils/"

# Unit tests - Auth
mv test_auth.py unit/auth/ 2>/dev/null && echo "  ✓ test_auth.py → unit/auth/"
mv test_register.py unit/auth/ 2>/dev/null && echo "  ✓ test_register.py → unit/auth/"
mv test_email_auth.py unit/auth/ 2>/dev/null && echo "  ✓ test_email_auth.py → unit/auth/"

# Integration tests - API
mv test_*_api.py integration/api/ 2>/dev/null && echo "  ✓ *_api.py tests → integration/api/"
mv test_endpoints.py integration/api/ 2>/dev/null && echo "  ✓ test_endpoints.py → integration/api/"
mv test_comprehensive_api.py integration/api/ 2>/dev/null && echo "  ✓ test_comprehensive_api.py → integration/api/"
mv test_move_endpoint.py integration/api/ 2>/dev/null && echo "  ✓ test_move_endpoint.py → integration/api/"
mv test_rack_endpoints.py integration/api/ 2>/dev/null && echo "  ✓ test_rack_endpoints.py → integration/api/"
mv test_moves_rack_api.py integration/api/ 2>/dev/null && echo "  ✓ test_moves_rack_api.py → integration/api/"
mv test_gameplay.py integration/api/ 2>/dev/null && echo "  ✓ test_gameplay.py → integration/api/"
mv test_gameplay_auth.py integration/api/ 2>/dev/null && echo "  ✓ test_gameplay_auth.py → integration/api/"
mv test_game_lifecycle.py integration/api/ 2>/dev/null && echo "  ✓ test_game_lifecycle.py → integration/api/"
mv test_game_completion.py integration/api/ 2>/dev/null && echo "  ✓ test_game_completion.py → integration/api/"
mv test_game_language.py integration/api/ 2>/dev/null && echo "  ✓ test_game_language.py → integration/api/"
mv test_chat.py integration/api/ 2>/dev/null && echo "  ✓ test_chat.py → integration/api/"
mv test_profile.py integration/api/ 2>/dev/null && echo "  ✓ test_profile.py → integration/api/"
mv test_user_management.py integration/api/ 2>/dev/null && echo "  ✓ test_user_management.py → integration/api/"

# Integration tests - Database
mv test_database_operations.py integration/database/ 2>/dev/null && echo "  ✓ test_database_operations.py → integration/database/"

# Integration tests - WebSocket
mv test_websocket*.py integration/websocket/ 2>/dev/null && echo "  ✓ test_websocket*.py → integration/websocket/"
mv test_scrabble_connectivity.py integration/websocket/ 2>/dev/null && echo "  ✓ test_scrabble_connectivity.py → integration/websocket/"

echo ""
echo "✅ Test organization complete!"
echo ""
echo "📊 Test structure:"
find . -type d -name "__pycache__" -prune -o -type f -name "test_*.py" -print | sort
