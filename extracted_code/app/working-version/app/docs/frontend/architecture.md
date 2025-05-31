# Technical Architecture

## Overview

The WordBattle Flutter app follows a clean architecture pattern with clear separation of concerns, ensuring maintainability, testability, and scalability.

## Architecture Layers

```
┌─────────────────────────────────────────┐
│              Presentation               │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │   Screens   │  │     Widgets     │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│            Business Logic               │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │  Providers  │  │   Use Cases     │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│                Data                     │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │ Repositories│  │   Data Sources  │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────┘
```

## Project Structure

```
lib/
├── main.dart
├── app/
│   ├── app.dart
│   ├── routes.dart
│   └── theme.dart
├── core/
│   ├── constants/
│   ├── errors/
│   ├── network/
│   ├── storage/
│   └── utils/
├── features/
│   ├── auth/
│   │   ├── data/
│   │   ├── domain/
│   │   └── presentation/
│   ├── game/
│   │   ├── data/
│   │   ├── domain/
│   │   └── presentation/
│   ├── profile/
│   │   ├── data/
│   │   ├── domain/
│   │   └── presentation/
│   └── social/
│       ├── data/
│       ├── domain/
│       └── presentation/
└── shared/
    ├── widgets/
    ├── models/
    └── services/
```

## Core Components

### 1. Network Layer

```dart
// core/network/api_client.dart
class ApiClient {
  static const String baseUrl = 'http://localhost:8000';
  final http.Client _client;
  final TokenStorage _tokenStorage;
  
  ApiClient({
    required http.Client client,
    required TokenStorage tokenStorage,
  }) : _client = client, _tokenStorage = tokenStorage;
  
  Future<ApiResponse<T>> get<T>(
    String endpoint, {
    Map<String, String>? queryParams,
    T Function(Map<String, dynamic>)? fromJson,
  }) async {
    try {
      final uri = _buildUri(endpoint, queryParams);
      final headers = await _buildHeaders();
      
      final response = await _client.get(uri, headers: headers);
      return _handleResponse<T>(response, fromJson);
    } catch (e) {
      return ApiResponse.error(NetworkException(e.toString()));
    }
  }
  
  Future<ApiResponse<T>> post<T>(
    String endpoint, {
    Map<String, dynamic>? body,
    T Function(Map<String, dynamic>)? fromJson,
  }) async {
    try {
      final uri = _buildUri(endpoint);
      final headers = await _buildHeaders();
      
      final response = await _client.post(
        uri,
        headers: headers,
        body: body != null ? jsonEncode(body) : null,
      );
      
      return _handleResponse<T>(response, fromJson);
    } catch (e) {
      return ApiResponse.error(NetworkException(e.toString()));
    }
  }
  
  Future<Map<String, String>> _buildHeaders() async {
    final headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    
    final token = await _tokenStorage.getAccessToken();
    if (token != null) {
      headers['Authorization'] = 'Bearer $token';
    }
    
    return headers;
  }
  
  ApiResponse<T> _handleResponse<T>(
    http.Response response,
    T Function(Map<String, dynamic>)? fromJson,
  ) {
    switch (response.statusCode) {
      case 200:
      case 201:
        if (fromJson != null) {
          final data = jsonDecode(response.body);
          return ApiResponse.success(fromJson(data));
        }
        return ApiResponse.success(null);
      case 401:
        return ApiResponse.error(UnauthorizedException());
      case 404:
        return ApiResponse.error(NotFoundException());
      case 422:
        final data = jsonDecode(response.body);
        return ApiResponse.error(ValidationException(data['detail']));
      default:
        return ApiResponse.error(ServerException(response.statusCode));
    }
  }
}
```

### 2. Storage Layer

