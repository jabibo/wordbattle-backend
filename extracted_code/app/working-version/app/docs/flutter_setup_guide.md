# 📱 Flutter WordBattle App Setup Guide

This guide will help you set up the Flutter mobile app for WordBattle with email authentication.

## 🚀 **Quick Start**

### **1. Prerequisites**

- **Flutter SDK** (3.0.0 or higher)
- **Dart SDK** (included with Flutter)
- **Android Studio** (for Android development)
- **Xcode** (for iOS development, macOS only)
- **VS Code** or **Android Studio** as IDE

### **2. Project Setup**

```bash
# Create new Flutter project
flutter create wordbattle
cd wordbattle

# Replace pubspec.yaml with the provided one
# Copy all the Dart files to appropriate locations
```

### **3. File Structure**

```
lib/
├── main.dart                 # Main app entry point
├── services/
│   └── auth_service.dart     # Authentication service
├── screens/
│   ├── auth/
│   │   ├── login_screen.dart
│   │   ├── register_screen.dart
│   │   └── verification_screen.dart
│   ├── home/
│   │   ├── home_screen.dart
│   │   ├── game_list_screen.dart
│   │   └── profile_screen.dart
│   └── splash_screen.dart
├── widgets/
│   └── auth_wrapper.dart
└── utils/
    └── constants.dart
```

## 📋 **Required Dependencies**

Add these to your `pubspec.yaml`:

```yaml
dependencies:
  flutter:
    sdk: flutter
  provider: ^6.1.1                    # State management
  http: ^1.1.0                        # HTTP requests
  flutter_secure_storage: ^9.0.0      # Secure token storage
  cupertino_icons: ^1.0.6            # iOS-style icons

# Optional but recommended:
  dio: ^5.3.2                         # Better HTTP client
  flutter_local_notifications: ^16.3.0 # Local notifications
  firebase_core: ^2.24.2              # Firebase (for push notifications)
  firebase_messaging: ^14.7.9         # Push notifications
  intl: ^0.19.0                       # Date formatting
```

## 🔧 **Configuration**

### **1. Update API Base URL**

In `auth_service.dart`, update the base URL:

```dart
static const String _baseUrl = 'https://your-api-domain.com'; // Change this!
```

### **2. Android Configuration**

**android/app/src/main/AndroidManifest.xml:**
```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <!-- Internet permission -->
    <uses-permission android:name="android.permission.INTERNET" />
    
    <!-- For secure storage -->
    <uses-permission android:name="android.permission.USE_FINGERPRINT" />
    <uses-permission android:name="android.permission.USE_BIOMETRIC" />
    
    <application
        android:label="WordBattle"
        android:name="${applicationName}"
        android:icon="@mipmap/ic_launcher">
        
        <!-- Main activity -->
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:launchMode="singleTop"
            android:theme="@style/LaunchTheme"
            android:configChanges="orientation|keyboardHidden|keyboard|screenSize|smallestScreenSize|locale|layoutDirection|fontScale|screenLayout|density|uiMode"
            android:hardwareAccelerated="true"
            android:windowSoftInputMode="adjustResize">
            
            <meta-data
              android:name="io.flutter.embedding.android.NormalTheme"
              android:resource="@style/NormalTheme" />
              
            <intent-filter android:autoVerify="true">
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
        
        <!-- Don't delete the meta-data below -->
        <meta-data
            android:name="flutterEmbedding"
            android:value="2" />
    </application>
</manifest>
```

**android/app/build.gradle:**
```gradle
android {
    compileSdkVersion 34
    ndkVersion flutter.ndkVersion

    compileOptions {
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }

    defaultConfig {
        applicationId "com.yourcompany.wordbattle"  // Change this!
        minSdkVersion 21  // Required for secure storage
        targetSdkVersion 34
        versionCode flutterVersionCode.toInteger()
        versionName flutterVersionName
    }
}
```

### **3. iOS Configuration**

**ios/Runner/Info.plist:**
```xml
<dict>
    <!-- App name -->
    <key>CFBundleName</key>
    <string>WordBattle</string>
    
    <!-- Bundle identifier -->
    <key>CFBundleIdentifier</key>
    <string>com.yourcompany.wordbattle</string>  <!-- Change this! -->
    
    <!-- Network permissions -->
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <true/>
    </dict>
    
    <!-- Keychain access for secure storage -->
    <key>keychain-access-groups</key>
    <array>
        <string>$(AppIdentifierPrefix)com.yourcompany.wordbattle</string>
    </array>
</dict>
```

## 🔐 **Security Configuration**

### **Secure Storage Setup**

The app uses `flutter_secure_storage` for token storage. This provides:

- **Android**: EncryptedSharedPreferences with AES encryption
- **iOS**: Keychain Services with hardware-backed security

**Configuration in auth_service.dart:**
```dart
static const FlutterSecureStorage _storage = FlutterSecureStorage(
  aOptions: AndroidOptions(
    encryptedSharedPreferences: true,
  ),
  iOptions: IOSOptions(
    accessibility: IOSAccessibility.first_unlock_this_device,
  ),
);
```

