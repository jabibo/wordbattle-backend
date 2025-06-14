import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.config import (
    SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, 
    FROM_EMAIL, VERIFICATION_CODE_EXPIRE_MINUTES, SMTP_USE_SSL, FRONTEND_URL
)

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.username = SMTP_USERNAME
        self.password = SMTP_PASSWORD
        self.from_email = FROM_EMAIL
        self.use_ssl = SMTP_USE_SSL
        
        # Common test/dummy domains that might be blocked by SMTP servers
        self.problematic_domains = {
            'example.com', 'example.org', 'example.net',
            'test.com', 'test.org', 'test.net',
            'dummy.com', 'fake.com', 'invalid.com',
            'localhost.com', '10minutemail.com'
        }
    
    def _is_problematic_email(self, email: str) -> bool:
        """Check if email domain might be problematic for SMTP delivery."""
        try:
            domain = email.split('@')[1].lower()
            return domain in self.problematic_domains
        except (IndexError, AttributeError):
            return True  # Invalid email format
    
    def send_verification_code(self, to_email: str, verification_code: str, username: str) -> bool:
        """Send verification code email to user."""
        try:
            # For testing environment, just log the code instead of sending email
            if os.getenv("TESTING") == "1" or not self.username:
                logger.info(f"TESTING MODE: Verification code for {to_email}: {verification_code}")
                return True
            
            # Check if SMTP password is configured
            if not self.password:
                logger.error("SMTP_PASSWORD not configured - cannot send emails")
                return False
            
            # Warn about potentially problematic email domains
            if self._is_problematic_email(to_email):
                logger.warning(f"Sending to potentially problematic email domain: {to_email}")
                logger.warning("This domain might be blocked by SMTP server policies")
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = "WordBattle - Your Login Code"
            
            # Email body
            body = f"""
Hello {username},

Your WordBattle login verification code is: {verification_code}

This code will expire in {VERIFICATION_CODE_EXPIRE_MINUTES} minutes.

If you didn't request this code, please ignore this email.

Best regards,
WordBattle Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            logger.info(f"Attempting to send verification email to {to_email}")
            logger.info(f"Connecting to SMTP server: {self.smtp_server}:{self.smtp_port}, SSL: {self.use_ssl}")
            
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
                logger.info("Using SMTP_SSL connection")
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                logger.info("Using SMTP with STARTTLS")
            
            logger.info(f"Logging in with username: {self.username}")
            server.login(self.username, self.password)
            logger.info("SMTP login successful")
            
            text = msg.as_string()
            server.sendmail(self.from_email, to_email, text)
            logger.info(f"Email sent successfully from {self.from_email} to {to_email}")
            server.quit()
            
            logger.info(f"Verification code sent successfully to {to_email}")
            return True
            
        except smtplib.SMTPRecipientsRefused as e:
            # Handle SMTP recipient refused errors (like blacklisted domains)
            logger.error(f"SMTP server refused to send to {to_email}: {str(e)}")
            logger.error("This might be due to domain blacklisting or SMTP server policies")
            return False
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {str(e)}")
            logger.error("Check SMTP username and password configuration")
            return False
        except smtplib.SMTPServerDisconnected as e:
            logger.error(f"SMTP server disconnected: {str(e)}")
            logger.error("Check SMTP server and port configuration")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending verification code to {to_email}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending verification code to {to_email}: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            return False
    
    def send_welcome_email(self, to_email: str, username: str) -> bool:
        """Send welcome email to new user."""
        try:
            # For testing environment, just log instead of sending email
            if os.getenv("TESTING") == "1" or not self.username:
                logger.info(f"TESTING MODE: Welcome email for {to_email}")
                return True
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = "Welcome to WordBattle!"
            
            # Email body
            body = f"""
Hello {username},

Welcome to WordBattle! Your account has been successfully created.

You can now log in using your email address. We'll send you a verification code each time you log in for security.

Start playing by creating or joining a game!

