# Screen Specifications

## Screen Overview

The WordBattle app consists of 12 main screens organized into 4 main flows:

1. **Authentication Flow**: Splash, Welcome, Login, Registration, Verification
2. **Main App Flow**: Home, Profile, Settings
3. **Game Flow**: Game List, Game Board, Game Results
4. **Social Flow**: Friends, Invitations

## Authentication Screens

### 1. Splash Screen
**Purpose**: App initialization and auto-login attempt

**Layout**:
```
┌─────────────────────────┐
│                         │
│                         │
│      [WordBattle]       │
│         Logo            │
│                         │
│    [Loading Spinner]    │
│                         │
│                         │
└─────────────────────────┘
```

**Components**:
- WordBattle logo (centered)
- Subtle loading animation
- App version number (bottom)

**Functionality**:
- Auto-login attempt using persistent token
- Navigate to Home if successful
- Navigate to Welcome if no token or expired
- 2-second minimum display time

**States**:
- Loading: Show spinner
- Success: Fade to Home screen
- Error: Fade to Welcome screen

---

### 2. Welcome Screen
**Purpose**: First-time user introduction

**Layout**:
```
┌─────────────────────────┐
│                         │
│      [WordBattle]       │
│         Logo            │
│                         │
│   "Welcome to the most  │
│    fun word game!"      │
│                         │
│   [Illustration of      │
│    game board]          │
│                         │
│    [Get Started]        │
│                         │
│  "Already have account? │
│       [Sign In]"        │
└─────────────────────────┘
```

**Components**:
- App logo and tagline
- Attractive game illustration
- Primary "Get Started" button
- Secondary "Sign In" link

**Functionality**:
- "Get Started" → Registration screen
- "Sign In" → Login screen
- Smooth animations on load

---

### 3. Registration Screen
**Purpose**: New user account creation

**Layout**:
```
┌─────────────────────────┐
│    [←] Create Account   │
│                         │
│   "Join WordBattle"     │
│                         │
│  ┌─────────────────┐    │
│  │ Username        │    │
│  └─────────────────┘    │
│                         │
│  ┌─────────────────┐    │
│  │ Email Address   │    │
│  └─────────────────┘    │
│                         │
│    [Create Account]     │
│                         │
│  "By signing up, you    │
│   agree to our Terms"   │
│                         │
│  "Already registered?   │
│      [Sign In]"         │
└─────────────────────────┘
```

**Components**:
- Back button (top-left)
- Username input field
- Email input field
- Create Account button
- Terms agreement text
- Sign In link

**Functionality**:
- Input validation (username 3-20 chars, valid email)
- Real-time validation feedback
- API call to register endpoint
- Navigate to Verification on success
- Error handling with user-friendly messages

**Validation Rules**:
- Username: 3-20 characters, alphanumeric + underscore
- Email: Valid email format
- Both fields required

---

### 4. Login Screen
**Purpose**: Existing user authentication

**Layout**:
```
┌─────────────────────────┐
│    [←] Sign In          │
│                         │
│   "Welcome back!"       │
│                         │
│  ┌─────────────────┐    │
│  │ Email Address   │    │
│  └─────────────────┘    │
│                         │
│  ☐ Remember me          │
│                         │
│    [Send Login Code]    │
│                         │
│                         │
│  "Don't have account?   │
│     [Sign Up]"          │
└─────────────────────────┘
```

**Components**:
- Back button
- Email input field
- "Remember me" checkbox
- Send Login Code button
- Sign Up link

**Functionality**:
- Email validation
- Remember me option (persistent token)
- API call to request verification code
- Navigate to Verification screen
- Show success message about email sent

---

### 5. Verification Screen
**Purpose**: Email verification code entry

**Layout**:
```
┌─────────────────────────┐
│    [←] Verify Email     │
│                         │
│  "Enter the 6-digit     │
│   code sent to:"        │
│   user@example.com      │
│                         │
│  ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐│
│  │ │ │ │ │ │ │ │ │ │ │ ││
│  └─┘ └─┘ └─┘ └─┘ └─┘ └─┘│
│                         │
│     [Verify Code]       │
│                         │
│  "Didn't receive code?  │
│     [Resend Code]"      │
│                         │
│   "Code expires in      │
│      09:45"             │
└─────────────────────────┘
```

**Components**:
- Back button
- Email display
- 6-digit code input boxes
- Verify Code button
- Resend Code link
- Countdown timer

