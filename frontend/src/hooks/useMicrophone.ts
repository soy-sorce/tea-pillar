// src/hooks/useMicrophone.ts
import { useCallback, useRef, useState } from "react";
import { blobToBase64 } from "@/lib/audioUtils";

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

    const startRecording = useCallback(async (): Promise<void> => {
        setError(null);
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const recorder = new MediaRecorder(stream);
            mediaRecorderRef.current = recorder;
            chunksRef.current = [];

            recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
            recorder.onstop = async () => {
                const blob = new Blob(chunksRef.current, { type: "audio/wav" });
                const base64 = await blobToBase64(blob);
                setAudioBase64(base64);
                stream.getTracks().forEach((t) => t.stop());
            };

            recorder.start();
            setIsRecording(true);
        } catch (_e) {
            setError("マイクへのアクセスが許可されていません");
        }
    }, []);

    const stopRecording = useCallback((): void => {
        mediaRecorderRef.current?.stop();
        setIsRecording(false);
    }, []);

    return { isRecording, audioBase64, startRecording, stopRecording, error };
}
