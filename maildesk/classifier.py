from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import AssignmentResult, CategoryConfig, EmailMessageData


STOPWORDS = {
    "и", "в", "на", "с", "по", "к", "из", "это", "the", "for", "from", "that", "with",
    "что", "как", "а", "но", "или", "to", "of", "is", "are", "be", "мы", "вы", "ваш",
}


class EmailClassifier:
    def __init__(self, categories: List[CategoryConfig], enable_heatmap: bool = True) -> None:
        self.categories = categories or []
        self.enable_heatmap = enable_heatmap

    def _category_document(self, category: CategoryConfig) -> str:
        return " ".join([category.name, category.description, *category.keywords]).strip()

    def _keyword_score(self, email_text: str, category: CategoryConfig) -> float:
        lowered = email_text.lower()
        hits = 0
        for keyword in category.keywords:
            if keyword.lower() in lowered:
                hits += 1
        if not category.keywords:
            return 0.0
        return hits / len(category.keywords)

    def _top_terms(self, text: str, limit: int = 8) -> tuple[list[str], list[float]]:
        words = re.findall(r"[\w-]{4,}", text.lower(), flags=re.UNICODE)
        words = [word for word in words if word not in STOPWORDS and not word.isdigit()]
        counts = Counter(words)
        most_common = counts.most_common(limit)
        max_count = most_common[0][1] if most_common else 1
        terms = [term for term, _ in most_common]
        values = [round(count / max_count, 3) for _, count in most_common]
        return terms, values

    def _propose_new_category(self, text: str) -> str:
        terms, _ = self._top_terms(text, limit=3)
        if not terms:
            return "Новая категория"
        title = " ".join(term.capitalize() for term in terms[:2])
        return f"Новая категория: {title}"

    def assign(self, email_item: EmailMessageData) -> AssignmentResult:
        if not self.categories:
            terms, values = self._top_terms(email_item.normalized_body)
            return AssignmentResult(
                category=self._propose_new_category(email_item.normalized_body),
                confidence=0.0,
                suggested_new_category=True,
                category_reason="Категории не заданы, создано предложение новой категории.",
                heatmap_terms=terms,
                heatmap_values=values,
            )

        text = f"{email_item.subject} {email_item.normalized_body}".strip()
        keyword_scores = [self._keyword_score(text, category) for category in self.categories]
        terms, values = self._top_terms(email_item.normalized_body)

        if not self.enable_heatmap:
            best_index = max(range(len(self.categories)), key=lambda idx: keyword_scores[idx])
            best_score = keyword_scores[best_index]
            if best_score <= 0:
                return AssignmentResult(
                    category="Без категории",
                    confidence=0.0,
                    suggested_new_category=False,
                    category_reason="Модуль тепловых карт отключен, письмо не совпало с ключевыми словами категорий.",
                    heatmap_terms=terms,
                    heatmap_values=values,
                )
            return AssignmentResult(
                category=self.categories[best_index].name,
                confidence=round(best_score, 3),
                suggested_new_category=False,
                category_reason="Категория выбрана по ключевым словам, потому что модуль тепловых карт отключен.",
                heatmap_terms=terms,
                heatmap_values=values,
            )

        category_docs = [self._category_document(category) for category in self.categories]
        corpus = category_docs + [text]
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=2500)
        matrix = vectorizer.fit_transform(corpus)
        category_vectors = matrix[:-1]
        email_vector = matrix[-1]
        semantic_scores = cosine_similarity(email_vector, category_vectors)[0]

        final_scores: list[float] = []
        for idx, semantic_score in enumerate(semantic_scores):
            combined = semantic_score * 0.7 + keyword_scores[idx] * 0.3
            final_scores.append(float(combined))

        best_index = max(range(len(final_scores)), key=lambda idx: final_scores[idx])
        best_score = final_scores[best_index]

        if best_score < 0.22:
            proposed_name = self._propose_new_category(text)
            return AssignmentResult(
                category=proposed_name,
                confidence=round(best_score, 3),
                suggested_new_category=True,
                category_reason="Письмо слабо совпало с существующими темами, предложено создать новую категорию.",
                heatmap_terms=terms,
                heatmap_values=values,
            )

        return AssignmentResult(
            category=self.categories[best_index].name,
            confidence=round(best_score, 3),
            suggested_new_category=False,
            category_reason="Категория выбрана по сочетанию ключевых слов и семантической близости.",
            heatmap_terms=terms,
            heatmap_values=values,
        )
