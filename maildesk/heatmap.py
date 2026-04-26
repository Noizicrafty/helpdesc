from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt

from .models import ProcessedEmail
from .utils import ensure_directory, slugify


class HeatmapBuilder:
    def save_category_heatmaps(self, grouped_emails: Dict[str, List[ProcessedEmail]], output_dir: str | Path) -> dict[str, Path]:
        output_path = ensure_directory(output_dir)
        created: dict[str, Path] = {}

        for category, items in grouped_emails.items():
            if not items:
                continue
            labels = []
            values = []
            for item in items[:10]:
                top_terms = item.assignment.heatmap_terms[:6]
                top_values = item.assignment.heatmap_values[:6]
                if not top_terms:
                    continue
                labels.extend(top_terms)
                values.extend(top_values)

            if not labels:
                continue

            fig, ax = plt.subplots(figsize=(8, 3.8))
            ax.imshow([values], aspect="auto")
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=45, ha="right")
            ax.set_yticks([0])
            ax.set_yticklabels([category])
            ax.set_title(f"Тепловая карта: {category}")
            fig.tight_layout()

            file_path = output_path / f"{slugify(category)}_heatmap.png"
            fig.savefig(file_path, dpi=160)
            plt.close(fig)
            created[category] = file_path
        return created
