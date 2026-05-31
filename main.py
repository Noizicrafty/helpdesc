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
        choices=("ui", "cli"),
        default="ui",
        help="Режим запуска приложения: ui — графический интерфейс, cli — консольное меню. По умолчанию: ui.",
    )
    return parser


def run_ui_mode() -> None:
    from maildesk.ui import run_ui

    run_ui()


def run_cli_mode() -> None:
    from maildesk.cli import MailCLI

    MailCLI().run()


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.mode == "cli":
            run_cli_mode()
        else:
            run_ui_mode()
    except KeyboardInterrupt:
        print("\nРабота приложения прервана пользователем.")
        return 130
    except Exception as exc:
        print(f"Ошибка запуска приложения: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
