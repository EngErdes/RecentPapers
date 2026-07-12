"""Notion ページ・プロパティ生成ヘルパー。

アクセス先 data source のスキーマ（カラム定義）を取得し、そこに実在する
カラムだけを型に合わせて埋めたレコードを作成する。カラムに収まらなかった
主要情報はページ本文のブロックへ退避して情報欠落を防ぐ。
"""

from notion_client import Client as NotionClient

from config import NOTION_DATA_SOURCE_ID

# ---------------------------------------------------------------------------
# カラム名エイリアス
# ---------------------------------------------------------------------------
# DB ごとにカラム名が異なりうるため、論理フィールドごとに候補名を定義する。
# プロパティ割り当て（_build_properties）と本文フォールバック判定の両方で
# 同じ定義を共有し、名称の食い違いを防ぐ。
# （タイトルは名前ではなく title 型で特定するためエイリアスは持たない）
_ALIAS_AUTHORS = ["著者", "Authors", "Author"]
_ALIAS_JOURNAL = ["掲載誌", "Journal", "雑誌", "出典"]
_ALIAS_SUMMARY = ["要約", "概要", "Summary", "Abstract"]
_ALIAS_MEMO = ["メモ", "一言要約", "キャッチコピー", "Memo", "Note"]
_ALIAS_KEYWORD = ["アラートキーワード", "キーワード", "Keyword", "Keywords", "タグ", "Tags"]
_ALIAS_PDF = ["pdf", "PDF リンク", "PDFリンク", "PDF"]
_ALIAS_DOI = ["DOI", "doi"]
_ALIAS_GIT = ["gitリポジトリ", "gitレポジトリ", "Git", "GitHub", "Repository", "Code", "コード"]
_ALIAS_PAPER_URL = ["原文リンク", "URL", "リンク", "Link"]


# ---------------------------------------------------------------------------
# ブロック生成ヘルパー
# ---------------------------------------------------------------------------
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


def _section(heading: str, body: str, divider: bool = True) -> list[dict]:
    """見出し＋本文（＋任意で区切り線）のブロック群を返す。"""
    blocks = [_heading(heading), _paragraph(body)]
    if divider:
        blocks.append(_divider())
    return blocks


# ---------------------------------------------------------------------------
# スキーマ取得・プロパティ整形
# ---------------------------------------------------------------------------
def get_data_source_schema(
    notion: NotionClient,
    data_source_id: str = NOTION_DATA_SOURCE_ID,
) -> dict:
    """アクセス先 data source のプロパティ（カラム）定義を取得する。

    返り値は {プロパティ名: プロパティ定義dict} の辞書。
    各定義には少なくとも "type" が含まれる。
    """
    ds = notion.data_sources.retrieve(data_source_id=data_source_id)
    return ds.get("properties", {})


def _find_property(schema: dict, candidates: list[str]) -> tuple[str, str] | None:
    """候補名リストのうち、schema に存在する最初のプロパティを (名前, 型) で返す。

    完全一致を優先し、見つからなければ大文字小文字を無視して照合する。
    """
    for name in candidates:
        if name in schema:
            return name, schema[name]["type"]
    lowered = {name.lower(): name for name in schema}
    for cand in candidates:
        actual = lowered.get(cand.lower())
        if actual:
            return actual, schema[actual]["type"]
    return None


def _format_value(prop_type: str, prop_def: dict, value: str) -> dict | None:
    """プロパティの型に合わせて Notion API 用の値を組み立てる。

    値が空、または型に対応できない場合は None を返し、呼び出し側でスキップする。
    """
    value = (value or "").strip()
    if not value:
        return None

    if prop_type == "title":
        return {"title": _rich_text(value)}
    if prop_type == "rich_text":
        return {"rich_text": _rich_text(value)}
    if prop_type == "url":
        return {"url": value[:2000]}
    if prop_type == "email":
        return {"email": value}
    if prop_type == "phone_number":
        return {"phone_number": value}
    if prop_type == "number":
        try:
            return {"number": float(value)}
        except ValueError:
            return None
    if prop_type == "checkbox":
        return {"checkbox": value.lower() in ("true", "yes", "1", "on")}
    if prop_type == "select":
        return {"select": {"name": value[:100]}}
    if prop_type == "multi_select":
        items = [v.strip() for v in value.replace("、", ",").split(",") if v.strip()]
        return {"multi_select": [{"name": v[:100]} for v in items]}
    if prop_type == "status":
        # status は既存オプションのみ指定可能。一致しなければスキップ。
        options = {o["name"] for o in prop_def.get("status", {}).get("options", [])}
        return {"status": {"name": value}} if value in options else None
    if prop_type == "date":
        return {"date": {"start": value}}
    # people / files / relation / formula など、文字列から生成できない型はスキップ
    return None