## 🎨 **UI Customization**

### **Color Scheme**
The app uses a dark theme with these colors:
- **Primary**: `#6366F1` (Indigo)
- **Background**: `#1E1E2E` (Dark)
- **Surface**: `#374151` (Gray)
- **Text**: `#FFFFFF` (White)
- **Secondary Text**: `#9CA3AF` (Light Gray)

### **Custom Fonts**
Add Inter font files to `assets/fonts/` and update `pubspec.yaml`:
```yaml
fonts:
  - family: Inter
    fonts:
      - asset: assets/fonts/Inter-Regular.ttf
      - asset: assets/fonts/Inter-Bold.ttf
        weight: 700
```

## 🚀 **Running the App**

### **Development**
```bash
# Get dependencies
flutter pub get

# Run on connected device/emulator
flutter run

# Run in debug mode with hot reload
flutter run --debug

# Run in release mode
flutter run --release
```

### **Building for Production**

**Android APK:**
```bash
flutter build apk --release
```

**Android App Bundle (recommended for Play Store):**
```bash
flutter build appbundle --release
```

**iOS:**
```bash
flutter build ios --release
```

## 🔧 **Backend Integration**

### **API Endpoints Used**

The Flutter app connects to these backend endpoints:

- `POST /users/register-email-only` - Register with email only
- `POST /users/register` - Register with email and password
- `POST /auth/email-login` - Request verification code
- `POST /auth/verify-code` - Verify code and login
- `POST /auth/persistent-login` - Auto-login with persistent token
- `POST /auth/logout` - Logout and invalidate tokens
- `GET /auth/me` - Get current user info
- `POST /games/` - Create new game
- `GET /games/{id}` - Get game details
- `POST /games/{id}/join` - Join game

### **Authentication Flow**

1. **Registration**: User enters username + email
2. **Login Request**: User enters email, receives verification code
3. **Verification**: User enters 6-digit code
4. **Token Storage**: Access token (30min) + persistent token (30 days)
5. **Auto-Login**: App automatically logs in using persistent token

## 📱 **Platform-Specific Features**

### **Android**
- **Biometric Authentication**: Can be added for additional security
- **Background Sync**: For game updates when app is closed
- **Push Notifications**: Firebase Cloud Messaging integration

### **iOS**
- **Face ID/Touch ID**: Native biometric authentication
- **Background App Refresh**: For real-time game updates
- **Apple Push Notifications**: Native iOS notifications

## 🧪 **Testing**

### **Unit Tests**
```bash
flutter test
```

### **Integration Tests**
```bash
flutter drive --target=test_driver/app.dart
```

### **Widget Tests**
Create test files in `test/` directory:
```dart
// test/auth_service_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:wordbattle/services/auth_service.dart';

void main() {
  group('AuthService Tests', () {
    test('should initialize correctly', () {
      final authService = WordBattleAuthService();
      expect(authService.isLoggedIn, false);
    });
  });
}
```

## 🚀 **Deployment**

### **Google Play Store**
1. Create signed APK/App Bundle
2. Upload to Google Play Console
3. Configure app details and screenshots
4. Submit for review

### **Apple App Store**
1. Build iOS app in Xcode
2. Archive and upload to App Store Connect
3. Configure app metadata
4. Submit for review

## 🔍 **Troubleshooting**

### **Common Issues**

**1. Secure Storage Issues:**
```bash
# Clear app data if storage is corrupted
flutter clean
flutter pub get
```

**2. Network Issues:**
- Check API base URL configuration
- Verify internet permissions in manifests
- Test with real device (not just emulator)

**3. Build Issues:**
```bash
# Clean and rebuild
flutter clean
flutter pub get
flutter pub deps
flutter build apk
```

**4. iOS Keychain Issues:**
- Reset iOS Simulator: Device → Erase All Content and Settings
- Check bundle identifier matches in Info.plist

### **Debug Mode**

Enable debug logging in `auth_service.dart`:
```dart
import 'package:flutter/foundation.dart';

// Add this for debug prints
if (kDebugMode) {
  print('Auth debug: $message');
}
```

## 📚 **Additional Resources**

- [Flutter Documentation](https://docs.flutter.dev/)
- [Flutter Secure Storage](https://pub.dev/packages/flutter_secure_storage)
- [Provider State Management](https://pub.dev/packages/provider)
- [HTTP Package](https://pub.dev/packages/http)

## 🎯 **Next Steps**

1. **Game Logic**: Implement actual game screens and logic
2. **Real-time Updates**: Add WebSocket support for live games
3. **Push Notifications**: Implement Firebase messaging
4. **Offline Support**: Add local storage for offline play
5. **Social Features**: Add friend lists and chat
6. **Analytics**: Add Firebase Analytics or similar

---

Your Flutter WordBattle app is now ready for development! The authentication system is fully integrated with your backend API and provides a secure, modern mobile experience. 🎮📱 