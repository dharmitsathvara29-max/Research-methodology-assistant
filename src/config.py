"""Configuration, environment loading, and Gemini SDK client manager with automated model fallback."""

import os
import time
import socket
from typing import Optional, List, Any
from dotenv import load_dotenv

# Ensure robust, fast DNS resolution on macOS by prioritizing IPv4
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_preferring_getaddrinfo(*args, **kwargs):
    try:
        res = _orig_getaddrinfo(*args, **kwargs)
        ipv4_res = [r for r in res if r[0] == socket.AF_INET]
        return ipv4_res if ipv4_res else res
    except Exception:
        return _orig_getaddrinfo(*args, **kwargs)

socket.getaddrinfo = _ipv4_preferring_getaddrinfo

# Load environment variables
load_dotenv()

DEFAULT_PRIMARY_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
FALLBACK_MODELS_ENV = os.getenv("FALLBACK_MODELS", "gemini-3.1-flash-lite,gemini-3.5-flash-lite")
FALLBACK_MODELS = [m.strip() for m in FALLBACK_MODELS_ENV.split(",") if m.strip()]


def get_api_key() -> Optional[str]:
    """Retrieve GEMINI_API_KEY from environment or return None if missing/blank."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    return key if key else None


def is_api_configured() -> bool:
    """Return True if a non-empty API key is available."""
    key = get_api_key()
    return bool(key and key != "your_gemini_api_key_here")


def get_genai_client():
    """Instantiate and return the google.genai Client, or None if unconfigured."""
    if not is_api_configured():
        return None
    try:
        from google import genai
        from google.genai import types
        # Note: timeout is in milliseconds (120,000 ms = 120 seconds)
        http_options = types.HttpOptions(
            timeout=120000,
            retry_options=types.HttpRetryOptions(
                attempts=2,
                initial_delay=1.0,
                max_delay=3.0
            )
        )
        return genai.Client(api_key=get_api_key(), http_options=http_options)
    except Exception as e:
        try:
            print(f"Error initializing genai Client: {e}")
        except (OSError, IOError):
            pass
        return None


def call_gemini_model(
    contents: str,
    system_instruction: Optional[str] = None,
    temperature: float = 0.2,
    response_schema: Optional[Any] = None,
    preferred_model: Optional[str] = None
) -> str:
    """Execute generate_content against Gemini with automatic fallback on transient errors."""
    client = get_genai_client()
    if not client:
        raise ValueError(
            "Gemini API key is not configured. Please add GEMINI_API_KEY to your .env file or environment."
        )

    primary = preferred_model or DEFAULT_PRIMARY_MODEL
    models_to_try: List[str] = [primary] + [m for m in FALLBACK_MODELS if m != primary]

    last_error = None
    for model_name in models_to_try:
        try:
            # Build request config
            config_params = {"temperature": temperature}
            if system_instruction:
                config_params["system_instruction"] = system_instruction
            if response_schema:
                config_params["response_mime_type"] = "application/json"
                config_params["response_schema"] = response_schema

            # Call SDK
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config_params,
            )
            if response and response.text:
                return response.text
        except Exception as err:
            last_error = err
            time.sleep(0.5)
            continue

    raise RuntimeError(f"All Gemini model attempts failed. Last error: {last_error}")


def get_gmail_address() -> Optional[str]:
    """Retrieve GMAIL_ADDRESS from environment."""
    load_dotenv(override=True)
    addr = os.getenv("GMAIL_ADDRESS", "").strip()
    return addr if addr else None


def get_gmail_app_password() -> Optional[str]:
    """Retrieve GMAIL_APP_PASSWORD from environment, stripping any Google formatting spaces."""
    load_dotenv(override=True)
    pwd = os.getenv("GMAIL_APP_PASSWORD", "").strip()
    if pwd:
        # Strip internal spaces commonly copied from Google App Password screen ("xxxx xxxx xxxx xxxx")
        return pwd.replace(" ", "")
    return None


def get_email_from_name() -> str:
    """Retrieve EMAIL_FROM_NAME or default to 'MethodWise AI'."""
    return os.getenv("EMAIL_FROM_NAME", "MethodWise AI").strip() or "MethodWise AI"


def is_gmail_configured() -> bool:
    """Check if Gmail credentials are fully configured."""
    addr = get_gmail_address()
    pwd = get_gmail_app_password()
    invalid_addrs = {"your_email@gmail.com", "your.app.sender@gmail.com", "example@gmail.com"}
    invalid_pwds = {"your_16_char_app_password", "xxxxxxxxxxxxxxxx"}
    return bool(addr and pwd and addr not in invalid_addrs and pwd not in invalid_pwds and len(pwd) >= 16)


def get_email_backend_name() -> str:
    """Retrieve EMAIL_BACKEND or default to 'gmail'."""
    return os.getenv("EMAIL_BACKEND", "gmail").strip().lower() or "gmail"


def get_email_daily_cap() -> int:
    """Retrieve EMAIL_DAILY_CAP or default to 100."""
    try:
        return int(os.getenv("EMAIL_DAILY_CAP", "100").strip())
    except ValueError:
        return 100


def get_email_reply_to() -> Optional[str]:
    """Retrieve EMAIL_REPLY_TO or None."""
    addr = os.getenv("EMAIL_REPLY_TO", "").strip()
    return addr if addr else None

