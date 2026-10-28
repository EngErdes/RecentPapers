"""要約 PDF と Markdown を新しい Git ブランチに README.pdf / README.md として登録・push するヘルパー。"""

from datetime import datetime
import os
import re
import subprocess


def _make_branch_slug(title: str, max_len: int = 40) -> str:
    """論文タイトルから Git ブランチ名に使える ASCII スラグを生成する。"""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", (title or "").lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)[:max_len].strip("-")
    return slug or "paper"


def generate_summary_markdown(paper: dict, jp: dict, keyword: str = "") -> str:
    """論文の日本語要約・解説を GitHub 表示用の Markdown (README.md) 文字列として生成する。"""
    jp_title = jp.get("japanese_title") or paper.get("title", "（タイトル不明）")
    orig_title = paper.get("title", "")
    journal_str = f"{paper.get('journal', '')} {paper.get('year', '')}".strip()

    lines = [f"# {jp_title}", ""]
    if orig_title and orig_title != jp_title:
        lines += [f"**原題**: {orig_title}", ""]

    meta_items = [
        ("著者", paper.get("authors", "")),
        ("掲載誌", journal_str),
        ("アラートキーワード", keyword),
        ("PDF", paper.get("pdf_link") or paper.get("pdf_url", "")),
        ("DOI", paper.get("doi_url", "")),
        ("Git リポジトリ", paper.get("git_url", "")),
        ("原文リンク", paper.get("paper_url", "")),
    ]
    for label, val in meta_items:
        if val:
            lines.append(f"- **{label}**: {val}")
    lines.append("- **PDF版要約**: [README.pdf](./README.pdf)")
    lines.append("")
    lines.append("---")
    lines.append("")

    sections = [
        ("📌 一言キャッチコピー", jp.get("one_liner", "")),
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


def publish_readme_pdf_to_branch(
    pdf_bytes: bytes,
    title: str,
    markdown_text: str | None = None,
    repo_dir: str | None = None,
) -> str | None:
    """要約 PDF（および README.md）を新しいブランチ (paper/YYYYMMDD-slug) にコミット＆push する。

    処理完了後は元のブランチ（main 等）に戻る。成功時は作成したブランチ名を返す。
    """
    if repo_dir is None:
        repo_dir = os.path.dirname(os.path.abspath(__file__))

    date_str = datetime.now().strftime("%Y%m%d")
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
        branch_name = f"{branch_name}-{datetime.now():%H%M%S}"

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
        return branch_name
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip()
        stdout = (e.stdout or "").strip()
        print(
            f"      ⚠ [git-branch] failed to publish README ({e.cmd}): {stderr or stdout}"
        )
        return None
    finally:
        # 作業ツリーをクリーンにして元のブランチへ戻る
        _run_git(["checkout", "-f", orig_branch], repo_dir, check=False)