```dart
// core/storage/token_storage.dart
class TokenStorage {
  static const FlutterSecureStorage _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(
      encryptedSharedPreferences: true,
    ),
    iOptions: IOSOptions(
      accessibility: IOSAccessibility.first_unlock_this_device,
    ),
  );
  
  static const String _accessTokenKey = 'wb_access_token';
  static const String _persistentTokenKey = 'wb_persistent_token';
  static const String _userDataKey = 'wb_user_data';
  
  Future<void> storeTokens({
    required String accessToken,
    String? persistentToken,
  }) async {
    await _storage.write(key: _accessTokenKey, value: accessToken);
    if (persistentToken != null) {
      await _storage.write(key: _persistentTokenKey, value: persistentToken);
    }
  }
  
  Future<String?> getAccessToken() async {
    return await _storage.read(key: _accessTokenKey);
  }
  
  Future<String?> getPersistentToken() async {
    return await _storage.read(key: _persistentTokenKey);
  }
  
  Future<void> storeUserData(User user) async {
    await _storage.write(key: _userDataKey, value: jsonEncode(user.toJson()));
  }
  
  Future<User?> getUserData() async {
    final userData = await _storage.read(key: _userDataKey);
    if (userData != null) {
      return User.fromJson(jsonDecode(userData));
    }
    return null;
  }
  
  Future<void> clearAll() async {
    await _storage.deleteAll();
  }
}
```

### 3. Error Handling

```dart
// core/errors/exceptions.dart
abstract class AppException implements Exception {
  final String message;
  final String? code;
  
  const AppException(this.message, [this.code]);
  
  @override
  String toString() => message;
}

class NetworkException extends AppException {
  const NetworkException(String message) : super(message, 'NETWORK_ERROR');
}

class UnauthorizedException extends AppException {
  const UnauthorizedException() : super('Unauthorized access', 'UNAUTHORIZED');
}

class ValidationException extends AppException {
  const ValidationException(String message) : super(message, 'VALIDATION_ERROR');
}

class GameException extends AppException {
  const GameException(String message) : super(message, 'GAME_ERROR');
}

// core/errors/failure.dart
abstract class Failure {
  final String message;
  final String? code;
  
  const Failure(this.message, [this.code]);
}

class NetworkFailure extends Failure {
  const NetworkFailure(String message) : super(message, 'NETWORK_FAILURE');
}

class AuthFailure extends Failure {
  const AuthFailure(String message) : super(message, 'AUTH_FAILURE');
}

class GameFailure extends Failure {
  const GameFailure(String message) : super(message, 'GAME_FAILURE');
}
```

## Feature Architecture

### Authentication Feature

