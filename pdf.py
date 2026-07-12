"""論文 PDF の取得と本文解析ヘルパー。

各論文の pdf_url / doi_url / paper_url を順に試して PDF を取得し（Google Scholar の
リダイレクト URL は実 URL に解決）、本文テキストから git リポジトリ URL を抽出する。
取得した PDF は DEBUG 時にファイルへ保存することもできる。
"""

import io
import os
import re
from urllib.parse import parse_qs, unquote, urlparse

import requests
from pypdf import PdfReader

# 論文本文からリポジトリ URL を検出するための正規表現。
# 主要な git ホスト（GitHub / GitLab / Bitbucket / Codeberg）の owner/repo 形式を対象とする。
_GIT_HOSTS = r"(?:github\.com|gitlab\.com|bitbucket\.org|codeberg\.org)"
_GIT_URL_RE = re.compile(
    r"(?:https?://)?(?:www\.)?" + _GIT_HOSTS + r"/[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+",
    re.IGNORECASE,
)
# 「著者自身のリポジトリ」を示唆する文脈語。引用中の GitHub リンク（他者の実装）と
# 区別するため、URL の直前にこれらが現れる候補を優先する。
_GIT_CONTEXT_RE = re.compile(
    r"(code|available|released?|project\s*page|implementation|repositor|"
    r"source|reproduc|open[\s-]?source|our)",
    re.IGNORECASE,
)
# owner 部分が repo ではないことが明らかな GitHub の予約パス
_NON_REPO_OWNERS = {
    "about", "features", "pricing", "sponsors", "topics", "collections",
    "marketplace", "explore", "settings", "login", "join", "orgs", "search",
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def _resolve_scholar_url(url: str) -> str:
    """Scholar のリダイレクト URL（scholar_url?url=...）から実 URL を取り出す。"""
    parsed = urlparse(url)
    if "scholar.google" in parsed.netloc and "scholar_url" in parsed.path:
        qs = parse_qs(parsed.query)
        if qs.get("url"):
            return unquote(qs["url"][0])
    return url


def _safe_filename(name: str, max_len: int = 80) -> str:
    """タイトルからファイル名に使える安全な文字列を生成する。"""
    name = re.sub(r"[^\w\s\-.]", "", name, flags=re.UNICODE).strip()
    name = re.sub(r"\s+", "_", name)
    return name[:max_len] or "paper"


def fetch_pdf_bytes(paper: dict) -> tuple[str, bytes] | None:
    """論文の PDF を取得する。成功時は (実 URL, bytes)、失敗時は None。

    pdf_url → doi_url → paper_url の順で候補 URL を試し、
    実際に PDF を返した最初の URL とその内容を返す。
    返す URL は Scholar のリダイレクトを解決した後の直接ダウンロード URL。
    """
    candidates = [
        paper.get("pdf_url"),
        paper.get("doi_url"),
        paper.get("paper_url"),
    ]
    candidates = [c for c in candidates if c]
    if not candidates:
        return None

    for raw_url in candidates:
        url = _resolve_scholar_url(raw_url)
        try:
            resp = requests.get(
                url, headers=_HEADERS, timeout=30, allow_redirects=True
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"      [pdf] 取得失敗 ({e}): {url[:80]}")
            continue

        content_type = resp.headers.get("Content-Type", "").lower()
        is_pdf = "application/pdf" in content_type or resp.content[:5] == b"%PDF-"
        if not is_pdf:
            # PDF でなければ（HTML ページ等）次の候補へ
            continue

        # リダイレクト後の最終 URL を実リンクとして採用する
        return str(resp.url), resp.content

    return None


def save_pdf_bytes(content: bytes, dest_dir: str, index: int, title: str) -> str:
    """取得済みの PDF バイト列を dest_dir に保存し、保存パスを返す。"""
    base = f"{index:03d}_{_safe_filename(title)}"
    path = os.path.join(dest_dir, base + ".pdf")
    with open(path, "wb") as f:
        f.write(content)
    return path


def _normalize_git_url(match: str) -> str | None:
    """正規表現でヒットした文字列を正規化した git URL に整える。

    末尾の記号や `.git` の後処理、予約パスの除外を行う。無効なら None。
    """
    url = match.strip().rstrip(".,;:)]}>\"'")
    # スキームが無ければ https:// を補う
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        return None
    owner, repo = parts[0], parts[1]
    if owner.lower() in _NON_REPO_OWNERS:
        return None
    # owner/repo までを URL として採用（サブパスは落とす）
    repo = repo[:-4] if repo.lower().endswith(".git") else repo
    return f"https://{parsed.netloc}/{owner}/{repo}"


def find_git_url_in_text(text: str) -> str | None:
    """テキスト中から最初の git リポジトリ URL を抽出する。無ければ None。"""
    if not text:
        return None
    # PDF 由来のテキストは URL が行末で折り返されて改行で分断されることがある。
    # そこで、通常テキストと「改行（と前後の水平空白）を除去して行を連結した版」の
    # 両方を走査する。通常のスペースは語の区切りとして温存し、過剰連結を防ぐ。
    joined = re.sub(r"[ \t]*\n[ \t]*", "", text)
    for candidate_text in (text, joined):
        matches = list(_GIT_URL_RE.finditer(candidate_text))
        if not matches:
            continue
        # 1) 直前に文脈語（code / available / our など）がある候補を優先。
        #    引用として列挙された他者リポジトリの誤検出を避ける。
        for m in matches:
            preceding = candidate_text[max(0, m.start() - 80):m.start()]
            if _GIT_CONTEXT_RE.search(preceding):
                url = _normalize_git_url(m.group(0))
                if url:
                    return url
        # 2) 文脈語が見つからなければ、最初の有効な候補にフォールバック。
        for m in matches:
            url = _normalize_git_url(m.group(0))
            if url:
                return url
    return None


def extract_git_url_from_pdf(content: bytes) -> str | None:
    """PDF バイト列のテキストを解析し、git リポジトリ URL を抽出する。"""
    try:
        reader = PdfReader(io.BytesIO(content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:  # pypdf は多様な例外を投げうるため広めに捕捉
        print(f"      [git] PDF 解析失敗: {e}")
        return None
    return find_git_url_in_text(text)
