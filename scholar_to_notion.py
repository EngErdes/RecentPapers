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

# デバッグフラグ: True のときだけデバッグ用の出力処理を実行する
DEBUG = True

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
from pdf import download_paper_pdf


def main() -> None:
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] Scholar → Notion pipeline starting")

    # 必須環境変数が設定されているか確認
    required = ["ANTHROPIC_API_KEY", "NOTION_TOKEN"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        sys.exit(f"Missing environment variables: {', '.join(missing)}")

    # 各APIクライアントを初期化
    anthropic_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    notion_client = NotionClient(auth=os.environ["NOTION_TOKEN"])
    gmail_service = get_gmail_service()

    # 対象ラベルのIDを取得し、過去24時間のスレッドを取得
    label_id = get_label_id(gmail_service, GMAIL_LABEL)
    threads = fetch_recent_threads(gmail_service, label_id, hours=72)
    print(f"Found {len(threads)} thread(s) in the past 72 hours")

    # デバッグ: 取得したスレッド一覧を debug ディレクトリに JSON 出力
    pdf_dir = None
    if DEBUG:
        debug_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug")
        os.makedirs(debug_dir, exist_ok=True)
        debug_path = os.path.join(
            debug_dir, f"threads_{datetime.now():%Y%m%d_%H%M%S}.json"
        )
        with open(debug_path, "w", encoding="utf-8") as f:
            json.dump(threads, f, ensure_ascii=False, indent=2)
        print(f"  [debug] threads dumped to {debug_path}")

        # 論文 PDF の保存先ディレクトリを用意
        pdf_dir = os.path.join(debug_dir, f"pdf_{datetime.now():%Y%m%d_%H%M%S}")
        os.makedirs(pdf_dir, exist_ok=True)

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

            # デバッグ: 論文の元 PDF を保存し、重い日本語生成はスキップ
            if DEBUG:
                path = download_paper_pdf(paper, pdf_dir, pdf_index)
                pdf_index += 1
                if path:
                    print(f"      [pdf] saved: {path}")
                else:
                    print("      [pdf] PDF が見つからずスキップ")
                total += 1
                continue

            # Claudeで日本語タイトル・要約・解説などのコンテンツを生成
            jp = generate_japanese_content(anthropic_client, paper)


            # Notionデータベースに論文レコードを作成
            # url = create_notion_page(notion_client, paper, jp, keyword)
            # print(f"      ✓ {url}")
            total += 1

    print(f"[{datetime.now():%Y-%m-%d %H:%M}] Done — {total} page(s) created in Notion")


if __name__ == "__main__":
    main()