```dart
// features/auth/domain/entities/user.dart
class User {
  final String id;
  final String username;
  final String email;
  final String? displayName;
  final String? avatarUrl;
  final DateTime createdAt;
  final DateTime? lastLogin;
  
  const User({
    required this.id,
    required this.username,
    required this.email,
    this.displayName,
    this.avatarUrl,
    required this.createdAt,
    this.lastLogin,
  });
  
  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      username: json['username'],
      email: json['email'],
      displayName: json['display_name'],
      avatarUrl: json['avatar_url'],
      createdAt: DateTime.parse(json['created_at']),
      lastLogin: json['last_login'] != null 
        ? DateTime.parse(json['last_login']) 
        : null,
    );
  }
  
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'username': username,
      'email': email,
      'display_name': displayName,
      'avatar_url': avatarUrl,
      'created_at': createdAt.toIso8601String(),
      'last_login': lastLogin?.toIso8601String(),
    };
  }
}

// features/auth/domain/repositories/auth_repository.dart
abstract class AuthRepository {
  Future<Either<Failure, User>> register({
    required String username,
    required String email,
  });
  
  Future<Either<Failure, void>> requestLoginCode(String email);
  
  Future<Either<Failure, AuthTokens>> verifyCode({
    required String email,
    required String code,
  });
  
  Future<Either<Failure, AuthTokens>> persistentLogin(String token);
  
  Future<Either<Failure, void>> logout();
}

// features/auth/data/repositories/auth_repository_impl.dart
class AuthRepositoryImpl implements AuthRepository {
  final AuthRemoteDataSource remoteDataSource;
  final TokenStorage tokenStorage;
  
  AuthRepositoryImpl({
    required this.remoteDataSource,
    required this.tokenStorage,
  });
  
  @override
  Future<Either<Failure, User>> register({
    required String username,
    required String email,
  }) async {
    try {
      final user = await remoteDataSource.register(
        username: username,
        email: email,
      );
      return Right(user);
    } on AppException catch (e) {
      return Left(AuthFailure(e.message));
    }
  }
  
  @override
  Future<Either<Failure, AuthTokens>> verifyCode({
    required String email,
    required String code,
  }) async {
    try {
      final tokens = await remoteDataSource.verifyCode(
        email: email,
        code: code,
      );
      
      await tokenStorage.storeTokens(
        accessToken: tokens.accessToken,
        persistentToken: tokens.persistentToken,
      );
      
      return Right(tokens);
    } on AppException catch (e) {
      return Left(AuthFailure(e.message));
    }
  }
}

// features/auth/presentation/providers/auth_provider.dart
class AuthProvider extends ChangeNotifier {
  final AuthRepository _authRepository;
  final TokenStorage _tokenStorage;
  
  AuthState _state = AuthState.initial;
  User? _currentUser;
  String? _errorMessage;
  
  AuthProvider({
    required AuthRepository authRepository,
    required TokenStorage tokenStorage,
  }) : _authRepository = authRepository, _tokenStorage = tokenStorage;
  
  AuthState get state => _state;
  User? get currentUser => _currentUser;
  String? get errorMessage => _errorMessage;
  bool get isAuthenticated => _state == AuthState.authenticated;
  
  Future<void> initialize() async {
    _setState(AuthState.initial);
    
    final persistentToken = await _tokenStorage.getPersistentToken();
    if (persistentToken != null) {
      await _attemptPersistentLogin(persistentToken);
    } else {
      _setState(AuthState.unauthenticated);
    }
  }
  
  Future<void> register({
    required String username,
    required String email,
  }) async {
    _setState(AuthState.authenticating);
    
    final result = await _authRepository.register(
      username: username,
      email: email,
    );
    
    result.fold(
      (failure) => _setError(failure.message),
      (user) {
        _currentUser = user;
        _setState(AuthState.registered);
      },
    );
  }
  
  Future<void> requestLoginCode(String email) async {
    _setState(AuthState.authenticating);
    
    final result = await _authRepository.requestLoginCode(email);
    
    result.fold(
      (failure) => _setError(failure.message),
      (_) => _setState(AuthState.codeRequested),
    );
  }
  
  Future<void> verifyCode({
    required String email,
    required String code,
  }) async {
    _setState(AuthState.authenticating);
    
    final result = await _authRepository.verifyCode(
      email: email,
      code: code,
    );
    
    result.fold(
      (failure) => _setError(failure.message),
      (tokens) {
        _currentUser = tokens.user;
        _setState(AuthState.authenticated);
      },
    );
  }
  
  Future<void> logout() async {
    await _authRepository.logout();
    await _tokenStorage.clearAll();
    _currentUser = null;
    _setState(AuthState.unauthenticated);
  }
  
  void _setState(AuthState newState) {
    _state = newState;
    _errorMessage = null;
    notifyListeners();
  }
  
  void _setError(String message) {
    _errorMessage = message;
    _state = AuthState.error;
    notifyListeners();
  }
  
  Future<void> _attemptPersistentLogin(String token) async {
    final result = await _authRepository.persistentLogin(token);
    
    result.fold(
      (failure) {
        _tokenStorage.clearAll();
        _setState(AuthState.unauthenticated);
      },
      (tokens) {
        _currentUser = tokens.user;
        _setState(AuthState.authenticated);
      },
    );
  }
}
```

## State Management

### Provider Pattern Implementation

