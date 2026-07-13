import base64
import os
import pickle
import re
from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import CREDENTIALS_PATH, GMAIL_SCOPES, TOKEN_PATH


def _client_config_from_env() -> dict | None:
    """GitHub Actions の repository secret（環境変数）から OAuth client config を組み立てる。

    gmail_credentials.json を置けない環境向け。標準的で秘匿性の低い項目（auth_uri 等）は
    デフォルト値を持つ。必須項目（client_id / client_secret / project_id）が揃わなければ
    None を返し、呼び出し側はファイル（CREDENTIALS_PATH）にフォールバックする。
    """
    client_id = os.getenv("GMAIL_CLIENT_ID")
    client_secret = os.getenv("GMAIL_CLIENT_SECRET")
    project_id = os.getenv("GMAIL_PROJECT_ID")
    if not (client_id and client_secret and project_id):
        return None

    redirect_uris = os.getenv("GMAIL_REDIRECT_URIS", "http://localhost")
    return {
        "installed": {
            "client_id": client_id,
            "project_id": project_id,
            "auth_uri": os.getenv(
                "GMAIL_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"
            ),
            "token_uri": os.getenv(
                "GMAIL_TOKEN_URI", "https://oauth2.googleapis.com/token"
            ),
            "auth_provider_x509_cert_url": os.getenv(
                "GMAIL_AUTH_PROVIDER_X509_CERT_URL",
                "https://www.googleapis.com/oauth2/v1/certs",
            ),
            "client_secret": client_secret,
            "redirect_uris": [u.strip() for u in redirect_uris.split(",") if u.strip()],
        }
    }


def get_gmail_service():
    creds = None
    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # repository secret（環境変数）に client 情報があればそれを、
            # 無ければ従来どおり gmail_credentials.json を使う。
            client_config = _client_config_from_env()
            if client_config is not None:
                flow = InstalledAppFlow.from_client_config(
                    client_config, GMAIL_SCOPES
                )
            elif CREDENTIALS_PATH.exists():
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(CREDENTIALS_PATH), GMAIL_SCOPES
                )
            else:
                raise RuntimeError(
                    "OAuth client 情報が見つかりません。gmail_credentials.json を配置するか、"
                    "GMAIL_CLIENT_ID / GMAIL_CLIENT_SECRET / GMAIL_PROJECT_ID を設定してください。"
                )
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)
    return build("gmail", "v1", credentials=creds)


def get_label_id(service, label_name: str) -> str:
    labels = service.users().labels().list(userId="me").execute().get("labels", [])
    for label in labels:
        if label["name"] == label_name:
            return label["id"]
    raise ValueError(f"Gmail label not found: '{label_name}'")


def fetch_recent_threads(service, label_id: str, hours: int = 24) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    query = f"after:{int(cutoff.timestamp())}"
    result = (
        service.users()
        .threads()
        .list(userId="me", labelIds=[label_id], q=query)
        .execute()
    )
    return result.get("threads", [])


def _iter_parts(payload):
    yield payload
    for part in payload.get("parts", []):
        yield from _iter_parts(part)


def get_thread_content(service, thread_id: str) -> tuple[str, str]:
    """Return (subject, html_body) for the first message in the thread."""
    thread = service.users().threads().get(
        userId="me", id=thread_id, format="full"
    ).execute()

    subject = ""
    html_body = ""

    for msg in thread.get("messages", []):
        payload = msg.get("payload", {})

        if not subject:
            for header in payload.get("headers", []):
                if header["name"] == "Subject":
                    subject = header["value"]
                    break

        for part in _iter_parts(payload):
            if part.get("mimeType") == "text/html":
                data = part.get("body", {}).get("data", "")
                if data:
                    html_body = base64.urlsafe_b64decode(data).decode(
                        "utf-8", errors="replace"
                    )
                    break

        if not html_body:
            data = payload.get("body", {}).get("data", "")
            if data:
                html_body = base64.urlsafe_b64decode(data).decode(
                    "utf-8", errors="replace"
                )

        if html_body:
            break

    return subject, html_body


def extract_keyword_from_subject(subject: str) -> str:
    # e.g. '"zero shot"; 言語: 英語, 日本語 - 新しい結果'
    m = re.match(r'^"?([^";]+)"?\s*;', subject)
    if m:
        return m.group(1).strip().strip('"')
    return subject.split(";")[0].strip().strip('"')
