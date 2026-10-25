import html
import json
import os
import re
import time
from urllib.parse import parse_qs, unquote, urlparse

import anthropic
import requests

from config import CLAUDE_MODEL, GEMINI_MODEL, USE_GEMINI

_GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class QuotaExhaustedError(RuntimeError):
    """AI API のクォータ上限または連続した高負荷により処理を継続できない場合の例外。"""

_EXTRACT_SYSTEM = (
    "You are a precise data extraction assistant. "
    "Always respond with valid JSON only, no markdown fences."
)

_JP_SYSTEM = (
    "あなたは学術論文を日本語でわかりやすく解説する専門家です。"
    "必ず有効なJSONのみを返してください（マークダウン不要）。"
)


def _parse_json(text: str) -> dict | list | None:
    text = re.sub(r"^```(?:json)?\n?", "", text.strip()).rstrip("`").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"[\[{].*[\]}]", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    return None


def _is_daily_quota_exceeded(resp: requests.Response) -> bool:
    """429 エラーが 1 日あたりのリクエスト上限（RPD / Free Tier）によるものか判定する。"""
    if resp.status_code != 429:
        return False
    body_lower = resp.text.lower()
    return (
        "per day" in body_lower
        or "per_day" in body_lower
        or "free_tier_requests" in body_lower
    )


