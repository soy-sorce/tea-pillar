// src/components/experience/MicButton.tsx
import { useEffect, useState } from "react";
import { Mic, Square } from "lucide-react";

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
}: MicButtonProps): React.JSX.Element {
    const [countdown, setCountdown] = useState(0);

    useEffect(() => {
        if (!isRecording) { setCountdown(0); return; }
        setCountdown(1);
        const interval = setInterval(() => setCountdown((p) => p + 1), 1000);
        return () => clearInterval(interval);
    }, [isRecording]);

    return (
        <button
            onClick={isRecording ? onStop : onStart}
            disabled={disabled}
            className={[
                "relative flex items-center gap-2.5 rounded-btn px-5 py-2.5 text-sm font-semibold transition-all duration-200",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
                "disabled:opacity-40 disabled:cursor-not-allowed",
                isRecording
                    ? "bg-red-500 text-white shadow-lg"
                    : "bg-surface border border-border text-text-secondary hover:border-accent hover:text-accent hover:bg-accent-light",
            ].join(" ")}
            aria-label={isRecording ? "録音停止" : "マイクで録音"}
        >
            {/* パルスリング（録音中のみ） */}
            {isRecording && (
                <span className="absolute -inset-1 rounded-btn bg-red-400 animate-pulse-ring opacity-0" />
            )}
            {isRecording ? (
                <Square size={15} fill="currentColor" />
            ) : (
                <Mic size={15} />
            )}
            <span>
                {isRecording ? `録音停止 (${countdown}秒)` : "マイクで録音"}
            </span>
        </button>
    );
}
