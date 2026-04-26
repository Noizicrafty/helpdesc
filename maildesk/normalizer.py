from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Tuple

from bs4 import BeautifulSoup


AD_PATTERNS = [
    r"unsubscribe",
    r"отписаться",
    r"скидк",
    r"акци",
    r"sale",
    r"promo",
    r"offer",
    r"реклам",
]

SPAM_PATTERNS = [
    r"urgent response",
    r"won prize",
    r"free money",
    r"срочно переведите",
    r"bitcoin",
    r"casino",
    r"криптовалют",
]


@dataclass
class NormalizationResult:
    text: str
    is_spam_like: bool
    spam_score: float


class EmailNormalizer:
    @staticmethod
    def strip_html(raw_text: str) -> str:
        if not raw_text:
            return ""
        soup = BeautifulSoup(raw_text, "html.parser")
        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()
        text = soup.get_text(" ")
        return html.unescape(text)

    @staticmethod
    def normalize_text(raw_text: str) -> str:
        text = EmailNormalizer.strip_html(raw_text)
        text = re.sub(r"https?://\S+", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"\b\S+@\S+\b", " ", text)
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[_*#>{}\[\]|~`]+", " ", text)
        return text.strip()

    @staticmethod
    def spam_score(text: str) -> Tuple[bool, float]:
        lowered = text.lower()
        score = 0.0
        for pattern in AD_PATTERNS:
            if re.search(pattern, lowered, flags=re.IGNORECASE):
                score += 0.15
        for pattern in SPAM_PATTERNS:
            if re.search(pattern, lowered, flags=re.IGNORECASE):
                score += 0.25
        if len(re.findall(r"[!$€₸₽]{2,}", text)) > 0:
            score += 0.2
        if sum(char.isupper() for char in text[:200]) > 40:
            score += 0.1
        return score >= 0.35, min(score, 1.0)

    def process(self, raw_text: str) -> NormalizationResult:
        normalized = self.normalize_text(raw_text)
        is_spam_like, score = self.spam_score(normalized)
        return NormalizationResult(text=normalized, is_spam_like=is_spam_like, spam_score=score)
