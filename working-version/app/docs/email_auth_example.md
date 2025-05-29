# Email-Based Authentication Guide

WordBattle now supports email-based authentication with verification codes. This provides a more secure and user-friendly authentication experience.

## Overview

The new authentication system works as follows:

1. **Registration**: User registers with username and email (no password required)
2. **Login Request**: User enters their email to request login
3. **Verification Code**: System sends a 6-digit code to their email
4. **Code Verification**: User enters the code to complete login
5. **Persistent Authentication**: Optional "remember me" functionality stores a long-lived token

## API Endpoints

### 1. Register User (Email Only)

```http
POST /users/register-email-only
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com"
}
```

**Response:**
```json
{
  "message": "User successfully registered with email-only authentication",
  "id": 123,
  "username": "john_doe",
  "email": "john@example.com",
  "auth_method": "email_only"
}
```

### 2. Request Login Code

```http
POST /auth/email-login
Content-Type: application/json

{
  "email": "john@example.com",
  "remember_me": true
}
```

**Response:**
```json
{
  "message": "If this email is registered, you will receive a verification code.",
  "email_sent": true,
  "expires_in_minutes": 10
}
```

### 3. Verify Code and Login

```http
POST /auth/verify-code
Content-Type: application/json

{
  "email": "john@example.com",
  "verification_code": "123456",
  "remember_me": true
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": 123,
    "username": "john_doe",
    "email": "john@example.com"
  },
  "persistent_token": "abc123def456...",
  "persistent_expires_at": "2024-02-15T10:30:00Z"
}
```

### 4. Login with Persistent Token

```http
POST /auth/persistent-login
Content-Type: application/json

{
  "persistent_token": "abc123def456..."
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": 123,
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

## Client-Side Implementation

### JavaScript/TypeScript Example

```typescript
class WordBattleAuth {
  private baseUrl: string;
  private accessToken: string | null = null;
  private persistentToken: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    this.loadStoredTokens();
  }

  // Load tokens from localStorage
  private loadStoredTokens() {
    this.accessToken = localStorage.getItem('wb_access_token');
    this.persistentToken = localStorage.getItem('wb_persistent_token');
  }

  // Save tokens to localStorage
  private saveTokens(accessToken: string, persistentToken?: string) {
    this.accessToken = accessToken;
    localStorage.setItem('wb_access_token', accessToken);
    
    if (persistentToken) {
      this.persistentToken = persistentToken;
      localStorage.setItem('wb_persistent_token', persistentToken);
    }
  }

  // Register new user
  async register(username: string, email: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/users/register-email-only`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email })
    });
    return response.json();
  }

  // Request login code
  async requestLoginCode(email: string, rememberMe: boolean = false): Promise<any> {
    const response = await fetch(`${this.baseUrl}/auth/email-login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, remember_me: rememberMe })
    });
    return response.json();
  }

  // Verify code and complete login
  async verifyCode(email: string, code: string, rememberMe: boolean = false): Promise<any> {
    const response = await fetch(`${this.baseUrl}/auth/verify-code`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        email, 
        verification_code: code, 
        remember_me: rememberMe 
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      this.saveTokens(data.access_token, data.persistent_token);
      return data;
    }
    
    throw new Error('Invalid verification code');
  }

  // Auto-login with persistent token
  async autoLogin(): Promise<boolean> {
    if (!this.persistentToken) return false;

    try {
      const response = await fetch(`${this.baseUrl}/auth/persistent-login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ persistent_token: this.persistentToken })
      });

      if (response.ok) {
        const data = await response.json();
        this.saveTokens(data.access_token);
        return true;
      }
    } catch (error) {
      console.error('Auto-login failed:', error);
    }

    // Clear invalid persistent token
    this.clearTokens();
    return false;
  }

  // Logout
  async logout(): Promise<void> {
    if (this.accessToken) {
      try {
        await fetch(`${this.baseUrl}/auth/logout`, {
          method: 'POST',
          headers: { 
            'Authorization': `Bearer ${this.accessToken}`,
            'Content-Type': 'application/json'
          }
        });
      } catch (error) {
        console.error('Logout request failed:', error);
      }
    }
    
    this.clearTokens();
  }

  // Clear all tokens
  private clearTokens() {
    this.accessToken = null;
    this.persistentToken = null;
    localStorage.removeItem('wb_access_token');
    localStorage.removeItem('wb_persistent_token');
  }

  // Get current access token
  getAccessToken(): string | null {
    return this.accessToken;
  }

  // Check if user is logged in
  isLoggedIn(): boolean {
    return !!this.accessToken;
  }

  // Make authenticated API request
  async apiRequest(endpoint: string, options: RequestInit = {}): Promise<Response> {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    return fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers
    });
  }
}

// Usage example
const auth = new WordBattleAuth('http://localhost:8000');

// On app startup, try auto-login
auth.autoLogin().then(success => {
  if (success) {
    console.log('Auto-login successful');
    // Redirect to game dashboard
  } else {
    console.log('Auto-login failed, showing login form');
    // Show login form
  }
});

// Login flow
async function loginUser(email: string, rememberMe: boolean = false) {
  try {
    // Step 1: Request verification code
    await auth.requestLoginCode(email, rememberMe);
    
    // Step 2: Show code input form
    const code = prompt('Enter the 6-digit code sent to your email:');
    
    // Step 3: Verify code and login
    const result = await auth.verifyCode(email, code, rememberMe);
    
    console.log('Login successful:', result.user);
    // Redirect to game dashboard
    
  } catch (error) {
    console.error('Login failed:', error);
    alert('Login failed. Please try again.');
  }
}
```

## Security Features

1. **No Password Storage**: Eliminates password-related security risks
2. **Time-Limited Codes**: Verification codes expire in 10 minutes
3. **Secure Token Generation**: Uses cryptographically secure random generation
4. **Persistent Token Validation**: Server-side validation of long-lived tokens
5. **Email Enumeration Protection**: Doesn't reveal if email exists during login

## Configuration

Add these environment variables to your `.env` file:

```env
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@wordbattle.com
VERIFICATION_CODE_EXPIRE_MINUTES=10

# Token Configuration
PERSISTENT_TOKEN_EXPIRE_DAYS=30
```

## Migration

To migrate existing users to the new system:

1. Run the database migration: `python migrations/add_email_auth_fields.py`
2. Update existing users to add email addresses
3. Both old (username/password) and new (email/code) authentication will work simultaneously

## Testing

In testing mode (`TESTING=1`), verification codes are logged instead of sent via email:

```
INFO:app.utils.email_service:TESTING MODE: Verification code for user@example.com: 123456
``` 