```dart
// app/providers.dart
class AppProviders {
  static List<ChangeNotifierProvider> get providers => [
    ChangeNotifierProvider<AuthProvider>(
      create: (context) => GetIt.instance<AuthProvider>(),
    ),
    ChangeNotifierProvider<GameProvider>(
      create: (context) => GetIt.instance<GameProvider>(),
    ),
    ChangeNotifierProvider<ProfileProvider>(
      create: (context) => GetIt.instance<ProfileProvider>(),
    ),
    ChangeNotifierProvider<SocialProvider>(
      create: (context) => GetIt.instance<SocialProvider>(),
    ),
  ];
}

// Usage in main.dart
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await setupDependencies();
  
  runApp(
    MultiProvider(
      providers: AppProviders.providers,
      child: WordBattleApp(),
    ),
  );
}
```

### Dependency Injection

```dart
// core/di/injection.dart
final GetIt getIt = GetIt.instance;

Future<void> setupDependencies() async {
  // External dependencies
  getIt.registerLazySingleton<http.Client>(() => http.Client());
  getIt.registerLazySingleton<TokenStorage>(() => TokenStorage());
  
  // Core services
  getIt.registerLazySingleton<ApiClient>(
    () => ApiClient(
      client: getIt<http.Client>(),
      tokenStorage: getIt<TokenStorage>(),
    ),
  );
  
  // Data sources
  getIt.registerLazySingleton<AuthRemoteDataSource>(
    () => AuthRemoteDataSourceImpl(apiClient: getIt<ApiClient>()),
  );
  
  getIt.registerLazySingleton<GameRemoteDataSource>(
    () => GameRemoteDataSourceImpl(apiClient: getIt<ApiClient>()),
  );
  
  // Repositories
  getIt.registerLazySingleton<AuthRepository>(
    () => AuthRepositoryImpl(
      remoteDataSource: getIt<AuthRemoteDataSource>(),
      tokenStorage: getIt<TokenStorage>(),
    ),
  );
  
  getIt.registerLazySingleton<GameRepository>(
    () => GameRepositoryImpl(
      remoteDataSource: getIt<GameRemoteDataSource>(),
    ),
  );
  
  // Providers
  getIt.registerFactory<AuthProvider>(
    () => AuthProvider(
      authRepository: getIt<AuthRepository>(),
      tokenStorage: getIt<TokenStorage>(),
    ),
  );
  
  getIt.registerFactory<GameProvider>(
    () => GameProvider(
      gameRepository: getIt<GameRepository>(),
    ),
  );
}
```

## Navigation Architecture

```dart
// app/routes.dart
class AppRoutes {
  static const String splash = '/';
  static const String welcome = '/welcome';
  static const String login = '/login';
  static const String register = '/register';
  static const String verification = '/verification';
  static const String home = '/home';
  static const String profile = '/profile';
  static const String settings = '/settings';
  static const String gameList = '/games';
  static const String gameBoard = '/game';
  static const String gameResults = '/game/results';
  static const String friends = '/friends';
  
  static Route<dynamic> generateRoute(RouteSettings settings) {
    switch (settings.name) {
      case splash:
        return MaterialPageRoute(builder: (_) => SplashScreen());
      case welcome:
        return MaterialPageRoute(builder: (_) => WelcomeScreen());
      case login:
        return MaterialPageRoute(builder: (_) => LoginScreen());
      case register:
        return MaterialPageRoute(builder: (_) => RegisterScreen());
      case verification:
        final args = settings.arguments as VerificationArgs;
        return MaterialPageRoute(
          builder: (_) => VerificationScreen(email: args.email),
        );
      case home:
        return MaterialPageRoute(builder: (_) => HomeScreen());
      case gameBoard:
        final args = settings.arguments as GameArgs;
        return MaterialPageRoute(
          builder: (_) => GameScreen(gameId: args.gameId),
        );
      default:
        return MaterialPageRoute(
          builder: (_) => Scaffold(
            body: Center(
              child: Text('Route not found: ${settings.name}'),
            ),
          ),
        );
    }
  }
}

// Navigation service
class NavigationService {
  static final GlobalKey<NavigatorState> navigatorKey = 
      GlobalKey<NavigatorState>();
  
  static NavigatorState? get navigator => navigatorKey.currentState;
  
  static Future<T?> pushNamed<T>(String routeName, {Object? arguments}) {
    return navigator!.pushNamed<T>(routeName, arguments: arguments);
  }
  
  static Future<T?> pushReplacementNamed<T>(String routeName, {Object? arguments}) {
    return navigator!.pushReplacementNamed<T>(routeName, arguments: arguments);
  }
  
  static void pop<T>([T? result]) {
    return navigator!.pop<T>(result);
  }
  
  static Future<T?> pushNamedAndClearStack<T>(String routeName, {Object? arguments}) {
    return navigator!.pushNamedAndRemoveUntil<T>(
      routeName,
      (route) => false,
      arguments: arguments,
    );
  }
}
```

