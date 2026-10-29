"""要約 PDF と Markdown を新しい Git ブランチに README.pdf / README.md として登録・push するヘルパー。"""

from datetime import datetime, timedelta, timezone
import os
import re
import subprocess

from pdf import extract_diagram_steps

_JST = timezone(timedelta(hours=9))


def _make_branch_slug(title: str, max_len: int = 40) -> str:
    """論文タイトルから Git ブランチ名に使える ASCII スラグを生成する。"""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", (title or "").lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)[:max_len].strip("-")
    return slug or "paper"


def _sanitize_mermaid_label(text: str) -> str:
    """Mermaid ノードラベル内で構文エラーを起こさないよう特殊文字を整形する。"""
    cleaned = (text or "").replace('"', "'").replace("`", "'")
    cleaned = re.sub(r"[\r\n]+", " ", cleaned).strip()
    return cleaned


def _build_mermaid_diagram(jp: dict) -> list[str]:
    """要約ステップから GitHub 表示用の横長 Mermaid フローチャートブロックを生成する。"""
    steps = extract_diagram_steps(jp)
    if not steps:
        return []

    lines = [
        "## 📊 新規性の図解（先行研究との違いと本研究のブレークスルー）",
        "",
        "```mermaid",
        "%%{init: {'flowchart': {'wrappingWidth': 520, 'nodeSpacing': 18, 'rankSpacing': 28, 'padding': 14, 'curve': 'basis'}, 'themeVariables': {'fontSize': '14px'}}}%%",
        "flowchart TD",
    ]
    node_ids = []
    divider = "─" * 30
    for idx, item in enumerate(steps, 1):
        node_id = f"S{idx}"
        node_ids.append(node_id)
        step_label = _sanitize_mermaid_label(item.get("step") or f"Step {idx}")
        title_label = _sanitize_mermaid_label(item.get("title") or "")
        detail_label = _sanitize_mermaid_label(item.get("detail") or "")

        header = f"<b>【{step_label}】 {title_label}</b>".strip()
        if detail_label:
            label_body = f"{header}<br/>{divider}<br/>{detail_label}"
        else:
            label_body = header
        lines.append(f'    {node_id}["{label_body}"]')

    for i in range(len(node_ids) - 1):
        lines.append(f"    {node_ids[i]} --> {node_ids[i + 1]}")

    style_defs = [
        "fill:#EFF6FF,stroke:#1E40AF,stroke-width:2px,color:#111827,rx:8,ry:8",
        "fill:#F0FDFA,stroke:#0F766E,stroke-width:2px,color:#111827,rx:8,ry:8",
        "fill:#F5F3FF,stroke:#6D28D9,stroke-width:2px,color:#111827,rx:8,ry:8",
        "fill:#FFF7ED,stroke:#C2410C,stroke-width:2px,color:#111827,rx:8,ry:8",
    ]
    for idx, node_id in enumerate(node_ids):
        style_str = style_defs[idx % len(style_defs)]
        lines.append(f"    style {node_id} {style_str}")

    lines += ["```", ""]
    return lines


def _escape_md_table_cell(text: str) -> str:
    """Markdown テーブルセル内で崩れないようパイプと改行を整形する。"""
    return (text or "").replace("|", "｜").replace("\n", " ").strip()


