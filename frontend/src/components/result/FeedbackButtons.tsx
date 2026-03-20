// src/components/result/FeedbackButtons.tsx
import { useFeedback } from "@/hooks/useFeedback";
import type { Reaction } from "@/types/app";

interface FeedbackButtonsProps {
    sessionId: string;
}

const REACTIONS: { reaction: Reaction; emoji: string; label: string; activeClass: string }[] = [
    { reaction: "good", emoji: "😺", label: "テンション\n上がった！", activeClass: "bg-accent-light border-accent text-accent-dark" },
    { reaction: "neutral", emoji: "😐", label: "まあまあ", activeClass: "bg-amber-50 border-amber-300 text-amber-700" },
    { reaction: "bad", emoji: "😾", label: "興味なし", activeClass: "bg-red-50 border-red-300 text-red-600" },
];

export function FeedbackButtons({
    sessionId,
}: FeedbackButtonsProps): React.JSX.Element {
    const { submitFeedback, submitted, isLoading } = useFeedback();

    if (submitted) {
        return (
            <div className="text-center py-6 animate-fadeIn">
                <div className="inline-flex items-center gap-2 rounded-full bg-accent-light px-5 py-2.5">
                    <span className="text-lg">🐱</span>
                    <p className="text-sm font-semibold text-accent">フィードバックありがとうございます！</p>
                </div>
                <p className="text-xs text-text-muted mt-2">学習に反映されました</p>
            </div>
        );
    }

    return (
        <div className="animate-slideUp">
            <p className="text-sm font-semibold text-text-secondary mb-4 text-center">
                猫の反応はどうでしたか？
            </p>
            <div className="flex gap-3">
                {REACTIONS.map(({ reaction, emoji, label, activeClass }) => (
                    <button
                        key={reaction}
                        id={`feedback-${reaction}`}
                        onClick={() => void submitFeedback({ session_id: sessionId, reaction })}
                        disabled={isLoading}
                        className={[
                            "group flex flex-col items-center gap-2 rounded-card-lg p-4 text-center transition-all duration-200 flex-1 border",
                            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
                            "disabled:opacity-40 disabled:cursor-not-allowed",
                            `hover:${activeClass} hover:scale-[1.03] hover:shadow-card-hover`,
                            "bg-surface border-border shadow-card",
                        ].join(" ")}
                    >
                        <span className="text-3xl transition-transform duration-200 group-hover:scale-110">
                            {emoji}
                        </span>
                        <span className="text-xs text-text-secondary font-medium leading-tight whitespace-pre-line">
                            {label}
                        </span>
                    </button>
                ))}
            </div>
        </div>
    );
}
