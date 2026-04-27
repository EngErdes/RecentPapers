#!/usr/bin/env python3
"""
Google Scholar Alert → Notion Pipeline

Fetches Google Scholar alert emails from Gmail and creates Notion DB records
with Japanese titles, summaries, and explanations via the Anthropic API.
"""

import base64
import json
import os
import pickle
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from notion_client import Client as NotionClient

load_dotenv()

# ── Constants ──────────────────────────────────────────────────────────────────
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "34ea03616fa080d88a97d6eb8549c0a0")
GMAIL_LABEL = "01.日々の情報収集/01.03GoogleScholar"
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
BASE_DIR = Path(__file__).parent
TOKEN_PATH = BASE_DIR / "gmail_token.pickle"
CREDENTIALS_PATH = BASE_DIR / "gmail_credentials.json"
CLAUDE_MODEL = "claude-sonnet-4-6"


# ── Gmail ──────────────────────────────────────────────────────────────────────
def get_gmail_service():
    creds = None
    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), GMAIL_SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)
    return build("gmail", "v1", credentials=creds)


def get_label_id(service, label_name: str) -> str:
    labels = service.users().labels().list(userId="me").execute().get("labels", [])
    for label in labels:
        if label["name"] == label_name:
            return label["id"]
    raise ValueError(f"Gmail label not found: '{label_name}'")


def fetch_recent_threads(service, label_id: str, hours: int = 24) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    query = f"after:{int(cutoff.timestamp())}"
    result = (
        service.users()
        .threads()
        .list(userId="me", labelIds=[label_id], q=query)
        .execute()
    )
    return result.get("threads", [])


def _iter_parts(payload):
    yield payload
    for part in payload.get("parts", []):
        yield from _iter_parts(part)


def get_thread_content(service, thread_id: str) -> tuple[str, str]:
    """Return (subject, html_body) for the first message in the thread."""
    thread = service.users().threads().get(
        userId="me", id=thread_id, format="full"
    ).execute()

    subject = ""
    html_body = ""

    for msg in thread.get("messages", []):
        payload = msg.get("payload", {})

        if not subject:
            for header in payload.get("headers", []):
                if header["name"] == "Subject":
                    subject = header["value"]
                    break

        for part in _iter_parts(payload):
            if part.get("mimeType") == "text/html":
                data = part.get("body", {}).get("data", "")
                if data:
                    html_body = base64.urlsafe_b64decode(data).decode(
                        "utf-8", errors="replace"
                    )
                    break

        if not html_body:
            data = payload.get("body", {}).get("data", "")
            if data:
                html_body = base64.urlsafe_b64decode(data).decode(
                    "utf-8", errors="replace"
                )

        if html_body:
            break

    return subject, html_body


def extract_keyword_from_subject(subject: str) -> str:
    # e.g. '"zero shot"; 言語: 英語, 日本語 - 新しい結果'
    m = re.match(r'^"?([^";]+)"?\s*;', subject)
    if m:
        return m.group(1).strip().strip('"')
    return subject.split(";")[0].strip().strip('"')


# ── Claude: paper extraction ───────────────────────────────────────────────────
_EXTRACT_SYSTEM = (
    "You are a precise data extraction assistant. "
    "Always respond with valid JSON only, no markdown fences."
)


