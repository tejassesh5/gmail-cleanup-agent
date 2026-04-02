"""AI agent layer — uses Gemini to classify borderline emails."""
import os
from google import genai
from config import GEMINI_MODEL


def _client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set.\n"
            "Get a key at https://aistudio.google.com/app/apikey\n"
            "Then run:  set GEMINI_API_KEY=your_key_here"
        )
    return genai.Client(api_key=api_key)


def should_delete(subject: str, sender: str) -> bool:
    """Ask Gemini whether an email is safe to delete. Returns True = delete."""
    try:
        client = _client()
        prompt = (
            "You are an email cleanup assistant. Decide if this email is safe to permanently delete.\n"
            "Reply with only YES or NO.\n\n"
            f"From: {sender}\n"
            f"Subject: {subject}\n\n"
            "Is this email safe to permanently delete? (promotional, newsletter, notification, spam)"
        )
        resp = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        return resp.text.strip().upper().startswith("YES")
    except Exception:
        return False


def summarize_plan(actions: dict) -> str:
    """Ask Gemini to summarize the cleanup plan in plain English."""
    try:
        client = _client()
        prompt = (
            f"Summarize this Gmail cleanup plan in 3-4 friendly sentences:\n"
            f"- Spam/Promotions to delete: {actions.get('spam', 0)}\n"
            f"- Mailing lists to unsubscribe: {actions.get('unsubscribe', 0)}\n"
            f"- Old emails to delete: {actions.get('old', 0)}\n"
            f"- Large attachment emails to delete: {actions.get('large', 0)}\n"
        )
        resp = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        return resp.text.strip()
    except Exception:
        total = sum(actions.values())
        return f"Ready to clean up {total} emails across all categories."
