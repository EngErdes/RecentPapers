"""Gmail から Google Scholar アラートメールを取得する。

認証は Google Workspace で発行したアプリパスワードによる IMAP ログイン
（GMAIL_USER / GMAIL_APP_PASSWORD）。OAuth2 の同意フローが不要なため、
ブラウザを開けない GitHub Actions でもそのまま動作する。
"""

import base64
import email
import imaplib
import os
import re
import time
from datetime import datetime, timedelta, timezone
from email.header import decode_header, make_header
from email.message import Message

from config import IMAP_HOST, IMAP_PORT

# FETCH レスポンス（例: b'1 (X-GM-THRID 1699... UID 42 INTERNALDATE "01-Aug-2026 ...")'）の解析用
_THRID_RE = re.compile(rb"X-GM-THRID\s+(\d+)")
_UID_RE = re.compile(rb"UID\s+(\d+)")


def _require_credentials() -> tuple[str, str]:
    """GMAIL_USER / GMAIL_APP_PASSWORD を読み出す。未設定なら明示的に失敗する。"""
    user = os.getenv("GMAIL_USER")
    password = os.getenv("GMAIL_APP_PASSWORD")

    missing = [
        name
        for name, value in (("GMAIL_USER", user), ("GMAIL_APP_PASSWORD", password))
        if not value
    ]
    if missing:
        raise RuntimeError(
            f"Gmail の認証情報が未設定です: {', '.join(missing)}。"
            "ローカルでは .env に、GitHub Actions では repository secret に設定してください。"
        )

    # Google はアプリパスワードを4文字ずつ空白区切りで表示する。
    # そのまま貼り付けられていても通るよう空白を除去する。
    return user, password.replace(" ", "")


def get_gmail_connection() -> imaplib.IMAP4_SSL:
    """アプリパスワードで Gmail の IMAP に接続し、ログイン済みの接続を返す。"""
    user, password = _require_credentials()

    conn = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    try:
        conn.login(user, password)
    except imaplib.IMAP4.error as e:
        conn.logout()
        raise RuntimeError(
            f"Gmail への IMAP ログインに失敗しました（{user}）: {e}。"
            "アプリパスワードが有効か、対象アカウントで IMAP が有効になっているか確認してください。"
        ) from e
    return conn


def _encode_mailbox(name: str) -> str:
    """メールボックス名を modified UTF-7（RFC 3501 5.1.3）で符号化する。

    Gmail のラベルは日本語を含むため、そのままでは SELECT できない。
    印字可能 ASCII はそのまま、'&' は '&-'、それ以外は UTF-16BE を base64 化して
    '&...-' で囲む（base64 の '/' は ',' に置換する）。
    """
    out: list[str] = []
    buf: list[str] = []

    def flush() -> None:
        if buf:
            encoded = base64.b64encode("".join(buf).encode("utf-16-be")).decode("ascii")
            out.append("&" + encoded.rstrip("=").replace("/", ",") + "-")
            buf.clear()

    for ch in name:
        if ch == "&":
            flush()
            out.append("&-")
        elif "\x20" <= ch <= "\x7e":
            flush()
            out.append(ch)
        else:
            buf.append(ch)
    flush()
    return "".join(out)


def _decode_mailbox(raw: bytes) -> str:
    """modified UTF-7 のメールボックス名を復号する（_encode_mailbox の逆）。"""
    text = raw.decode("ascii", errors="replace")

    out: list[str] = []
    i = 0
    while i < len(text):
        if text[i] != "&":
            out.append(text[i])
            i += 1
            continue

        end = text.find("-", i + 1)
        if end == -1:  # 閉じられていない符号化。そのまま残す
            out.append(text[i:])
            break

        chunk = text[i + 1 : end]
        if not chunk:  # '&-' はリテラルの '&'
            out.append("&")
        else:
            b64 = chunk.replace(",", "/")
            b64 += "=" * (-len(b64) % 4)
            try:
                out.append(base64.b64decode(b64).decode("utf-16-be"))
            except (ValueError, UnicodeDecodeError):
                out.append(text[i : end + 1])
        i = end + 1
    return "".join(out)


def _list_labels(conn: imaplib.IMAP4_SSL) -> list[str]:
    """サーバ上のラベル（メールボックス）名を復号して列挙する。"""
    typ, data = conn.list()
    if typ != "OK":
        return []

    labels = []
    for line in data:
        if not isinstance(line, bytes):
            continue
        # 例: b'(\\HasNoChildren) "/" "INBOX"'
        m = re.search(rb'"([^"]*)"$', line)
        if m:
            labels.append(_decode_mailbox(m.group(1)))
    return labels


