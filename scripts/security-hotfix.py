#!/usr/bin/env python3
"""
Security Hotfix Script for WordBattle Backend
Addresses critical security vulnerabilities immediately.
"""

import os
import secrets
import re
from pathlib import Path

def generate_secure_secret(length=32):
    """Generate a cryptographically secure secret."""
    return secrets.token_hex(length)

def fix_config_file():
    """Fix hardcoded secrets in app/config.py."""
    config_path = Path("app/config.py")
    
    if not config_path.exists():
        print("❌ app/config.py not found!")
        return False
    
    print("🔧 Fixing hardcoded secrets in app/config.py...")
    
    with open(config_path, 'r') as f:
        content = f.read()
    
    # Remove hardcoded SECRET_KEY default
    content = re.sub(
        r'SECRET_KEY = os\.getenv\("SECRET_KEY", "[^"]+"\)',
        'SECRET_KEY = os.getenv("SECRET_KEY")\nif not SECRET_KEY:\n    raise ValueError("SECRET_KEY environment variable is required in production")',
        content
    )
    
    # Remove hardcoded SMTP_PASSWORD default
    content = re.sub(
        r'SMTP_PASSWORD = os\.getenv\("SMTP_PASSWORD", "[^"]+"\)',
        'SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")\nif not SMTP_PASSWORD:\n    print("⚠️  SMTP_PASSWORD not set - email functionality disabled")',
        content
    )
    
    # Fix CORS to be more restrictive
    cors_fix = '''# CORS origins - should be configured per environment
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "https://localhost:3000").split(",")
if os.getenv("ENVIRONMENT") == "production" and "*" in CORS_ORIGINS:
    raise ValueError("Wildcard CORS origins not allowed in production")'''
    
    content = re.sub(
        r'CORS_ORIGINS = os\.getenv\("CORS_ORIGINS", "\*"\)\.split\(","\)',
        cors_fix,
        content
    )
    
    with open(config_path, 'w') as f:
        f.write(content)
    
    print("✅ Fixed app/config.py")
    return True

def fix_main_cors():
    """Fix overly permissive CORS in main.py."""
    main_path = Path("app/main.py")
    
    if not main_path.exists():
        print("❌ app/main.py not found!")
        return False
    
    print("🔧 Fixing CORS configuration in app/main.py...")
    
    with open(main_path, 'r') as f:
        content = f.read()
    
    # Replace wildcard CORS with environment-based configuration
    cors_replacement = '''# Add CORS middleware with environment-based configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # Use configured origins, not wildcard
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
    ],
    expose_headers=[
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Credentials",
    ],
    max_age=600,
)'''
    
    # Find and replace the CORS middleware section
    content = re.sub(
        r'# Add CORS middleware\napp\.add_middleware\(\s*CORSMiddleware,.*?\)',
        cors_replacement,
        content,
        flags=re.DOTALL
    )
    
    with open(main_path, 'w') as f:
        f.write(content)
    
    print("✅ Fixed CORS configuration in app/main.py")
    return True

def disable_debug_endpoints():
    """Disable debug endpoints in production."""
    main_path = Path("app/main.py")
    admin_path = Path("app/routers/admin.py")
    
    print("🔧 Adding production guards to debug endpoints...")
    
    # Add environment check to main.py debug endpoints
    if main_path.exists():
        with open(main_path, 'r') as f:
            content = f.read()
        
        # Add production check to debug endpoints
        debug_guard = '''# Debug endpoints - disabled in production
if os.getenv("ENVIRONMENT") != "production":'''
        
        # Find debug endpoints and add guards
        content = re.sub(
            r'(@app\.get\("/debug/.*?"\))',
            f'{debug_guard}\n    \\1',
            content,
            flags=re.MULTILINE
        )
        
        with open(main_path, 'w') as f:
            f.write(content)
        
        print("✅ Added production guards to main.py debug endpoints")
    
    # Add environment check to admin debug endpoints
    if admin_path.exists():
        with open(admin_path, 'r') as f:
            content = f.read()
        
        # Add production check to debug token creation
        production_check = '''    # Disable in production
    if os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(status_code=403, detail="Debug endpoints disabled in production")
    '''
        
        # Add check to create-test-tokens endpoint
        content = re.sub(
            r'(@router\.post\("/debug/create-test-tokens"\)\nasync def create_test_tokens\(.*?\n\):\n    """.*?""")',
            f'\\1\n{production_check}',
            content,
            flags=re.DOTALL
        )
        
        with open(admin_path, 'w') as f:
            f.write(content)
        
        print("✅ Added production guards to admin debug endpoints")

