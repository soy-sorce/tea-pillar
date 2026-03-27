import { useCallback, useEffect, useRef, useState, type RefObject } from "react";

import { canvasToBase64 } from "@/lib/imageUtils";

interface UseCameraReturn {
    videoRef: RefObject<HTMLVideoElement | null>;
    isReady: boolean;
    error: string | null;
    startCamera: () => Promise<void>;
    stopCamera: () => void;
    captureFrame: () => string | null;
    getStream: () => MediaStream | null;
}

export function useCamera(): UseCameraReturn {
    const videoRef = useRef<HTMLVideoElement | null>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const [isReady, setIsReady] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const stopCamera = useCallback((): void => {
        streamRef.current?.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
        if (videoRef.current) {
            videoRef.current.srcObject = null;
        }
        setIsReady(false);
    }, []);

    const startCamera = useCallback(async (): Promise<void> => {
        setError(null);
        if (streamRef.current) {
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: "user",
                },
                audio: false,
            });
            streamRef.current = stream;

            if (!videoRef.current) {
                setError("カメラプレビューの初期化に失敗しました");
                return;
            }

            videoRef.current.srcObject = stream;
            await videoRef.current.play();
            setIsReady(true);
        } catch {
            setError("カメラへのアクセスが許可されていません");
            stopCamera();
        }
    }, [stopCamera]);

    const captureFrame = useCallback((): string | null => {
        const video = videoRef.current;
        if (!video || video.videoWidth === 0 || video.videoHeight === 0) {
            return null;
        }

        const canvas = document.createElement("canvas");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const context = canvas.getContext("2d");
        if (!context) {
            return null;
        }
        context.drawImage(video, 0, 0);
        return canvasToBase64(canvas);
    }, []);

    const getStream = useCallback((): MediaStream | null => streamRef.current, []);

    useEffect(() => stopCamera, [stopCamera]);

    return {
        videoRef,
        isReady,
        error,
        startCamera,
        stopCamera,
        captureFrame,
        getStream,
    };
}