def generate_summary_markdown(paper: dict, jp: dict, keyword: str = "") -> str:
    """論文の日本語要約・解説を GitHub 表示用の Markdown (README.md) 文字列として生成する。"""
    jp_title = jp.get("japanese_title") or paper.get("title", "（タイトル不明）")
    orig_title = paper.get("title", "")
    journal_str = f"{paper.get('journal', '')} {paper.get('year', '')}".strip()

    lines = [f"# {jp_title}", ""]
    if orig_title and orig_title != jp_title:
        lines += [f"**Original Title**: *{orig_title}*", ""]

    one_liner = (jp.get("one_liner") or "").strip()
    if one_liner:
        lines += [
            f"> **💡 一言要約**: {one_liner}",
            "",
        ]

    meta_items = [
        ("著者", paper.get("authors", "")),
        ("掲載誌", journal_str),
        ("アラートキーワード", keyword),
        ("PDF", paper.get("pdf_link") or paper.get("pdf_url", "")),
        ("DOI", paper.get("doi_url", "")),
        ("Git リポジトリ", paper.get("git_url", "")),
        ("原文リンク", paper.get("paper_url", "")),
    ]
    lines += [
        "| 項目 | 内容 |",
        "|---|---|",
    ]
    for label, val in meta_items:
        if val:
            val_stripped = val.strip()
            if val_stripped.lower().startswith(("http://", "https://")):
                cell = f"[{val_stripped}]({val_stripped})"
            else:
                cell = _escape_md_table_cell(val_stripped)
            lines.append(f"| **{label}** | {cell} |")
    lines.append("| **PDF版要約** | [README.pdf](./README.pdf) |")
    lines += ["", "---", ""]

    lines.extend(_build_mermaid_diagram(jp))

    sections = [
        ("📝 要約", jp.get("summary", "")),
        ("❓ どんな問題に取り組んだか", jp.get("problem", "")),
        ("✨ 何が新しい？何がすごい？（新規性）", jp.get("novelty", "")),
        ("🎓 大学1年生向けの解説", jp.get("for_freshmen", "")),
    ]
    for sec_title, sec_body in sections:
        if sec_body:
            lines += [f"## {sec_title}", "", sec_body.strip(), ""]

    return "\n".join(lines).rstrip() + "\n"


def _run_git(args: list[str], repo_dir: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=check,
    )


def _get_github_repo_url(repo_dir: str) -> str:
    """git remote origin から GitHub リポジトリの Web URL (https://github.com/owner/repo) を取得する。"""
    res = _run_git(["remote", "get-url", "origin"], repo_dir, check=False)
    raw = (res.stdout or "").strip()
    m = re.search(r"github\.com[:/]([^/]+/[^/\s]+?)(?:\.git)?$", raw)
    if m:
        return f"https://github.com/{m.group(1)}"
    return "../.."


def _insert_row_into_readme(
    readme_text: str, date_str: str, jp_title: str, branch_url: str
) -> str:
    """README.md の『要約済み論文一覧』テーブルに新しい行を日付の降順（新しい順）で追加する。"""
    safe_title = (jp_title or "（タイトル不明）").replace("|", "｜").replace("\n", " ").strip()
    new_row = f"| {date_str} | [{safe_title}]({branch_url}) |"

    lines = readme_text.splitlines()
    header_idx = None
    for idx, line in enumerate(lines):
        if line.strip().startswith("| 日付") and "論文タイトル" in line:
            header_idx = idx
            break

    if header_idx is None:
        table_block = [
            "## 📚 要約済み論文一覧",
            "",
            "| 日付 | 論文タイトル |",
            "|---|---|",
            new_row,
            "",
        ]
        return "\n".join(table_block + lines).rstrip() + "\n"

    row_start = header_idx + 2
    row_end = row_start
    existing_rows: list[str] = []
    while row_end < len(lines) and lines[row_end].strip().startswith("|"):
        row_line = lines[row_end].strip()
        if row_line != new_row:
            existing_rows.append(row_line)
        row_end += 1

    # 新しい行を先頭に入れ、日付 (YYYY-MM-DD) の降順で安定ソート（同日なら最新が上）
    all_rows = [new_row, *existing_rows]

    def _extract_date_key(row: str) -> str:
        cols = [c.strip() for c in row.strip("|").split("|")]
        return cols[0] if cols else ""

    all_rows.sort(key=_extract_date_key, reverse=True)

    updated_lines = lines[:row_start] + all_rows + lines[row_end:]
    return "\n".join(updated_lines).rstrip() + "\n"


def _update_main_readme_index(
    repo_dir: str,
    main_branch: str,
    date_display: str,
    jp_title: str,
    branch_name: str,
) -> None:
    """main ブランチの README.md に要約済み論文へのリンクを日付降順で追記して push する。"""
    readme_md_path = os.path.join(repo_dir, "README.md")
    existing_text = ""
    if os.path.exists(readme_md_path):
        with open(readme_md_path, "r", encoding="utf-8") as f:
            existing_text = f.read()

    repo_url = _get_github_repo_url(repo_dir)
    branch_url = f"{repo_url}/tree/{branch_name}"
    updated_text = _insert_row_into_readme(
        existing_text, date_display, jp_title, branch_url
    )

    with open(readme_md_path, "w", encoding="utf-8") as f:
        f.write(updated_text)

    try:
        _run_git(["add", "README.md"], repo_dir)
        _run_git(
            ["commit", "-m", f"Add {branch_name} to README.md paper list"],
            repo_dir,
        )
        _run_git(["push", "origin", main_branch], repo_dir)
        print(f"      [git-main] updated README.md on '{main_branch}' with link to '{branch_name}'")
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip()
        stdout = (e.stdout or "").strip()
        print(
            f"      ⚠ [git-main] failed to update README.md on '{main_branch}' ({e.cmd}): {stderr or stdout}"
        )


