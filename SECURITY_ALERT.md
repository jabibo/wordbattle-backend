# 🚨 SECURITY ALERT - Exposed SMTP Credentials

## Issue
SMTP password `z1nUNGrz1ZDmu4J` was exposed in the git repository in 64 locations including:
- Environment files (deploy.env, deploy.production.env, etc.)
- Documentation files
- Archive/old deployment scripts

This exposure occurred in **multiple commits over time** and has been pushed to GitHub.

## Immediate Actions Required

### 1. ✅ Repository Cleanup (COMPLETED)
- ✅ Removed deploy*.env files from git tracking
- ✅ Created template files with placeholders
- ✅ Updated .gitignore to prevent future exposure
- ✅ Cleaned documentation files

### 2. 🔴 ROTATE SMTP PASSWORD (CRITICAL - DO THIS NOW!)

**You MUST change the SMTP password immediately:**

1. Log in to your Strato email account for `service@binge-wordbattle.de`
2. Change the email password
3. Update the password on the production server:
   ```bash
   ssh -i ~/.ssh/id_rsa_strato_server root@82.165.170.52
   nano /home/wordbattle/wordbattle/.env
   # Update SMTP_PASSWORD with new password
   docker restart wordbattle-backend
   ```
4. Update your local deploy.env files with the new password

### 3. 🔴 CLEAN GIT HISTORY (RECOMMENDED)

The old password still exists in git history. To completely remove it:

#### Option A: Using BFG Repo-Cleaner (Easiest)
```bash
# Install BFG
brew install bfg  # macOS
# or download from https://rtyley.github.io/bfg-repo-cleaner/

# Clone a fresh copy
cd ~/Desktop
git clone --mirror https://github.com/jabibo/wordbattle-backend.git

# Remove the password from all history
bfg --replace-text passwords.txt wordbattle-backend.git

# Create passwords.txt with:
# z1nUNGrz1ZDmu4J

cd wordbattle-backend.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push (⚠️ DESTRUCTIVE!)
git push --force
```

#### Option B: Using git filter-branch
```bash
cd /Users/janbinge/git/wordbattle/wordbattle-backend

git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch deploy.*.env deploy.*.env.backup' \
  --prune-empty --tag-name-filter cat -- --all

git filter-branch --force --tree-filter \
  'find . -type f -exec sed -i "" "s/z1nUNGrz1ZDmu4J/REDACTED/g" {} \;' \
  HEAD

git push --force
```

#### ⚠️ WARNING: Force Push Impact
- Force pushing rewrites git history
- Anyone with a clone will need to re-clone or reset
- Coordinate with team members before doing this

### 4. 📋 Verify Production Server

Check that production is using environment variables, not hardcoded values:
```bash
ssh -i ~/.ssh/id_rsa_strato_server root@82.165.170.52
cat /home/wordbattle/wordbattle/.env | grep SMTP_PASSWORD
# Should show the password (stored server-side only, not in git)
```

## Prevention

### For Future Reference:
1. ✅ Never commit .env files to git
2. ✅ Always use .example templates with placeholders
3. ✅ Use environment variables for secrets
4. ✅ Add secrets to .gitignore before first commit
5. ✅ Use GitHub secret scanning (enabled by default)
6. ✅ Consider using secret management tools (AWS Secrets Manager, etc.)

### Pre-commit Hook (Optional)
To prevent future exposure, add this to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
if git diff --cached --name-only | grep -qE 'deploy.*\.env$|\.env$'; then
    echo "ERROR: Attempting to commit .env file!"
    echo "Please use .env.example instead."
    exit 1
fi

if git diff --cached | grep -qE 'PASSWORD=.{8,}'; then
    echo "WARNING: Possible password in staged changes!"
    echo "Please review your commit."
    exit 1
fi
```

## Timeline
- **2025-11-08**: Issue identified by GitHub secret scanning
- **2025-11-08**: Repository cleanup completed
- **Pending**: Password rotation
- **Pending**: Git history cleaning

## Status
- [x] Repository cleanup
- [ ] Password rotation (URGENT)
- [ ] Git history cleaning (RECOMMENDED)
- [ ] Team notification (if applicable)

---

**Created**: 2025-11-08  
**Last Updated**: 2025-11-08