**Functionality**:
- Auto-focus next input box
- Auto-submit when 6 digits entered
- Countdown timer (10 minutes)
- Resend code functionality
- Navigate to Home on success
- Clear inputs on error

---

## Main App Screens

### 6. Home Screen
**Purpose**: Main dashboard and navigation hub

**Layout**:
```
┌─────────────────────────┐
│ WordBattle    [Profile] │
│                         │
│  "Welcome back, John!"  │
│                         │
│ ┌─ Active Games ──────┐ │
│ │ vs Sarah    [Your]  │ │
│ │ vs Mike     [Their] │ │
│ │ vs Emma     [Your]  │ │
│ └─────────────────────┘ │
│                         │
│    [+ New Game]         │
│                         │
│ ┌─ Quick Actions ─────┐ │
│ │ [Friends] [Stats]   │ │
│ │ [Settings] [Help]   │ │
│ └─────────────────────┘ │
└─────────────────────────┘
```

**Components**:
- App title and profile button
- Welcome message with username
- Active games list with turn indicators
- New Game button (prominent)
- Quick action buttons grid

**Functionality**:
- Pull-to-refresh for game updates
- Tap game to open Game Board
- Real-time turn notifications
- Badge counts for pending actions

---

### 7. Profile Screen
**Purpose**: User profile and statistics

**Layout**:
```
┌─────────────────────────┐
│    [←] Profile  [Edit]  │
│                         │
│     [Avatar Image]      │
│      John Smith         │
│   john@example.com      │
│                         │
│ ┌─ Statistics ────────┐ │
│ │ Games Played:   42  │ │
│ │ Games Won:      28  │ │
│ │ Win Rate:      67%  │ │
│ │ Best Score:    156  │ │
│ │ Avg Score:      89  │ │
│ └─────────────────────┘ │
│                         │
│ ┌─ Achievements ──────┐ │
│ │ 🏆 First Win        │ │
│ │ 🎯 High Scorer      │ │
│ │ 📚 Word Master      │ │
│ └─────────────────────┘ │
└─────────────────────────┘
```

**Components**:
- Back and Edit buttons
- Avatar image (tappable)
- Username and email
- Statistics cards
- Achievements list

**Functionality**:
- Edit profile information
- Change avatar image
- View detailed statistics
- Achievement progress tracking

---

### 8. Settings Screen
**Purpose**: App configuration and preferences

**Layout**:
```
┌─────────────────────────┐
│    [←] Settings         │
│                         │
│ ┌─ Account ───────────┐ │
│ │ Change Email     >  │ │
│ │ Privacy Settings >  │ │
│ │ Delete Account   >  │ │
│ └─────────────────────┘ │
│                         │
│ ┌─ Game Settings ─────┐ │
│ │ Language        EN  │ │
│ │ Notifications   ON  │ │
│ │ Sound Effects   ON  │ │
│ │ Vibration       ON  │ │
│ └─────────────────────┘ │
│                         │
│ ┌─ Support ───────────┐ │
│ │ Help & FAQ       >  │ │
│ │ Contact Support  >  │ │
│ │ Rate App         >  │ │
│ └─────────────────────┘ │
│                         │
│     [Sign Out]          │
└─────────────────────────┘
```

**Components**:
- Grouped settings sections
- Toggle switches for preferences
- Navigation arrows for sub-screens
- Sign Out button (bottom)

**Functionality**:
- Save preferences locally
- Sync settings with backend
- Confirmation dialogs for destructive actions
- Deep linking to system settings

---

## Game Screens

### 9. Game List Screen
**Purpose**: Overview of all user's games

**Layout**:
```
┌─────────────────────────┐
│    [←] Games   [Filter] │
│                         │
│ ┌─ Your Turn (2) ─────┐ │
│ │ vs Sarah    Score   │ │
│ │ 89 - 76     [Play]  │ │
│ │                     │ │
│ │ vs Mike     Score   │ │
│ │ 45 - 52     [Play]  │ │
│ └─────────────────────┘ │
│                         │
│ ┌─ Their Turn (1) ────┐ │
│ │ vs Emma     Score   │ │
│ │ 67 - 71     [Wait]  │ │
│ └─────────────────────┘ │
│                         │
│ ┌─ Completed (5) ─────┐ │
│ │ vs Tom      Won     │ │
│ │ 134 - 98    [View]  │ │
│ └─────────────────────┘ │
└─────────────────────────┘
```

**Components**:
- Filter/sort options
- Grouped game lists by status
- Game cards with scores and actions
- Expandable sections