def publish_readme_pdf_to_branch(
    pdf_bytes: bytes,
    title: str,
    markdown_text: str | None = None,
    japanese_title: str = "",
    repo_dir: str | None = None,
) -> str | None:
    """要約 PDF（および README.md）を新しいブランチ (paper/YYYYMMDD-slug) にコミット＆push する。

    push 成功時は元のブランチ（main）に戻ったうえで、main ブランチの README.md の
    論文一覧テーブル（日付降順）に該当ブランチへのリンクを追記して push する。
    """
    if repo_dir is None:
        repo_dir = os.path.dirname(os.path.abspath(__file__))

    now_jst = datetime.now(_JST)
    date_str = now_jst.strftime("%Y%m%d")
    date_display = now_jst.strftime("%Y-%m-%d")
    slug = _make_branch_slug(title)
    branch_name = f"paper/{date_str}-{slug}"

    # 現在のブランチ名を取得（detached HEAD 時は main にフォールバック）
    cur = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo_dir, check=False)
    orig_branch = cur.stdout.strip() if cur.returncode == 0 else "main"
    if not orig_branch or orig_branch == "HEAD":
        orig_branch = "main"

    # 同名ブランチが既に存在する場合は時刻サフィックスを付与して一意にする
    ref_check = _run_git(
        ["show-ref", "--verify", "--quiet", f"refs/heads/{branch_name}"],
        repo_dir,
        check=False,
    )
    remote_check = _run_git(
        ["ls-remote", "--exit-code", "--heads", "origin", branch_name],
        repo_dir,
        check=False,
    )
    if ref_check.returncode == 0 or remote_check.returncode == 0:
        branch_name = f"{branch_name}-{now_jst:%H%M%S}"

    # GitHub Actions 等で git user.name / user.email が未設定の場合に備えてローカル設定を補完
    name_cfg = _run_git(["config", "user.name"], repo_dir, check=False)
    if not name_cfg.stdout.strip():
        _run_git(["config", "user.name", "github-actions[bot]"], repo_dir, check=False)
    email_cfg = _run_git(["config", "user.email"], repo_dir, check=False)
    if not email_cfg.stdout.strip():
        _run_git(
            ["config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"],
            repo_dir,
            check=False,
        )

    readme_pdf_path = os.path.join(repo_dir, "README.pdf")
    readme_md_path = os.path.join(repo_dir, "README.md")
    pushed_branch: str | None = None
    try:
        _run_git(["checkout", "-b", branch_name], repo_dir)
        with open(readme_pdf_path, "wb") as f:
            f.write(pdf_bytes)

        files_to_add = ["README.pdf"]
        if markdown_text is not None:
            with open(readme_md_path, "w", encoding="utf-8") as f:
                f.write(markdown_text)
            files_to_add.append("README.md")

        _run_git(["add", "-f", *files_to_add], repo_dir)
        commit_msg = f"Add summary README.pdf and README.md for {title[:60]}"
        _run_git(["commit", "-m", commit_msg], repo_dir)
        _run_git(["push", "-u", "origin", branch_name], repo_dir)
        print(
            f"      [git-branch] pushed {', '.join(files_to_add)} to branch '{branch_name}'"
        )
        pushed_branch = branch_name
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip()
        stdout = (e.stdout or "").strip()
        print(
            f"      ⚠ [git-branch] failed to publish README ({e.cmd}): {stderr or stdout}"
        )
    finally:
        # 作業ツリーをクリーンにして元のブランチへ戻る
        _run_git(["checkout", "-f", orig_branch], repo_dir, check=False)

    if pushed_branch:
        _update_main_readme_index(
            repo_dir=repo_dir,
            main_branch=orig_branch,
            date_display=date_display,
            jp_title=japanese_title or title,
            branch_name=pushed_branch,
        )

    return pushed_branch
