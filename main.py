"""Gmail Cleanup Agent — interactive CLI."""
import sys
from gmail_auth import get_service
from gmail_queries import (
    fetch_message_ids,
    get_message_headers,
    query_spam,
    query_promotions,
    query_ads,
    query_newsletters,
    query_social_notifications,
    query_automated_notifications,
    query_spam_promotions,
    query_older_than,
    query_large_attachments,
    query_unsubscribable,
)
from cleaner import batch_delete, extract_unsubscribe_url, one_click_unsubscribe
from agent import should_delete, summarize_plan
from config import DEFAULT_DAYS_OLD, DEFAULT_MAX_ATTACHMENT_MB

PAGE_SIZE = 100


def hr():
    print("-" * 65)


def header():
    print("\n" + "=" * 65)
    print("           GMAIL CLEANUP AGENT  (Gemini-powered)")
    print("=" * 65)


def confirm(prompt: str) -> bool:
    return input(f"{prompt} [y/N]: ").strip().lower() == "y"


def preview_emails(service, ids):
    """Show emails 100 at a time with pagination."""
    total = len(ids)
    page = 0
    while True:
        start = page * PAGE_SIZE
        end = min(start + PAGE_SIZE, total)
        chunk = ids[start:end]

        print(f"\n  Showing {start + 1}–{end} of {total} emails\n")
        print(f"  {'#':<5} {'From':<35} {'Subject':<40} {'Date':<12}")
        print(f"  {'-'*5} {'-'*35} {'-'*40} {'-'*12}")
        for i, msg_id in enumerate(chunk, start + 1):
            h = get_message_headers(service, msg_id)
            sender = h.get("From", "unknown")[:33]
            subject = h.get("Subject", "(no subject)")[:38]
            date = h.get("Date", "")[:11]
            print(f"  {i:<5} {sender:<35} {subject:<40} {date:<12}")

        print()
        if end >= total:
            print("  (end of list)")
            break
        nav = input(f"  [n] Next 100  [q] Stop previewing: ").strip().lower()
        if nav != "n":
            break
        page += 1
    print()


def run_category_cleanup(service, label, query):
    print(f"\n  Scanning {label}...")
    ids = fetch_message_ids(service, query)
    if not ids:
        print(f"  No {label} found.")
        return 0
    print(f"  Found {len(ids)} emails.")
    if confirm("  Preview before deleting?"):
        preview_emails(service, ids)
    if confirm(f"  Permanently delete all {len(ids)} {label}?"):
        deleted = batch_delete(service, ids)
        print(f"  Deleted {deleted} emails.")
        return deleted
    return 0


def run_spam_menu(service):
    while True:
        print("\n  -- Spam & Email Category Cleanup --")
        hr()
        print("  [1] Spam only")
        print("  [2] Promotions (all)")
        print("  [3] Ad & sale emails only")
        print("  [4] Newsletters & digests only")
        print("  [5] Social notifications (LinkedIn, Twitter, etc.)")
        print("  [6] Automated notifications (orders, alerts, receipts)")
        print("  [7] All of the above")
        print("  [b] Back")
        hr()
        choice = input("  Choice: ").strip().lower()

        if choice == "1":
            run_category_cleanup(service, "spam emails", query_spam())
        elif choice == "2":
            run_category_cleanup(service, "promotion emails", query_promotions())
        elif choice == "3":
            run_category_cleanup(service, "ad & sale emails", query_ads())
        elif choice == "4":
            run_category_cleanup(service, "newsletters", query_newsletters())
        elif choice == "5":
            run_category_cleanup(service, "social notifications", query_social_notifications())
        elif choice == "6":
            run_category_cleanup(service, "automated notifications", query_automated_notifications())
        elif choice == "7":
            for label, query in [
                ("spam", query_spam()),
                ("promotions", query_promotions()),
                ("social notifications", query_social_notifications()),
                ("automated notifications", query_automated_notifications()),
            ]:
                run_category_cleanup(service, label, query)
        elif choice == "b":
            break
        else:
            print("  Invalid choice.")


