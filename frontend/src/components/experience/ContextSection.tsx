// src/components/experience/ContextSection.tsx
import { Button } from "@/components/ui/Button";
import { PERSONALITY_OPTIONS, type PersonalityType } from "@/types/app";

interface ContextSectionProps {
    selected: PersonalityType | null;
    onSelect: (type: PersonalityType | null) => void;
}

export function ContextSection({
    selected,
    onSelect,
}: ContextSectionProps): JSX.Element {
    return (
        <section aria-labelledby="context-section-title">
            <h2
                id="context-section-title"
                className="mb-1 text-lg font-medium text-text-primary"
            >
                Step 3 🐱 性格
                <span className="ml-2 text-sm font-normal text-text-muted">
                    （任意）
                </span>
            </h2>
            <p className="mb-3 text-sm text-text-secondary">
                猫の性格を選ぶと、より合った動画が生成されます
            </p>

            <div className="flex flex-wrap gap-2 mb-2">
                {PERSONALITY_OPTIONS.map(({ type, emoji, label }) => (
                    <button
                        key={type}
                        onClick={() => onSelect(selected === type ? null : type)}
                        className={[
                            "flex items-center gap-1.5 rounded-btn px-4 py-2 text-sm font-medium transition-all",
                            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
                            selected === type
                                ? "bg-accent text-white"
                                : "bg-surface border border-border text-text-primary hover:border-accent",
                        ].join(" ")}
                    >
                        {emoji} {label}
                    </button>
                ))}
            </div>

            {selected && (
                <Button
                    variant="text"
                    size="sm"
                    onClick={() => onSelect(null)}
                    className="text-text-muted hover:text-text-secondary"
                >
                    スキップ（選択解除）
                </Button>
            )}
        </section>
    );
}
