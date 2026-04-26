from __future__ import annotations

import email
import imaplib
from datetime import datetime, timedelta
from email.message import Message
from email.utils import parsedate_to_datetime
from typing import List

from .models import EmailMessageData
from .utils import parse_sender, safe_decode_header


class IMAPMailClient:
    def __init__(self, email_address: str, password: str, host: str, port: int = 993, use_ssl: bool = True) -> None:
        self.email_address = email_address
        self.password = password
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.connection: imaplib.IMAP4 | imaplib.IMAP4_SSL | None = None

    def connect(self) -> None:
        if self.use_ssl:
            self.connection = imaplib.IMAP4_SSL(self.host, self.port)
        else:
            self.connection = imaplib.IMAP4(self.host, self.port)

        try:
            self.connection.login(self.email_address, self.password)
            self.connection.select("INBOX")
        except imaplib.IMAP4.error as exc:
            raw = exc.args[0] if exc.args else b""
            message = raw.decode("utf-8", "ignore") if isinstance(raw, (bytes, bytearray)) else str(raw)
            lowered = message.lower()

            if "application-specific password required" in lowered:
                raise RuntimeError(
                    "Gmail отклонил обычный пароль. Для Gmail и Google Mail используйте 16-значный app-password."
                ) from None
            if "invalid credentials" in lowered or "authentication failed" in lowered:
                raise RuntimeError(
                    "Не удалось войти в почтовый ящик. Проверьте email, пароль и настройки IMAP."
                ) from None
            raise RuntimeError(f"Ошибка IMAP-авторизации: {message}") from None

    def disconnect(self) -> None:
        if self.connection is None:
            return
        try:
            self.connection.close()
        except Exception:
            pass
        try:
            self.connection.logout()
        except Exception:
            pass
        self.connection = None

    def _extract_body(self, msg: Message) -> str:
        text_parts: list[str] = []
        html_parts: list[str] = []
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                disposition = str(part.get("Content-Disposition", "")).lower()
                if "attachment" in disposition:
                    continue
                payload = part.get_payload(decode=True)
                if payload is None:
                    continue
                charset = part.get_content_charset() or "utf-8"
                try:
                    decoded = payload.decode(charset, errors="ignore")
                except Exception:
                    decoded = payload.decode("utf-8", errors="ignore")
                if content_type == "text/plain":
                    text_parts.append(decoded)
                elif content_type == "text/html":
                    html_parts.append(decoded)
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                try:
                    decoded = payload.decode(charset, errors="ignore")
                except Exception:
                    decoded = payload.decode("utf-8", errors="ignore")
                if msg.get_content_type() == "text/html":
                    html_parts.append(decoded)
                else:
                    text_parts.append(decoded)
        return "\n".join(text_parts or html_parts)

    def fetch_emails_by_date_range(self, start_date: datetime, end_date: datetime) -> List[EmailMessageData]:
        if self.connection is None:
            raise RuntimeError("Нет активного соединения с IMAP")

        start_str = start_date.strftime("%d-%b-%Y")
        end_str = (end_date + timedelta(days=1)).strftime("%d-%b-%Y")
        status, message_ids = self.connection.search(None, f'(SINCE "{start_str}" BEFORE "{end_str}")')
        if status != "OK":
            raise RuntimeError("Не удалось выполнить поиск писем")

        messages: list[EmailMessageData] = []
        for uid in message_ids[0].split():
            status, data = self.connection.fetch(uid, "(RFC822)")
            if status != "OK" or not data or not data[0]:
                continue
            msg = email.message_from_bytes(data[0][1])
            subject = safe_decode_header(msg.get("Subject", ""))
            sender_name, sender_email = parse_sender(msg.get("From", ""))
            body = self._extract_body(msg)
            date_value = msg.get("Date", "")
            try:
                received_at = parsedate_to_datetime(date_value)
                if received_at.tzinfo is not None:
                    received_at = received_at.astimezone().replace(tzinfo=None)
            except Exception:
                received_at = datetime.now()

            headers = {
                "Message-ID": msg.get("Message-ID", ""),
                "Date": date_value,
                "From": msg.get("From", ""),
                "Subject": msg.get("Subject", ""),
            }
            messages.append(
                EmailMessageData(
                    message_id=headers["Message-ID"] or uid.decode("utf-8", errors="ignore"),
                    sender_name=sender_name,
                    sender_email=sender_email,
                    subject=subject,
                    body=body,
                    received_at=received_at,
                    raw_headers=headers,
                )
            )
        return sorted(messages, key=lambda item: item.received_at)