def resolve_label_mailbox(conn: imaplib.IMAP4_SSL, label_name: str) -> str:
    """ラベル名を SELECT 可能なメールボックス名に変換し、存在を確認して返す。

    Gmail API のラベル ID に相当するものは IMAP には無く、
    符号化済みのメールボックス名がそのまま識別子になる。
    """
    mailbox = f'"{_encode_mailbox(label_name)}"'

    typ, data = conn.select(mailbox, readonly=True)
    if typ != "OK":
        available = "\n  ".join(_list_labels(conn))
        raise ValueError(
            f"Gmail label not found: '{label_name}'\n利用可能なラベル:\n  {available}"
        )

    # ラベル自体が空なのか、期間の絞り込みで0件になったのかを切り分けられるようにする
    total = int(data[0]) if data and data[0] and data[0].isdigit() else 0
    print(f"  [imap] label '{label_name}' → {total} message(s) total")
    return mailbox


def fetch_recent_threads(
    conn: imaplib.IMAP4_SSL,
    mailbox: str,
    hours: int = 24,
    limit: int | None = None,
) -> list[dict]:
    """直近 hours 時間のメッセージをスレッド単位（新しい順）で返す。

    IMAP の SEARCH SINCE は日単位でしか絞れないため、日付で粗く検索したうえで
    INTERNALDATE により時刻まで厳密に判定する。同一スレッド（X-GM-THRID）の
    メッセージは最新の1通だけを残す。

    limit を指定すると、新しい順に最大その件数までで打ち切る。
    """
    typ, _ = conn.select(mailbox, readonly=True)
    if typ != "OK":
        raise RuntimeError(f"メールボックスを開けませんでした: {mailbox}")

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    # サーバとローカルのタイムゾーン差で取りこぼさないよう、検索は1日広く取る
    since = (cutoff - timedelta(days=1)).strftime("%d-%b-%Y")

    typ, data = conn.uid("SEARCH", None, "SINCE", since)
    if typ != "OK":
        raise RuntimeError(f"IMAP SEARCH に失敗しました: {typ}")

    uids = data[0].split() if data and data[0] else []
    print(f"  [imap] SEARCH SINCE {since} → {len(uids)} message(s)")
    if not uids:
        return []

    uid_set = ",".join(uid.decode("ascii") for uid in uids)
    typ, data = conn.uid("FETCH", uid_set, "(X-GM-THRID INTERNALDATE)")
    if typ != "OK":
        raise RuntimeError(f"IMAP FETCH に失敗しました: {typ}")

    cutoff_ts = cutoff.timestamp()
    candidates = []
    for line in data:
        if not isinstance(line, bytes):
            continue

        uid_match = _UID_RE.search(line)
        if not uid_match:
            continue

        received = imaplib.Internaldate2tuple(line)
        if received is None or time.mktime(received) < cutoff_ts:
            continue

        thrid_match = _THRID_RE.search(line)
        # X-GM-THRID が返らない場合は UID をスレッド識別子として扱う
        thread_id = (thrid_match or uid_match).group(1).decode("ascii")
        candidates.append(
            {
                "id": uid_match.group(1).decode("ascii"),
                "thread_id": thread_id,
                "received": time.mktime(received),
            }
        )

    candidates.sort(key=lambda c: c["received"], reverse=True)

    threads = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate["thread_id"] in seen:
            continue
        seen.add(candidate["thread_id"])
        threads.append(candidate)
        if limit is not None and len(threads) >= limit:
            break

    print(
        f"  [imap] {len(candidates)} message(s) within {hours}h "
        f"→ {len(threads)} thread(s)"
    )
    return threads


def _decode_subject(raw: str) -> str:
    """RFC 2047 で符号化された件名を復号する。"""
    if not raw:
        return ""
    try:
        return str(make_header(decode_header(raw)))
    except (UnicodeDecodeError, LookupError, ValueError):
        return raw


def _extract_body(msg: Message) -> str:
    """text/html パートを優先して本文を取り出す。無ければ text/plain。"""
    plain = ""
    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue

        payload = part.get_payload(decode=True)
        if not payload:
            continue

        text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        if part.get_content_type() == "text/html":
            return text
        if part.get_content_type() == "text/plain" and not plain:
            plain = text
    return plain


def get_thread_content(conn: imaplib.IMAP4_SSL, message_uid: str) -> tuple[str, str]:
    """Return (subject, html_body) for the given message UID."""
    # BODY.PEEK[] は \Seen を立てずに本文を取得する
    typ, data = conn.uid("FETCH", message_uid, "(BODY.PEEK[])")
    if typ != "OK" or not data or not isinstance(data[0], tuple):
        return "", ""

    msg = email.message_from_bytes(data[0][1])
    return _decode_subject(msg.get("Subject", "")), _extract_body(msg)


def extract_keyword_from_subject(subject: str) -> str:
    # e.g. '"zero shot"; 言語: 英語, 日本語 - 新しい結果'
    m = re.match(r'^"?([^";]+)"?\s*;', subject)
    if m:
        return m.group(1).strip().strip('"')
    return subject.split(";")[0].strip().strip('"')
