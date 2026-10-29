#!/usr/bin/env python3
"""現在 Notion データベースに登録済みの全論文を取得し、各論文の要約 README.pdf / README.md を
Git ブランチ (paper/YYYYMMDD-slug) に登録・push した上で、main ブランチの README.md 一覧表を更新するスクリプト。
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
import os
import re
import subprocess
import sys
import tempfile
import time

from notion_client import Client as NotionClient
from notion_client.errors import APIResponseError

import config
from git_publish import (
    _get_github_repo_url,
    _insert_row_into_readme,
    _make_branch_slug,
    generate_summary_markdown,
)
from pdf import generate_summary_pdf_bytes

_JST = timezone(timedelta(hours=9))


def _plain_text_from_rich(items: list[dict]) -> str:
    if not isinstance(items, list):
        return ""
    return "".join(item.get("plain_text", "") for item in items).strip()


def _extract_prop_text(props: dict, names: list[str]) -> str:
    for name in names:
        prop = props.get(name)
        if not prop:
            continue
        ptype = prop.get("type")
        if ptype in ("title", "rich_text"):
            val = _plain_text_from_rich(prop.get(ptype, []))
            if val:
                return val
        elif ptype == "url":
            val = (prop.get("url") or "").strip()
            if val:
                return val
        elif ptype == "select" and prop.get("select"):
            val = (prop["select"].get("name") or "").strip()
            if val:
                return val
    return ""


def _extract_page_date_jst(page: dict) -> str:
    props = page.get("properties", {})
    for name in ("日付", "登録日", "追加日", "取得日", "Date", "date"):
        prop = props.get(name)
        if prop and prop.get("type") == "date" and prop.get("date"):
            start = (prop["date"].get("start") or "").strip()
            if len(start) >= 10:
                return start[:10]

    created_raw = (page.get("created_time") or "").strip()
    if created_raw:
        try:
            dt = datetime.fromisoformat(created_raw.replace("Z", "+00:00")).astimezone(_JST)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            if len(created_raw) >= 10:
                return created_raw[:10]
    return datetime.now(_JST).strftime("%Y-%m-%d")


def _fetch_blocks_with_retry(notion: NotionClient, page_id: str) -> list[dict]:
    for attempt in range(8):
        try:
            res = notion.blocks.children.list(block_id=page_id, page_size=100)
            return res.get("results", [])
        except APIResponseError as e:
            if e.status in (429, 500, 502, 503, 504) and attempt < 7:
                time.sleep(3.0 * (attempt + 1))
                continue
            print(f"  ⚠ ブロック取得失敗 ({page_id}): {e}")
            return []
        except Exception as e:
            if attempt < 7:
                time.sleep(3.0 * (attempt + 1))
                continue
            print(f"  ⚠ ブロック取得例外 ({page_id}): {e}")
            return []
    return []


def _parse_page_and_blocks(page: dict, blocks: list[dict]) -> tuple[dict, dict, str, str]:
    """Notion ページと本文ブロックから (paper, jp, keyword, date_display) を復元する。"""
    props = page.get("properties", {})

    jp_title = re.sub(r"\s+", " ", _extract_prop_text(props, ["タイトル", "Name", "Title"])).strip()
    orig_title = re.sub(r"\s+", " ", _extract_prop_text(props, ["原題", "原文タイトル", "Original Title"])).strip()
    if not orig_title:
        orig_title = jp_title or "paper"
    if not jp_title:
        jp_title = orig_title

    one_liner = _extract_prop_text(props, ["メモ", "一言要約", "キャッチコピー", "Memo", "Note"])
    pdf_link = _extract_prop_text(props, ["pdf", "PDF リンク", "PDFリンク", "PDF"])
    doi_url = _extract_prop_text(props, ["DOI", "doi"])
    git_url = _extract_prop_text(props, ["gitリポジトリ", "gitレポジトリ", "Git", "GitHub", "Repository"])
    paper_url = _extract_prop_text(props, ["原文リンク", "URL", "リンク", "Link"])
    authors = _extract_prop_text(props, ["著者", "Authors", "Author"])
    journal = _extract_prop_text(props, ["掲載誌", "Journal", "雑誌", "出典"])
    keyword = _extract_prop_text(props, ["アラートキーワード", "キーワード", "Keyword", "Keywords"])
    summary = _extract_prop_text(props, ["要約", "概要", "Summary", "Abstract"])

    problem = ""
    novelty = ""
    for_freshmen = ""
    fallback_paragraphs: list[str] = []

    current_heading = ""
    has_structured_heading = False

    for b in blocks:
        btype = b.get("type", "")
        if btype in ("heading_1", "heading_2", "heading_3"):
            current_heading = _plain_text_from_rich(b.get(btype, {}).get("rich_text", []))
            if any(k in current_heading for k in ("要約", "どんな問題", "何が新しい", "新規性", "大学1年生", "原文リンク")):
                has_structured_heading = True
            continue

        if btype in ("paragraph", "bulleted_list_item", "numbered_list_item", "quote", "callout"):
            txt = _plain_text_from_rich(b.get(btype, {}).get("rich_text", []))
            if not txt:
                continue

            # 先頭のメタデータ段落（著者 / 掲載誌 / アラートキーワード）の解析
            if not current_heading and ("著者:" in txt or "掲載誌:" in txt or "アラートキーワード:" in txt):
                for line in txt.splitlines():
                    line = line.strip()
                    if line.startswith("著者:") and not authors:
                        authors = line.split("著者:", 1)[1].strip()
                    elif line.startswith("掲載誌:") and not journal:
                        journal = line.split("掲載誌:", 1)[1].strip()
                    elif line.startswith("アラートキーワード:") and not keyword:
                        keyword = line.split("アラートキーワード:", 1)[1].strip()
                continue

            if "一言" in current_heading:
                one_liner = f"{one_liner}\n{txt}".strip() if one_liner else txt
            elif "要約" in current_heading:
                summary = f"{summary}\n{txt}".strip() if summary else txt
            elif "どんな問題" in current_heading:
                problem = f"{problem}\n{txt}".strip() if problem else txt
            elif "何が新しい" in current_heading or "新規性" in current_heading:
                novelty = f"{novelty}\n{txt}".strip() if novelty else txt
            elif "大学1年生" in current_heading:
                for_freshmen = f"{for_freshmen}\n{txt}".strip() if for_freshmen else txt
            elif "原文リンク" in current_heading:
                if not paper_url:
                    paper_url = txt.strip()
            else:
                fallback_paragraphs.append(txt)

    if not summary and fallback_paragraphs:
        summary = "\n\n".join(fallback_paragraphs)

    date_display = _extract_page_date_jst(page)

    paper = {
        "title": orig_title,
        "authors": authors,
        "journal": journal,
        "year": "",
        "pdf_link": pdf_link,
        "doi_url": doi_url,
        "git_url": git_url,
        "paper_url": paper_url,
    }
    jp = {
        "japanese_title": jp_title,
        "one_liner": one_liner,
        "summary": summary,
        "problem": problem,
        "novelty": novelty,
        "for_freshmen": for_freshmen,
    }
    return paper, jp, keyword, date_display


def _run_git(args: list[str], repo_dir: str, input_bytes: bytes | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo_dir,
        input=input_bytes,
        capture_output=True,
        check=check,
    )


def _create_branch_commit_fast(
    repo_dir: str,
    base_commit: str,
    branch_name: str,
    pdf_bytes: bytes,
    md_text: str,
    commit_msg: str,
    tmp_index_path: str,
) -> None:
    """作業ツリーを切り替えずに Git plumbing コマンドで高速にブランチコミットを作成する。"""
    pdf_blob = _run_git(["hash-object", "-w", "--stdin"], repo_dir, input_bytes=pdf_bytes).stdout.decode().strip()
    md_blob = _run_git(
        ["hash-object", "-w", "--stdin"], repo_dir, input_bytes=md_text.encode("utf-8")
    ).stdout.decode().strip()

    env = os.environ.copy()
    env["GIT_INDEX_FILE"] = tmp_index_path

    subprocess.run(["git", "read-tree", base_commit], cwd=repo_dir, env=env, check=True, capture_output=True)
    subprocess.run(
        ["git", "update-index", "--add", "--cacheinfo", f"100644,{pdf_blob},README.pdf"],
        cwd=repo_dir,
        env=env,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "update-index", "--add", "--cacheinfo", f"100644,{md_blob},README.md"],
        cwd=repo_dir,
        env=env,
        check=True,
        capture_output=True,
    )
    tree_sha = subprocess.run(
        ["git", "write-tree"], cwd=repo_dir, env=env, check=True, capture_output=True, text=True
    ).stdout.strip()
    commit_sha = subprocess.run(
        ["git", "commit-tree", tree_sha, "-p", base_commit, "-m", commit_msg],
        cwd=repo_dir,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    _run_git(["update-ref", f"refs/heads/{branch_name}", commit_sha], repo_dir)


def main() -> None:
    if not os.getenv("NOTION_TOKEN"):
        sys.exit("Missing environment variable: NOTION_TOKEN")

    repo_dir = os.path.dirname(os.path.abspath(__file__))
    notion = NotionClient(auth=os.environ["NOTION_TOKEN"])

    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Fetching all pages from Notion...")
    pages: list[dict] = []
    cursor = None
    while True:
        params = {
            "data_source_id": config.NOTION_DATA_SOURCE_ID,
            "page_size": 100,
            "sorts": [{"timestamp": "created_time", "direction": "ascending"}],
        }
        if cursor:
            params["start_cursor"] = cursor
        res = notion.data_sources.query(**params)
        pages.extend(res.get("results", []))
        if not res.get("has_more"):
            break
        cursor = res.get("next_cursor")

    print(f"  Fetched {len(pages)} page(s) from Notion. Fetching page blocks...")

    blocks_by_id: dict[str, list[dict]] = {}
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_to_id = {
            executor.submit(_fetch_blocks_with_retry, notion, p["id"]): p["id"]
            for p in pages
        }
        done_count = 0
        for fut in as_completed(future_to_id):
            pid = future_to_id[fut]
            blocks_by_id[pid] = fut.result()
            done_count += 1
            if done_count % 50 == 0 or done_count == len(pages):
                print(f"    Blocks fetched: {done_count}/{len(pages)}")

    # リモートに既存の paper/* ブランチを確認
    ls_res = _run_git(["ls-remote", "--heads", "origin", "refs/heads/paper/*"], repo_dir, check=False)
    existing_remote_branches: set[str] = set()
    for line in ls_res.stdout.decode("utf-8", errors="ignore").splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].startswith("refs/heads/"):
            existing_remote_branches.add(parts[1][len("refs/heads/"):])

    base_commit = _run_git(["rev-parse", "HEAD"], repo_dir).stdout.decode().strip()
    repo_url = _get_github_repo_url(repo_dir)

    used_branch_names: set[str] = set()
    branches_to_push: list[str] = []
    readme_entries: list[tuple[str, str, str, str]] = []  # (date_display, jp_title, branch_url, keyword)

    with tempfile.NamedTemporaryFile(prefix="git_idx_", delete=False) as tf:
        tmp_index_path = tf.name

    try:
        for idx, page in enumerate(pages, 1):
            blocks = blocks_by_id.get(page["id"], [])
            paper, jp, keyword, date_display = _parse_page_and_blocks(page, blocks)
            date_compact = date_display.replace("-", "")
            slug = _make_branch_slug(paper.get("title") or jp.get("japanese_title") or "paper")
            base_branch = f"paper/{date_compact}-{slug}"

            branch_name = base_branch
            suffix = 2
            while branch_name in used_branch_names:
                branch_name = f"{base_branch}-{suffix}"
                suffix += 1
            used_branch_names.add(branch_name)

            jp_title = jp.get("japanese_title") or paper.get("title", "（タイトル不明）")
            branch_url = f"{repo_url}/tree/{branch_name}"
            readme_entries.append((date_display, jp_title, branch_url, keyword))

            if branch_name in existing_remote_branches:
                continue

            pdf_bytes = generate_summary_pdf_bytes(paper, jp, keyword)
            md_text = generate_summary_markdown(paper, jp, keyword)
            commit_msg = f"Add summary README.pdf and README.md for {(paper.get('title') or jp_title)[:60]}"

            _create_branch_commit_fast(
                repo_dir=repo_dir,
                base_commit=base_commit,
                branch_name=branch_name,
                pdf_bytes=pdf_bytes,
                md_text=md_text,
                commit_msg=commit_msg,
                tmp_index_path=tmp_index_path,
            )
            branches_to_push.append(branch_name)

            if idx % 50 == 0 or idx == len(pages):
                print(f"    Prepared {idx}/{len(pages)} branch(es)")
    finally:
        if os.path.exists(tmp_index_path):
            os.remove(tmp_index_path)

    print(f"  Pushing {len(branches_to_push)} new branch(es) to origin in batches...")
    batch_size = 40
    for i in range(0, len(branches_to_push), batch_size):
        batch = branches_to_push[i : i + batch_size]
        refspecs = [f"refs/heads/{b}:refs/heads/{b}" for b in batch]
        _run_git(["push", "origin", *refspecs], repo_dir)
        print(f"    Pushed branches {i + 1}..{i + len(batch)} / {len(branches_to_push)}")

    # main ブランチの README.md に全論文を日付降順で反映して push
    readme_md_path = os.path.join(repo_dir, "README.md")
    readme_text = ""
    if os.path.exists(readme_md_path):
        with open(readme_md_path, "r", encoding="utf-8") as f:
            readme_text = f.read()

    for date_display, jp_title, branch_url, keyword in readme_entries:
        readme_text = _insert_row_into_readme(
            readme_text, date_display, jp_title, branch_url, keyword=keyword
        )

    with open(readme_md_path, "w", encoding="utf-8") as f:
        f.write(readme_text)

    _run_git(["add", "README.md"], repo_dir)
    status_out = _run_git(["status", "--porcelain", "README.md"], repo_dir).stdout.decode().strip()
    if status_out:
        _run_git(
            ["commit", "-m", f"Update README.md with all {len(readme_entries)} Notion papers"],
            repo_dir,
        )
        _run_git(["pull", "--rebase", "origin", "main"], repo_dir, check=False)
        _run_git(["push", "origin", "main"], repo_dir)
        print(f"  ✓ Updated and pushed README.md on 'main' with {len(readme_entries)} paper(s).")
    else:
        print("  ✓ README.md on 'main' is already up to date.")

    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Sync completed successfully!")


if __name__ == "__main__":
    main()
