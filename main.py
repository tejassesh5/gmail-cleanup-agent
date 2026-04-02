"""Gmail Cleanup Agent — interactive CLI."""
import sys
from gmail_auth import get_service
from gmail_queries import (
    fetch_message_ids,
    get_message_headers,
    query_spam_promotions,
    query_older_than,
    query_large_attachments,
    query_unsubscribable,
)
from cleaner import batch_delete, batch_trash, extract_unsubscribe_url, one_click_unsubscribe
from agent import should_delete, summarize_plan
from config import DEFAULT_DAYS_OLD, DEFAULT_MAX_ATTACHMENT_MB


def hr():
    print("-" * 55)


def header():
    print("\n" + "=" * 55)
    print("        GMAIL CLEANUP AGENT  (Gemini-powered)")
    print("=" * 55)


def confirm(prompt: str) -> bool:
    return input(f"{prompt} [y/N]: ").strip().lower() == "y"


def preview_emails(service, ids, limit=None):
    """Print a preview table of emails before deletion."""
    print(f"\n  {'#':<4} {'From':<35} {'Subject':<45}")
    print(f"  {'-'*4} {'-'*35} {'-'*45}")
    show = ids if limit is None else ids[:limit]
    for i, msg_id in enumerate(show, 1):
        h = get_message_headers(service, msg_id)
        sender = h.get("From", "unknown")[:33]
        subject = h.get("Subject", "(no subject)")[:43]
        print(f"  {i:<4} {sender:<35} {subject:<45}")
    print()


def run_spam_cleanup(service):
    print("\n[1/4] Scanning spam & promotions...")
    ids = fetch_message_ids(service, query_spam_promotions())
    if not ids:
        print("  Nothing found.")
        return 0
    print(f"  Found {len(ids)} emails. Fetching preview...")
    preview_emails(service, ids)
    if confirm(f"  Permanently delete all {len(ids)} spam/promotion emails?"):
        deleted = batch_delete(service, ids)
        print(f"  Deleted {deleted} emails.")
        return deleted
    return 0


def run_unsubscribe(service):
    print("\n[2/4] Scanning mailing lists...")
    ids = fetch_message_ids(service, query_unsubscribable(), max_results=100)
    if not ids:
        print("  No mailing list emails found.")
        return 0

    unsub_targets = []
    seen_senders = set()
    for msg_id in ids:
        headers = get_message_headers(service, msg_id)
        sender = headers.get("From", "")
        unsub_header = headers.get("List-Unsubscribe", "")
        url = extract_unsubscribe_url(unsub_header)
        if url and sender not in seen_senders:
            seen_senders.add(sender)
            unsub_targets.append({
                "id": msg_id,
                "sender": sender,
                "subject": headers.get("Subject", "(no subject)"),
                "url": url,
            })

    if not unsub_targets:
        print("  No unsubscribe links found.")
        return 0

    print(f"\n  Found {len(unsub_targets)} unique mailing lists:\n")
    for i, t in enumerate(unsub_targets, 1):
        print(f"  [{i}] {t['sender']}")
        print(f"      {t['subject'][:60]}")

    print()
    if not confirm(f"  Unsubscribe from all {len(unsub_targets)} and delete their emails?"):
        return 0

    success = 0
    for t in unsub_targets:
        result = one_click_unsubscribe(service, t["id"], t["url"])
        status = "OK" if result else "FAILED"
        print(f"  {status}  {t['sender']}")
        if result:
            success += 1

    # Delete all matching emails from those senders
    all_ids = fetch_message_ids(service, query_unsubscribable(), max_results=500)
    if all_ids:
        batch_delete(service, all_ids)
        print(f"  Deleted {len(all_ids)} mailing list emails.")
    return success


def run_old_email_cleanup(service):
    days = input(f"\n[3/4] Delete emails older than how many days? [{DEFAULT_DAYS_OLD}]: ").strip()
    days = int(days) if days.isdigit() else DEFAULT_DAYS_OLD
    print(f"  Scanning for emails older than {days} days...")
    ids = fetch_message_ids(service, query_older_than(days))
    if not ids:
        print("  Nothing found.")
        return 0
    print(f"  Found {len(ids)} emails older than {days} days. Fetching preview...")
    preview_emails(service, ids)
    if confirm(f"  Permanently delete all {len(ids)} old emails?"):
        deleted = batch_delete(service, ids)
        print(f"  Deleted {deleted} emails.")
        return deleted
    return 0


def run_large_attachment_cleanup(service):
    mb = input(f"\n[4/4] Delete emails with attachments larger than how many MB? [{DEFAULT_MAX_ATTACHMENT_MB}]: ").strip()
    mb = int(mb) if mb.isdigit() else DEFAULT_MAX_ATTACHMENT_MB
    print(f"  Scanning for emails with attachments > {mb} MB...")
    ids = fetch_message_ids(service, query_large_attachments(mb))
    if not ids:
        print("  Nothing found.")
        return 0

    print(f"  Found {len(ids)} large-attachment emails. Fetching preview...")
    preview_emails(service, ids)
    print("  Sampling top emails for AI review...")

    sample = ids[:10]
    ai_flagged = []
    for msg_id in sample:
        h = get_message_headers(service, msg_id)
        if should_delete(h.get("Subject", ""), h.get("From", "")):
            ai_flagged.append(msg_id)

    print(f"  AI confirmed {len(ai_flagged)}/{len(sample)} sampled emails are safe to delete.")
    if confirm(f"  Delete all {len(ids)} large-attachment emails?"):
        deleted = batch_delete(service, ids)
        print(f"  Deleted {deleted} emails.")
        return deleted
    return 0


def run_full_cleanup(service):
    actions = {
        "spam": len(fetch_message_ids(service, query_spam_promotions())),
        "unsubscribe": 0,
        "old": len(fetch_message_ids(service, query_older_than(DEFAULT_DAYS_OLD))),
        "large": len(fetch_message_ids(service, query_large_attachments(DEFAULT_MAX_ATTACHMENT_MB))),
    }
    print("\nAnalyzing your inbox...")
    summary = summarize_plan(actions)
    print(f"\n  {summary}\n")


def main():
    header()
    print("\nConnecting to Gmail...")
    try:
        service = get_service()
        print("Connected.\n")
    except Exception as e:
        print(f"Auth failed: {e}")
        sys.exit(1)

    while True:
        hr()
        print("  [1] Delete spam & promotions")
        print("  [2] Unsubscribe from mailing lists")
        print("  [3] Delete emails older than X days")
        print("  [4] Delete large attachment emails")
        print("  [5] Run full cleanup (all of the above)")
        print("  [6] Preview inbox summary (AI)")
        print("  [0] Quit")
        hr()
        choice = input("Choice: ").strip()

        if choice == "1":
            run_spam_cleanup(service)
        elif choice == "2":
            run_unsubscribe(service)
        elif choice == "3":
            run_old_email_cleanup(service)
        elif choice == "4":
            run_large_attachment_cleanup(service)
        elif choice == "5":
            print("\nRunning full cleanup...")
            run_spam_cleanup(service)
            run_unsubscribe(service)
            run_old_email_cleanup(service)
            run_large_attachment_cleanup(service)
            print("\nFull cleanup complete.")
        elif choice == "6":
            run_full_cleanup(service)
        elif choice == "0":
            print("Goodbye.")
            sys.exit(0)
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
