// src/components/result/FeedbackButtons.tsx
import { useFeedback } from "@/hooks/useFeedback";
import type { Reaction } from "@/types/app";

interface FeedbackButtonsProps {
    sessionId: string;
}

const REACTIONS: { reaction: Reaction; emoji: string; label: string }[] = [
    { reaction: "good", emoji: "😺", label: "テンション上がった！" },
    { reaction: "neutral", emoji: "😐", label: "まあまあ" },
    { reaction: "bad", emoji: "😾", label: "興味なし" },
];

export function FeedbackButtons({
    sessionId,
}: FeedbackButtonsProps): JSX.Element {
    const { submitFeedback, submitted, isLoading } = useFeedback();

    if (submitted) {
        return (
            <div className="text-center py-4">
                <p className="text-sm text-accent font-medium">
                    🐱 フィードバックありがとうございます！
                </p>
                <p className="text-xs text-text-muted mt-1">
                    学習に反映されました
                </p>
            </div>
        );
    }

    return (
        <div>
            <p className="text-sm font-medium text-text-secondary mb-3 text-center">
                猫の反応はどうでしたか？
            </p>
            <div className="flex gap-3 justify-center">
                {REACTIONS.map(({ reaction, emoji, label }) => (
                    <button
                        key={reaction}
                        id={`feedback-${reaction}`}
                        onClick={() => void submitFeedback({ session_id: sessionId, reaction })}
                        disabled={isLoading}
                        className={[
                            "flex flex-col items-center gap-1.5 rounded-card p-4 text-center transition-all flex-1",
                            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
                            "hover:bg-accent-light hover:border-accent disabled:opacity-40 disabled:cursor-not-allowed",
                            "shadow-card bg-surface border border-border",
                        ].join(" ")}
                    >
                        <span className="text-3xl">{emoji}</span>
                        <span className="text-xs text-text-secondary font-medium leading-tight">
                            {label}
                        </span>
                    </button>
                ))}
            </div>
        </div>
    );
}
