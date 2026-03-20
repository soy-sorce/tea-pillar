// src/lib/audioUtils.ts
// 音声 Blob → Base64 変換ユーティリティ

/**
 * Blob（WAV等）を Base64 文字列に変換する.
 */
export function blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            const result = reader.result as string;
            // "data:audio/wav;base64,xxxx" から "xxxx" 部分だけ取り出す
            const base64 = result.split(",")[1] ?? result;
            resolve(base64);
        };
        reader.onerror = () => reject(new Error("Failed to read audio blob"));
        reader.readAsDataURL(blob);
    });
}

/**
 * URL（サンプル音声など）を fetch して Base64 文字列に変換する.
 */
export async function audioUrlToBase64(url: string): Promise<string> {
    const res = await fetch(url);
    const blob = await res.blob();
    return blobToBase64(blob);
}
