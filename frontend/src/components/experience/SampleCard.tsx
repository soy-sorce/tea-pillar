// src/components/experience/SampleCard.tsx
interface SampleCardProps {
    emoji: string;
    label: string;
    sublabel?: string;
    selected: boolean;
    onClick: () => void;
}

export function SampleCard({
    emoji,
    label,
    sublabel,
    selected,
    onClick,
}: SampleCardProps): JSX.Element {
    return (
        <button
            onClick={onClick}
            className={[
                "flex flex-col items-center gap-1 rounded-card p-4 text-center transition-all w-full",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
                selected
                    ? "shadow-card-selected bg-accent-light border-2 border-border-selected"
                    : "shadow-card bg-surface border border-border hover:border-accent",
            ].join(" ")}
        >
            <span className="text-2xl">{emoji}</span>
            <span className="text-sm font-medium text-text-primary">{label}</span>
            {sublabel && <span className="text-xs text-text-muted">{sublabel}</span>}
        </button>
    );
}
