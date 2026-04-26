from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from .models import ProcessedEmail
from .utils import ensure_directory, format_datetime


class ExportService:
    def export(
        self,
        processed_emails: List[ProcessedEmail],
        destination: str | Path,
        include_replies: bool,
        include_heatmaps: bool,
    ) -> Path:
        """Экспортирует результат в один CSV-файл.

        У CSV нет листов и страниц, поэтому темы сохраняются как секции внутри одного файла:
        сначала служебная строка с названием темы, затем строки писем этой темы.
        Параметр include_heatmaps сохранён для совместимости, но внешние файлы тепловых карт
        больше не создаются: тепловые карты используются только во внутренней логике обработки.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = ensure_directory(Path(destination))
        export_path = export_dir / f"mail_export_{timestamp}.csv"

        grouped: Dict[str, List[ProcessedEmail]] = defaultdict(list)
        for item in processed_emails:
            grouped[item.assignment.category].append(item)

        fieldnames = [
            "section",
            "sender_name",
            "sender_email",
            "subject",
            "body",
            "received_at",
            "category",
            "category_confidence",
        ]
        if include_replies:
            fieldnames.append("suggested_reply")

        with export_path.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()

            for category in sorted(grouped.keys(), key=lambda value: value.lower()):
                writer.writerow(
                    {
                        "section": f"=== ТЕМА: {category} ===",
                        "sender_name": "",
                        "sender_email": "",
                        "subject": "",
                        "body": "",
                        "received_at": "",
                        "category": category,
                        "category_confidence": "",
                        **({"suggested_reply": ""} if include_replies else {}),
                    }
                )

                items = sorted(grouped[category], key=lambda item: item.email.received_at)
                for item in items:
                    row = {
                        "section": category,
                        "sender_name": item.email.sender_name,
                        "sender_email": item.email.sender_email,
                        "subject": item.email.subject,
                        "body": item.email.normalized_body,
                        "received_at": format_datetime(item.email.received_at),
                        "category": item.assignment.category,
                        "category_confidence": item.assignment.confidence,
                    }
                    if include_replies:
                        row["suggested_reply"] = item.suggested_reply or ""
                    writer.writerow(row)

                writer.writerow({name: "" for name in fieldnames})

        return export_path
