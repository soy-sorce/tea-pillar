"""Load fallback templates from the repository seed file."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Self

from pydantic import ValidationError

from src.exceptions import TemplateSelectionError
from src.models.firestore import TemplateDocument

_REPO_ROOT = Path(__file__).resolve().parents[4]
_DEFAULT_TEMPLATE_PATH = _REPO_ROOT / "infra" / "firestore_initial_setup" / "templates.json"


class FallbackTemplateLoader:
    """Select a random active template from the seed file."""

    def __init__(
        self: Self,
        template_path: Path = _DEFAULT_TEMPLATE_PATH,
        rng: random.Random | None = None,
    ) -> None:
        self._template_path = template_path
        self._rng = rng or random.Random()

    def get_random_template(self: Self) -> TemplateDocument:
        """Return one active template."""
        templates = self._load_active_templates()
        if not templates:
            raise TemplateSelectionError(
                message="フォールバック用テンプレートが存在しません",
                detail=f"template_path={self._template_path}",
            )
        return self._rng.choice(templates)

    def _load_active_templates(self: Self) -> list[TemplateDocument]:
        try:
            raw = json.loads(self._template_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise TemplateSelectionError(
                message="フォールバック用テンプレートの読み込みに失敗しました",
                detail=f"template file not found: {self._template_path}",
            ) from exc
        except json.JSONDecodeError as exc:
            raise TemplateSelectionError(
                message="フォールバック用テンプレートの読み込みに失敗しました",
                detail=str(exc),
            ) from exc

        try:
            templates = [TemplateDocument.model_validate(item) for item in raw]
        except ValidationError as exc:
            raise TemplateSelectionError(
                message="フォールバック用テンプレートの形式が不正です",
                detail=str(exc),
            ) from exc
        return [template for template in templates if template.is_active]
