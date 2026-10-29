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
    """PDF 内に描画する新規性フローチャート図（横長2カラムカード＋矢印）の Flowable 群を生成する。"""
    steps = extract_diagram_steps(jp)
    if not steps:
        return []

    badge_style = ParagraphStyle(
        "DiagramBadge",
        fontName=font_name,
        fontSize=9.5,
        leading=13,
        alignment=1,  # center
        textColor=colors.white,
        wordWrap="CJK",
    )
    card_title_style = ParagraphStyle(
        "DiagramCardTitle",
        fontName=font_name,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#111827"),
        spaceAfter=2,
        wordWrap="CJK",
    )
    card_body_style = ParagraphStyle(
        "DiagramCardBody",
        fontName=font_name,
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor("#374151"),
        wordWrap="CJK",
    )
    arrow_style = ParagraphStyle(
        "DiagramArrow",
        fontName=font_name,
        fontSize=10,
        leading=11,
        alignment=1,  # center
        textColor=colors.HexColor("#64748B"),
    )

    palette = [
        ("#1E40AF", "#EFF6FF", "#BFDBFE"),  # Blue: 先行研究の限界
        ("#0F766E", "#F0FDFA", "#99F6E4"),  # Teal: 本研究の着眼点
        ("#6D28D9", "#F5F3FF", "#DDD6FE"),  # Purple: 技術的な新規性
        ("#C2410C", "#FFF7ED", "#FED7AA"),  # Orange: 新規性による優位性
    ]

    flowables = [
        Spacer(1, 2 * mm),
        Paragraph(
            escape("■ 新規性の図解（先行研究との違いと本研究のブレークスルー）"),
            heading_style,
        ),
        Spacer(1, 3 * mm),
    ]

    # 左右に余白（各15mm）を持たせた中央配置の横長ボックス（幅 140mm = 左34mm + 右106mm）
    left_col_w = 34 * mm
    right_col_w = 106 * mm

    for idx, item in enumerate(steps):
        accent_hex, bg_hex, border_hex = palette[idx % len(palette)]
        step_label = (item.get("step") or f"Step {idx + 1}").strip()
        title_label = (item.get("title") or "").strip()
        detail_text = (item.get("detail") or "").strip()

        badge_para = Paragraph(escape(step_label), badge_style)

        right_cells = []
        if title_label:
            title_html = f'<font color="{accent_hex}"><b>{escape(title_label)}</b></font>'
            right_cells.append(Paragraph(title_html, card_title_style))
        if detail_text:
            right_cells.append(Paragraph(escape(detail_text), card_body_style))
        if not right_cells:
            right_cells.append(Paragraph(escape(step_label), card_body_style))

        card = Table(
            [[badge_para, right_cells]],
            colWidths=[left_col_w, right_col_w],
            cornerRadii=[5, 5, 5, 5],
            hAlign="CENTER",
        )
        card.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), colors.HexColor(accent_hex)),
                    ("BACKGROUND", (1, 0), (1, 0), colors.HexColor(bg_hex)),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor(border_hex)),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (0, 0), 6),
                    ("RIGHTPADDING", (0, 0), (0, 0), 6),
                    ("LEFTPADDING", (1, 0), (1, 0), 10),
                    ("RIGHTPADDING", (1, 0), (1, 0), 10),
                ]
            )
        )
        flowables.append(card)

        if idx < len(steps) - 1:
            flowables.append(Spacer(1, 1.2 * mm))
            flowables.append(Paragraph("▼", arrow_style))
            flowables.append(Spacer(1, 1.2 * mm))

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
        fontSize=15.5,
        leading=22,
        alignment=0,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=4,
        wordWrap="CJK",
    )
    subtitle_style = ParagraphStyle(
        "OrigTitle",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#475569"),
        spaceAfter=8,
        wordWrap="CJK",
    )
    meta_key_style = ParagraphStyle(
        "MetaKey",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
        wordWrap="CJK",
    )
    meta_val_style = ParagraphStyle(
        "MetaVal",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1E293B"),
        wordWrap="CJK",
    )
    oneliner_style = ParagraphStyle(
        "OneLiner",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#1E3A8A"),
        wordWrap="CJK",
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName=font_name,
        fontSize=11.5,
        leading=17,
        textColor=colors.HexColor("#1E40AF"),
        spaceBefore=10,
        spaceAfter=5,
        wordWrap="CJK",
    )
    body_style = ParagraphStyle(
        "JpBody",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=10,
        leading=17,
        textColor=colors.HexColor("#1F2937"),
        spaceAfter=8,
        wordWrap="CJK",
    )

    def _p(text: str, style: ParagraphStyle) -> Paragraph:
        safe = escape(text or "").replace("\n", "<br/>")
        return Paragraph(safe, style)

    def _val_paragraph(val: str) -> Paragraph:
        val_stripped = (val or "").strip()
        if val_stripped.lower().startswith(("http://", "https://")):
            safe_href = escape(val_stripped, {'"': "&quot;"})
            safe_text = escape(val_stripped)
            html_str = (
                f'<a href="{safe_href}" color="#1D4ED8"><u>{safe_text}</u></a>'
            )
            return Paragraph(html_str, meta_val_style)
        return _p(val_stripped, meta_val_style)

    story = []
    full_width = 170 * mm

    jp_title = jp.get("japanese_title") or paper.get("title", "（タイトル不明）")
    orig_title = paper.get("title", "")
    story.append(_p(jp_title, title_style))
    if orig_title and orig_title != jp_title:
        story.append(_p(f"Original Title: {orig_title}", subtitle_style))

    # 一言キャッチコピーがあれば上部にハイライトバナーとして配置
    one_liner = (jp.get("one_liner") or "").strip()
    if one_liner:
        banner = Table(
            [[_p(f"💡 一言要約: {one_liner}", oneliner_style)]],
            colWidths=[full_width],
            cornerRadii=[4, 4, 4, 4],
        )
        banner.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#93C5FD")),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        story.append(banner)
        story.append(Spacer(1, 3 * mm))

    # メタデータ表（2カラム・横幅170mm）
    journal_str = f"{paper.get('journal', '')} {paper.get('year', '')}".strip()
    meta_items = [
        ("著者", paper.get("authors", "")),
        ("掲載誌", journal_str),
        ("キーワード", keyword),
        ("PDF", paper.get("pdf_link") or paper.get("pdf_url", "")),
        ("DOI", paper.get("doi_url", "")),
        ("Git リポジトリ", paper.get("git_url", "")),
        ("原文リンク", paper.get("paper_url", "")),
    ]
    meta_rows = [
        [_p(label, meta_key_style), _val_paragraph(val)]
        for label, val in meta_items
        if val
    ]
    if meta_rows:
        meta_table = Table(
            meta_rows,
            colWidths=[32 * mm, 138 * mm],
            cornerRadii=[4, 4, 4, 4],
        )
        meta_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F1F5F9")),
                    ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#F8FAFC")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(meta_table)

    story.append(Spacer(1, 4 * mm))
    story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#CBD5E1")))

    # 新規性の図解（横長フローチャート）を挿入
    story.extend(_build_diagram_flowables(jp, font_name, heading_style))

    sections = [
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
