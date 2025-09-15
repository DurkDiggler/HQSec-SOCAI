from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from typing import List, Tuple

from .config import SETTINGS

logger = logging.getLogger(__name__)


def send_email(subject: str, body: str, subtype: str = "plain") -> Tuple[bool, str]:
    """Send email notification with improved error handling and validation."""
    if not SETTINGS.enable_email:
        logger.debug("Email notifications disabled")
        return False, "Email disabled"
    
    if not (SETTINGS.smtp_host and SETTINGS.email_from and SETTINGS.email_to):
        logger.warning("Email not properly configured")
        return False, "Email not configured"

    # Validate email addresses
    try:
        from_addr = formataddr(("SOC Agent", SETTINGS.email_from))
        to_addrs = [addr.strip() for addr in SETTINGS.email_to if addr.strip()]
        
        if not to_addrs:
            logger.warning("No valid recipient email addresses")
            return False, "No valid recipients"
            
    except Exception as e:
        logger.error(f"Email address validation failed: {e}")
        return False, f"Invalid email addresses: {e}"

    # Create message
    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    msg["Subject"] = subject
    msg["X-Priority"] = "1"  # High priority
    
    # Set content with proper encoding
    try:
        msg.set_content(body, subtype=subtype, charset="utf-8")
    except Exception as e:
        logger.error(f"Failed to set email content: {e}")
        return False, f"Content encoding failed: {e}"

    # Send email with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with smtplib.SMTP(SETTINGS.smtp_host, SETTINGS.smtp_port, timeout=30) as s:
                s.set_debuglevel(0)  # Disable debug output
                
                # Start TLS
                s.starttls()
                
                # Authenticate if credentials provided
                if SETTINGS.smtp_username and SETTINGS.smtp_password:
                    s.login(SETTINGS.smtp_username, SETTINGS.smtp_password)
                
                # Send message
                s.send_message(msg)
                
            logger.info(f"Email sent successfully to {len(to_addrs)} recipients")
            return True, "sent"
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return False, f"Authentication failed: {e}"
            
        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"Recipients refused: {e}")
            return False, f"Recipients refused: {e}"
            
        except smtplib.SMTPServerDisconnected as e:
            logger.warning(f"SMTP server disconnected (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                return False, f"Server disconnected after {max_retries} attempts: {e}"
            continue
            
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                return False, f"SMTP error after {max_retries} attempts: {e}"
            continue
            
        except Exception as e:
            logger.error(f"Unexpected error sending email (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                return False, f"Unexpected error after {max_retries} attempts: {e}"
            continue

    return False, "Max retries exceeded"
