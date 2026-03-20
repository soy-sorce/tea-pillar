// src/components/experience/MicButton.tsx
import { useEffect, useState } from "react";

interface MicButtonProps {
    isRecording: boolean;
    onStart: () => void;
    onStop: () => void;
    disabled?: boolean;
}

export function MicButton({
    isRecording,
    onStart,
    onStop,
    disabled = false,
}: MicButtonProps): JSX.Element {
    const [countdown, setCountdown] = useState(0);

    useEffect(() => {
        if (!isRecording) {
            setCountdown(0);
            return;
        }
        setCountdown(1);
        const interval = setInterval(() => {
            setCountdown((prev) => prev + 1);
        }, 1000);
        return () => clearInterval(interval);
    }, [isRecording]);

    return (
        <button
            onClick={isRecording ? onStop : onStart}
            disabled={disabled}
            className={[
                "flex items-center gap-2 rounded-btn px-4 py-2.5 text-sm font-medium transition-all",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
                "disabled:opacity-40 disabled:cursor-not-allowed",
                isRecording
                    ? "bg-red-50 border border-red-300 text-red-600 animate-pulse"
                    : "bg-surface border border-border text-text-secondary hover:border-accent hover:text-accent",
            ].join(" ")}
            aria-label={isRecording ? "録音停止" : "マイクで録音"}
        >
            <span>{isRecording ? "🔴" : "🎤"}</span>
            <span>
                {isRecording
                    ? `録音中... ${countdown}秒`
                    : "マイクで鳴いてみる"}
            </span>
        </button>
    );
}
