"""Core cleanup operations: delete, trash, unsubscribe."""
import re
import urllib.request
from config import BATCH_SIZE


def batch_delete(service, message_ids: list[str]) -> int:
    """Permanently delete messages in batches. Returns count deleted."""
    total = 0
    for i in range(0, len(message_ids), BATCH_SIZE):
        chunk = message_ids[i:i + BATCH_SIZE]
        service.users().messages().batchDelete(
            userId="me", body={"ids": chunk}
        ).execute()
        total += len(chunk)
    return total


def batch_trash(service, message_ids: list[str]) -> int:
    """Move messages to Trash in batches. Returns count trashed."""
    total = 0
    for msg_id in message_ids:
        service.users().messages().trash(userId="me", id=msg_id).execute()
        total += 1
    return total


def extract_unsubscribe_url(header_value: str) -> str | None:
    """Parse List-Unsubscribe header and return the HTTP URL if present."""
    if not header_value:
        return None
    urls = re.findall(r'<(https?://[^>]+)>', header_value)
    return urls[0] if urls else None


def one_click_unsubscribe(service, msg_id: str, unsubscribe_url: str) -> bool:
    """Attempt a GET request to the unsubscribe URL. Returns True on success."""
    try:
        req = urllib.request.Request(
            unsubscribe_url,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception:
        return False


def mark_as_read(service, message_ids: list[str]) -> None:
    for msg_id in message_ids:
        service.users().messages().modify(
            userId="me", id=msg_id,
            body={"removeLabelIds": ["UNREAD"]}
        ).execute()