def extract_papers_with_claude(
    client: anthropic.Anthropic, html_body: str
) -> list[dict]:
    """Parse Google Scholar alert HTML → list of paper dicts using Claude."""
    # Trim to avoid excessive token usage; Scholar alerts are usually < 30 KB
    body = html_body[:40000] if len(html_body) > 40000 else html_body

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        system=_EXTRACT_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": (
                    "Extract all academic papers from this Google Scholar alert HTML.\n\n"
                    "For each paper return a JSON object with:\n"
                    '- "title": original title (string)\n'
                    '- "authors": comma-separated author names (string)\n'
                    '- "journal": journal or conference name (string)\n'
                    '- "year": publication year as string, e.g. "2024" (string)\n'
                    '- "snippet": abstract snippet (string)\n'
                    '- "pdf_url": direct PDF URL if a [PDF] link exists (string)\n'
                    '- "doi_url": DOI URL starting with https://doi.org/ if present (string)\n'
                    '- "paper_url": link to the paper page (string)\n\n'
                    "Return ONLY a JSON array.\n\n"
                    f"HTML:\n{body}"
                ),
            }
        ],
    )

    text = response.content[0].text.strip()
    text = re.sub(r"^```(?:json)?\n?", "", text).rstrip("`").strip()

    try:
        papers = json.loads(text)
        return papers if isinstance(papers, list) else []
    except json.JSONDecodeError:
        m = re.search(r"\[.*\]", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    return []


# ── Claude: Japanese content generation ───────────────────────────────────────
_JP_SYSTEM = (
    "あなたは学術論文を日本語でわかりやすく解説する専門家です。"
    "必ず有効なJSONのみを返してください（マークダウン不要）。"
)


def generate_japanese_content(
    client: anthropic.Anthropic, paper: dict
) -> dict:
    """Generate Japanese title, summary, and explanations for a paper."""
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2048,
        system=_JP_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": (
                    "以下の論文情報をもとに日本語コンテンツを生成してください。\n\n"
                    f"タイトル: {paper.get('title', '')}\n"
                    f"著者: {paper.get('authors', '')}\n"
                    f"掲載誌: {paper.get('journal', '')} {paper.get('year', '')}\n"
                    f"概要: {paper.get('snippet', '')}\n\n"
                    "次のJSONを返してください:\n"
                    "{\n"
                    '  "japanese_title": "論文タイトルの自然な日本語訳",\n'
                    '  "summary": "内容を2〜3文で要約した日本語テキスト",\n'
                    '  "one_liner": "この論文を一言で表すキャッチコピー（25文字以内）",\n'
                    '  "problem": "この論文が取り組んだ問題・課題の説明（2〜3文）",\n'
                    '  "for_freshmen": "大学1年生でも理解できる平易な説明（3〜5文）"\n'
                    "}"
                ),
            }
        ],
    )

    text = response.content[0].text.strip()
    text = re.sub(r"^```(?:json)?\n?", "", text).rstrip("`").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass

    return {
        "japanese_title": paper.get("title", ""),
        "summary": paper.get("snippet", ""),
        "one_liner": "",
        "problem": "",
        "for_freshmen": "",
    }


# ── Notion ─────────────────────────────────────────────────────────────────────
def _rich_text(content: str) -> list[dict]:
    return [{"text": {"content": content[:2000]}}]


def _heading(text: str) -> dict:
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }


def _paragraph(text: str) -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}]
        },
    }


def _divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def create_notion_page(
    notion: NotionClient,
    paper: dict,
    jp: dict,
    keyword: str,
) -> str:
    """Create a Notion database record and return its URL."""
    title = jp.get("japanese_title") or paper.get("title", "（タイトル不明）")
    journal_str = (
        f"{paper.get('journal', '')} {paper.get('year', '')}".strip()
    )

    properties: dict = {
        "名前": {"title": _rich_text(title)},
        "著者": {"rich_text": _rich_text(paper.get("authors", ""))},
        "掲載誌": {"rich_text": _rich_text(journal_str)},
        "要約": {"rich_text": _rich_text(jp.get("summary", paper.get("snippet", "")))},
        "アラートキーワード": {"rich_text": _rich_text(keyword)},
    }

    if paper.get("pdf_url"):
        properties["PDF リンク"] = {"url": paper["pdf_url"]}

    if paper.get("doi_url"):
        properties["DOI"] = {"url": paper["doi_url"]}

    # Page body blocks
    blocks: list[dict] = []

    if jp.get("one_liner"):
        blocks += [
            _heading("📌 論文の一言要約"),
            _paragraph(jp["one_liner"]),
            _divider(),
        ]

    if jp.get("problem"):
        blocks += [
            _heading("❓ どんな問題？"),
            _paragraph(jp["problem"]),
            _divider(),
        ]

    if jp.get("for_freshmen"):
        blocks += [
            _heading("🎓 大学1年生向けの説明"),
            _paragraph(jp["for_freshmen"]),
            _divider(),
        ]

    if paper.get("paper_url"):
        blocks += [
            _heading("🔗 原文リンク"),
            _paragraph(paper["paper_url"]),
        ]

    page = notion.pages.create(
        parent={"database_id": NOTION_DATABASE_ID},
        properties=properties,
        children=blocks,
    )
    return page.get("url", "")


# ── Main ───────────────────────────────────────────────────────────────────────
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
