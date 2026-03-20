// src/lib/imageUtils.ts
// 画像 → Base64 変換ユーティリティ

/**
 * File または Blob を Base64 文字列に変換する.
 */
export function fileToBase64(file: File | Blob): Promise<string> {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            const result = reader.result as string;
            // "data:image/jpeg;base64,xxxx" から "xxxx" 部分だけ取り出す
            const base64 = result.split(",")[1] ?? result;
            resolve(base64);
        };
        reader.onerror = () => reject(new Error("Failed to read file"));
        reader.readAsDataURL(file);
    });
}

/**
 * HTMLCanvasElement を Base64 JPEG 文字列に変換する.
 */
export function canvasToBase64(canvas: HTMLCanvasElement): string {
    const dataUrl = canvas.toDataURL("image/jpeg", 0.9);
    return dataUrl.split(",")[1] ?? dataUrl;
}

/**
 * URL（サンプル画像など）を fetch して Base64 文字列に変換する.
 */
export async function urlToBase64(url: string): Promise<string> {
    const res = await fetch(url);
    const blob = await res.blob();
    return fileToBase64(blob);
}
