import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "34ea03616fa080d88a97d6eb8549c0a0")
GMAIL_LABEL = "01.日々の情報収集/01.03GoogleScholar"
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
BASE_DIR = Path(__file__).parent
TOKEN_PATH = BASE_DIR / "gmail_token.pickle"
CREDENTIALS_PATH = BASE_DIR / "gmail_credentials.json"
CLAUDE_MODEL = "claude-sonnet-4-6"
