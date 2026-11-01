"""Gmail Automation & Multi-User Email Delivery Engine for MethodWise.
Features:
- Provider abstraction (EmailBackend interface, GmailSMTPBackend, Resend stub, SendGrid stub)
- OTP Recipient Verification (secrets module, salted hash, 10-minute expiry, max 5 attempts, max 3 requests/hour)
- Multi-tier Rate Limiting (per-address max 3/hour, per-session max 5/hour, global daily cap)
- Privacy safeguards (masked address, SHA-256 email hash, zero secret logging)
- Deliverability standards (multipart plain-text/HTML, clear subject, Reply-To, explanation footer)
"""

import os
import re
import time
import hmac
import secrets
import hashlib
import smtplib
from abc import ABC, abstractmethod
from email.message import EmailMessage
from email.utils import make_msgid, formatdate
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List

from src.config import (
    get_gmail_address,
    get_gmail_app_password,
    get_email_from_name,
    is_gmail_configured,
    get_email_backend_name,
    get_email_daily_cap,
    get_email_reply_to
)
from src.storage import (
    mask_email,
    hash_email,
    record_email_dispatch,
    get_email_dispatch_counts
)

# Email address validation regex (RFC 5322 simplified strict pattern)
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

# Security and rate limit constants
MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024  # 10 MB max attachment size
MAX_EMAILS_PER_HOUR_SESSION = 5          # Hourly rate limit per session
MAX_REPORTS_PER_HOUR_ADDRESS = 3         # Hourly report rate limit per recipient address
MAX_OTP_PER_HOUR_ADDRESS = 3             # Hourly OTP verification requests per address
OTP_EXPIRY_SECONDS = 600                 # 10 minutes OTP validity
OTP_MAX_ATTEMPTS = 5                     # Max failed verification attempts per code
SMTP_TIMEOUT_SECONDS = 10                # Socket timeout

# Module-level sliding window rate limiter: session_id -> list of float timestamps
_RATE_LIMIT_STORE: Dict[str, List[float]] = {}


# ==============================================================================
# 1. PROVIDER ABSTRACTION (EmailBackend)
# ==============================================================================

class EmailBackend(ABC):
    """Abstract Base Class for email delivery providers."""

    @abstractmethod
    def send(self, message: EmailMessage) -> Dict[str, Any]:
        """Dispatch an EmailMessage and return result dictionary."""
        pass


class GmailSMTPBackend(EmailBackend):
    """Production Gmail SMTP_SSL:465 provider using standard library smtplib."""

    def __init__(self, host: str = "smtp.gmail.com", port: int = 465, timeout: int = SMTP_TIMEOUT_SECONDS):
        self.host = host
        self.port = port
        self.timeout = timeout

    def send(self, message: EmailMessage) -> Dict[str, Any]:
        sender_addr = get_gmail_address()
        sender_pwd = get_gmail_app_password()

        if not is_gmail_configured():
            return {
                "status": "SKIPPED_NO_CREDENTIALS",
                "message_id": None,
                "error": "Gmail credentials (GMAIL_ADDRESS and GMAIL_APP_PASSWORD) are not configured in environment."
            }

        max_attempts = 2
        last_error = None
        msg_id = message["Message-ID"]

        for attempt in range(1, max_attempts + 1):
            try:
                with smtplib.SMTP_SSL(self.host, self.port, timeout=self.timeout) as server:
                    server.login(sender_addr, sender_pwd)
                    server.send_message(message)

                return {
                    "status": "SENT",
                    "message_id": str(msg_id),
                    "error": None
                }
            except smtplib.SMTPAuthenticationError as auth_err:
                return {
                    "status": "FAILED",
                    "message_id": None,
                    "error": "Gmail authentication failed. Verify that GMAIL_ADDRESS is correct and GMAIL_APP_PASSWORD is a valid 16-character Google App Password."
                }
            except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, TimeoutError, OSError) as transient_err:
                last_error = transient_err
                if attempt < max_attempts:
                    time.sleep(1.0)
                    continue
            except Exception as general_err:
                last_error = general_err
                break

        return {
            "status": "FAILED",
            "message_id": None,
            "error": f"Email dispatch failed: {last_error}"
        }


