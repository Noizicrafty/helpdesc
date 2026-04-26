from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

from .models import AppSettings, CategoryConfig


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "runtime"
AUTH_PATH = CONFIG_DIR / "auth.json"
SETTINGS_PATH = CONFIG_DIR / "settings.json"
CATEGORIES_PATH = CONFIG_DIR / "categories.json"


DEFAULT_CATEGORIES = [
    CategoryConfig(name="Поддержка", keywords=["ошибка", "проблема", "не работает", "help", "support"]),
    CategoryConfig(name="Продажи", keywords=["цена", "коммерческое предложение", "счет", "purchase", "quote"]),
    CategoryConfig(name="Документы", keywords=["договор", "акт", "счет", "приложение", "document"]),
    CategoryConfig(name="Реклама и рассылки", keywords=["скидка", "акция", "unsubscribe", "sale", "offer"]),
]


def ensure_runtime_files() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not CATEGORIES_PATH.exists():
        serialized = [
            {"name": category.name, "keywords": category.keywords, "description": category.description}
            for category in DEFAULT_CATEGORIES
        ]
        CATEGORIES_PATH.write_text(json.dumps(serialized, ensure_ascii=False, indent=2), encoding="utf-8")

    if not SETTINGS_PATH.exists():
        settings = AppSettings(categories=DEFAULT_CATEGORIES)
        SETTINGS_PATH.write_text(json.dumps(settings.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    if not AUTH_PATH.exists():
        AUTH_PATH.write_text(
            json.dumps(
                {
                    "email": "",
                    "password": "",
                    "imap_host": "imap.gmail.com",
                    "imap_port": 993,
                    "use_ssl": True,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


def load_auth() -> Dict[str, object]:
    ensure_runtime_files()
    return json.loads(AUTH_PATH.read_text(encoding="utf-8"))


def save_auth(data: Dict[str, object]) -> None:
    ensure_runtime_files()
    AUTH_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_categories() -> list[CategoryConfig]:
    ensure_runtime_files()
    data = json.loads(CATEGORIES_PATH.read_text(encoding="utf-8"))
    categories = []
    for item in data:
        categories.append(
            CategoryConfig(
                name=item.get("name", "Без названия"),
                keywords=list(item.get("keywords", [])),
                description=item.get("description", ""),
            )
        )
    return categories


def save_categories(categories: list[CategoryConfig]) -> None:
    ensure_runtime_files()
    serialized = [
        {"name": category.name, "keywords": category.keywords, "description": category.description}
        for category in categories
    ]
    CATEGORIES_PATH.write_text(json.dumps(serialized, ensure_ascii=False, indent=2), encoding="utf-8")


def load_settings() -> AppSettings:
    ensure_runtime_files()
    data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    settings = AppSettings.from_dict(data)
    settings.categories = load_categories()
    return settings


def save_settings(settings: AppSettings) -> None:
    ensure_runtime_files()
    SETTINGS_PATH.write_text(json.dumps(settings.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    save_categories(settings.categories)


def load_full_config() -> Tuple[Dict[str, object], AppSettings]:
    return load_auth(), load_settings()
