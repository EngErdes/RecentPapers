"""論文 PDF の取得と本文解析ヘルパー。

各論文の pdf_url / doi_url / paper_url を順に試して PDF を取得し（Google Scholar の
リダイレクト URL は実 URL に解決）、本文テキストから git リポジトリ URL を抽出する。
取得した PDF は DEBUG 時にファイルへ保存することもできる。
"""

import io
import os
import re
from urllib.parse import parse_qs, unquote, urlparse
from xml.sax.saxutils import escape

import requests
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

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


def extract_diagram_steps(jp: dict) -> list[dict]:
    """要約図解用のステップ一覧を取り出す。未設定時は他の要約フィールドから自動構成する。"""
    raw = jp.get("diagram_steps")
    steps: list[dict] = []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict) and (item.get("title") or item.get("detail")):
                steps.append(
                    {
                        "step": str(item.get("step") or "").strip(),
                        "title": str(item.get("title") or "").strip(),
                        "detail": str(item.get("detail") or "").strip(),
                    }
                )
    if steps:
        return steps

    # フォールバック: 新規性 (novelty) と課題 (problem) を文単位で分解して図解ステップを構成
    novelty_text = (jp.get("novelty") or "").strip()
    sentences = [s.strip() for s in re.split(r"(?<=[。．.!?])\s*", novelty_text) if s.strip()]
    fallback_candidates = [
        ("1. 先行研究の限界", "従来のボトルネック", (jp.get("problem") or "")[:90]),
        ("2. 本研究の着眼点", "核心アイデア", jp.get("one_liner") or (sentences[0] if sentences else "")),
        (
            "3. 技術的な新規性",
            "先行研究との違い・工夫",
            sentences[1] if len(sentences) >= 2 else novelty_text[:90],
        ),
        (
            "4. 新規性による優位性",
            "主要な貢献・ブレークスルー",
            " ".join(sentences[2:])[:90] if len(sentences) >= 3 else (jp.get("summary") or "")[:90],
        ),
    ]
    return [
        {"step": s, "title": t, "detail": d}
        for s, t, d in fallback_candidates
        if d
    ]


def _build_diagram_flowables(
    jp: dict, font_name: str, heading_style: ParagraphStyle
) -> list:
    """PDF 内に描画する要約フローチャート図（ボックス＋矢印）の Flowable 群を生成する。"""
    steps = extract_diagram_steps(jp)
    if not steps:
        return []

    step_header_style = ParagraphStyle(
        "DiagramHeader",
        fontName=font_name,
        fontSize=10,
        leading=14,
        textColor=colors.white,
        wordWrap="CJK",
    )
    step_body_style = ParagraphStyle(
        "DiagramBody",
        fontName=font_name,
        fontSize=9.5,
        leading=15,
        textColor=colors.HexColor("#222222"),
        wordWrap="CJK",
    )
    arrow_style = ParagraphStyle(
        "DiagramArrow",
        fontName=font_name,
        fontSize=12,
        leading=14,
        alignment=1,  # center
        textColor=colors.HexColor("#4A6CF7"),
    )

    palette = [
        ("#2B579A", "#EEF3FB"),
        ("#1E7E5A", "#EBF7F2"),
        ("#8E44AD", "#F5EEF8"),
        ("#C05621", "#FDF2E9"),
    ]

    flowables = [
        Paragraph(
            escape("■ 新規性の図解（先行研究との違いと本研究のブレークスルー）"),
            heading_style,
        ),
        Spacer(1, 2 * mm),
    ]

    box_width = 170 * mm
    for idx, item in enumerate(steps):
        header_bg, body_bg = palette[idx % len(palette)]
        step_label = item.get("step") or f"Step {idx + 1}"
        title_label = item.get("title") or ""
        header_text = (
            f"{step_label} ｜ {title_label}" if title_label else step_label
        )
        detail_text = item.get("detail") or title_label

        card = Table(
            [
                [Paragraph(escape(header_text), step_header_style)],
                [Paragraph(escape(detail_text), step_body_style)],
            ],
            colWidths=[box_width],
        )
        card.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_bg)),
                    ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor(body_bg)),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor(header_bg)),
                    ("TOPPADDING", (0, 0), (-1, 0), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 1), (-1, 1), 7),
                    ("BOTTOMPADDING", (0, 1), (-1, 1), 7),
                ]
            )
        )
        flowables.append(card)

        if idx < len(steps) - 1:
            flowables.append(Spacer(1, 1 * mm))
            flowables.append(Paragraph("▼", arrow_style))
            flowables.append(Spacer(1, 1 * mm))

    flowables.append(Spacer(1, 4 * mm))
    return [KeepTogether(flowables)]


def generate_summary_pdf_bytes(paper: dict, jp: dict, keyword: str = "") -> bytes:
    """Gemini API 等で生成した論文の日本語要約・解説を整形した PDF バイト列として返す。"""
    font_name = "HeiseiKakuGo-W5"
    try:
        pdfmetrics.getFont(font_name)
    except KeyError:
        pdfmetrics.registerFont(UnicodeCIDFont(font_name))

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "JpTitle",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=16,
        leading=22,
        alignment=0,
        spaceAfter=6,
        wordWrap="CJK",
    )
    subtitle_style = ParagraphStyle(
        "OrigTitle",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#555555"),
        spaceAfter=10,
        wordWrap="CJK",
    )
    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#333333"),
        spaceAfter=4,
        wordWrap="CJK",
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName=font_name,
        fontSize=12,
        leading=18,
        textColor=colors.HexColor("#1a0dab"),
        spaceBefore=12,
        spaceAfter=4,
        wordWrap="CJK",
    )
    body_style = ParagraphStyle(
        "JpBody",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=10.5,
        leading=17,
        spaceAfter=8,
        wordWrap="CJK",
    )

    def _p(text: str, style: ParagraphStyle) -> Paragraph:
        safe = escape(text or "").replace("\n", "<br/>")
        return Paragraph(safe, style)

    story = []

    jp_title = jp.get("japanese_title") or paper.get("title", "（タイトル不明）")
    orig_title = paper.get("title", "")
    story.append(_p(jp_title, title_style))
    if orig_title and orig_title != jp_title:
        story.append(_p(f"原題: {orig_title}", subtitle_style))

    journal_str = f"{paper.get('journal', '')} {paper.get('year', '')}".strip()
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
            story.append(_p(f"{label}: {val}", meta_style))

    story.append(Spacer(1, 4 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))

    # 要約図解（フローチャート）を挿入
    story.extend(_build_diagram_flowables(jp, font_name, heading_style))

    sections = [
        ("一言キャッチコピー", jp.get("one_liner", "")),
        ("要約", jp.get("summary", "")),
        ("どんな問題に取り組んだか", jp.get("problem", "")),
        ("何が新しい？何がすごい？（新規性）", jp.get("novelty", "")),
        ("大学1年生向けの解説", jp.get("for_freshmen", "")),
    ]
    for sec_title, sec_body in sections:
        if sec_body:
            story.append(_p(f"■ {sec_title}", heading_style))
            story.append(_p(sec_body, body_style))

    doc.build(story)
    return buf.getvalue()
