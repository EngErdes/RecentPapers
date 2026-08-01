import os

from dotenv import load_dotenv

load_dotenv()

NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "34ea03616fa080d88a97d6eb8549c0a0")
# Notion API 2025-09-03 以降、ページ作成の親には data source を指定する。
# 統合（RecentPapers）が共有されている data source「論文メモ(local)」の ID。
NOTION_DATA_SOURCE_ID = os.getenv(
    "NOTION_DATA_SOURCE_ID", "1c0a0361-6fa0-80d1-a4cf-000b631d183e"
)
GMAIL_LABEL = "01.日々の情報収集/01.03GoogleScholar"
# Gmail への接続はアプリパスワードによる IMAP。認証情報は
# GMAIL_USER / GMAIL_APP_PASSWORD（.env または repository secret）から読む。
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
CLAUDE_MODEL = "claude-sonnet-4-6"

def _env_bool(name: str, default: bool) -> bool:
    """repository secret（環境変数）を真偽値として読む。未設定なら default。

    "1" / "true" / "yes" / "on"（大文字小文字問わず）を True とみなす。
    """
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


# デバッグフラグ: True でも Claude / Notion への処理内容は本番と同じ（ダミーは使わない）。
# 変わるのは処理範囲と中間成果物の保存のみ:
#   - 日付で絞らず、最新 DEBUG_THREAD_LIMIT スレッドだけを対象にする
#   - スレッド一覧の JSON と取得した PDF を debug/ 配下に保存する
# GitHub Actions では repository secret / variable の DEBUG で制御する（例: DEBUG=false）。
DEBUG = _env_bool("DEBUG", default=True)

# DEBUG 時に処理するスレッド数の上限（新しいものから）。
# 動作確認のたびに全スレッドを処理しないよう件数を絞る。
# なお DEBUG 時は日付でも絞らず、ラベル内の最新スレッドを対象にする。
DEBUG_THREAD_LIMIT = int(os.getenv("DEBUG_THREAD_LIMIT", "1"))

