"""Local template fallback repository."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Self

from src.models.firestore import TemplateDocument

_DEFAULT_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "data" / "templates.json"


class LocalTemplateRepository:
    """Load active templates from the bundled local JSON fallback."""

    def __init__(self: Self, template_path: Path | None = None) -> None:
        self._template_path = template_path or _DEFAULT_TEMPLATE_PATH

    def get_active_templates(self: Self) -> list[TemplateDocument]:
        """Return active templates from the local JSON bundle."""
        payload = json.loads(self._template_path.read_text(encoding="utf-8"))
        return sorted(
            [
                TemplateDocument.model_validate(template)
                for template in payload
                if _is_active_template(template)
            ],
            key=lambda template: template.template_id,
        )


def _is_active_template(template: object) -> bool:
    if not isinstance(template, dict):
        return False
    return bool(template.get("is_active", True))
