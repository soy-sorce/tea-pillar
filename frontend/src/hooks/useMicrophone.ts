import { useCallback, useEffect, useRef, useState } from "react";

import { blobToBase64 } from "@/lib/audioUtils";
import { MAX_AUDIO_RECORDING_SECONDS } from "@/lib/uploadLimits";

interface UseMicrophoneReturn {
    isRecording: boolean;
    audioBase64: string | null;
    error: string | null;
    startTimedRecording: (seconds?: number) => Promise<string | null>;
    resetAudio: () => void;
}

export function useMicrophone(): UseMicrophoneReturn {
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<Blob[]>([]);
    const streamRef = useRef<MediaStream | null>(null);
    const stopTimeoutRef = useRef<number | null>(null);

    const [isRecording, setIsRecording] = useState(false);
    const [audioBase64, setAudioBase64] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const stopStream = useCallback((): void => {
        streamRef.current?.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
    }, []);

    const clearTimeoutRef = useCallback((): void => {
        if (stopTimeoutRef.current !== null) {
            window.clearTimeout(stopTimeoutRef.current);
            stopTimeoutRef.current = null;
        }
    }, []);

    const resetAudio = useCallback((): void => {
        setAudioBase64(null);
        setError(null);
    }, []);

    const startTimedRecording = useCallback(
        async (seconds = MAX_AUDIO_RECORDING_SECONDS): Promise<string | null> => {
            setError(null);
            setAudioBase64(null);
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const recorder = new MediaRecorder(stream);
                mediaRecorderRef.current = recorder;
                streamRef.current = stream;
                chunksRef.current = [];

                const result = await new Promise<string | null>((resolve, reject) => {
                    recorder.ondataavailable = (event) => {
                        if (event.data.size > 0) {
                            chunksRef.current.push(event.data);
                        }
                    };
                    recorder.onerror = () => reject(new Error("audio recording failed"));
                    recorder.onstop = async () => {
                        try {
                            const blob = new Blob(chunksRef.current, {
                                type: recorder.mimeType || "audio/webm",
                            });
                            const base64 = await blobToBase64(blob);
                            setAudioBase64(base64);
                            resolve(base64);
                        } catch (recordingError) {
                            reject(recordingError);
                        } finally {
                            setIsRecording(false);
                            clearTimeoutRef();
                            stopStream();
                        }
                    };

                    recorder.start();
                    setIsRecording(true);
                    stopTimeoutRef.current = window.setTimeout(() => {
                        if (recorder.state === "recording") {
                            recorder.stop();
                        }
                    }, seconds * 1000);
                });

                return result;
            } catch {
                setIsRecording(false);
                clearTimeoutRef();
                stopStream();
                setError("マイクへのアクセスが許可されていません");
                return null;
            }
        },
        [clearTimeoutRef, stopStream],
    );

    useEffect(
        () => () => {
            clearTimeoutRef();
            if (mediaRecorderRef.current?.state === "recording") {
                mediaRecorderRef.current.stop();
            }
            stopStream();
        },
        [clearTimeoutRef, stopStream],
    );

    return {
        isRecording,
        audioBase64,
        error,
        startTimedRecording,
        resetAudio,
    };
}
