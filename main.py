from __future__ import annotations

import argparse
import sys
from typing import Sequence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="JEM",
        description="Just Enough Mails: локальная обработка и категоризация входящей почты.",
    )
    parser.add_argument(
        "--mode",
        choices=("menu", "ui", "cli"),
        default="menu",
        help=(
            "Режим запуска приложения: menu — стартовое меню, "
            "ui — графический интерфейс, cli — консольное меню. "
            "По умолчанию: menu."
        ),
    )
    return parser


def run_ui_mode() -> None:
    from maildesk.ui import run_ui

    run_ui()


def run_cli_mode() -> None:
    from maildesk.cli import MailCLI

    MailCLI().run()


def run_settings_menu() -> None:
    from maildesk.cli import MailCLI

    cli = MailCLI()
    while True:
        print("\n=== Настройки JEM ===")
        print("1. Настроить авторизацию и IMAP")
        print("2. Настроить категории")
        print("3. Настроить модули")
        print("0. Назад")
        choice = input("Выберите пункт: ").strip()

        if choice == "1":
            cli.configure_auth()
        elif choice == "2":
            cli.configure_categories()
        elif choice == "3":
            cli.configure_modules()
        elif choice == "0":
            return
        else:
            print("Неизвестная команда. Выберите пункт из меню.")


def run_start_menu() -> int:
    while True:
        print("\n=== JEM — почтовый помощник ===")
        print("1. Запустить графический интерфейс")
        print("2. Запустить CLI-режим")
        print("3. Настройки")
        print("0. Выход")
        choice = input("Выберите режим работы: ").strip()

        if choice == "1":
            run_ui_mode()
        elif choice == "2":
            run_cli_mode()
        elif choice == "3":
            run_settings_menu()
        elif choice == "0":
            print("Выход из приложения.")
            return 0
        else:
            print("Неизвестная команда. Выберите пункт из меню.")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.mode == "cli":
            run_cli_mode()
        elif args.mode == "ui":
            run_ui_mode()
        else:
            return run_start_menu()
    except KeyboardInterrupt:
        print("\nРабота приложения прервана пользователем.")
        return 130
    except Exception as exc:
        print(f"Ошибка запуска приложения: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
