import { useCallback, useEffect, useRef, useState } from "react";

import {
    MAX_REACTION_VIDEO_BYTES,
    MAX_REACTION_VIDEO_SECONDS,
} from "@/lib/uploadLimits";

interface UseReactionRecorderReturn {
    isRecording: boolean;
    recordedBlob: Blob | null;
    error: string | null;
    startRecording: (stream: MediaStream, seconds?: number) => void;
    reset: () => void;
}

export function useReactionRecorder(): UseReactionRecorderReturn {
    const recorderRef = useRef<MediaRecorder | null>(null);
    const timeoutRef = useRef<number | null>(null);
    const chunksRef = useRef<Blob[]>([]);

    const [isRecording, setIsRecording] = useState(false);
    const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
    const [error, setError] = useState<string | null>(null);

    const clearTimeoutRef = useCallback((): void => {
        if (timeoutRef.current !== null) {
            window.clearTimeout(timeoutRef.current);
            timeoutRef.current = null;
        }
    }, []);

    const reset = useCallback((): void => {
        setRecordedBlob(null);
        setError(null);
    }, []);

    const startRecording = useCallback(
        (stream: MediaStream, seconds = MAX_REACTION_VIDEO_SECONDS): void => {
            reset();
            if (recorderRef.current?.state === "recording") {
                return;
            }

            try {
                const recorder = new MediaRecorder(stream, { mimeType: "video/webm" });
                recorderRef.current = recorder;
                chunksRef.current = [];

                recorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        chunksRef.current.push(event.data);
                    }
                };

                recorder.onerror = () => {
                    setError("反応動画の録画に失敗しました");
                    setIsRecording(false);
                };

                recorder.onstop = () => {
                    const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "video/webm" });
                    if (blob.size > MAX_REACTION_VIDEO_BYTES) {
                        setError("反応動画が20MBを超えたためアップロードできません");
                        setRecordedBlob(null);
                    } else {
                        setRecordedBlob(blob);
                    }
                    setIsRecording(false);
                    clearTimeoutRef();
                };

                recorder.start();
                setIsRecording(true);
                timeoutRef.current = window.setTimeout(() => {
                    if (recorder.state === "recording") {
                        recorder.stop();
                    }
                }, seconds * 1000);
            } catch {
                setError("反応動画の録画を開始できませんでした");
                setIsRecording(false);
            }
        },
        [clearTimeoutRef, reset],
    );

    useEffect(
        () => () => {
            clearTimeoutRef();
            if (recorderRef.current?.state === "recording") {
                recorderRef.current.stop();
            }
        },
        [clearTimeoutRef],
    );

    return { isRecording, recordedBlob, error, startRecording, reset };
}
