// src/components/experience/ContextSection.tsx
import { Heart } from "lucide-react";
import { CONTEXT_EXAMPLES } from "@/types/app";

interface ContextSectionProps {
    value: string;
    onChange: (value: string) => void;
}

export function ContextSection({
    value,
    onChange,
}: ContextSectionProps): React.JSX.Element {
    return (
        <section aria-labelledby="context-section-title">
            <div className="mb-4 flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-light">
                    <Heart size={16} className="text-accent" />
                </div>
                <h2 id="context-section-title" className="font-semibold text-text-primary">
                    猫の性格・好みを入力
                </h2>
                <span className="rounded-full bg-surface-alt px-2 py-0.5 text-xs text-text-muted">任意</span>
            </div>

            <p className="mb-4 text-sm leading-6 text-text-secondary sm:text-[15px]">
                性格や好み、普段の様子を補足すると、生成される動画の雰囲気や内容をより猫らしく調整できます。
            </p>

            {/* テキストエリア */}
            <textarea
                id="experience-context-input"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                maxLength={500}
                rows={3}
                placeholder="例：魚が大好きで、遊び好きな活発な猫"
                className="w-full resize-none rounded-card border border-border bg-surface-alt px-4 py-3 text-sm text-text-primary placeholder:text-text-muted transition-colors focus:border-accent focus:bg-surface focus:outline-none focus:ring-1 focus:ring-accent"
            />
            <p className="mt-1 text-right text-xs text-text-muted">
                {value.length} / 500
            </p>

            {/* サンプル例 */}
            <div className="mt-3">
                <p className="mb-2 text-xs font-medium text-text-muted">
                    例をクリックすると自動入力されます：
                </p>
                <div className="flex flex-wrap gap-2">
                    {CONTEXT_EXAMPLES.map((example) => (
                        <button
                            key={example}
                            type="button"
                            onClick={() => onChange(example)}
                            className={[
                                "rounded-btn border px-3 py-1.5 text-xs font-medium transition-all duration-150",
                                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
                                value === example
                                    ? "border-accent bg-accent-light text-accent-dark"
                                    : "border-border bg-surface text-text-secondary hover:border-accent hover:bg-accent-light hover:text-accent",
                            ].join(" ")}
                        >
                            {example}
                        </button>
                    ))}
                </div>
            </div>
        </section>
    );
}
