#!/usr/bin/env python3
"""
Google Scholar Alert → Notion Pipeline

Fetches Google Scholar alert emails from Gmail and creates Notion DB records
with Japanese titles, summaries, and explanations via the Anthropic API.
"""

import os
import sys
from datetime import datetime

import anthropic
from notion_client import Client as NotionClient

from ai import extract_papers_with_claude, generate_japanese_content
from config import GMAIL_LABEL
from gmail import (
    extract_keyword_from_subject,
    fetch_recent_threads,
    get_gmail_service,
    get_label_id,
    get_thread_content,
)
from notion import create_notion_page


def main() -> None:
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] Scholar → Notion pipeline starting")

    required = ["ANTHROPIC_API_KEY", "NOTION_TOKEN"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        sys.exit(f"Missing environment variables: {', '.join(missing)}")

    anthropic_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    notion_client = NotionClient(auth=os.environ["NOTION_TOKEN"])
    gmail_service = get_gmail_service()

    label_id = get_label_id(gmail_service, GMAIL_LABEL)
    threads = fetch_recent_threads(gmail_service, label_id, hours=24)
    print(f"Found {len(threads)} thread(s) in the past 24 hours")

    total = 0
    for thread in threads:
        subject, html_body = get_thread_content(gmail_service, thread["id"])
        keyword = extract_keyword_from_subject(subject)
        print(f"  Thread: {subject[:70]}")

        if not html_body:
            print("    ⚠ No HTML body found, skipping")
            continue

        papers = extract_papers_with_claude(anthropic_client, html_body)
        print(f"    Extracted {len(papers)} paper(s)")

        for paper in papers:
            if not paper.get("title"):
                continue
            print(f"    → {paper['title'][:70]}")
            jp = generate_japanese_content(anthropic_client, paper)
            url = create_notion_page(notion_client, paper, jp, keyword)
            print(f"      ✓ {url}")
            total += 1

    print(f"[{datetime.now():%Y-%m-%d %H:%M}] Done — {total} page(s) created in Notion")


if __name__ == "__main__":
    main()
