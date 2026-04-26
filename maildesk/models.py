from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class EmailMessageData:
    message_id: str
    sender_name: str
    sender_email: str
    subject: str
    body: str
    received_at: datetime
    normalized_body: str = ""
    is_spam_like: bool = False
    spam_score: float = 0.0
    raw_headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class CategoryConfig:
    name: str
    keywords: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class AssignmentResult:
    category: str
    confidence: float
    suggested_new_category: bool = False
    category_reason: str = ""
    heatmap_terms: List[str] = field(default_factory=list)
    heatmap_values: List[float] = field(default_factory=list)


@dataclass
class ProcessedEmail:
    email: EmailMessageData
    assignment: AssignmentResult
    suggested_reply: Optional[str] = None


@dataclass
class AppSettings:
    imap_host: str = "imap.gmail.com"
    imap_port: int = 993
    use_ssl: bool = True
    theme: str = "light"
    enable_reply_module: bool = True
    enable_heatmap_module: bool = True
    export_directory: str = "exports"
    font_scale: int = 13
    categories: List[CategoryConfig] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "imap_host": self.imap_host,
            "imap_port": self.imap_port,
            "use_ssl": self.use_ssl,
            "theme": self.theme,
            "enable_reply_module": self.enable_reply_module,
            "enable_heatmap_module": self.enable_heatmap_module,
            "export_directory": self.export_directory,
            "font_scale": self.font_scale,
            "categories": [
                {
                    "name": category.name,
                    "keywords": category.keywords,
                    "description": category.description,
                }
                for category in self.categories
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppSettings":
        categories = [
            CategoryConfig(
                name=item.get("name", "Без названия"),
                keywords=list(item.get("keywords", [])),
                description=item.get("description", ""),
            )
            for item in data.get("categories", [])
        ]
        return cls(
            imap_host=data.get("imap_host", "imap.gmail.com"),
            imap_port=int(data.get("imap_port", 993)),
            use_ssl=bool(data.get("use_ssl", True)),
            theme=data.get("theme", "light"),
            enable_reply_module=bool(data.get("enable_reply_module", True)),
            enable_heatmap_module=bool(data.get("enable_heatmap_module", True)),
            export_directory=data.get("export_directory", "exports"),
            font_scale=int(data.get("font_scale", 13)),
            categories=categories,
        )
