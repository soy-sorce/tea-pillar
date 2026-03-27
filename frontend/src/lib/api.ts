import type {
    GenerateRequest,
    GenerateResponse,
    ReactionUploadCompleteRequest,
    ReactionUploadResponse,
    ReactionUploadUrlResponse,
} from "@/types/api";

const BASE_URL = (import.meta.env.VITE_BACKEND_URL as string) ?? "";
const TIMEOUT_MS = 360_000;

export class ApiError extends Error {
    errorCode: string;
    status: number;

    constructor(errorCode: string, message: string, status: number) {
        super(message);
        this.name = "ApiError";
        this.errorCode = errorCode;
        this.status = status;
    }
}

async function parseErrorResponse(res: Response): Promise<ApiError> {
    try {
        const err = (await res.json()) as { error_code?: string; message?: string };
        return new ApiError(
            err.error_code ?? "UNKNOWN_ERROR",
            err.message ?? "API error",
            res.status,
        );
    } catch {
        return new ApiError("UNKNOWN_ERROR", "API error", res.status);
    }
}

export async function postJson<TResponse>(path: string, body: unknown): Promise<TResponse> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

    try {
        const res = await fetch(`${BASE_URL}${path}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
            signal: controller.signal,
        });

        if (!res.ok) {
            throw await parseErrorResponse(res);
        }

        return (await res.json()) as TResponse;
    } catch (e) {
        if (e instanceof ApiError) throw e;
        if (e instanceof DOMException && e.name === "AbortError") {
            throw new ApiError("TIMEOUT", "リクエストがタイムアウトしました", 504);
        }
        throw new ApiError("NETWORK_ERROR", "ネットワークエラーが発生しました", 0);
    } finally {
        clearTimeout(timeoutId);
    }
}

export async function putBinary(uploadUrl: string, blob: Blob, contentType: string): Promise<void> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

    try {
        const res = await fetch(uploadUrl, {
            method: "PUT",
            headers: { "Content-Type": contentType },
            body: blob,
            signal: controller.signal,
        });
        if (!res.ok) {
            throw new ApiError("UPLOAD_FAILED", "動画アップロードに失敗しました", res.status);
        }
    } catch (e) {
        if (e instanceof ApiError) throw e;
        if (e instanceof DOMException && e.name === "AbortError") {
            throw new ApiError("TIMEOUT", "アップロードがタイムアウトしました", 504);
        }
        throw new ApiError("NETWORK_ERROR", "ネットワークエラーが発生しました", 0);
    } finally {
        clearTimeout(timeoutId);
    }
}

export function generateVideo(body: GenerateRequest): Promise<GenerateResponse> {
    return postJson<GenerateResponse>("/generate", body);
}

export function issueReactionUploadUrl(sessionId: string): Promise<ReactionUploadUrlResponse> {
    return postJson<ReactionUploadUrlResponse>(`/sessions/${sessionId}/reaction-upload-url`, {});
}

export function completeReactionUpload(
    sessionId: string,
    body: ReactionUploadCompleteRequest,
): Promise<ReactionUploadResponse> {
    return postJson<ReactionUploadResponse>(`/sessions/${sessionId}/reaction`, body);
}
