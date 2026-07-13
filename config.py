import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "34ea03616fa080d88a97d6eb8549c0a0")
# Notion API 2025-09-03 以降、ページ作成の親には data source を指定する。
# 統合（RecentPapers）が共有されている data source「論文メモ(local)」の ID。
NOTION_DATA_SOURCE_ID = os.getenv(
    "NOTION_DATA_SOURCE_ID", "1c0a0361-6fa0-80d1-a4cf-000b631d183e"
)
GMAIL_LABEL = "01.日々の情報収集/01.03GoogleScholar"
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
BASE_DIR = Path(__file__).parent
TOKEN_PATH = BASE_DIR / "gmail_token.pickle"
CREDENTIALS_PATH = BASE_DIR / "gmail_credentials.json"
CLAUDE_MODEL = "claude-sonnet-4-6"

def _env_bool(name: str, default: bool) -> bool:
    """repository secret（環境変数）を真偽値として読む。未設定なら default。

    "1" / "true" / "yes" / "on"（大文字小文字問わず）を True とみなす。
    """
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


# デバッグフラグ: True のとき Claude API を呼ばず、ダミーの日本語コンテンツを返す。
# GitHub Actions では repository secret / variable の DEBUG で制御する（例: DEBUG=false）。
DEBUG = _env_bool("DEBUG", default=True)

# DEBUG 時に extract_papers_with_claude が返す固定のダミー論文リスト
DEBUG_PAPERS = [
    {
        "title": "[Dummy] A Sample Paper Title for Debugging",
        "authors": "Taro Yamada, Hanako Suzuki",
        "journal": "Journal of Debugging",
        "year": "2024",
        "snippet": "This is a dummy abstract snippet used only for debugging.",
        "pdf_url": "",
        "doi_url": "",
        "paper_url": "https://example.com/dummy-paper",
    },
]

# DEBUG 時に generate_japanese_content が返す固定のダミー内容
DEBUG_JAPANESE_CONTENT = {
    "japanese_title": "【ダミー】日本語タイトル",
    "summary": "【ダミー】これはデバッグ用のダミー要約です。実際の論文内容は反映されていません。",
    "one_liner": "【ダミー】一言キャッチコピー",
    "problem": "【ダミー】この論文が取り組んだ問題・課題の説明（ダミー）。",
    "for_freshmen": "【ダミー】大学1年生向けの平易な説明（ダミー）。",
}