Best regards,
WordBattle Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            logger.info(f"Connecting to SMTP server: {self.smtp_server}:{self.smtp_port}, SSL: {self.use_ssl}")
            
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
                logger.info("Using SMTP_SSL connection")
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                logger.info("Using SMTP with STARTTLS")
            
            logger.info(f"Logging in with username: {self.username}")
            server.login(self.username, self.password)
            logger.info("Login successful")
            
            text = msg.as_string()
            server.sendmail(self.from_email, to_email, text)
            logger.info(f"Email sent from {self.from_email} to {to_email}")
            server.quit()
            
            logger.info(f"Welcome email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {to_email}: {str(e)}")
            return False

    def send_game_invitation(self, to_email: str, invitee_username: str, inviter_username: str, 
                           game_id: str, join_token: str, base_url: str = None) -> bool:
        """Send game invitation email with join link."""
        try:
            # Use frontend URL if no base_url provided
            if base_url is None:
                base_url = FRONTEND_URL
            
            # For testing environment, just log instead of sending email
            if os.getenv("TESTING") == "1" or not self.username:
                logger.info(f"TESTING MODE: Game invitation for {to_email} - Game: {game_id}, Token: {join_token}")
                return True
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = f"WordBattle Game Invitation from {inviter_username}"
            
            # Create join link - use frontend URL for user-facing links
            join_link = f"{base_url}/games/{game_id}/join?token={join_token}"
            
            # Email body
            body = f"""
Hello {invitee_username},

{inviter_username} has invited you to play WordBattle!

Click the link below to join the game:
{join_link}

Or you can:
1. Log in to WordBattle
2. Go to your invitations
3. Accept the invitation from {inviter_username}

Game Details:
- Game ID: {game_id}
- Invited by: {inviter_username}

Don't keep them waiting - start playing now!

Best regards,
WordBattle Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            logger.info(f"Connecting to SMTP server: {self.smtp_server}:{self.smtp_port}, SSL: {self.use_ssl}")
            
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
                logger.info("Using SMTP_SSL connection")
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                logger.info("Using SMTP with STARTTLS")
            
            logger.info(f"Logging in with username: {self.username}")
            server.login(self.username, self.password)
            logger.info("Login successful")
            
            text = msg.as_string()
            server.sendmail(self.from_email, to_email, text)
            logger.info(f"Email sent from {self.from_email} to {to_email}")
            server.quit()
            
            logger.info(f"Game invitation sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send game invitation to {to_email}: {str(e)}")
            return False

    def send_random_player_invitation(self, to_email: str, invitee_username: str, inviter_username: str, 
                                    game_id: str, join_token: str, base_url: str = None) -> bool:
        """Send game invitation email to a random existing player."""
        try:
            # Use frontend URL if no base_url provided
            if base_url is None:
                base_url = FRONTEND_URL
            
            # For testing environment, just log instead of sending email
            if os.getenv("TESTING") == "1" or not self.username:
                logger.info(f"TESTING MODE: Random player invitation for {to_email} - Game: {game_id}, Token: {join_token}")
                return True
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = f"WordBattle Game Invitation from {inviter_username}"
            
            # Create join link - use frontend URL for user-facing links
            join_link = f"{base_url}/games/{game_id}/join?token={join_token}"
            
            # Email body for random invitation
            body = f"""
Hello {invitee_username},

{inviter_username} is looking for players and has invited you to join a WordBattle game!

We thought you might be interested in playing since you're an active WordBattle player.

Click the link below to join the game:
{join_link}

Game Details:
- Game ID: {game_id}
- Invited by: {inviter_username}
- This is a random invitation to an active player

Join now and show off your word skills!

Best regards,
WordBattle Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            logger.info(f"Connecting to SMTP server: {self.smtp_server}:{self.smtp_port}, SSL: {self.use_ssl}")
            
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
                logger.info("Using SMTP_SSL connection")
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                logger.info("Using SMTP with STARTTLS")
            
            logger.info(f"Logging in with username: {self.username}")
            server.login(self.username, self.password)
            logger.info("Login successful")
            
            text = msg.as_string()
            server.sendmail(self.from_email, to_email, text)
            logger.info(f"Email sent from {self.from_email} to {to_email}")
            server.quit()
            
            logger.info(f"Random player invitation sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send random player invitation to {to_email}: {str(e)}")
            return False

# Global email service instance
email_service = EmailService() 