"""Application-specific exceptions."""

from http import HTTPStatus


class NekkoflixBaseError(Exception):
    """Base application error."""

    error_code: str = "INTERNAL_ERROR"
    message: str = "予期しないエラーが発生しました"
    detail: str | None = None
    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR

    def __init__(
        self,
        message: str | None = None,
        detail: str | None = None,
    ) -> None:
        if message is not None:
            self.message = message
        if detail is not None:
            self.detail = detail
        super().__init__(self.message)

    def to_response_content(self) -> dict[str, str]:
        """Serialize the safe response payload."""
        return {
            "error_code": self.error_code,
            "message": self.message,
        }


class InvalidInputError(NekkoflixBaseError):
    """Invalid request data."""

    error_code = "INVALID_INPUT"
    message = "入力データに問題があります"
    status_code = HTTPStatus.BAD_REQUEST


class ResourceNotFoundError(NekkoflixBaseError):
    """Requested resource was not found."""

    error_code = "NOT_FOUND"
    message = "対象データが見つかりません"
    status_code = HTTPStatus.NOT_FOUND


class SessionConflictError(NekkoflixBaseError):
    """Session state is not compatible with the request."""

    error_code = "SESSION_CONFLICT"
    message = "セッション状態が不正です"
    status_code = HTTPStatus.CONFLICT


class VertexAITimeoutError(NekkoflixBaseError):
    """Vertex AI timeout."""

    error_code = "VERTEX_TIMEOUT"
    message = "猫の状態解析に時間がかかっています。もう一度お試しください"
    status_code = HTTPStatus.GATEWAY_TIMEOUT


class VertexAIError(NekkoflixBaseError):
    """Vertex AI general failure."""

    error_code = "VERTEX_FAILED"
    message = "猫の状態解析に失敗しました"
    status_code = HTTPStatus.BAD_GATEWAY


class GeminiError(NekkoflixBaseError):
    """Gemini failure."""

    error_code = "GEMINI_FAILED"
    message = "プロンプトの生成に失敗しました"
    status_code = HTTPStatus.BAD_GATEWAY


class VeoGenerationError(NekkoflixBaseError):
    """Veo generation failure."""

    error_code = "VEO_FAILED"
    message = "動画の生成に失敗しました。もう一度お試しください"
    status_code = HTTPStatus.BAD_GATEWAY


class VeoTimeoutError(NekkoflixBaseError):
    """Veo generation timeout."""

    error_code = "VEO_TIMEOUT"
    message = "動画生成がタイムアウトしました"
    status_code = HTTPStatus.GATEWAY_TIMEOUT


class FirestoreError(NekkoflixBaseError):
    """Firestore failure."""

    error_code = "FIRESTORE_FAILED"
    message = "データの保存または取得に失敗しました"
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR


class TemplateSelectionError(NekkoflixBaseError):
    """Template lookup / selection failure."""

    error_code = "TEMPLATE_SELECTION_FAILED"
    message = "テンプレート選択に失敗しました"
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR


class NotConfiguredError(NekkoflixBaseError):
    """Required runtime configuration is missing."""

    error_code = "NOT_CONFIGURED"
    message = "必要な設定が未完了です"
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
