// src/components/ui/ExampleChips.tsx
import { Lightbulb } from "lucide-react";

interface ExampleChipsProps {
    examples: readonly string[];
    onSelect: (text: string) => void;
    label?: string;
}

export function ExampleChips({
    examples,
    onSelect,
    label = "例を試す",
}: ExampleChipsProps): React.JSX.Element {
    return (
        <div className="mt-3">
            <p className="mb-2 flex items-center gap-1 text-xs font-medium text-text-muted">
                <Lightbulb size={11} />
                {label}
            </p>
            <div className="flex flex-wrap gap-2">
                {examples.map((example, i) => (
                    <button
                        key={i}
                        type="button"
                        onClick={() => onSelect(example)}
                        className="rounded-full border border-accent/30 bg-accent-light px-3 py-1.5 text-xs font-medium text-accent-dark transition-all duration-150 hover:border-accent hover:bg-accent hover:text-white active:scale-95"
                    >
                        {example}
                    </button>
                ))}
            </div>
        </div>
    );
}
