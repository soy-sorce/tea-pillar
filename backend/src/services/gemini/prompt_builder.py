"""Gemini prompt builder."""

from src.models.internal import CatFeatures

_SYSTEM_INSTRUCTION = """\
あなたは猫向け動画のプロンプトクリエイターです。
以下の情報を元に、Veo で生成する動画のプロンプトを 1 件だけ出力してください。
出力はプロンプト文字列のみとし、説明文や前置きは不要です。"""

_CONSTRAINTS = """\
- 動画は音声なし
- 猫が興味を持ちやすい動きのある映像
- 10〜15秒程度の短編
- 実写寄りで不気味さを避ける
- 画面全体で視線誘導がしやすい構図"""


class PromptBuilder:
    """Build the Gemini input prompt."""

    def build(
        self,
        template_text: str,
        cat_features: CatFeatures | None,
        state_key: str | None,
        user_context: str | None,
    ) -> str:
        """Assemble the prompt from model outputs and template text."""
        context_section = user_context if user_context else "（指定なし）"
        if cat_features is None:
            labels_section = """\
- emotion_label: unknown
- clip_top_label: unknown
- meow_label: unknown"""
            feature_lines = "（利用不可: Vertex AI fallback）"
        else:
            labels_section = f"""\
- emotion_label: {cat_features.emotion_label}
- clip_top_label: {cat_features.clip_top_label}
- meow_label: {cat_features.meow_label or "unknown"}"""
            feature_lines = "\n".join(
                f"- {key}: {value:.4f}" for key, value in sorted(cat_features.features.items())
            )
        state_key_section = state_key or "fallback"
        return f"""{_SYSTEM_INSTRUCTION}

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
{_CONSTRAINTS}
"""
