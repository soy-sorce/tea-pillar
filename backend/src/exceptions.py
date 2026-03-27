"""Application-specific exceptions."""

from http import HTTPStatus
from typing import Self


class NekkoflixBaseError(Exception):
    """Base application error."""

    error_code: str = "INTERNAL_ERROR"
    message: str = "予期しないエラーが発生しました"
    detail: str | None = None
    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR

    def __init__(
        self: Self,
        message: str | None = None,
        detail: str | None = None,
    ) -> None:
        if message is not None:
            self.message = message
        if detail is not None:
            self.detail = detail
        super().__init__(self.message)

    def to_response_content(self: Self) -> dict[str, str]:
        """Serialize the safe response payload."""
        return {
            "error_code": self.error_code,
            "message": self.message,
        }


class InvalidInputError(NekkoflixBaseError):
    error_code = "INVALID_INPUT"
    message = "入力データに問題があります"
    status_code = HTTPStatus.BAD_REQUEST


class ResourceNotFoundError(NekkoflixBaseError):
    error_code = "NOT_FOUND"
    message = "対象データが見つかりません"
    status_code = HTTPStatus.NOT_FOUND


class SessionConflictError(NekkoflixBaseError):
    error_code = "SESSION_CONFLICT"
    message = "セッション状態が不正です"
    status_code = HTTPStatus.CONFLICT


class RateLimitExceededError(NekkoflixBaseError):
    error_code = "RATE_LIMIT_EXCEEDED"
    message = "リクエスト上限を超えました"
    status_code = HTTPStatus.TOO_MANY_REQUESTS


class ModelServiceTimeoutError(NekkoflixBaseError):
    error_code = "MODEL_TIMEOUT"
    message = "モデルサービスの応答がタイムアウトしました"
    status_code = HTTPStatus.GATEWAY_TIMEOUT


class ModelServiceError(NekkoflixBaseError):
    error_code = "MODEL_FAILED"
    message = "モデルサービスの呼び出しに失敗しました"
    status_code = HTTPStatus.BAD_GATEWAY


class GeminiError(NekkoflixBaseError):
    error_code = "GEMINI_FAILED"
    message = "プロンプトの生成に失敗しました"
    status_code = HTTPStatus.BAD_GATEWAY


class VeoGenerationError(NekkoflixBaseError):
    error_code = "VEO_FAILED"
    message = "動画の生成に失敗しました。もう一度お試しください"
    status_code = HTTPStatus.BAD_GATEWAY


class VeoTimeoutError(NekkoflixBaseError):
    error_code = "VEO_TIMEOUT"
    message = "動画生成がタイムアウトしました"
    status_code = HTTPStatus.GATEWAY_TIMEOUT


class FirestoreError(NekkoflixBaseError):
    error_code = "FIRESTORE_FAILED"
    message = "データの保存または取得に失敗しました"
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR


class TemplateSelectionError(NekkoflixBaseError):
    error_code = "TEMPLATE_SELECTION_FAILED"
    message = "テンプレート選択に失敗しました"
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR


class NotConfiguredError(NekkoflixBaseError):
    error_code = "NOT_CONFIGURED"
    message = "必要な設定が未完了です"
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR


class ReactionVideoUploadError(NekkoflixBaseError):
    error_code = "REACTION_UPLOAD_FAILED"
    message = "反応動画の保存に失敗しました"
    status_code = HTTPStatus.BAD_GATEWAY


class RewardAnalysisError(NekkoflixBaseError):
    error_code = "REWARD_ANALYSIS_FAILED"
    message = "報酬解析に失敗しました"
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
