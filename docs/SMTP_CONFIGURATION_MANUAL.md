# 📧 Manual SMTP Configuration for WordBattle Production Server

**Date:** October 31, 2025  
**Server:** wordbattle2.de (82.165.170.52)  
**Purpose:** Enable email verification for user authentication

---

## ✅ Quick Setup (5 minutes)

### Step 1: Connect to Your Server

**⚠️ IMPORTANT: SSH May Be Locked Due to Security Hardening**

If SSH is not working (connection refused or permission denied), use **Option B** below.

**Option A: SSH Access (if you have the key)**
```bash
# Try SSH with wordbattle user
ssh -i ~/.ssh/id_rsa wordbattle@82.165.170.52

# Or if root is still enabled
ssh root@82.165.170.52
```

**Option B: Hosting Provider Console (RECOMMENDED)** 🎯
```bash
# Use Strato's web-based console/terminal:
# 1. Log into Strato control panel
# 2. Navigate to: Server → Console/Terminal
# 3. You'll have direct root access!

# Once in console, you can proceed with all commands below
```

**Option C: Re-enable Root SSH (if locked out)**
```bash
# Via Strato console, run:
nano /etc/ssh/sshd_config

# Change this line:
# PermitRootLogin no  →  PermitRootLogin yes

# Save and restart:
systemctl restart sshd

# Now SSH works again:
ssh root@82.165.170.52
```

### Step 2: Navigate to WordBattle Directory

```bash
cd /opt/wordbattle
```

### Step 3: Edit .env File

```bash
# Open the .env file in nano editor
nano .env
```

### Step 4: Add SMTP Configuration

Add these lines to the end of your `.env` file:

```bash
# SMTP Email Configuration
SMTP_SERVER=smtp.strato.de
SMTP_PORT=465
SMTP_USERNAME=service@binge-wordbattle.de
SMTP_PASSWORD=z1nUNGrz1ZDmu4J
FROM_EMAIL=service@binge-wordbattle.de
SMTP_USE_SSL=true
```

**Save and exit:**
- Press `Ctrl + O` to save
- Press `Enter` to confirm
- Press `Ctrl + X` to exit

### Step 5: Restart Backend Container

```bash
# Restart the backend to apply changes
docker-compose restart backend

# Or use the full restart
docker-compose down
docker-compose up -d
```

### Step 6: Verify Configuration

```bash
# Check backend logs for SMTP messages
docker logs wordbattle-backend --tail 50 | grep -i smtp

# You should NOT see:
# ❌ "SMTP_PASSWORD not set - email functionality disabled"

# If you see the error message, the .env wasn't loaded correctly
```

---

## 🧪 Testing Email Functionality

### Test from the App

1. Open WordBattle app on iPad
2. Enter email: `jan@binge.de`
3. Click "Send Verification Code"
4. Check your email inbox (and spam folder!)

### Monitor Backend Logs

```bash
# Watch logs in real-time
docker logs -f wordbattle-backend

# Look for:
# "Sending email to jan@binge.de"
# "Email sent successfully"
```

---

## 🔧 Troubleshooting

### Issue 1: "SMTP_PASSWORD not set" Error

```bash
# Check if .env file has SMTP configuration
cat /opt/wordbattle/.env | grep SMTP

# If empty, you're editing the wrong .env file
# Make sure you're in /opt/wordbattle directory

# Check for syntax errors (no spaces around =)
# CORRECT:   SMTP_PASSWORD=z1nUNGrz1ZDmu4J
# INCORRECT: SMTP_PASSWORD = z1nUNGrz1ZDmu4J
```

### Issue 2: Still No Email Received

```bash
# 1. Check backend logs for errors
docker logs wordbattle-backend --tail 100 | grep -i "email\|smtp\|error"

# 2. Test SMTP connection manually
apt-get update && apt-get install -y swaks

swaks --to jan@binge.de \
      --from service@binge-wordbattle.de \
      --server smtp.strato.de \
      --port 465 \
      --auth LOGIN \
      --auth-user service@binge-wordbattle.de \
      --auth-password "z1nUNGrz1ZDmu4J" \
      --tls

# 3. Check spam folder in email client
```

### Issue 3: Container Won't Restart

```bash
# Check container status
docker ps -a

# Check logs for errors
docker logs wordbattle-backend --tail 50

# Force recreate container
docker-compose down
docker-compose up -d --force-recreate backend
```

---

## 📱 Alternative: Quick Test Without SMTP

If you want to test the app immediately without waiting for SMTP setup, you can create a user directly in the database:

```bash
# Connect to database
docker exec -it wordbattle-db psql -U wordbattle_user -d wordbattle_prod

# Create test user (run these SQL commands)
INSERT INTO users (username, email, created_at) 
VALUES ('testuser', 'test@example.com', NOW());

# Exit database
\q

# Now you can use alternative login methods in the app
```

---

## 🔐 Security Notes

1. **Never commit `.env` to git** - It contains sensitive passwords
2. **Change SMTP password regularly** - Every 90 days recommended
3. **Use app-specific passwords** - If using Gmail, generate app password
4. **Monitor email logs** - Watch for suspicious activity

---

## 📚 Full Documentation

Complete SMTP configuration guide is now in:
- **Backend Repo:** `docs/SELF_HOSTED_MIGRATION_PLAN.md` (Section: SMTP Email Configuration)
- **Script:** `scripts/configure-smtp.sh` (automated setup)

---

## 🆘 If SSH is Not Working

### Enable SSH Access

```bash
# If you're locked out, use hosting provider console

# 1. Check SSH status
systemctl status ssh

# 2. If stopped, start it
systemctl start ssh
systemctl enable ssh

# 3. Check firewall
ufw status
ufw allow 22/tcp

# 4. Check SSH config
cat /etc/ssh/sshd_config | grep PermitRootLogin
# Should be: PermitRootLogin yes (or prohibit-password if using keys)

# 5. Restart SSH
systemctl restart ssh
```

---

## ✅ Success Checklist

- [ ] Connected to server (SSH or console)
- [ ] Edited `/opt/wordbattle/.env` file
- [ ] Added all 6 SMTP environment variables
- [ ] Saved .env file correctly
- [ ] Restarted backend container
- [ ] Checked logs (no "SMTP_PASSWORD not set" error)
- [ ] Tested email login from app
- [ ] Received verification email

---

## 🎯 Quick Command Reference

```bash
# Navigate to directory
cd /opt/wordbattle

# Edit config
nano .env

# Restart backend
docker-compose restart backend

# View logs
docker logs -f wordbattle-backend

# Check SMTP config (without showing password)
grep "^SMTP\|^FROM_EMAIL" .env | grep -v PASSWORD
```

---

## 📞 Need Help?

1. Check backend logs: `docker logs wordbattle-backend`
2. Review migration guide: `docs/SELF_HOSTED_MIGRATION_PLAN.md`
3. Test SMTP manually with `swaks` command above
4. Verify .env file has no syntax errors

---

**Status:** Ready to Configure ✅  
**Time Required:** ~5 minutes  
**Difficulty:** Easy

