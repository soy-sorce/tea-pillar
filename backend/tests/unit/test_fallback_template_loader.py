"""Unit tests for fallback template loading."""

from __future__ import annotations

import random
from pathlib import Path

import pytest

from src.exceptions import TemplateSelectionError
from src.services.fallback_templates.loader import FallbackTemplateLoader


def test_loader_returns_random_active_template(tmp_path: Path) -> None:
    template_path = tmp_path / "templates.json"
    template_path.write_text(
        """[
  {"template_id": "video-1", "name": "one", "prompt_text": "p1", "is_active": true, "auto_generated": false},
  {"template_id": "video-2", "name": "two", "prompt_text": "p2", "is_active": false, "auto_generated": false},
  {"template_id": "video-3", "name": "three", "prompt_text": "p3", "is_active": true, "auto_generated": false}
]""",
        encoding="utf-8",
    )
    loader = FallbackTemplateLoader(template_path=template_path, rng=random.Random(0))

    template = loader.get_random_template()

    assert template.template_id in {"video-1", "video-3"}
    assert template.is_active is True


def test_loader_raises_when_no_active_template(tmp_path: Path) -> None:
    template_path = tmp_path / "templates.json"
    template_path.write_text(
        """[
  {"template_id": "video-2", "name": "two", "prompt_text": "p2", "is_active": false, "auto_generated": false}
]""",
        encoding="utf-8",
    )
    loader = FallbackTemplateLoader(template_path=template_path)

    with pytest.raises(TemplateSelectionError):
        loader.get_random_template()