class ResendBackend(EmailBackend):
    """Stub provider for Resend API (Documented for future integration)."""

    def send(self, message: EmailMessage) -> Dict[str, Any]:
        api_key = os.getenv("RESEND_API_KEY", "").strip()
        if not api_key:
            return {
                "status": "FAILED",
                "message_id": None,
                "error": "Resend API key (RESEND_API_KEY) is not configured. Provider stub available for future work."
            }
        return {
            "status": "FAILED",
            "message_id": None,
            "error": "Resend REST backend is documented as future work. Use EMAIL_BACKEND=gmail for production delivery."
        }


class SendGridBackend(EmailBackend):
    """Stub provider for SendGrid API (Documented for future integration)."""

    def send(self, message: EmailMessage) -> Dict[str, Any]:
        api_key = os.getenv("SENDGRID_API_KEY", "").strip()
        if not api_key:
            return {
                "status": "FAILED",
                "message_id": None,
                "error": "SendGrid API key (SENDGRID_API_KEY) is not configured. Provider stub available for future work."
            }
        return {
            "status": "FAILED",
            "message_id": None,
            "error": "SendGrid REST backend is documented as future work. Use EMAIL_BACKEND=gmail for production delivery."
        }


def get_email_backend() -> EmailBackend:
    """Factory to retrieve configured EmailBackend instance."""
    backend_name = get_email_backend_name()
    if backend_name == "resend":
        return ResendBackend()
    elif backend_name == "sendgrid":
        return SendGridBackend()
    return GmailSMTPBackend()


# ==============================================================================
# 2. VALIDATION & RATE LIMITING
# ==============================================================================

def validate_recipient(recipient: Optional[str]) -> Tuple[bool, str]:
    """Validate recipient email for format, control characters, and injection vectors."""
    if not recipient or not recipient.strip():
        return False, "Recipient email address is empty."

    recipient = recipient.strip()

    # Reject header injection characters (CRLF, null bytes)
    if any(c in recipient for c in ("\r", "\n", "\0", "\t")):
        return False, "Recipient address contains illegal control characters (header injection rejected)."

    # Enforce strictly single recipient (reject commas, semicolons, multiple addresses)
    if any(c in recipient for c in (",", ";", " ")):
        return False, "Multiple recipient addresses are forbidden. Enter a single email address."

    # Validate regex pattern
    if not EMAIL_REGEX.match(recipient):
        return False, f"Invalid email format: '{recipient}'."

    return True, ""


def check_rate_limit(session_id: str = "default_session") -> Tuple[bool, str]:
    """Check whether the session has exceeded the in-memory sliding window rate limit."""
    now = time.time()
    cutoff = now - 3600.0

    if session_id not in _RATE_LIMIT_STORE:
        _RATE_LIMIT_STORE[session_id] = []

    # Retain only timestamps from the last hour
    _RATE_LIMIT_STORE[session_id] = [t for t in _RATE_LIMIT_STORE[session_id] if t > cutoff]

    if len(_RATE_LIMIT_STORE[session_id]) >= MAX_EMAILS_PER_HOUR_SESSION:
        return False, f"Hourly rate limit exceeded: maximum {MAX_EMAILS_PER_HOUR_SESSION} emails allowed per hour."

    return True, ""


def record_email_sent(session_id: str = "default_session"):
    """Record an email dispatch timestamp in the in-memory window."""
    now = time.time()
    if session_id not in _RATE_LIMIT_STORE:
        _RATE_LIMIT_STORE[session_id] = []
    _RATE_LIMIT_STORE[session_id].append(now)


def reset_rate_limit(session_id: str = "default_session"):
    """Reset rate limiter for tests or administrative use."""
    if session_id in _RATE_LIMIT_STORE:
        _RATE_LIMIT_STORE[session_id] = []


# ==============================================================================
# 3. RECIPIENT VERIFICATION (OTP)
# ==============================================================================

def generate_otp_code() -> str:
    """Generate a cryptographically secure 6-digit verification code."""
    return f"{secrets.randbelow(900000) + 100000}"


def create_otp_record(email: str, code: str) -> Dict[str, Any]:
    """Create a salted hash record for OTP verification. Never stores plain code."""
    salt = secrets.token_hex(16)
    salted_hash = hashlib.sha256((salt + code.strip()).encode("utf-8")).hexdigest()
    return {
        "email_hash": hash_email(email),
        "salt": salt,
        "hash": salted_hash,
        "expires_at": time.time() + OTP_EXPIRY_SECONDS,
        "attempts": 0,
        "created_at": time.time()
    }


