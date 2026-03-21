// src/hooks/useMicrophone.ts
import { useCallback, useEffect, useRef, useState } from "react";
import { blobToBase64 } from "@/lib/audioUtils";

export const MAX_RECORDING_SECONDS = 5;

interface UseMicrophoneReturn {
    isRecording: boolean;
    audioBase64: string | null;
    startRecording: () => Promise<void>;
    stopRecording: () => void;
    error: string | null;
}

export function useMicrophone(): UseMicrophoneReturn {
    const [isRecording, setIsRecording] = useState(false);
    const [audioBase64, setAudioBase64] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<Blob[]>([]);
    const streamRef = useRef<MediaStream | null>(null);
    const autoStopTimeoutRef = useRef<number | null>(null);
    const autoStoppedRef = useRef(false);

    const clearAutoStopTimeout = useCallback((): void => {
        if (autoStopTimeoutRef.current !== null) {
            window.clearTimeout(autoStopTimeoutRef.current);
            autoStopTimeoutRef.current = null;
        }
    }, []);

    const stopStream = useCallback((): void => {
        streamRef.current?.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
    }, []);

    const startRecording = useCallback(async (): Promise<void> => {
        setError(null);
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const recorder = new MediaRecorder(stream);
            mediaRecorderRef.current = recorder;
            streamRef.current = stream;
            chunksRef.current = [];
            autoStoppedRef.current = false;

            recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
            recorder.onstop = async () => {
                clearAutoStopTimeout();
                const blob = new Blob(chunksRef.current, { type: "audio/wav" });
                const base64 = await blobToBase64(blob);
                setAudioBase64(base64);
                stopStream();
                if (autoStoppedRef.current) {
                    setError(`録音は最大${MAX_RECORDING_SECONDS}秒です`);
                }
            };

            recorder.start();
            autoStopTimeoutRef.current = window.setTimeout(() => {
                autoStoppedRef.current = true;
                recorder.stop();
                setIsRecording(false);
            }, MAX_RECORDING_SECONDS * 1000);
            setIsRecording(true);
        } catch (_e) {
            setError("マイクへのアクセスが許可されていません");
        }
    }, [clearAutoStopTimeout, stopStream]);

    const stopRecording = useCallback((): void => {
        if (mediaRecorderRef.current?.state === "recording") {
            mediaRecorderRef.current.stop();
        }
        clearAutoStopTimeout();
        setIsRecording(false);
    }, [clearAutoStopTimeout]);

    useEffect(() => {
        return () => {
            clearAutoStopTimeout();
            stopStream();
        };
    }, [clearAutoStopTimeout, stopStream]);

    return { isRecording, audioBase64, startRecording, stopRecording, error };
}
