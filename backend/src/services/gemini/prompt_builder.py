from src.models.internal import CatFeatures

_SYSTEM_INSTRUCTION = """\
  あなたは猫向け動画のプロンプトクリエイターです。
  以下の情報を元に、Veo3で生成する動画のプロンプトを1件出力してください。
  出力はプロンプト文字列のみ（説明文・前置き不要）。"""

_CONSTRAINTS = """\
  - 動画は音声なし
  - 猫が興味を持ちやすい動きのある映像
  - 10〜15秒程度の短編"""


class PromptBuilder:
      """Gemini プロンプト組み立てクラス."""

      def build(
          self,
          template_text: str,
          cat_features: CatFeatures,
          state_key: str,
          user_context: str | None,
      ) -> str:
          context_section = (
              f"[オーナーが設定した猫の性格・好み]\n{user_context}"
              if user_context
              else "[オーナーが設定した猫の性格・好み]\n（指定なし）"
          )

          attentive = cat_features.clip_scores.get("attentive", 0.0)

          return f"""{_SYSTEM_INSTRUCTION}

  [テンプレート]
  {template_text}

  [猫の現在の状態]
  感情: {cat_features.emotion_label}
  鳴き声: {cat_features.meow_label or "不明"}
  注目スコア: {attentive:.2f}
  活発度: {cat_features.pose_activity_score:.2f}
  状態キー: {state_key}

  {context_section}

  [制約]
  {_CONSTRAINTS}"""

  
  
  


