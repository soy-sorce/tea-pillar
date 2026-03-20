"""Seed Firestore with initial templates and optional bandit_table entries."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from google.cloud import firestore
from google.cloud.firestore import AsyncClient

TEMPLATES_COLLECTION = "templates"
BANDIT_TABLE_COLLECTION = "bandit_table"

EMOTION_LABELS = ("happy", "sad", "angry")
CLIP_TOP_LABELS = (
    "attentive_cat",
    "relaxed_cat",
    "stressed_cat",
    "playful_cat",
    "sleepy_cat",
    "curious_cat",
    "alert_cat",
    "comfortable_cat",
)


@dataclass(frozen=True)
class SeedTemplate:
    template_id: str
    name: str
    prompt_text: str
    is_active: bool
    auto_generated: bool
    category: str
    source_content_ja: str
    source_query_ja: str
    source_train_data_dir: str

    def to_firestore_document(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "prompt_text": self.prompt_text,
            "is_active": self.is_active,
            "auto_generated": self.auto_generated,
            "category": self.category,
            "source_content_ja": self.source_content_ja,
            "source_query_ja": self.source_query_ja,
            "source_train_data_dir": self.source_train_data_dir,
            "created_at": firestore.SERVER_TIMESTAMP,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed Firestore initial data.")
    parser.add_argument("--project-id", required=True, help="GCP project id.")
    parser.add_argument(
        "--database-id",
        default="(default)",
        help="Firestore database id. Default: (default)",
    )
    parser.add_argument(
        "--templates-path",
        default=str(Path(__file__).with_name("templates.json")),
        help="Path to templates JSON.",
    )
    parser.add_argument(
        "--seed-bandit-table",
        action="store_true",
        help="Also initialize unknown_* state keys in bandit_table.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be written without writing to Firestore.",
    )
    return parser.parse_args()


def load_templates(path: str) -> list[SeedTemplate]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [SeedTemplate(**item) for item in payload]


def build_initial_state_keys() -> list[str]:
    state_keys: list[str] = []
    for emotion_label in EMOTION_LABELS:
        for clip_top_label in CLIP_TOP_LABELS:
            state_keys.append(f"unknown_{emotion_label}_{clip_top_label}")
    return state_keys


async def seed_templates(
    client: AsyncClient,
    templates: list[SeedTemplate],
    *,
    dry_run: bool,
) -> None:
    for template in templates:
        document_id = template.template_id
        document = template.to_firestore_document()
        if dry_run:
            print(
                f"[dry-run] templates/{document_id}: {json.dumps(document, ensure_ascii=False)}"
            )
            continue
        await (
            client.collection(TEMPLATES_COLLECTION).document(document_id).set(document)
        )


async def seed_bandit_table(
    client: AsyncClient,
    templates: list[SeedTemplate],
    *,
    dry_run: bool,
) -> None:
    for state_key in build_initial_state_keys():
        for template in templates:
            document_id = f"{state_key}__{template.template_id}"
            document = {
                "template_id": template.template_id,
                "state_key": state_key,
                "selection_count": 1,
                "cumulative_reward": 0.0,
                "mean_reward": 0.0,
                "updated_at": firestore.SERVER_TIMESTAMP,
            }
            if dry_run:
                print(
                    f"[dry-run] bandit_table/{document_id}: "
                    f"{json.dumps({k: v for k, v in document.items() if k != 'updated_at'}, ensure_ascii=False)}"
                )
                continue
            await (
                client.collection(BANDIT_TABLE_COLLECTION)
                .document(document_id)
                .set(document)
            )


async def main() -> None:
    args = parse_args()
    templates = load_templates(args.templates_path)
    client = firestore.AsyncClient(
        project=args.project_id,
        database=args.database_id,
    )

    print(f"Loaded templates: {len(templates)}")
    await seed_templates(client, templates, dry_run=args.dry_run)

    if args.seed_bandit_table:
        state_keys = build_initial_state_keys()
        print(f"Initializing bandit_table for {len(state_keys)} state keys")
        await seed_bandit_table(client, templates, dry_run=args.dry_run)

    if args.dry_run:
        print("Dry run completed.")
    else:
        print("Firestore initialization completed.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
