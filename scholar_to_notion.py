#!/usr/bin/env python3
"""
Google Scholar Alert → Notion Pipeline

Fetches Google Scholar alert emails from Gmail and creates Notion DB records
with Japanese titles, summaries, and explanations via the Anthropic API.
"""

import json
import os
import sys
from datetime import datetime

import anthropic
from notion_client import Client as NotionClient

from ai import extract_papers_with_claude, generate_japanese_content
from config import DEBUG, GMAIL_LABEL
from gmail import (
    extract_keyword_from_subject,
    fetch_recent_threads,
    get_gmail_service,
    get_label_id,
    get_thread_content,
)
from notion import create_notion_page, get_data_source_schema
from pdf import extract_git_url_from_pdf, fetch_pdf_bytes, save_pdf_bytes

FETCH_HOURS = 72  # 取得対象とするスレッドの遡り時間


def _require_env() -> None:
    """必須環境変数が無ければ終了する。"""
    missing = [k for k in ("ANTHROPIC_API_KEY", "NOTION_TOKEN") if not os.getenv(k)]
    if missing:
        sys.exit(f"Missing environment variables: {', '.join(missing)}")


def _prepare_debug_dir(threads: list[dict]) -> str:
    """DEBUG 用に threads を JSON 出力し、PDF 保存先ディレクトリを作成して返す。"""
    debug_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug")
    os.makedirs(debug_dir, exist_ok=True)

    debug_path = os.path.join(debug_dir, f"threads_{datetime.now():%Y%m%d_%H%M%S}.json")
    with open(debug_path, "w", encoding="utf-8") as f:
        json.dump(threads, f, ensure_ascii=False, indent=2)
    print(f"  [debug] threads dumped to {debug_path}")

    pdf_dir = os.path.join(debug_dir, f"pdf_{datetime.now():%Y%m%d_%H%M%S}")
    os.makedirs(pdf_dir, exist_ok=True)
    return pdf_dir


def _attach_pdf_and_git(paper: dict, pdf_dir: str | None, pdf_index: int) -> int:
    """論文の PDF を取得し、paper に pdf_link / git_url を付与する。

    pdf_dir が指定されていれば（DEBUG 時）取得した PDF をファイル保存する。
    次に使う pdf_index を返す。
    """
    fetched = fetch_pdf_bytes(paper)
    if not fetched:
        print("      [pdf] PDF が見つからずスキップ")
        return pdf_index

    pdf_link, pdf_bytes = fetched
    paper["pdf_link"] = pdf_link  # 取得可能だった PDF の直リンク
    print(f"      [pdf] link: {pdf_link}")

    git_url = extract_git_url_from_pdf(pdf_bytes)
    if git_url:
        paper["git_url"] = git_url
        print(f"      [git] {git_url}")

    if pdf_dir is not None:
        path = save_pdf_bytes(pdf_bytes, pdf_dir, pdf_index, paper.get("title", "paper"))
        print(f"      [pdf] saved: {path}")
        pdf_index += 1

    return pdf_index


def main() -> None:
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] Scholar → Notion pipeline starting")
    _require_env()

    # 各APIクライアントを初期化
    anthropic_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    notion_client = NotionClient(auth=os.environ["NOTION_TOKEN"])
    gmail_service = get_gmail_service()

    # レコード作成前に、アクセス先データベースのプロパティ（カラム）を取得しておく。
    # 以降のページ作成はこのスキーマに基づいて動的に組み立てる。
    notion_schema = get_data_source_schema(notion_client)
    print(f"Notion columns: {', '.join(notion_schema)}")

    # 対象ラベルのIDを取得し、直近 FETCH_HOURS 時間のスレッドを取得
    label_id = get_label_id(gmail_service, GMAIL_LABEL)
    threads = fetch_recent_threads(gmail_service, label_id, hours=FETCH_HOURS)
    print(f"Found {len(threads)} thread(s) in the past {FETCH_HOURS} hours")

    # DEBUG 時はスレッド一覧を JSON 出力し、PDF 保存先を用意する
    pdf_dir = _prepare_debug_dir(threads) if DEBUG else None

    total = 0
    pdf_index = 0  # PDF ファイル名の連番（スレッドをまたいで一意にする）
    for thread in threads:
        # スレッドの件名とHTML本文を取得し、検索キーワードを抽出
        subject, html_body = get_thread_content(gmail_service, thread["id"])
        keyword = extract_keyword_from_subject(subject)
        print(f"  Thread: {subject[:70]}")

        if not html_body:
            print("    ⚠ No HTML body found, skipping")
            continue

        # ClaudeでHTML本文を解析し、論文メタデータ（タイトル・著者・掲載誌・URLなど）を抽出
        papers = extract_papers_with_claude(anthropic_client, html_body)
        print(f"    Extracted {len(papers)} paper(s)")

        for paper in papers:
            if not paper.get("title"):
                continue
            print(f"    → {paper['title'][:70]}")

            # 論文本文（PDF）を取得し、pdf_link / git_url を付与
            pdf_index = _attach_pdf_and_git(paper, pdf_dir, pdf_index)

            # Claudeで日本語タイトル・要約・解説などを生成（DEBUG 時はダミー）
            jp = generate_japanese_content(anthropic_client, paper)

            # Notionデータベースに論文レコードを作成
            url = create_notion_page(
                notion_client, paper, jp, keyword, schema=notion_schema
            )
            print(f"      ✓ {url}")
            total += 1

    print(f"[{datetime.now():%Y-%m-%d %H:%M}] Done — {total} page(s) created in Notion")


if __name__ == "__main__":
    main()