def _complete_json_gemini(
    system: str, prompt: str, max_tokens: int
) -> dict | list | None:
    """Gemini REST API（GEMINI_MODEL のみ使用）にプロンプトを投げ、JSON として解釈する。"""
    api_key = os.environ["GEMINI_API_KEY"].strip()
    url = _GEMINI_API_URL.format(model=GEMINI_MODEL)

    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            # 思考トークンも出力上限に含まれるため余裕を持たせる
            "maxOutputTokens": max(max_tokens, 8192),
            "responseMimeType": "application/json",
        },
    }
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }

    # 一時的な高負荷（503）や分間レート制限（429 RPM）はバックオフしてリトライし、
    # 1日のリクエスト上限（429 RPD）に達した場合は即座に QuotaExhaustedError で安全に終了する。
    wait_schedule = (5, 10, 20, 30)
    resp = None
    for attempt in range(len(wait_schedule) + 1):
        if attempt > 0:
            wait_sec = wait_schedule[attempt - 1]
            print(
                f"  [gemini] waiting {wait_sec}s before retry (attempt {attempt + 1}/{len(wait_schedule) + 1})..."
            )
            time.sleep(wait_sec)

        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        if _is_daily_quota_exceeded(resp):
            print(
                f"  [gemini] model '{GEMINI_MODEL}' reached daily quota limit (429 RPD)"
            )
            raise QuotaExhaustedError(
                f"{GEMINI_MODEL} の 1 日あたりの無料枠リクエスト上限に達しました。"
            )
        if resp.status_code in _RETRYABLE_STATUS_CODES:
            print(
                f"  [gemini] model '{GEMINI_MODEL}' returned {resp.status_code} (temporary overload/rate limit)"
            )
            continue
        break

    if resp is None or resp.status_code in _RETRYABLE_STATUS_CODES:
        if resp is not None:
            print(f"  [gemini] HTTP {resp.status_code} error body: {resp.text[:500]}")
        raise QuotaExhaustedError(
            f"{GEMINI_MODEL} の一時的な高負荷またはレート制限（503/429）が解消しなかったため中断します。"
        )

    if not resp.ok:
        print(f"  [gemini] HTTP {resp.status_code} error body: {resp.text[:500]}")
        resp.raise_for_status()
    data = resp.json()

    candidates = data.get("candidates") or []
    if not candidates:
        return None
    parts = candidates[0].get("content", {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    return _parse_json(text)


def _complete_json_claude(
    client: anthropic.Anthropic | None, system: str, prompt: str, max_tokens: int
) -> dict | list | None:
    """Claude に単発のユーザープロンプトを投げ、レスポンスを JSON として解釈する。"""
    if client is None:
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_json(response.content[0].text)


def _complete_json(
    client: anthropic.Anthropic | None,
    system: str,
    prompt: str,
    max_tokens: int,
    *,
    use_gemini: bool = USE_GEMINI,
) -> dict | list | None:
    """フラグに応じて Gemini または Claude にプロンプトを投げ、JSON として解釈する。"""
    if use_gemini:
        return _complete_json_gemini(system, prompt, max_tokens)
    return _complete_json_claude(client, system, prompt, max_tokens)


_GIT_URL_SNIPPET_RE = re.compile(
    r"https?://(?:www\.)?(?:github\.com|gitlab\.com|bitbucket\.org|codeberg\.org)"
    r"/[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+",
    re.IGNORECASE,
)
_DOI_URL_RE = re.compile(
    r"https?://(?:dx\.)?doi\.org/[^\s\"'<>]+", re.IGNORECASE
)


def _strip_tags(html_fragment: str) -> str:
    """HTML タグを除去し、実体参照をデコードして空白を正規化する。"""
    text = re.sub(r"<br\s*/?>", " ", html_fragment, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def _unwrap_scholar_url(raw_url: str) -> str:
    """Google Scholar のリダイレクト URL（scholar_url?url=...）から実 URL を取り出す。"""
    url = html.unescape(raw_url).strip()
    parsed = urlparse(url)
    if "scholar.google" in parsed.netloc and "scholar_url" in parsed.path:
        qs = parse_qs(parsed.query)
        if qs.get("url"):
            return unquote(qs["url"][0])
    return url


def _extract_papers_from_html(html_body: str) -> list[dict]:
    """Google Scholar アラートメールの HTML を直接パースして論文リストを抽出する（API 消費 0）。"""
    h3_matches = list(
        re.finditer(r"<h3\b[^>]*>.*?</h3>", html_body, flags=re.DOTALL | re.IGNORECASE)
    )
    if not h3_matches:
        return []

    papers: list[dict] = []
    for idx, h3_match in enumerate(h3_matches):
        h3_html = h3_match.group(0)
        title_link = re.search(
            r"<a\b([^>]*\bclass=[\"'][^\"']*gse_alrt_title[^\"']*[\"'][^>]*)>(.*?)</a>",
            h3_html,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if not title_link:
            continue

        a_attrs, title_inner = title_link.group(1), title_link.group(2)
        title = _strip_tags(title_inner)
        if not title:
            continue

        href_match = re.search(r"href=[\"']([^\"']+)[\"']", a_attrs, flags=re.IGNORECASE)
        paper_url = _unwrap_scholar_url(href_match.group(1)) if href_match else ""

        # この <h3> から次の <h3>（または末尾）までのブロックを切り出す
        block_start = h3_match.start()
        block_end = (
            h3_matches[idx + 1].start() if idx + 1 < len(h3_matches) else len(html_body)
        )
        block_html = html_body[block_start:block_end]

        # [PDF] バッジまたは PDF 直リンクの判定
        has_pdf_badge = bool(re.search(r"\[PDF\]", h3_html, flags=re.IGNORECASE))
        is_direct_pdf = bool(
            re.search(r"(?:\.pdf(?:$|\?)|arxiv\.org/pdf/)", paper_url, flags=re.IGNORECASE)
        )
        pdf_url = paper_url if (has_pdf_badge or is_direct_pdf) else ""

        # 著者・掲載誌・発行年（緑色テキストの div）
        authors = ""
        journal = ""
        year = ""
        meta_match = re.search(
            r"<div\b[^>]*style=[\"'][^\"']*color:\s*#006621[^\"']*[\"'][^>]*>(.*?)</div>",
            block_html,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if meta_match:
            meta_text = _strip_tags(meta_match.group(1))
            parts = re.split(r"\s+-\s+", meta_text)
            if parts:
                authors = parts[0].strip()
            if len(parts) >= 2:
                pub_part = parts[1].strip()
                year_match = re.search(r"\b((?:19|20)\d{2})\b", pub_part)
                if not year_match and len(parts) >= 3:
                    year_match = re.search(r"\b((?:19|20)\d{2})\b", parts[2])
                if year_match:
                    year = year_match.group(1)
                journal = re.sub(r",?\s*\b(?:19|20)\d{2}\b", "", pub_part).strip(" ,-")

        # 概要スニペット（class="gse_alrt_sni"）
        snippet = ""
        sni_match = re.search(
            r"<div\b[^>]*class=[\"'][^\"']*gse_alrt_sni[^\"']*[\"'][^>]*>(.*?)</div>",
            block_html,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if sni_match:
            snippet = _strip_tags(sni_match.group(1))

        # DOI URL
        doi_url = ""
        if "doi.org/" in paper_url.lower():
            doi_url = paper_url
        else:
            doi_m = _DOI_URL_RE.search(block_html)
            if doi_m:
                doi_url = html.unescape(doi_m.group(0)).rstrip(".,;)")

        # スニペット内の Git URL
        git_m = _GIT_URL_SNIPPET_RE.search(snippet)
        git_url = git_m.group(0).rstrip(".,;)") if git_m else ""

        papers.append(
            {
                "title": title,
                "authors": authors,
                "journal": journal,
                "year": year,
                "snippet": snippet,
                "pdf_url": pdf_url,
                "doi_url": doi_url,
                "paper_url": paper_url,
                "git_url": git_url,
            }
        )

    return papers


def extract_papers_with_claude(
    client: anthropic.Anthropic | None,
    html_body: str,
    *,
    use_gemini: bool = USE_GEMINI,
) -> list[dict]:
    """Parse Google Scholar alert HTML → list of paper dicts (local parser first, AI fallback)."""
    # まずローカル HTML パーサーで抽出（API クォータを消費しない）
    parsed = _extract_papers_from_html(html_body)
    if parsed:
        return parsed

    # ローカルパースで 0 件だった場合のみ AI 抽出にフォールバック
    # Trim to avoid excessive token usage; Scholar alerts are usually < 30 KB
    body = html_body[:40000] if len(html_body) > 40000 else html_body

    prompt = (
        "Extract all academic papers from this Google Scholar alert HTML.\n\n"
        "For each paper return a JSON object with:\n"
        '- "title": original title (string)\n'
        '- "authors": comma-separated author names (string)\n'
        '- "journal": journal or conference name (string)\n'
        '- "year": publication year as string, e.g. "2024" (string)\n'
        '- "snippet": abstract snippet (string)\n'
        '- "pdf_url": direct PDF URL if a [PDF] link exists (string)\n'
        '- "doi_url": DOI URL starting with https://doi.org/ if present (string)\n'
        '- "paper_url": link to the paper page (string)\n'
        '- "git_url": code repository URL (GitHub/GitLab/Bitbucket) if the '
        'snippet mentions one, otherwise "" (string)\n\n'
        "Return ONLY a JSON array.\n\n"
        f"HTML:\n{body}"
    )

    result = _complete_json(
        client, _EXTRACT_SYSTEM, prompt, max_tokens=4096, use_gemini=use_gemini
    )
    return result if isinstance(result, list) else []


def generate_japanese_content(
    client: anthropic.Anthropic | None,
    paper: dict,
    *,
    use_gemini: bool = USE_GEMINI,
) -> dict:
    """Generate Japanese title, summary, and explanations for a paper."""

    prompt = (
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
        '  "novelty": "この論文の新規性は何か、何がすごいのかの説明。'
        '先行研究との違いと、この研究の主要な貢献を具体的に示す（3〜4文）",\n'
        '  "for_freshmen": "大学1年生でも理解できる平易な説明（3〜5文）"\n'
        "}"
    )

    result = _complete_json(
        client, _JP_SYSTEM, prompt, max_tokens=3072, use_gemini=use_gemini
    )
    if isinstance(result, dict):
        return result

    return {
        "japanese_title": paper.get("title", ""),
        "summary": paper.get("snippet", ""),
        "one_liner": "",
        "problem": "",
        "novelty": "",
        "for_freshmen": "",
    }
