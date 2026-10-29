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

from ai import (
    QuotaExhaustedError,
    extract_papers_with_claude,
    generate_japanese_content,
)
from config import (
    CLAUDE_MODEL,
    DEBUG,
    DEBUG_THREAD_LIMIT,
    GEMINI_MODEL,
    GMAIL_LABEL,
    MAX_PAPERS_PER_RUN,
    USE_GEMINI,
)
from git_publish import generate_summary_markdown, publish_readme_pdf_to_branch
from gmail import (
    extract_keyword_from_subject,
    get_gmail_connection,
    get_thread_content,
    iter_threads_newest_first,
    resolve_label_mailbox,
)
from notion import (
    create_notion_page,
    fetch_registered_titles,
    get_data_source_schema,
    normalize_title,
)
from pdf import (
    extract_git_url_from_pdf,
    fetch_pdf_bytes,
    generate_summary_pdf_bytes,
    save_pdf_bytes,
)

FETCH_HOURS = 72  # 取得対象とするスレッドの遡り時間


def _require_env() -> None:
    """必須環境変数が無ければ終了する。"""
    ai_key = "GEMINI_API_KEY" if USE_GEMINI else "ANTHROPIC_API_KEY"
    required = (ai_key, "NOTION_TOKEN", "GMAIL_USER", "GMAIL_APP_PASSWORD")
    missing = [k for k in required if not os.getenv(k)]
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

    # [debug] GitHub Actions から渡された NOTION_TOKEN を確認する
    print(f"  [debug] NOTION_TOKEN={os.getenv('NOTION_TOKEN')}")

    # 各APIクライアントを初期化
    if USE_GEMINI:
        print(f"  AI provider: Gemini ({GEMINI_MODEL})")
        anthropic_client = None
    else:
        print(f"  AI provider: Claude ({CLAUDE_MODEL})")
        anthropic_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    notion_client = NotionClient(auth=os.environ["NOTION_TOKEN"])
    gmail_conn = get_gmail_connection()

    try:
        # レコード作成前に、アクセス先データベースのプロパティ（カラム）を取得しておく。
        # 以降のページ作成はこのスキーマに基づいて動的に組み立てる。
        notion_schema = get_data_source_schema(notion_client)
        print(f"Notion columns: {', '.join(notion_schema)}")

        # 登録済みのタイトル（原題・タイトル列）を比較用に読み込み、同じ論文を二重登録しないようにする
        registered = fetch_registered_titles(notion_client, notion_schema)
        if registered is None:
            print("  ⚠ タイトル/原題カラムが無いため重複チェックを行いません")
        else:
            print(f"  {len(registered)} title(s) already registered in Notion")

        # 対象ラベルのメールボックスを開き、未登録論文が MAX_PAPERS_PER_RUN 件に達するまで
        # 新しいメールから過去へ順番に遡って処理する。
        mailbox = resolve_label_mailbox(gmail_conn, GMAIL_LABEL)
        limit = DEBUG_THREAD_LIMIT if DEBUG else None
        threads_iter = iter_threads_newest_first(gmail_conn, mailbox, limit=limit)

        if DEBUG:
            print(
                f"Target: up to {MAX_PAPERS_PER_RUN} unregistered paper(s)"
                f"（DEBUG: 最新 {DEBUG_THREAD_LIMIT} スレッドに制限）"
            )
        else:
            print(
                f"Target: {MAX_PAPERS_PER_RUN} unregistered paper(s) "
                "(scanning past mails from newest to oldest)"
            )

        # DEBUG 時は PDF 保存先を用意する
        pdf_dir = _prepare_debug_dir([]) if DEBUG else None

        total = 0
        skipped = 0  # 登録済みでスキップした論文数
        pdf_index = 0  # PDF ファイル名の連番（スレッドをまたいで一意にする）
        try:
            for mail_index, thread in enumerate(threads_iter, 1):
                if total >= MAX_PAPERS_PER_RUN:
                    break

                # スレッドの件名とHTML本文を取得し、検索キーワードを抽出
                subject, html_body = get_thread_content(gmail_conn, thread["id"])
                keyword = extract_keyword_from_subject(subject)
                print(
                    f"  Mail {mail_index} (new: {total}/{MAX_PAPERS_PER_RUN}): {subject[:70]}"
                )

                if not html_body:
                    print("    ⚠ No HTML body found, skipping")
                    continue

                # HTML本文を解析し、論文メタデータ（タイトル・著者・掲載誌・URLなど）を抽出
                papers = extract_papers_with_claude(anthropic_client, html_body)
                print(f"    Extracted {len(papers)} paper(s)")

                # 処理を始める前に、このメールに含まれる論文タイトルを一覧で出す
                for paper_index, paper in enumerate(papers, 1):
                    print(f"      {paper_index}. {paper.get('title') or '（タイトル不明）'}")

                for paper in papers:
                    if total >= MAX_PAPERS_PER_RUN:
                        break
                    if not paper.get("title"):
                        continue

                    # 登録済みなら PDF 取得も AI 呼び出しも行わずスキップする
                    key = normalize_title(paper["title"])
                    if registered is not None and key in registered:
                        print(f"    ⏭ 登録済み: {paper['title'][:60]}")
                        skipped += 1
                        continue

                    print(f"    → [{total + 1}/{MAX_PAPERS_PER_RUN}] {paper['title'][:65]}")

                    # 論文本文（PDF）を取得し、pdf_link / git_url を付与
                    pdf_index = _attach_pdf_and_git(paper, pdf_dir, pdf_index)

                    # AIで日本語タイトル・要約・解説などを生成
                    jp = generate_japanese_content(anthropic_client, paper)

                    # Notionデータベースに論文レコードを作成
                    url = create_notion_page(
                        notion_client, paper, jp, keyword, schema=notion_schema
                    )
                    print(f"      ✓ {url}")
                    total += 1

                    # Notion に登録したすべての論文について、要約内容を PDF・Markdown 化して
                    # 新しい Git ブランチに README.pdf / README.md として登録し、main の README.md に追記する
                    try:
                        summary_pdf = generate_summary_pdf_bytes(paper, jp, keyword)
                        summary_md = generate_summary_markdown(paper, jp, keyword)
                        publish_readme_pdf_to_branch(
                            summary_pdf,
                            paper.get("title", "paper"),
                            markdown_text=summary_md,
                            japanese_title=jp.get("japanese_title") or paper.get("title", ""),
                            keyword=keyword,
                        )
                    except Exception as e:
                        print(f"      ⚠ [summary-pdf] 生成・登録エラー: {e}")

                    # 同一実行内でメールをまたいで重複するケースにも対応する
                    if registered is not None:
                        registered.add(key)

                if total >= MAX_PAPERS_PER_RUN:
                    print(
                        f"  ✓ 未登録論文を {MAX_PAPERS_PER_RUN} 件登録したため、本日の処理を完了します。"
                    )
                    break
        except QuotaExhaustedError as e:
            print(
                f"  ⚠ {e}\n"
                "  ⚠ 本日の AI API 利用枠上限（または連続高負荷）に達したため処理を中断します。"
                "残りの未登録論文は次回実行時に処理されます。"
            )
    finally:
        gmail_conn.logout()

    print(
        f"[{datetime.now():%Y-%m-%d %H:%M}] Done — {total} page(s) created in Notion"
        f"（登録済みスキップ: {skipped} 件）"
    )


if __name__ == "__main__":
    main()
