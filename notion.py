from notion_client import Client as NotionClient

from config import NOTION_DATABASE_ID


def _rich_text(content: str) -> list[dict]:
    return [{"text": {"content": content[:2000]}}]


def _heading(text: str) -> dict:
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }


def _paragraph(text: str) -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}]
        },
    }


def _divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def create_notion_page(
    notion: NotionClient,
    paper: dict,
    jp: dict,
    keyword: str,
) -> str:
    """Create a Notion database record and return its URL."""
    title = jp.get("japanese_title") or paper.get("title", "（タイトル不明）")
    journal_str = f"{paper.get('journal', '')} {paper.get('year', '')}".strip()

    properties: dict = {
        "名前": {"title": _rich_text(title)},
        "著者": {"rich_text": _rich_text(paper.get("authors", ""))},
        "掲載誌": {"rich_text": _rich_text(journal_str)},
        "要約": {"rich_text": _rich_text(jp.get("summary", paper.get("snippet", "")))},
        "アラートキーワード": {"rich_text": _rich_text(keyword)},
    }

    if paper.get("pdf_url"):
        properties["PDF リンク"] = {"url": paper["pdf_url"]}

    if paper.get("doi_url"):
        properties["DOI"] = {"url": paper["doi_url"]}

    blocks: list[dict] = []

    if jp.get("one_liner"):
        blocks += [_heading("📌 論文の一言要約"), _paragraph(jp["one_liner"]), _divider()]

    if jp.get("problem"):
        blocks += [_heading("❓ どんな問題？"), _paragraph(jp["problem"]), _divider()]

    if jp.get("for_freshmen"):
        blocks += [_heading("🎓 大学1年生向けの説明"), _paragraph(jp["for_freshmen"]), _divider()]

    if paper.get("paper_url"):
        blocks += [_heading("🔗 原文リンク"), _paragraph(paper["paper_url"])]

    page = notion.pages.create(
        parent={"database_id": NOTION_DATABASE_ID},
        properties=properties,
        children=blocks,
    )
    return page.get("url", "")
