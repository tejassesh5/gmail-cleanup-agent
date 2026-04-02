import os

# Path to your downloaded Google OAuth credentials JSON
CREDENTIALS_FILE = os.environ.get("GMAIL_CREDENTIALS_FILE", "credentials.json")

# Token cache (auto-created after first login)
TOKEN_FILE = "token.json"

# Gmail OAuth scopes
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.readonly",
]

# Gemini model for AI classification
GEMINI_MODEL = "gemini-1.5-flash"

# --- Cleanup defaults (can be overridden via CLI) ---
DEFAULT_DAYS_OLD = 30          # Delete emails older than this many days
DEFAULT_MAX_ATTACHMENT_MB = 10  # Delete emails with attachments larger than this (MB)
BATCH_SIZE = 100                # Gmail API batch delete size