def verify_otp_code(otp_record: Optional[Dict[str, Any]], entered_code: str, email: str) -> Tuple[bool, str]:
    """Verify an entered 6-digit code against the salted hash record. Enforces expiry & attempt limits."""
    if not otp_record:
        return False, "No verification request found. Please request a new verification code."

    now = time.time()
    if now > otp_record.get("expires_at", 0):
        return False, "Verification code has expired (valid for 10 minutes). Please request a new code."

    if otp_record.get("attempts", 0) >= OTP_MAX_ATTEMPTS:
        return False, "Maximum verification attempts exceeded (5 attempts). Please request a new code."

    if otp_record.get("email_hash") != hash_email(email):
        return False, "Email address does not match the active verification request."

    otp_record["attempts"] = otp_record.get("attempts", 0) + 1
    salt = otp_record.get("salt", "")
    target_hash = otp_record.get("hash", "")
    computed_hash = hashlib.sha256((salt + entered_code.strip()).encode("utf-8")).hexdigest()

    if hmac.compare_digest(target_hash, computed_hash):
        return True, "Email verified successfully."

    remaining = max(0, OTP_MAX_ATTEMPTS - otp_record["attempts"])
    return False, f"Incorrect verification code ({remaining} attempt{'s' if remaining != 1 else ''} remaining)."


