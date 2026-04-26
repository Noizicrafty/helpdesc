from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from .classifier import EmailClassifier
from .config_manager import load_auth, load_settings, save_auth, save_settings
from .exporter import ExportService
from .mail_client import IMAPMailClient
from .models import AppSettings, ProcessedEmail
from .normalizer import EmailNormalizer
from .reply_suggester import ReplySuggester


class MailProcessingService:
    def __init__(self) -> None:
        self.auth = load_auth()
        self.settings = load_settings()
        self.normalizer = EmailNormalizer()
        self.reply_suggester = ReplySuggester()
        self.exporter = ExportService()
        self.processed_emails: list[ProcessedEmail] = []

    def refresh_config(self) -> None:
        self.auth = load_auth()
        self.settings = load_settings()

    def save_auth_data(self, email: str, password: str, host: str, port: int, use_ssl: bool) -> None:
        save_auth(
            {
                "email": email,
                "password": password,
                "imap_host": host,
                "imap_port": port,
                "use_ssl": use_ssl,
            }
        )
        self.refresh_config()

    def save_settings_data(self, settings: AppSettings) -> None:
        save_settings(settings)
        self.refresh_config()

    def fetch_and_process(self, start_date: datetime, end_date: datetime) -> List[ProcessedEmail]:
        self.refresh_config()
        client = IMAPMailClient(
            email_address=str(self.auth.get("email", "")),
            password=str(self.auth.get("password", "")),
            host=str(self.auth.get("imap_host", self.settings.imap_host)),
            port=int(self.auth.get("imap_port", self.settings.imap_port)),
            use_ssl=bool(self.auth.get("use_ssl", self.settings.use_ssl)),
        )
        if not client.email_address or not client.password:
            raise ValueError("Не заполнены данные авторизации в runtime/auth.json или через настройки приложения.")

        try:
            client.connect()
            emails = client.fetch_emails_by_date_range(start_date, end_date)
        finally:
            client.disconnect()

        classifier = EmailClassifier(self.settings.categories, enable_heatmap=self.settings.enable_heatmap_module)
        processed: list[ProcessedEmail] = []
        for email_item in emails:
            normalized = self.normalizer.process(email_item.body)
            email_item.normalized_body = normalized.text
            email_item.is_spam_like = normalized.is_spam_like
            email_item.spam_score = normalized.spam_score

            assignment = classifier.assign(email_item)
            processed_email = ProcessedEmail(email=email_item, assignment=assignment)
            if self.settings.enable_reply_module:
                processed_email.suggested_reply = self.reply_suggester.suggest(processed_email)
            processed.append(processed_email)

        self.processed_emails = processed
        return processed

    def export_results(self) -> str:
        if not self.processed_emails:
            raise ValueError("Нет обработанных писем для экспорта.")
        export_dir = self.exporter.export(
            processed_emails=self.processed_emails,
            destination=self.settings.export_directory,
            include_replies=self.settings.enable_reply_module,
            include_heatmaps=self.settings.enable_heatmap_module,
        )
        return str(export_dir)

    def grouped_results(self) -> Dict[str, List[ProcessedEmail]]:
        grouped: dict[str, list[ProcessedEmail]] = defaultdict(list)
        for item in self.processed_emails:
            grouped[item.assignment.category].append(item)
        return dict(grouped)