def _build_properties(
    schema: dict,
    title_value: str,
    field_values: list[tuple[list[str], str]],
) -> dict:
    """schema（実際のカラム定義）に基づき、存在するカラムだけを埋めた properties を返す。

    title 型のカラムは名前に依存せず型で特定し、必ず title_value で埋める。
    それ以外は field_values の (候補カラム名リスト, 値) を順に割り当てる。
    """
    properties: dict = {}

    # title 型カラムを型で特定して割り当てる（タイトルは必須）
    title_name = next(
        (name for name, d in schema.items() if d["type"] == "title"), None
    )
    if title_name:
        properties[title_name] = _format_value(
            "title", schema[title_name], title_value
        ) or {"title": _rich_text("（タイトル不明）")}

    # 残りのフィールドは候補名でカラムを探し、実際の型に合わせて整形
    for candidates, value in field_values:
        found = _find_property(schema, candidates)
        if not found:
            continue
        name, prop_type = found
        if name in properties:  # タイトルカラムと衝突する場合は上書きしない
            continue
        formatted = _format_value(prop_type, schema[name], value)
        if formatted is not None:
            properties[name] = formatted

    return properties


# ---------------------------------------------------------------------------
# ページ作成
# ---------------------------------------------------------------------------
def create_notion_page(
    notion: NotionClient,
    paper: dict,
    jp: dict,
    keyword: str,
    schema: dict | None = None,
) -> str:
    """data source のスキーマに基づき Notion レコードを作成し、その URL を返す。

    schema を渡さない場合はここで取得する（ループ処理では事前取得して渡すと効率的）。
    """
    if schema is None:
        schema = get_data_source_schema(notion)

    title = jp.get("japanese_title") or paper.get("title", "（タイトル不明）")
    journal_str = f"{paper.get('journal', '')} {paper.get('year', '')}".strip()
    summary = jp.get("summary", paper.get("snippet", ""))
    one_liner = jp.get("one_liner", "")

    # (候補カラム名リスト, 値) の並び。メモ列には一言キャッチコピーを入れる。
    # PDF は実取得できたリンクを優先し、無ければアラート記載の URL にフォールバック。
    field_values: list[tuple[list[str], str]] = [
        (_ALIAS_AUTHORS, paper.get("authors", "")),
        (_ALIAS_JOURNAL, journal_str),
        (_ALIAS_SUMMARY, summary),
        (_ALIAS_MEMO, one_liner),
        (_ALIAS_KEYWORD, keyword),
        (_ALIAS_PDF, paper.get("pdf_link") or paper.get("pdf_url", "")),
        (_ALIAS_DOI, paper.get("doi_url", "")),
        (_ALIAS_GIT, paper.get("git_url", "")),
        (_ALIAS_PAPER_URL, paper.get("paper_url", "")),
    ]

    properties = _build_properties(schema, title, field_values)
    filled = set(properties)

    def placed(aliases: list[str]) -> bool:
        """いずれかのエイリアス名が実際に埋まったプロパティに含まれるか。"""
        return bool(set(aliases) & filled)

    # --- 本文ブロック ---
    # プロパティに収まらなかった主要情報は本文へ退避して情報欠落を防ぐ。
    blocks: list[dict] = []

    meta_lines = []
    if paper.get("authors") and not placed(_ALIAS_AUTHORS):
        meta_lines.append(f"著者: {paper['authors']}")
    if journal_str and not placed(_ALIAS_JOURNAL):
        meta_lines.append(f"掲載誌: {journal_str}")
    if keyword and not placed(_ALIAS_KEYWORD):
        meta_lines.append(f"アラートキーワード: {keyword}")
    if meta_lines:
        blocks += [_paragraph("\n".join(meta_lines)), _divider()]

    if summary and not placed(_ALIAS_SUMMARY):
        blocks += _section("📝 要約", summary)
    if one_liner and not placed(_ALIAS_MEMO):
        blocks += _section("📌 論文の一言要約", one_liner)
    if jp.get("problem"):
        blocks += _section("❓ どんな問題？", jp["problem"])
    if jp.get("for_freshmen"):
        blocks += _section("🎓 大学1年生向けの説明", jp["for_freshmen"])
    if paper.get("paper_url") and not placed(_ALIAS_PAPER_URL):
        blocks += _section("🔗 原文リンク", paper["paper_url"], divider=False)

    page = notion.pages.create(
        parent={"type": "data_source_id", "data_source_id": NOTION_DATA_SOURCE_ID},
        properties=properties,
        children=blocks,
    )
    return page.get("url", "")