def send_otp_email(recipient: str, code: str, session_id: str = "default_session") -> Dict[str, Any]:
    """Send a 6-digit verification code to the recipient address."""
    start_time = time.time()

    valid, err_msg = validate_recipient(recipient)
    if not valid:
        return {
            "status": "INVALID_RECIPIENT",
            "message_id": None,
            "error": err_msg,
            "duration_ms": int((time.time() - start_time) * 1000)
        }

    email_h = hash_email(recipient)
    counts = get_email_dispatch_counts(email_h, session_id)
    if counts["hourly_address_otp"] >= MAX_OTP_PER_HOUR_ADDRESS:
        return {
            "status": "RATE_LIMITED_OTP",
            "message_id": None,
            "error": f"Maximum verification requests reached for this address (limit {MAX_OTP_PER_HOUR_ADDRESS} per hour). Please try again later.",
            "duration_ms": int((time.time() - start_time) * 1000)
        }

    sender_addr = get_gmail_address() or "noreply@methodwise.ai"
    sender_name = get_email_from_name()
    reply_to = get_email_reply_to()

    msg = EmailMessage()
    msg["Subject"] = f"Your MethodWise Verification Code: {code}"
    msg["From"] = f"{sender_name} <{sender_addr}>"
    msg["To"] = recipient.strip()
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="methodwise.ai")
    if reply_to:
        msg["Reply-To"] = reply_to

    text_body = f"""MethodWise • Email Verification Code

Hello,

Your 6-digit verification code for MethodWise is:

    {code}

This code is valid for 10 minutes and can be used to verify your email address for PDF report delivery.

PRIVACY & SECURITY:
Your email address is used solely to dispatch your requested methodology report and is not stored or shared.

DELIVERABILITY NOTICE:
You received this email because a verification code was requested at MethodWise. If you did not initiate this request, please disregard this email.

Warm regards,
{sender_name}
"""
    msg.set_content(text_body)

    html_body = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.5; color: #0F172A; background-color: #FAF7F2; margin: 0; padding: 24px; }}
  .container {{ max-width: 520px; margin: 0 auto; background: #FFFFFF; border: 1px solid #E7E2D9; border-radius: 8px; overflow: hidden; }}
  .header {{ background-color: #3730A3; color: #FFFFFF; padding: 20px 24px; }}
  .header h1 {{ margin: 0; font-size: 18px; font-weight: 700; }}
  .content {{ padding: 28px 24px; }}
  .code-box {{ background-color: #EEF2FF; border: 2px dashed #C7D2FE; border-radius: 8px; padding: 18px; text-align: center; margin: 20px 0; font-family: 'Courier New', monospace; font-size: 32px; font-weight: 700; letter-spacing: 6px; color: #3730A3; }}
  .footer {{ background-color: #F8FAFC; border-top: 1px solid #E7E2D9; padding: 14px 24px; font-size: 11px; color: #64748B; line-height: 1.4; }}
</style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>MethodWise • Email Verification</h1>
    </div>
    <div class="content">
      <p style="margin-top: 0; font-size: 15px;">Hello,</p>
      <p style="font-size: 14px; color: #475569;">
        Use the following 6-digit code to verify your recipient email address for methodology report delivery:
      </p>
      <div class="code-box">{code}</div>
      <p style="font-size: 13px; color: #64748B;">
        ⏳ This code expires in <strong>10 minutes</strong>. Never share this code.
      </p>
    </div>
    <div class="footer">
      <strong>Deliverability Notice:</strong> You received this email because a verification code was requested at MethodWise. If you did not initiate this request, please disregard this email.
    </div>
  </div>
</body>
</html>
"""
    msg.add_alternative(html_body, subtype="html")

    backend = get_email_backend()
    send_res = backend.send(msg)
    duration_ms = int((time.time() - start_time) * 1000)
    send_res["duration_ms"] = duration_ms

    if send_res.get("status") == "SENT":
        record_email_dispatch(email_hash=email_h, session_id=session_id, email_type="OTP")

    return send_res


# ==============================================================================
# 4. REPORT CONTENT BUILDER
# ==============================================================================

def build_email_content(
    recipient: str,
    sender_address: str,
    sender_name: str,
    subject: str,
    research_question: str,
    paradigm: str,
    design: str,
    confidence: str,
    validation_label: str,
    roadmap_preview: List[str],
    pdf_bytes: bytes,
    pdf_filename: str,
    reply_to: Optional[str] = None
) -> EmailMessage:
    """Construct multipart MIME email message with styled academic HTML and attached PDF."""
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{sender_address}>"
    msg["To"] = recipient
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="methodwise.ai")
    if reply_to:
        msg["Reply-To"] = reply_to

    # Roadmap preview lines formatted
    roadmap_text = "\n".join([f"  • {step}" for step in roadmap_preview]) if roadmap_preview else "  • Phased execution schedule detailed in PDF."
    roadmap_html = "".join([f"<li style='margin-bottom: 4px;'>{step}</li>" for step in roadmap_preview]) if roadmap_preview else "<li>Phased execution schedule detailed in PDF.</li>"

    # Plain text body
    text_content = f"""MethodWise • Academic Research Methodology Recommendation

Dear Researcher,

Your research methodology specification has been generated and validated by MethodWise.

RESEARCH QUESTION:
"{research_question}"

CORE SPECIFICATION:
• Recommended Paradigm: {paradigm}
• Specific Design: {design}
• Confidence Level: {confidence}
• Validation Outcome: {validation_label}

PHASED ROADMAP PREVIEW:
{roadmap_text}

ATTACHMENT:
The full, publication-grade Methodology Brief has been attached as a PDF ({pdf_filename}).

ACADEMIC ADVISORY:
This report provides algorithmic decision support to guide methodological planning. It does not replace doctoral supervisor consultation or mandatory Institutional Review Board (IRB / REC) approval.

DELIVERABILITY & CONSENT NOTICE:
You received this email because you requested a methodology report from MethodWise. Your email address was used solely for this dispatch and is not stored. If you did not request this report, please disregard this email.

Warm regards,
{sender_name}
"""
    msg.set_content(text_content)

    # HTML body with scholarly editorial palette
    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.5; color: #0F172A; background-color: #FAF7F2; margin: 0; padding: 24px; }}
  .container {{ max-width: 600px; margin: 0 auto; background: #FFFFFF; border: 1px solid #E7E2D9; border-radius: 8px; overflow: hidden; }}
  .header {{ background-color: #3730A3; color: #FFFFFF; padding: 24px 28px; }}
  .header h1 {{ margin: 0; font-size: 20px; font-weight: 700; }}
  .header p {{ margin: 4px 0 0 0; color: #E0E7FF; font-size: 13px; }}
  .content {{ padding: 28px; }}
  .question-box {{ background-color: #FAF7F2; border-left: 3px solid #3730A3; padding: 12px 16px; margin-bottom: 20px; font-style: italic; color: #1E293B; }}
  .spec-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
  .spec-table td {{ padding: 8px 12px; border-bottom: 1px solid #EFECE6; font-size: 14px; }}
  .spec-table td.label {{ color: #64748B; width: 38%; font-weight: 600; }}
  .badge {{ display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: 700; }}
  .badge-pass {{ background-color: #F0FDFA; color: #0F766E; border: 1px solid #99F6E4; }}
  .badge-review {{ background-color: #FEF3C7; color: #B45309; border: 1px solid #FDE68A; }}
  .roadmap-box {{ background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 14px 18px; margin-bottom: 20px; font-size: 13px; }}
  .roadmap-box ul {{ margin: 6px 0 0 0; padding-left: 18px; }}
  .footer {{ background-color: #F8FAFC; border-top: 1px solid #E7E2D9; padding: 16px 28px; font-size: 11px; color: #64748B; line-height: 1.4; }}
</style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>MethodWise Academic Research Assistant</h1>
      <p>Research Methodology Recommendation Specification</p>
    </div>
    <div class="content">
      <p style="margin-top: 0; font-size: 15px;">Dear Researcher,</p>
      <p style="font-size: 14px; color: #475569;">
        Your methodology recommendation has been synthesized and validated. Here is your executive summary:
      </p>

      <div class="question-box">
        &ldquo;{research_question}&rdquo;
      </div>

      <table class="spec-table">
        <tr>
          <td class="label">Recommended Paradigm</td>
          <td><strong style="color: #3730A3;">{paradigm}</strong></td>
        </tr>
        <tr>
          <td class="label">Specific Design</td>
          <td><strong>{design}</strong></td>
        </tr>
        <tr>
          <td class="label">Confidence Level</td>
          <td>{confidence}</td>
        </tr>
        <tr>
          <td class="label">Validation Status</td>
          <td><span class="badge { 'badge-pass' if validation_label == 'PASS' else 'badge-review' }">{validation_label}</span></td>
        </tr>
      </table>

      <div class="roadmap-box">
        <strong>Execution Roadmap Highlights:</strong>
        <ul>
          {roadmap_html}
        </ul>
      </div>

      <p style="font-size: 13px; color: #475569;">
        <strong>Attached Report:</strong> The comprehensive, 10-clause publication-grade specification is attached as <code>{pdf_filename}</code>.
      </p>
    </div>
    <div class="footer">
      <strong>Deliverability & Consent Notice:</strong> You received this email because you requested a methodology report from MethodWise. Your email address was used solely for this dispatch and is not stored. If you did not request this report, please disregard this email.<br><br>
      <strong>Academic Advisory:</strong> This report provides algorithmic decision support to guide methodological planning. It does not replace doctoral supervisor consultation or mandatory Institutional Review Board (IRB / REC) approval.
    </div>
  </div>
</body>
</html>
"""
    msg.add_alternative(html_content, subtype="html")

    # Attach PDF
    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=pdf_filename
    )

    return msg


# ==============================================================================
# 5. MAIN DISPATCH INTERFACE (send_report_email)
# ==============================================================================

def send_report_email(
    recipient: Optional[str],
    run_record: Dict[str, Any],
    pdf_path: Optional[str],
    summary: Optional[Dict[str, Any]] = None,
    is_review: bool = False,
    session_id: str = "default_session",
    is_verified: bool = False
) -> Dict[str, Any]:
    """Send recommendation PDF report via configured EmailBackend with verification check and multi-tier rate limiting."""
    start_time = time.time()
    summary = summary or {}

    # Check 1: Consent & recipient provided
    if not recipient or not recipient.strip():
        duration_ms = int((time.time() - start_time) * 1000)
        return {
            "status": "SKIPPED_NO_CONSENT",
            "message_id": None,
            "error": "No recipient email address provided.",
            "duration_ms": duration_ms
        }

    # Check 2: Recipient validation & anti-injection
    valid_rec, rec_err = validate_recipient(recipient)
    if not valid_rec:
        duration_ms = int((time.time() - start_time) * 1000)
        return {
            "status": "INVALID_RECIPIENT",
            "message_id": None,
            "error": rec_err,
            "duration_ms": duration_ms
        }

    # Check 3: OTP Recipient Verification Check
    if not is_verified:
        duration_ms = int((time.time() - start_time) * 1000)
        return {
            "status": "UNVERIFIED",
            "message_id": None,
            "error": "Recipient email address has not been verified via OTP. Please verify your email before requesting report delivery.",
            "duration_ms": duration_ms
        }

    # Check 4: Multi-tier Rate Limits (SQLite + in-memory window)
    email_h = hash_email(recipient)
    counts = get_email_dispatch_counts(email_h, session_id)
    daily_cap = get_email_daily_cap()

    # 4a. Global daily cap
    if counts["daily_global"] >= daily_cap:
        duration_ms = int((time.time() - start_time) * 1000)
        return {
            "status": "RATE_LIMITED_GLOBAL",
            "message_id": None,
            "error": f"Daily global email limit ({daily_cap}) reached for today. You can download your PDF report directly below.",
            "duration_ms": duration_ms
        }

    # 4b. Per-address hourly limit (max 3/hour)
    if counts["hourly_address"] >= MAX_REPORTS_PER_HOUR_ADDRESS:
        duration_ms = int((time.time() - start_time) * 1000)
        return {
            "status": "RATE_LIMITED_ADDRESS",
            "message_id": None,
            "error": f"Hourly limit reached for this address (maximum {MAX_REPORTS_PER_HOUR_ADDRESS} report emails per hour). You can download your PDF report directly below.",
            "duration_ms": duration_ms
        }

    # 4c. Per-session hourly limit (max 5/hour)
    if counts["hourly_session"] >= MAX_EMAILS_PER_HOUR_SESSION:
        duration_ms = int((time.time() - start_time) * 1000)
        return {
            "status": "RATE_LIMITED_SESSION",
            "message_id": None,
            "error": f"Hourly session limit reached (maximum {MAX_EMAILS_PER_HOUR_SESSION} report emails per hour). You can download your PDF report directly below.",
            "duration_ms": duration_ms
        }

    # In-memory sliding window check
    rate_ok, rate_msg = check_rate_limit(session_id)
    if not rate_ok:
        duration_ms = int((time.time() - start_time) * 1000)
        return {
            "status": "FAILED",
            "message_id": None,
            "error": rate_msg,
            "duration_ms": duration_ms
        }

    # Check 5: Backend configuration check
    backend = get_email_backend()
    if isinstance(backend, GmailSMTPBackend) and not is_gmail_configured():
        duration_ms = int((time.time() - start_time) * 1000)
        return {
            "status": "SKIPPED_NO_CREDENTIALS",
            "message_id": None,
            "error": "Gmail credentials (GMAIL_ADDRESS and GMAIL_APP_PASSWORD) are not configured in environment.",
            "duration_ms": duration_ms
        }

    # Check 6: PDF Attachment validation
    if not pdf_path or not os.path.exists(pdf_path):
        duration_ms = int((time.time() - start_time) * 1000)
        return {
            "status": "FAILED",
            "message_id": None,
            "error": f"PDF attachment file not found at: {pdf_path}",
            "duration_ms": duration_ms
        }

    file_size = os.path.getsize(pdf_path)
    if file_size > MAX_ATTACHMENT_BYTES:
        duration_ms = int((time.time() - start_time) * 1000)
        return {
            "status": "FAILED",
            "message_id": None,
            "error": f"Attachment size ({file_size / (1024*1024):.1f} MB) exceeds maximum limit of 10 MB.",
            "duration_ms": duration_ms
        }

    try:
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return {
            "status": "FAILED",
            "message_id": None,
            "error": f"Failed to read PDF attachment: {e}",
            "duration_ms": duration_ms
        }

    # Extract metadata for email
    raw_q = run_record.get("research_question", "Your research inquiry")
    short_q = raw_q[:48] + "..." if len(raw_q) > 48 else raw_q
    pdf_filename = os.path.basename(pdf_path)

    subject_prefix = "Supervisor Review Needed: " if is_review else ""
    subject = f"{subject_prefix}Your research methodology recommendation: {short_q}"

    sender_addr = get_gmail_address() or "noreply@methodwise.ai"
    sender_name = get_email_from_name()
    reply_to = get_email_reply_to()

    paradigm = summary.get("paradigm", "Specified in PDF")
    design = summary.get("design", "Specified in PDF")
    confidence = summary.get("confidence", "Evaluated")
    val_label = summary.get("label", "DELIVERED")
    roadmap_preview = summary.get("roadmap_preview", [])

    # Build MIME message
    msg = build_email_content(
        recipient=recipient.strip(),
        sender_address=sender_addr,
        sender_name=sender_name,
        subject=subject,
        research_question=raw_q,
        paradigm=paradigm,
        design=design,
        confidence=confidence,
        validation_label=val_label,
        roadmap_preview=roadmap_preview,
        pdf_bytes=pdf_bytes,
        pdf_filename=pdf_filename,
        reply_to=reply_to
    )

    # Dispatch via backend
    result = backend.send(msg)
    duration_ms = int((time.time() - start_time) * 1000)
    result["duration_ms"] = duration_ms

    if result.get("status") == "SENT":
        record_email_dispatch(email_hash=email_h, session_id=session_id, email_type="REPORT")
        record_email_sent(session_id)

    return result
