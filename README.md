# Just Enough Mails (JEM)

Инструмент для подключения к IMAP-почте, чтения писем за выбранный период, интеллектуальной категоризации, фильтрации рекламных сообщений, генерации шаблонных ответов и экспорта результатов.

## Назначение и возможности

В текущей версии реализованы:

- Подключение к IMAP (Gmail и другие провайдеры).
- Обработка писем по диапазону дат.
- Очистка HTML и нормализация текста писем.
- Поиск рекламных и потенциально спамовых сообщений.
- Категоризация по ключевым словам и семантическому сходству.
- Автогенерация предлагаемых ответов.
- Экспорт результатов в CSV.
- CLI и desktop UI режимы.
- Docker запуск проекта.

## Технологии и зависимости

- Python 3.12+
- scikit-learn
- matplotlib
- beautifulsoup4
- tkinter
- IMAP (imaplib)
- Docker / Docker Compose

## Установка

```bash
git clone <repo_url>
cd helpdesc
pip install -r requirements.txt
```

## Быстрый старт

### Локальный запуск CLI

```bash
python main.py --mode cli
```

### Локальный запуск UI

```bash
python main.py --mode ui
```

### Docker запуск

```bash
docker compose up --build
```

## Docker

Быстрый запуск CLI в контейнере

Для сохранения данных используются volume:

- ./runtime -> /app/runtime
- ./exports -> /app/exports

## Конфигурация

Файлы создаются автоматически:

- runtime/auth.json
- runtime/settings.json
- runtime/categories.json

## Структура проекта

```text
.
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── main.py
├── README.md
├── runtime/
├── exports/
└── maildesk/
    ├── __init__.py
    ├── app_service.py
    ├── classifier.py
    ├── cli.py
    ├── config_manager.py
    ├── exporter.py
    ├── heatmap.py
    ├── mail_client.py
    ├── models.py
    ├── normalizer.py
    ├── reply_suggester.py
    ├── ui.py
    └── utils.py
```

## Пример сценария работы

1. Указать email и пароль приложения.
2. Выбрать период обработки.
3. Получить распределение писем по категориям.
4. Проверить предлагаемые ответы.
5. Экспортировать CSV отчёт.

## Безопасность

Рекомендуется использовать app-password для доступа к большинству почтовых сервисов

