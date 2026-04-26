from __future__ import annotations

from datetime import datetime

from .app_service import MailProcessingService
from .models import CategoryConfig
from .utils import format_datetime, parse_date_input


class MailCLI:
    def __init__(self) -> None:
        self.service = MailProcessingService()

    def run(self) -> None:
        while True:
            print("\n=== Почтовый помощник ===")
            print("1. Обработать письма")
            print("2. Настроить авторизацию")
            print("3. Настроить категории")
            print("4. Настроить модули")
            print("5. Экспортировать результат")
            print("0. Выход")
            choice = input("Выберите пункт: ").strip()

            if choice == "1":
                self.process_emails()
            elif choice == "2":
                self.configure_auth()
            elif choice == "3":
                self.configure_categories()
            elif choice == "4":
                self.configure_modules()
            elif choice == "5":
                self.export()
            elif choice == "0":
                break
            else:
                print("Неизвестная команда.")

    def configure_auth(self) -> None:
        auth = self.service.auth
        email = input(f"Email [{auth.get('email', '')}]: ").strip() or str(auth.get("email", ""))
        password = input("Пароль или app-password [скрытие не реализовано в CLI]: ").strip() or str(auth.get("password", ""))
        host = input(f"IMAP host [{auth.get('imap_host', 'imap.gmail.com')}]: ").strip() or str(auth.get("imap_host", "imap.gmail.com"))
        port_raw = input(f"IMAP port [{auth.get('imap_port', 993)}]: ").strip() or str(auth.get("imap_port", 993))
        ssl_raw = input(f"SSL (y/n) [{'y' if auth.get('use_ssl', True) else 'n'}]: ").strip().lower()
        use_ssl = auth.get("use_ssl", True) if ssl_raw == "" else ssl_raw in {"y", "yes", "1", "д", "да"}
        self.service.save_auth_data(email, password, host, int(port_raw), bool(use_ssl))
        print("Данные авторизации сохранены.")

    def configure_categories(self) -> None:
        settings = self.service.settings
        print("\nТекущие категории:")
        for index, category in enumerate(settings.categories, start=1):
            print(f"{index}. {category.name} -> {', '.join(category.keywords)}")
        action = input("Добавить новую категорию? (y/n): ").strip().lower()
        if action not in {"y", "yes", "д", "да"}:
            return
        name = input("Название категории: ").strip()
        keywords = [item.strip() for item in input("Ключевые слова через запятую: ").split(",") if item.strip()]
        description = input("Краткое описание: ").strip()
        settings.categories.append(CategoryConfig(name=name, keywords=keywords, description=description))
        self.service.save_settings_data(settings)
        print("Категория сохранена.")

    def configure_modules(self) -> None:
        settings = self.service.settings
        reply_raw = input(f"Включить модуль ответов? (y/n) [{'y' if settings.enable_reply_module else 'n'}]: ").strip().lower()
        heatmap_raw = input(f"Включить тепловые карты? (y/n) [{'y' if settings.enable_heatmap_module else 'n'}]: ").strip().lower()
        if reply_raw:
            settings.enable_reply_module = reply_raw in {"y", "yes", "д", "да"}
        if heatmap_raw:
            settings.enable_heatmap_module = heatmap_raw in {"y", "yes", "д", "да"}
        self.service.save_settings_data(settings)
        print("Настройки модулей сохранены.")

    def process_emails(self) -> None:
        start_date = parse_date_input(input("Дата начала (YYYY-MM-DD): ").strip())
        end_date = parse_date_input(input("Дата конца (YYYY-MM-DD): ").strip())
        results = self.service.fetch_and_process(start_date, end_date)
        print(f"\nОбработано писем: {len(results)}")
        for item in results:
            print("-" * 70)
            print(f"Категория: {item.assignment.category} (уверенность: {item.assignment.confidence})")
            print(f"От: {item.email.sender_name} <{item.email.sender_email}>")
            print(f"Дата: {format_datetime(item.email.received_at)}")
            print(f"Тема: {item.email.subject}")
            print(f"Текст: {item.email.normalized_body[:300]}{'...' if len(item.email.normalized_body) > 300 else ''}")
            if self.service.settings.enable_reply_module and item.suggested_reply:
                print(f"Предлагаемый ответ:\n{item.suggested_reply}")

    def export(self) -> None:
        export_path = self.service.export_results()
        print(f"Экспорт завершён. Создан файл: {export_path}")