**Functionality**:
- Filter by game status
- Sort by date, score, opponent
- Quick actions (Play, View, Archive)
- Pull-to-refresh updates

---

### 10. Game Board Screen
**Purpose**: Main gameplay interface

**Layout**:
```
┌─────────────────────────┐
│ [←] vs Sarah    [Menu]  │
│ Score: You 89 - 76 Her  │
│                         │
│ ┌─────────────────────┐ │
│ │  [Game Board 15x15] │ │
│ │  [Letters placed    │ │
│ │   on board with     │ │
│ │   multipliers]      │ │
│ │                     │ │
│ │                     │ │
│ └─────────────────────┘ │
│                         │
│ Your tiles:             │
│ [A][E][R][T][I][N][G]   │
│                         │
│ [Pass] [Shuffle] [Play] │
└─────────────────────────┘
```

**Components**:
- Opponent name and scores
- 15x15 game board with zoom/pan
- Player's tile rack
- Action buttons (Pass, Shuffle, Play)
- Game menu (pause, resign, etc.)

**Functionality**:
- Drag-and-drop tile placement
- Word validation and scoring
- Zoom and pan board
- Undo/redo moves
- Real-time opponent moves
- Turn timer display

---

### 11. Game Results Screen
**Purpose**: End-game summary and next actions

**Layout**:
```
┌─────────────────────────┐
│    [×] Game Complete    │
│                         │
│      🎉 You Won! 🎉     │
│                         │
│ ┌─ Final Scores ──────┐ │
│ │ You:    134 points  │ │
│ │ Sarah:   98 points  │ │
│ │ Margin:  +36 points │ │
│ └─────────────────────┘ │
│                         │
│ ┌─ Game Stats ────────┐ │
│ │ Duration:  23 min   │ │
│ │ Moves:     18       │ │
│ │ Best Word: QUALITY  │ │
│ │ Best Score: 28 pts  │ │
│ └─────────────────────┘ │
│                         │
│  [Play Again] [Share]   │
│                         │
│     [Back to Games]     │
└─────────────────────────┘
```

**Components**:
- Win/lose announcement
- Final score comparison
- Game statistics
- Action buttons for next steps

**Functionality**:
- Celebrate wins with animations
- Share results to social media
- Rematch invitation
- Navigate back to game list

---

## Social Screens

### 12. Friends Screen
**Purpose**: Manage friends and send invitations

**Layout**:
```
┌─────────────────────────┐
│   [←] Friends   [Add]   │
│                         │
│ ┌─ Search ────────────┐ │
│ │ 🔍 Find friends...  │ │
│ └─────────────────────┘ │
│                         │
│ ┌─ Online Now (3) ────┐ │
│ │ 🟢 Sarah   [Invite] │ │
│ │ 🟢 Mike    [Invite] │ │
│ │ 🟢 Emma    [Invite] │ │
│ └─────────────────────┘ │
│                         │
│ ┌─ All Friends (12) ──┐ │
│ │ ⚫ Tom     [Invite] │ │
│ │ ⚫ Lisa    [Invite] │ │
│ │ ⚫ Alex    [Invite] │ │
│ │ ...                 │ │
│ └─────────────────────┘ │
└─────────────────────────┘
```

**Components**:
- Add friend button
- Search functionality
- Online status indicators
- Friend list with invite buttons
- Expandable sections

**Functionality**:
- Search friends by username/email
- Send game invitations
- View friend profiles
- Online status tracking
- Friend request management

---

## Navigation Patterns

### Tab Navigation (Bottom)
```
┌─────────────────────────┐
│                         │
│    [Main Content]       │
│                         │
│                         │
├─────────────────────────┤
│[Home][Games][Friends][Profile]│
└─────────────────────────┘
```

### Modal Screens
- Settings (slide up from bottom)
- Game menu (overlay)
- Profile edit (full screen)

### Gesture Navigation
- Swipe back to previous screen
- Pull-to-refresh on lists
- Long press for context menus
- Pinch-to-zoom on game board

## Responsive Design

### Phone Layouts (375-414px width)
- Single column layouts
- Stacked components
- Bottom tab navigation
- Floating action buttons

### Tablet Layouts (768px+ width)
- Two-column layouts where appropriate
- Side navigation panels
- Larger game board
- Split-screen game view

### Accessibility
- VoiceOver/TalkBack support
- High contrast mode
- Large text support
- Keyboard navigation
- Color-blind friendly design 