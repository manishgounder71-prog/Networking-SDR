"""
storage.py — Google Sheets integration for lead CRM storage.
Uses gspread + service account credentials. Falls back to CSV if unavailable.
"""

import os
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Networking_SDR_Leads")
CREDS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

# Column definitions for the Google Sheet
COLUMNS = [
    "Timestamp",
    "Name",
    "Company",
    "LinkedIn URL",
    "Tags",
    "Lead Score",
    "Sentiment",
    "Email Subject",
    "Opener",
    "Value Prop",
    "CTA",
    "News Summary",
    "Returning Lead",
    "Notes",
]

# ── CSV Fallback path ──────────────────────────────────────────────────────
FALLBACK_CSV = Path(__file__).parent / "leads_fallback.csv"

# ── Try gspread ────────────────────────────────────────────────────────────
_sheet = None
_use_sheets = False

try:
    import gspread
    from google.oauth2.service_account import Credentials

    creds_path = Path(CREDS_FILE)
    if creds_path.exists():
        scopes = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_file(str(creds_path), scopes=scopes)
        gc = gspread.authorize(creds)

        try:
            spreadsheet = gc.open(SHEET_NAME)
        except gspread.SpreadsheetNotFound:
            spreadsheet = gc.create(SHEET_NAME)
            print(f"[Storage] Created new Google Sheet: {SHEET_NAME}")

        _sheet = spreadsheet.sheet1

        # Init headers if the sheet is empty
        if not _sheet.row_values(1):
            _sheet.append_row(COLUMNS)
            print("[Storage] OK: Headers written to Google Sheet.")

        _use_sheets = True
        print(f"[Storage] OK: Google Sheets connected: '{SHEET_NAME}'")
    else:
        print(f"[Storage] WARNING: Credentials file '{CREDS_FILE}' not found.")
except Exception as e:
    print(f"[Storage] INFO: Google Sheets not available ({e}). Using CSV fallback.")

# Ensure CSV fallback has headers
if not _use_sheets and not FALLBACK_CSV.exists():
    with open(FALLBACK_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)


# ── Public API ─────────────────────────────────────────────────────────────

def save_lead(
    name: str,
    company: Optional[str],
    linkedin_url: Optional[str],
    suggestions: dict,
    research: dict,
    is_returning: bool,
    notes: Optional[str] = None,
) -> dict:
    """
    Saves a processed lead to Google Sheets (or CSV fallback).
    Returns a dict with status and row info.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tags = ", ".join(suggestions.get("tags", []))
    news_summary = research.get("summary", "")
    score = suggestions.get("score", 0)
    sentiment = suggestions.get("sentiment", "Neutral")

    row = [
        timestamp,
        name,
        company or "",
        linkedin_url or "",
        tags,
        score,
        sentiment,
        suggestions.get("subject", ""),
        suggestions.get("opener", ""),
        suggestions.get("value_prop", ""),
        suggestions.get("call_to_action", ""),
        news_summary,
        "Yes" if is_returning else "No",
        notes or "",
    ]

    if _use_sheets and _sheet:
        try:
            _sheet.append_row(row)
            return {"saved_to": "google_sheets", "sheet": SHEET_NAME}
        except Exception as e:
            print(f"[Storage] Sheet write error: {e}. Falling back to CSV.")

    # CSV Fallback
    with open(FALLBACK_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)

    return {"saved_to": "csv", "file": str(FALLBACK_CSV)}


def get_storage_status() -> dict:
    """Returns the current storage backend status."""
    if _use_sheets:
        return {"backend": "Google Sheets", "sheet": SHEET_NAME, "connected": True}
    return {"backend": "CSV Fallback", "file": str(FALLBACK_CSV), "connected": False}
