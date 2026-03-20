// src/hooks/useCamera.ts
import { useCallback, useState } from "react";
import { canvasToBase64 } from "@/lib/imageUtils";

interface UseCameraReturn {
    imageBase64: string | null;
    capturePhoto: () => Promise<void>;
    error: string | null;
}

export function useCamera(): UseCameraReturn {
    const [imageBase64, setImageBase64] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const capturePhoto = useCallback(async (): Promise<void> => {
        setError(null);
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            const video = document.createElement("video");
            video.srcObject = stream;
            await video.play();

            const canvas = document.createElement("canvas");
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext("2d")?.drawImage(video, 0, 0);

            const base64 = canvasToBase64(canvas);
            setImageBase64(base64);
            stream.getTracks().forEach((t) => t.stop());
        } catch (_e) {
            setError("カメラへのアクセスが許可されていません");
        }
    }, []);

    return { imageBase64, capturePhoto, error };
}
