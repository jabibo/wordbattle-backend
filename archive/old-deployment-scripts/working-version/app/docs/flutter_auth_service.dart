import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

/// WordBattle Authentication Service for Flutter
/// 
/// This service handles all authentication operations including:
/// - Email-based registration and login
/// - Verification code handling
/// - Persistent authentication with secure token storage
/// - Auto-login functionality
class WordBattleAuthService extends ChangeNotifier {
  // Configuration
  static const String _baseUrl = 'https://your-api-domain.com'; // Change this to your API URL
  static const FlutterSecureStorage _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(
      encryptedSharedPreferences: true,
    ),
    iOptions: IOSOptions(
      accessibility: IOSAccessibility.first_unlock_this_device,
    ),
  );

  // Storage keys
  static const String _accessTokenKey = 'wb_access_token';
  static const String _persistentTokenKey = 'wb_persistent_token';
  static const String _userDataKey = 'wb_user_data';

  // State
  bool _isLoggedIn = false;
  bool _isLoading = false;
  Map<String, dynamic>? _currentUser;
  String? _accessToken;

  // Getters
  bool get isLoggedIn => _isLoggedIn;
  bool get isLoading => _isLoading;
  Map<String, dynamic>? get currentUser => _currentUser;
  String? get accessToken => _accessToken;

  /// Initialize the auth service and attempt auto-login
  Future<void> initialize() async {
    _setLoading(true);
    
    try {
      // Try to load existing tokens
      _accessToken = await _storage.read(key: _accessTokenKey);
      final userDataString = await _storage.read(key: _userDataKey);
      
      if (userDataString != null) {
        _currentUser = jsonDecode(userDataString);
      }

      // If we have an access token, verify it's still valid
      if (_accessToken != null) {
        final isValid = await _verifyToken();
        if (isValid) {
          _isLoggedIn = true;
        } else {
          // Try auto-login with persistent token
          final success = await _autoLogin();
          _isLoggedIn = success;
        }
      } else {
        // Try auto-login with persistent token
        final success = await _autoLogin();
        _isLoggedIn = success;
      }
    } catch (e) {
      debugPrint('Auth initialization error: $e');
      _isLoggedIn = false;
    } finally {
      _setLoading(false);
    }
  }

  /// Register a new user with email-only authentication
  Future<AuthResult> registerEmailOnly(String username, String email) async {
    _setLoading(true);
    
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/users/register-email-only'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': username,
          'email': email,
        }),
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200) {
        return AuthResult.success(data['message']);
      } else {
        return AuthResult.error(data['detail'] ?? 'Registration failed');
      }
    } catch (e) {
      return AuthResult.error('Network error: $e');
    } finally {
      _setLoading(false);
    }
  }

  /// Register a new user with email and password
  Future<AuthResult> register(String username, String email, String password) async {
    _setLoading(true);
    
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/users/register'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': username,
          'email': email,
          'password': password,
        }),
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200) {
        return AuthResult.success(data['message']);
      } else {
        return AuthResult.error(data['detail'] ?? 'Registration failed');
      }
    } catch (e) {
      return AuthResult.error('Network error: $e');
    } finally {
      _setLoading(false);
    }
  }

  /// Request a verification code to be sent to the email
  Future<AuthResult> requestLoginCode(String email, {bool rememberMe = false}) async {
    _setLoading(true);
    
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/auth/email-login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email,
          'remember_me': rememberMe,
        }),
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200) {
        return AuthResult.success(
          data['message'],
          additionalData: {'expires_in_minutes': data['expires_in_minutes']},
        );
      } else {
        return AuthResult.error(data['detail'] ?? 'Failed to send verification code');
      }
    } catch (e) {
      return AuthResult.error('Network error: $e');
    } finally {
      _setLoading(false);
    }
  }

  /// Verify the email code and complete login
  Future<AuthResult> verifyCode(String email, String code, {bool rememberMe = false}) async {
    _setLoading(true);
    
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/auth/verify-code'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email,
          'verification_code': code,
          'remember_me': rememberMe,
        }),
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200) {
        // Save tokens and user data
        await _saveAuthData(data);
        
        _isLoggedIn = true;
        notifyListeners();
        
        return AuthResult.success('Login successful');
      } else {
        return AuthResult.error(data['detail'] ?? 'Invalid verification code');
      }
    } catch (e) {
      return AuthResult.error('Network error: $e');
    } finally {
      _setLoading(false);
    }
  }

  /// Logout the user and clear all stored data
  Future<void> logout() async {
    _setLoading(true);
    
    try {
      // Call logout endpoint if we have an access token
      if (_accessToken != null) {
        await http.post(
          Uri.parse('$_baseUrl/auth/logout'),
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer $_accessToken',
          },
        );
      }
    } catch (e) {
      debugPrint('Logout API call failed: $e');
    }

    // Clear all stored data
    await _clearAuthData();
    
    _isLoggedIn = false;
    _setLoading(false);
    notifyListeners();
  }

  /// Make an authenticated API request
  Future<http.Response> authenticatedRequest(
    String endpoint, {
    String method = 'GET',
    Map<String, dynamic>? body,
    Map<String, String>? additionalHeaders,
  }) async {
    final headers = {
      'Content-Type': 'application/json',
      if (_accessToken != null) 'Authorization': 'Bearer $_accessToken',
      ...?additionalHeaders,
    };

    final uri = Uri.parse('$_baseUrl$endpoint');

    switch (method.toUpperCase()) {
      case 'GET':
        return await http.get(uri, headers: headers);
      case 'POST':
        return await http.post(
          uri,
          headers: headers,
          body: body != null ? jsonEncode(body) : null,
        );
      case 'PUT':
        return await http.put(
          uri,
          headers: headers,
          body: body != null ? jsonEncode(body) : null,
        );
      case 'DELETE':
        return await http.delete(uri, headers: headers);
      default:
        throw ArgumentError('Unsupported HTTP method: $method');
    }
  }

  // Private methods

  void _setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  Future<bool> _autoLogin() async {
    try {
      final persistentToken = await _storage.read(key: _persistentTokenKey);
      if (persistentToken == null) return false;

      final response = await http.post(
        Uri.parse('$_baseUrl/auth/persistent-login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'persistent_token': persistentToken}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        await _saveAuthData(data);
        return true;
      } else {
        // Invalid persistent token, clear it
        await _storage.delete(key: _persistentTokenKey);
        return false;
      }
    } catch (e) {
      debugPrint('Auto-login failed: $e');
      return false;
    }
  }

  Future<bool> _verifyToken() async {
    if (_accessToken == null) return false;

    try {
      final response = await http.get(
        Uri.parse('$_baseUrl/auth/me'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $_accessToken',
        },
      );

      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  Future<void> _saveAuthData(Map<String, dynamic> data) async {
    // Save access token
    if (data['access_token'] != null) {
      _accessToken = data['access_token'];
      await _storage.write(key: _accessTokenKey, value: _accessToken!);
    }

    // Save persistent token if provided
    if (data['persistent_token'] != null) {
      await _storage.write(key: _persistentTokenKey, value: data['persistent_token']);
    }

    // Save user data
    if (data['user'] != null) {
      _currentUser = data['user'];
      await _storage.write(key: _userDataKey, value: jsonEncode(_currentUser!));
    }
  }

  Future<void> _clearAuthData() async {
    await _storage.delete(key: _accessTokenKey);
    await _storage.delete(key: _persistentTokenKey);
    await _storage.delete(key: _userDataKey);
    
    _accessToken = null;
    _currentUser = null;
  }
}

/// Result class for authentication operations
class AuthResult {
  final bool success;
  final String message;
  final Map<String, dynamic>? additionalData;

  AuthResult._(this.success, this.message, this.additionalData);

  factory AuthResult.success(String message, {Map<String, dynamic>? additionalData}) {
    return AuthResult._(true, message, additionalData);
  }

  factory AuthResult.error(String message) {
    return AuthResult._(false, message, null);
  }
}

/// Extension to make API calls easier
extension AuthServiceExtensions on WordBattleAuthService {
  /// Get current user profile
  Future<Map<String, dynamic>?> getCurrentUserProfile() async {
    try {
      final response = await authenticatedRequest('/auth/me');
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      debugPrint('Failed to get user profile: $e');
    }
    return null;
  }

  /// Create a new game
  Future<Map<String, dynamic>?> createGame({
    String language = 'en',
    int maxPlayers = 2,
  }) async {
    try {
      final response = await authenticatedRequest(
        '/games/',
        method: 'POST',
        body: {
          'language': language,
          'max_players': maxPlayers,
        },
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      debugPrint('Failed to create game: $e');
    }
    return null;
  }

  /// Get game details
  Future<Map<String, dynamic>?> getGame(String gameId) async {
    try {
      final response = await authenticatedRequest('/games/$gameId');
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      debugPrint('Failed to get game: $e');
    }
    return null;
  }

  /// Join a game
  Future<bool> joinGame(String gameId) async {
    try {
      final response = await authenticatedRequest(
        '/games/$gameId/join',
        method: 'POST',
      );
      return response.statusCode == 200;
    } catch (e) {
      debugPrint('Failed to join game: $e');
      return false;
    }
  }
} 