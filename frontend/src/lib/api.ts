// src/lib/api.ts
// fetchラッパー（タイムアウト・エラー処理）

const BASE_URL = (import.meta.env.VITE_BACKEND_URL as string) ?? "";
const TIMEOUT_MS = 360_000; // 360秒

export class ApiError extends Error {
    errorCode: string;
    status: number;

    constructor(
        errorCode: string,
        message: string,
        status: number
    ) {
        super(message);
        this.name = "ApiError";
        this.errorCode = errorCode;
        this.status = status;
    }
}

/**
 * Backend API への POST リクエストを送信する.
 *
 * @param path - エンドポイントパス（例: "/generate"）
 * @param body - リクエストボディ
 * @returns パース済みレスポンス
 * @throws {ApiError} HTTPエラーまたはタイムアウト時
 */
export async function post<TResponse>(
    path: string,
    body: unknown
): Promise<TResponse> {
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
            const err = (await res.json()) as { error_code: string; message: string };
            throw new ApiError(
                err.error_code ?? "UNKNOWN_ERROR",
                err.message,
                res.status
            );
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
