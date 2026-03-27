"""Gemini prompt builder."""

from typing import Self

from src.models.internal import CatFeatures

_NORMAL_SYSTEM_INSTRUCTION = """\
あなたは猫向け動画のプロンプトクリエイターです。
以下の情報を元に、Veo で生成する動画のプロンプトを 1 件だけ出力してください。
出力はプロンプト文字列のみとし、説明文や前置きは不要です。"""

_FALLBACK_SYSTEM_INSTRUCTION = """\
You create exactly one video prompt for a cat-focused video.
Use only the template and owner context below.
Do not mention labels, state keys, fallback, or unavailable analysis.
Preserve the core idea and motion of the template,
but expand it into a more vivid, specific, and imaginative concept.
Prioritize originality, playfulness, and strong visual interest.
Adapt the mood and pacing to the owner context when it suggests a clear preference.
For example, if the cat seems to prefer calm or relaxed experiences,
lean into soothing and gentle ideas instead of overstimulating ones.
Make the prompt concrete and detailed rather than short.
Output exactly one prompt in English, with no heading, explanation, or multiple options."""

_NORMAL_CONSTRAINTS = """\
- 動画は音声なし
- 猫が興味を持ちやすい動きのある映像
- 10〜15秒程度の短編
- 実写寄りで不気味さを避ける
- 画面全体で視線誘導がしやすい構図"""

_FALLBACK_REQUIREMENTS = """\
- silent video
- use the template as the creative foundation
- reflect the owner context when it is helpful
- favor interesting, distinctive, memorable ideas over generic ones
- describe the scene in enough detail that the final video concept feels clear and specific"""


class PromptBuilder:
    """Build the Gemini input prompt."""

    def build(
        self: Self,
        template_text: str,
        cat_features: CatFeatures | None,
        state_key: str | None,
        user_context: str | None,
    ) -> str:
        """Assemble the prompt from model outputs and template text."""
        if cat_features is None:
            return self._build_fallback(
                template_text=template_text,
                user_context=user_context,
            )

        context_section = user_context if user_context else "（指定なし）"
        labels_section = f"""\
- emotion_label: {cat_features.emotion_label}
- clip_top_label: {cat_features.clip_top_label}
- meow_label: {cat_features.meow_label or "unknown"}"""
        feature_lines = "\n".join(
            f"- {key}: {value:.4f}" for key, value in sorted(cat_features.features.items())
        )
        state_key_section = state_key or "fallback"
        return f"""{_NORMAL_SYSTEM_INSTRUCTION}

[テンプレート]
{template_text}

[状態キー]
{state_key_section}

[補助ラベル]
{labels_section}

[猫状態特徴量]
{feature_lines}

[オーナーコンテキスト]
{context_section}

[制約]
{_NORMAL_CONSTRAINTS}
"""

    def _build_fallback(
        self: Self,
        template_text: str,
        user_context: str | None,
    ) -> str:
        """Assemble a fallback prompt when cat analysis is unavailable."""
        context_section = user_context if user_context else "none"
        return f"""{_FALLBACK_SYSTEM_INSTRUCTION}

[Template]
{template_text}

[Owner Context]
{context_section}

[Requirements]
{_FALLBACK_REQUIREMENTS}
"""
