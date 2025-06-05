# WordBattle Flutter App Documentation

## Overview

WordBattle is a mobile word game application built with Flutter for iOS and Android. The app features email-based authentication, real-time multiplayer gameplay, and a modern, intuitive user interface.

## Key Features

- **Email-Only Authentication**: Passwordless login using verification codes
- **Real-time Multiplayer**: Play Scrabble-like games with friends
- **Cross-Platform**: Native iOS and Android apps
- **Secure Storage**: Hardware-backed token storage
- **Modern UI**: Dark theme with smooth animations
- **Offline Capability**: Local game state management

## Architecture

- **Frontend**: Flutter (Dart)
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Authentication**: JWT tokens with email verification
- **Storage**: FlutterSecureStorage (Keychain/EncryptedSharedPreferences)
- **State Management**: Provider pattern with ChangeNotifier

## Documentation Structure

- [App Concept & User Flow](./app-concept.md) - Overall app concept and user journey
- [Screen Specifications](./screens.md) - Detailed screen layouts and functionality
- [Authentication Flow](./authentication.md) - Email-based auth process
- [Game Flow](./game-flow.md) - Gameplay mechanics and screens
- [Technical Architecture](./architecture.md) - Technical implementation details
- [UI/UX Guidelines](./ui-guidelines.md) - Design system and components

## Quick Start

1. Review the [App Concept](./app-concept.md) for overall understanding
2. Check [Screen Specifications](./screens.md) for detailed UI requirements
3. Follow [Authentication Flow](./authentication.md) for login implementation
4. Implement [Game Flow](./game-flow.md) for core gameplay

## Target Platforms

- **iOS**: 12.0+
- **Android**: API 21+ (Android 5.0)
- **Flutter**: 3.0+
- **Dart**: 2.17+ 