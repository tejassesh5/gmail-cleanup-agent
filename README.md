# Gmail Cleanup Agent

An AI-powered Gmail cleanup agent that automatically removes spam, unsubscribes from mailing lists, deletes old emails, and clears large attachment emails — all from an interactive CLI.

---

## Features

| Feature | Description |
|---------|-------------|
| Spam & Promotions | Auto-detects and permanently deletes spam and promotional emails |
| Unsubscribe | Finds mailing lists, clicks unsubscribe links, and deletes all their emails |
| Old Emails | Deletes all emails older than X days (you choose) |
| Large Attachments | Finds and deletes emails with attachments above a size threshold |
| AI Review | Uses Gemini to confirm borderline emails are safe to delete |
| Full Cleanup | Runs all four operations in one go |

---

## Project Structure

```
gmail-cleanup-agent/
├── main.py             # CLI entry point and interactive menu
├── gmail_auth.py       # Gmail OAuth 2.0 authentication
├── gmail_queries.py    # Gmail search query builders and message fetchers
├── cleaner.py          # Delete, trash, and unsubscribe operations
├── agent.py            # Gemini AI classification and summarization
├── config.py           # Configuration and defaults
├── requirements.txt    # Python dependencies
└── .gitignore
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/tejassesh5/gmail-cleanup-agent.git
cd gmail-cleanup-agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Google Cloud — Gmail API credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (e.g. `gmail-cleanup-agent`)
3. Enable the **Gmail API** — APIs & Services → Library → search "Gmail API" → Enable
4. Go to **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**
5. Choose **Desktop app** as the application type
6. Download the JSON file, rename it to `credentials.json`, and place it in the project root

### 4. Gemini API key

1. Get a free API key at [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Set it as an environment variable:

```bash
# Windows
set GEMINI_API_KEY=your_key_here

# Linux / Mac
export GEMINI_API_KEY=your_key_here
```

---

## Usage

```bash
python main.py
```

On first run, a browser window opens for Gmail authorization. A `token.json` file is saved for future runs.

### CLI Menu

```
-------------------------------------------------------
  [1] Delete spam & promotions
  [2] Unsubscribe from mailing lists
  [3] Delete emails older than X days
  [4] Delete large attachment emails
  [5] Run full cleanup (all of the above)
  [6] Preview inbox summary (AI)
  [0] Quit
-------------------------------------------------------
```

---

## Configuration

Edit `config.py` to change defaults:

| Setting | Default | Description |
|---------|---------|-------------|
| `CREDENTIALS_FILE` | `credentials.json` | Path to your Google OAuth credentials |
| `TOKEN_FILE` | `token.json` | Where the OAuth token is cached |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Gemini model used for AI classification |
| `DEFAULT_DAYS_OLD` | `30` | Default age threshold for old email deletion |
| `DEFAULT_MAX_ATTACHMENT_MB` | `10` | Default size threshold for large attachment deletion |
| `BATCH_SIZE` | `100` | Number of emails deleted per API batch call |

---

## Security Notes

- `credentials.json` and `token.json` are in `.gitignore` — never commit them
- The agent only requests `gmail.modify` and `gmail.readonly` scopes — no access to other Google services
- Deletions via option 1/3/4/5 are **permanent** — use option 6 to preview before running

---

## Tech Stack

- **Python 3.11+**
- [Gmail API](https://developers.google.com/gmail/api)
- [google-auth-oauthlib](https://pypi.org/project/google-auth-oauthlib/)
- [google-api-python-client](https://pypi.org/project/google-api-python-client/)
- [google-genai](https://pypi.org/project/google-genai/) — Gemini AI SDK
- [python-dateutil](https://pypi.org/project/python-dateutil/)
