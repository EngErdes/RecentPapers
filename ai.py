import json
import re

import anthropic

from config import CLAUDE_MODEL, DEBUG, DEBUG_JAPANESE_CONTENT, DEBUG_PAPERS

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


def _complete_json(
    client: anthropic.Anthropic, system: str, prompt: str, max_tokens: int
) -> dict | list | None:
    """Claude に単発のユーザープロンプトを投げ、レスポンスを JSON として解釈する。"""
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_json(response.content[0].text)


def extract_papers_with_claude(
    client: anthropic.Anthropic, html_body: str
) -> list[dict]:
    """Parse Google Scholar alert HTML → list of paper dicts using Claude."""
    # DEBUG 時は Claude を呼ばず、あらかじめ指定したダミー論文リストを返す
    if DEBUG:
        return [dict(p) for p in DEBUG_PAPERS]

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

    result = _complete_json(client, _EXTRACT_SYSTEM, prompt, max_tokens=4096)
    return result if isinstance(result, list) else []


def generate_japanese_content(
    client: anthropic.Anthropic, paper: dict
) -> dict:
    """Generate Japanese title, summary, and explanations for a paper."""
    # DEBUG 時は Claude を呼ばず、あらかじめ指定したダミー内容を返す
    if DEBUG:
        return dict(DEBUG_JAPANESE_CONTENT)

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
        '  "for_freshmen": "大学1年生でも理解できる平易な説明（3〜5文）"\n'
        "}"
    )

    result = _complete_json(client, _JP_SYSTEM, prompt, max_tokens=2048)
    if isinstance(result, dict):
        return result

    return {
        "japanese_title": paper.get("title", ""),
        "summary": paper.get("snippet", ""),
        "one_liner": "",
        "problem": "",
        "for_freshmen": "",
    }
