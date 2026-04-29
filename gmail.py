import base64
import pickle
import re
from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import CREDENTIALS_PATH, GMAIL_SCOPES, TOKEN_PATH


def get_gmail_service():
    creds = None
    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), GMAIL_SCOPES
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