def create_env_template():
    """Create a secure .env template."""
    env_template = f"""# WordBattle Backend Environment Configuration
# SECURITY: Never commit actual secrets to version control!

# Critical Security Settings (REQUIRED)
SECRET_KEY={generate_secure_secret(32)}
SMTP_PASSWORD=your-secure-smtp-password-here

# Database Configuration
DATABASE_URL=postgresql://user:password@host:port/database
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your-secure-db-password
DB_NAME=wordbattle

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_USE_SSL=true
FROM_EMAIL=your-email@gmail.com

# Application Configuration
ENVIRONMENT=development
PORT=8000
CORS_ORIGINS=https://localhost:3000,https://yourdomain.com

# Rate Limiting
RATE_LIMIT=60

# Game Settings
DEFAULT_WORDLIST_PATH=data/de_words.txt
LETTER_POOL_SIZE=7
GAME_INACTIVE_DAYS=7

# Frontend/Backend URLs
FRONTEND_URL=https://localhost:3000
BACKEND_URL=https://localhost:8000
"""
    
    with open(".env.template", 'w') as f:
        f.write(env_template)
    
    print("✅ Created .env.template with secure defaults")
    print("📝 Please copy .env.template to .env and configure with your actual secrets")

def update_gitignore():
    """Ensure .env files are in .gitignore."""
    gitignore_path = Path(".gitignore")
    
    env_entries = [
        ".env",
        ".env.local", 
        ".env.production",
        ".env.*.local",
        "*.env"
    ]
    
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            content = f.read()
        
        missing_entries = []
        for entry in env_entries:
            if entry not in content:
                missing_entries.append(entry)
        
        if missing_entries:
            with open(gitignore_path, 'a') as f:
                f.write("\n# Environment files (Security)\n")
                for entry in missing_entries:
                    f.write(f"{entry}\n")
            
            print(f"✅ Added {len(missing_entries)} environment file patterns to .gitignore")
    else:
        with open(gitignore_path, 'w') as f:
            f.write("# Environment files (Security)\n")
            for entry in env_entries:
                f.write(f"{entry}\n")
        
        print("✅ Created .gitignore with environment file exclusions")

def main():
    """Run all security fixes."""
    print("🛡️  WordBattle Security Hotfix")
    print("=" * 40)
    print()
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    success = True
    
    # Fix critical issues
    if not fix_config_file():
        success = False
    
    if not fix_main_cors():
        success = False
    
    disable_debug_endpoints()
    create_env_template()
    update_gitignore()
    
    print()
    if success:
        print("✅ Security hotfix completed successfully!")
        print()
        print("🚨 CRITICAL NEXT STEPS:")
        print("1. Copy .env.template to .env and configure secrets")
        print("2. Set ENVIRONMENT=production in production deployments")
        print("3. Update CORS_ORIGINS with your actual frontend domains")
        print("4. Rotate all existing JWT tokens by changing SECRET_KEY")
        print("5. Review SECURITY_ASSESSMENT.md for additional fixes")
        print()
        print("🔐 New secrets generated:")
        print(f"   SECRET_KEY: {generate_secure_secret(32)}")
        print(f"   Alternative: {generate_secure_secret(32)}")
    else:
        print("❌ Some fixes failed. Please review the output above.")
        print("📖 See SECURITY_ASSESSMENT.md for manual fix instructions.")

if __name__ == "__main__":
    main() 