def run_unsubscribe(service):
    print("\n  Scanning mailing lists...")
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
        print(f"  [{i:>3}] {t['sender'][:50]}")
        print(f"        {t['subject'][:60]}")

    print()
    if not confirm(f"  Unsubscribe from all {len(unsub_targets)} and delete their emails?"):
        return 0

    success = 0
    for t in unsub_targets:
        result = one_click_unsubscribe(service, t["id"], t["url"])
        status = "OK    " if result else "FAILED"
        print(f"  [{status}] {t['sender'][:50]}")
        if result:
            success += 1

    all_ids = fetch_message_ids(service, query_unsubscribable(), max_results=500)
    if all_ids:
        batch_delete(service, all_ids)
        print(f"\n  Deleted {len(all_ids)} mailing list emails.")
    return success


def run_old_email_cleanup(service):
    days = input(f"\n  Delete emails older than how many days? [{DEFAULT_DAYS_OLD}]: ").strip()
    days = int(days) if days.isdigit() else DEFAULT_DAYS_OLD
    print(f"  Scanning for emails older than {days} days...")
    ids = fetch_message_ids(service, query_older_than(days))
    if not ids:
        print("  Nothing found.")
        return 0
    print(f"  Found {len(ids)} emails older than {days} days.")
    if confirm("  Preview before deleting?"):
        preview_emails(service, ids)
    if confirm(f"  Permanently delete all {len(ids)} old emails?"):
        deleted = batch_delete(service, ids)
        print(f"  Deleted {deleted} emails.")
        return deleted
    return 0


def run_large_attachment_cleanup(service):
    mb = input(f"\n  Delete emails with attachments larger than how many MB? [{DEFAULT_MAX_ATTACHMENT_MB}]: ").strip()
    mb = int(mb) if mb.isdigit() else DEFAULT_MAX_ATTACHMENT_MB
    print(f"  Scanning for emails with attachments > {mb} MB...")
    ids = fetch_message_ids(service, query_large_attachments(mb))
    if not ids:
        print("  Nothing found.")
        return 0

    print(f"  Found {len(ids)} large-attachment emails.")
    if confirm("  Preview before deleting?"):
        preview_emails(service, ids)

    sample = ids[:10]
    ai_flagged = []
    print("  Running AI review on sample...")
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
    print("\n  Analyzing your inbox...")
    actions = {
        "spam": len(fetch_message_ids(service, query_spam_promotions())),
        "unsubscribe": 0,
        "old": len(fetch_message_ids(service, query_older_than(DEFAULT_DAYS_OLD))),
        "large": len(fetch_message_ids(service, query_large_attachments(DEFAULT_MAX_ATTACHMENT_MB))),
    }
    summary = summarize_plan(actions)
    print(f"\n  {summary}\n")


def main():
    header()
    print("\n  Connecting to Gmail...")
    try:
        service = get_service()
        print("  Connected.\n")
    except Exception as e:
        print(f"  Auth failed: {e}")
        sys.exit(1)

    while True:
        hr()
        print("  [1] Spam & email category cleanup")
        print("  [2] Unsubscribe from mailing lists")
        print("  [3] Delete emails older than X days")
        print("  [4] Delete large attachment emails")
        print("  [5] Run full cleanup (all of the above)")
        print("  [6] Preview inbox summary (AI)")
        print("  [0] Quit")
        hr()
        choice = input("  Choice: ").strip()

        if choice == "1":
            run_spam_menu(service)
        elif choice == "2":
            run_unsubscribe(service)
        elif choice == "3":
            run_old_email_cleanup(service)
        elif choice == "4":
            run_large_attachment_cleanup(service)
        elif choice == "5":
            print("\n  Running full cleanup...")
            run_spam_menu(service)
            run_unsubscribe(service)
            run_old_email_cleanup(service)
            run_large_attachment_cleanup(service)
            print("\n  Full cleanup complete.")
        elif choice == "6":
            run_full_cleanup(service)
        elif choice == "0":
            print("  Goodbye.")
            sys.exit(0)
        else:
            print("  Invalid choice.")


if __name__ == "__main__":
    main()
