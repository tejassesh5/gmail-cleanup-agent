"""Gmail search query builders and message fetchers."""
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


def query_spam_promotions() -> str:
    return "category:promotions OR category:spam OR label:spam"


def query_older_than(days: int) -> str:
    cutoff = datetime.now() - timedelta(days=days)
    return f"before:{cutoff.strftime('%Y/%m/%d')}"


def query_large_attachments(min_mb: int) -> str:
    min_bytes = min_mb * 1024 * 1024
    return f"has:attachment larger:{min_bytes}"


def query_unsubscribable() -> str:
    return 'unsubscribe OR "opt out" OR "opt-out" OR "manage preferences"'


def fetch_message_ids(service, query: str, max_results: int = 500) -> list[str]:
    """Return all message IDs matching a Gmail search query."""
    ids = []
    page_token = None
    while True:
        params = {"userId": "me", "q": query, "maxResults": min(max_results - len(ids), 500)}
        if page_token:
            params["pageToken"] = page_token
        resp = service.users().messages().list(**params).execute()
        messages = resp.get("messages", [])
        ids.extend(m["id"] for m in messages)
        page_token = resp.get("nextPageToken")
        if not page_token or len(ids) >= max_results:
            break
    return ids


def get_message_headers(service, msg_id: str) -> dict:
    """Fetch minimal headers for a message."""
    msg = service.users().messages().get(
        userId="me", id=msg_id, format="metadata",
        metadataHeaders=["From", "Subject", "List-Unsubscribe", "Date"]
    ).execute()
    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
    headers["_id"] = msg_id
    headers["_size"] = msg.get("sizeEstimate", 0)
    return headers
