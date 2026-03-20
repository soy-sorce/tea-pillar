// src/components/experience/SampleCard.tsx
import { Check } from "lucide-react";

interface SampleCardProps {
    label: string;
    selected: boolean;
    onClick: () => void;
    // 画像表示モード（imageUrlがあればimg、なければemojiを表示）
    imageUrl?: string;
    emoji?: string;
    sublabel?: string;
}

export function SampleCard({
    label,
    selected,
    onClick,
    imageUrl,
    emoji,
    sublabel,
}: SampleCardProps): React.JSX.Element {
    return (
        <button
            onClick={onClick}
            className={[
                "group relative flex flex-col items-center gap-2 rounded-card-lg text-center transition-all duration-200 w-full overflow-hidden",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-1",
                selected
                    ? "border-2 border-accent shadow-glow scale-[1.02]"
                    : "border border-border shadow-card hover:border-accent hover:scale-[1.02] hover:shadow-card-hover",
                imageUrl ? "p-0" : "p-4",
            ].join(" ")}
        >
            {/* 選択済みチェック */}
            {selected && (
                <div className="absolute top-2 right-2 z-10 flex h-5 w-5 items-center justify-center rounded-full bg-accent text-white shadow-btn-primary">
                    <Check size={11} strokeWidth={3} />
                </div>
            )}

            {imageUrl ? (
                /* 画像モード */
                <>
                    <div className="relative w-full aspect-square overflow-hidden bg-surface-alt">
                        <img
                            src={imageUrl}
                            alt={label}
                            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                        />
                        {/* 選択時のオーバーレイ */}
                        {selected && (
                            <div className="absolute inset-0 bg-accent/10" />
                        )}
                    </div>
                    <span className={[
                        "pb-2 text-xs font-semibold",
                        selected ? "text-accent-dark" : "text-text-secondary",
                    ].join(" ")}>
                        {label}
                    </span>
                </>
            ) : (
                /* 絵文字モード */
                <>
                    <span className="text-3xl leading-none transition-transform duration-200 group-hover:scale-110">
                        {emoji}
                    </span>
                    <span className={[
                        "text-xs font-semibold leading-tight",
                        selected ? "text-accent-dark" : "text-text-primary",
                    ].join(" ")}>
                        {label}
                    </span>
                    {sublabel && (
                        <span className="text-xs text-text-muted">{sublabel}</span>
                    )}
                </>
            )}
        </button>
    );
}
