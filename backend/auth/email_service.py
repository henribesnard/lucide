import os
import logging
from typing import Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


async def send_verification_email(email: str, verification_token: str) -> bool:
    """Send email verification link to user."""
    try:
        verification_url = f"{FRONTEND_URL}/verify-email?token={verification_token}"

        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = "Vérifiez votre adresse email - Lucide"
        message["From"] = SMTP_USER
        message["To"] = email

        # HTML email content
        html = f"""
        <html>
          <body>
            <h2>Bienvenue sur Lucide!</h2>
            <p>Merci de vous être inscrit. Veuillez cliquer sur le lien ci-dessous pour vérifier votre adresse email:</p>
            <p><a href="{verification_url}">Vérifier mon email</a></p>
            <p>Ou copiez ce lien dans votre navigateur:</p>
            <p>{verification_url}</p>
            <p>Ce lien expirera dans 24 heures.</p>
            <br>
            <p>Si vous n'avez pas créé de compte sur Lucide, ignorez cet email.</p>
          </body>
        </html>
        """

        # Plain text fallback
        text = f"""
        Bienvenue sur Lucide!

        Merci de vous être inscrit. Veuillez cliquer sur le lien ci-dessous pour vérifier votre adresse email:

        {verification_url}

        Ce lien expirera dans 24 heures.

        Si vous n'avez pas créé de compte sur Lucide, ignorez cet email.
        """

        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")

        message.attach(part1)
        message.attach(part2)

        # Send email
        if SMTP_USER and SMTP_PASSWORD:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_USER, email, message.as_string())
            logger.info(f"Verification email sent to {email}")
            return True
        else:
            # In development, just log the URL
            logger.warning(f"SMTP not configured. Verification URL for {email}: {verification_url}")
            return True

    except Exception as e:
        logger.error(f"Failed to send verification email to {email}: {e}")
        return False
