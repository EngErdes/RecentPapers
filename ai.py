import json
import os
import re

import anthropic
import requests

from config import CLAUDE_MODEL, GEMINI_MODEL, USE_GEMINI

_GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)
_GEMINI_MODELS_LIST_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# 新規 API キーで gemini-2.5-flash 等が 404 になる場合に備えたフォールバック候補
_FALLBACK_GEMINI_MODELS = (
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite-preview",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
)
_active_gemini_model: str | None = None

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


def _discover_gemini_model(api_key: str) -> str | None:
    """API キーで利用可能な Gemini Flash 系モデル一覧を取得して返す。"""
    try:
        resp = requests.get(
            _GEMINI_MODELS_LIST_URL,
            headers={"x-goog-api-key": api_key},
            timeout=30,
        )
        if not resp.ok:
            print(f"  [gemini] models.list failed ({resp.status_code}): {resp.text[:300]}")
            return None
        models = resp.json().get("models") or []
        available = [
            m.get("name", "").removeprefix("models/")
            for m in models
            if "generateContent" in (m.get("supportedGenerationMethods") or [])
        ]
        print(f"  [gemini] available generateContent models: {', '.join(available[:10])}")
        for candidate in _FALLBACK_GEMINI_MODELS:
            if candidate in available:
                return candidate
        for name in available:
            if "gemini" in name and "flash" in name and "tts" not in name and "image" not in name:
                return name
        return available[0] if available else None
    except Exception as e:
        print(f"  [gemini] model discovery error: {e}")
        return None


def _complete_json_gemini(
    system: str, prompt: str, max_tokens: int
) -> dict | list | None:
    """Gemini REST API に単発のユーザープロンプトを投げ、レスポンスを JSON として解釈する。"""
    global _active_gemini_model
    api_key = os.environ["GEMINI_API_KEY"].strip()
    model = _active_gemini_model or GEMINI_MODEL

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

    # 指定モデルで 404 の場合はフォールバック候補・モデル一覧取得を順に試す
    candidates_to_try = [model] + [
        m for m in _FALLBACK_GEMINI_MODELS if m != model
    ]
    resp = None
    for candidate in candidates_to_try:
        url = _GEMINI_API_URL.format(model=candidate)
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        if resp.status_code == 404:
            print(
                f"  [gemini] model '{candidate}' returned 404: {resp.text[:200]}"
            )
            continue
        _active_gemini_model = candidate
        break
    else:
        # 候補がすべて 404 だった場合、models.list から利用可能モデルを自動検出
        discovered = _discover_gemini_model(api_key)
        if discovered and discovered not in candidates_to_try:
            print(f"  [gemini] retrying with discovered model: {discovered}")
            url = _GEMINI_API_URL.format(model=discovered)
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            if resp.ok:
                _active_gemini_model = discovered

    assert resp is not None
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


def extract_papers_with_claude(
    client: anthropic.Anthropic | None,
    html_body: str,
    *,
    use_gemini: bool = USE_GEMINI,
) -> list[dict]:
    """Parse Google Scholar alert HTML → list of paper dicts using Gemini or Claude."""
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