## Theme and Styling

```dart
// app/theme.dart
class AppTheme {
  static const Color primaryColor = Color(0xFF2196F3);
  static const Color secondaryColor = Color(0xFF03DAC6);
  static const Color errorColor = Color(0xFFB00020);
  static const Color backgroundColor = Color(0xFF121212);
  static const Color surfaceColor = Color(0xFF1E1E1E);
  
  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      primarySwatch: Colors.blue,
      primaryColor: primaryColor,
      colorScheme: ColorScheme.dark(
        primary: primaryColor,
        secondary: secondaryColor,
        error: errorColor,
        background: backgroundColor,
        surface: surfaceColor,
      ),
      scaffoldBackgroundColor: backgroundColor,
      appBarTheme: AppBarTheme(
        backgroundColor: surfaceColor,
        elevation: 0,
        titleTextStyle: TextStyle(
          color: Colors.white,
          fontSize: 20,
          fontWeight: FontWeight.w600,
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primaryColor,
          foregroundColor: Colors.white,
          padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surfaceColor,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(color: primaryColor),
        ),
      ),
      cardTheme: CardTheme(
        color: surfaceColor,
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
    );
  }
}
```

## Performance Optimization

### Image Caching

```dart
// core/utils/image_cache.dart
class ImageCacheManager {
  static final CachedNetworkImageProvider _provider = 
      CachedNetworkImageProvider('');
  
  static Widget cachedImage(
    String url, {
    double? width,
    double? height,
    BoxFit fit = BoxFit.cover,
    Widget? placeholder,
    Widget? errorWidget,
  }) {
    return CachedNetworkImage(
      imageUrl: url,
      width: width,
      height: height,
      fit: fit,
      placeholder: (context, url) => placeholder ?? 
          Center(child: CircularProgressIndicator()),
      errorWidget: (context, url, error) => errorWidget ?? 
          Icon(Icons.error),
      memCacheWidth: width?.toInt(),
      memCacheHeight: height?.toInt(),
    );
  }
}
```

### Memory Management

```dart
// core/utils/memory_manager.dart
class MemoryManager {
  static void clearImageCache() {
    PaintingBinding.instance.imageCache.clear();
    PaintingBinding.instance.imageCache.clearLiveImages();
  }
  
  static void optimizeMemory() {
    // Clear image cache if memory usage is high
    if (_isMemoryUsageHigh()) {
      clearImageCache();
    }
    
    // Force garbage collection
    GCUtils.gc();
  }
  
  static bool _isMemoryUsageHigh() {
    // Implementation depends on platform-specific memory monitoring
    return false;
  }
}
```

## Testing Architecture

### Unit Test Structure

```dart
// test/features/auth/domain/usecases/login_test.dart
void main() {
  late AuthRepository mockAuthRepository;
  late LoginUseCase loginUseCase;
  
  setUp(() {
    mockAuthRepository = MockAuthRepository();
    loginUseCase = LoginUseCase(mockAuthRepository);
  });
  
  group('LoginUseCase', () {
    test('should return AuthTokens when login is successful', () async {
      // Arrange
      const email = 'test@example.com';
      const code = '123456';
      final expectedTokens = AuthTokens(
        accessToken: 'access_token',
        persistentToken: 'persistent_token',
        user: User(id: '1', username: 'test', email: email),
      );
      
      when(mockAuthRepository.verifyCode(
        email: email,
        code: code,
      )).thenAnswer((_) async => Right(expectedTokens));
      
      // Act
      final result = await loginUseCase(email: email, code: code);
      
      // Assert
      expect(result, Right(expectedTokens));
      verify(mockAuthRepository.verifyCode(email: email, code: code));
    });
  });
}
```

