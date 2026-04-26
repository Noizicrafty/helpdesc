from __future__ import annotations

import re
from textwrap import shorten

from .models import ProcessedEmail


class ReplySuggester:
    def suggest(self, processed_email: ProcessedEmail) -> str:
        email = processed_email.email
        category = processed_email.assignment.category
        body = email.normalized_body
        short_issue = shorten(body, width=240, placeholder="...")
        subject = email.subject or "вашего письма"

        if email.is_spam_like:
            return (
                f"Здравствуйте, {email.sender_name}.\n\n"
                "Ваше письмо было автоматически отмечено как рекламное или потенциально спамовое. "
                "Если обращение требует ответа, пожалуйста, отправьте уточнение без рекламных вставок и лишнего оформления.\n\n"
                "С уважением."
            )

        if re.search(r"(ошибка|не работает|problem|issue|bug)", body, flags=re.IGNORECASE):
            return (
                f"Здравствуйте, {email.sender_name}.\n\n"
                f"Спасибо за сообщение по теме «{subject}». Мы приняли обращение в работу. "
                f"По описанию зафиксировано следующее: {short_issue}\n\n"
                "Если у вас есть дополнительные детали, скриншоты или шаги воспроизведения, пожалуйста, пришлите их ответом на это письмо.\n\n"
                "С уважением."
            )

        if re.search(r"(цена|стоимость|счет|quote|purchase|commercial)", body, flags=re.IGNORECASE):
            return (
                f"Здравствуйте, {email.sender_name}.\n\n"
                f"Спасибо за интерес к теме «{subject}». Мы подготовим ответ по категории «{category}» и направим детали в ближайшем письме.\n\n"
                "Если нужно ускорить обработку, пожалуйста, уточните объём, сроки и желаемый формат сотрудничества.\n\n"
                "С уважением."
            )

        return (
            f"Здравствуйте, {email.sender_name}.\n\n"
            f"Спасибо за письмо по теме «{subject}». Ваше обращение отнесено к категории «{category}».\n\n"
            f"Кратко по содержанию: {short_issue}\n\n"
            "Мы изучим детали и вернёмся с уточнённым ответом.\n\n"
            "С уважением."
        )