### Widget Test Structure

```dart
// test/features/auth/presentation/screens/login_screen_test.dart
void main() {
  late MockAuthProvider mockAuthProvider;
  
  setUp(() {
    mockAuthProvider = MockAuthProvider();
  });
  
  Widget createWidgetUnderTest() {
    return MaterialApp(
      home: ChangeNotifierProvider<AuthProvider>.value(
        value: mockAuthProvider,
        child: LoginScreen(),
      ),
    );
  }
  
  group('LoginScreen', () {
    testWidgets('should display email input field', (tester) async {
      // Arrange
      when(mockAuthProvider.state).thenReturn(AuthState.unauthenticated);
      
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      
      // Assert
      expect(find.byType(TextFormField), findsOneWidget);
      expect(find.text('Email Address'), findsOneWidget);
    });
    
    testWidgets('should call requestLoginCode when button is pressed', (tester) async {
      // Arrange
      when(mockAuthProvider.state).thenReturn(AuthState.unauthenticated);
      
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.enterText(find.byType(TextFormField), 'test@example.com');
      await tester.tap(find.text('Send Login Code'));
      await tester.pump();
      
      // Assert
      verify(mockAuthProvider.requestLoginCode('test@example.com'));
    });
  });
}
```

## Security Considerations

### Token Security

```dart
// core/security/token_security.dart
class TokenSecurity {
  static bool isTokenExpired(String token) {
    try {
      final payload = _decodeJwtPayload(token);
      final exp = payload['exp'] as int;
      final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;
      return exp < now;
    } catch (e) {
      return true; // Assume expired if can't decode
    }
  }
  
  static Map<String, dynamic> _decodeJwtPayload(String token) {
    final parts = token.split('.');
    if (parts.length != 3) {
      throw FormatException('Invalid JWT format');
    }
    
    final payload = parts[1];
    final normalized = base64Url.normalize(payload);
    final decoded = utf8.decode(base64Url.decode(normalized));
    return jsonDecode(decoded);
  }
  
  static void clearSensitiveData() {
    // Clear any sensitive data from memory
    // This is called when app goes to background
  }
}
```

### Input Validation

```dart
// core/validation/validators.dart
class Validators {
  static String? validateEmail(String? value) {
    if (value == null || value.isEmpty) {
      return 'Email is required';
    }
    
    final emailRegex = RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$');
    if (!emailRegex.hasMatch(value)) {
      return 'Please enter a valid email address';
    }
    
    return null;
  }
  
  static String? validateUsername(String? value) {
    if (value == null || value.isEmpty) {
      return 'Username is required';
    }
    
    if (value.length < 3 || value.length > 20) {
      return 'Username must be between 3 and 20 characters';
    }
    
    final usernameRegex = RegExp(r'^[a-zA-Z0-9_]+$');
    if (!usernameRegex.hasMatch(value)) {
      return 'Username can only contain letters, numbers, and underscores';
    }
    
    return null;
  }
  
  static String? validateVerificationCode(String? value) {
    if (value == null || value.isEmpty) {
      return 'Verification code is required';
    }
    
    if (value.length != 6) {
      return 'Verification code must be 6 digits';
    }
    
    final codeRegex = RegExp(r'^\d{6}$');
    if (!codeRegex.hasMatch(value)) {
      return 'Verification code must contain only numbers';
    }
    
    return null;
  }
}
```

This technical architecture provides a solid foundation for the WordBattle Flutter app with proper separation of concerns, testability, and maintainability. 