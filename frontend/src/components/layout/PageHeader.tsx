// src/components/layout/PageHeader.tsx
import { ArrowLeft } from "lucide-react";

interface PageHeaderProps {
    title: string;
    subtitle?: string;
    onBack?: () => void;
}

export function PageHeader({ title, subtitle, onBack }: PageHeaderProps): React.JSX.Element {
    return (
        <div className="flex items-center gap-4 py-4">
            {onBack && (
                <button
                    onClick={onBack}
                    className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full border border-border bg-surface text-text-secondary shadow-card hover:border-accent hover:text-accent hover:shadow-card-hover transition-all duration-200"
                    aria-label="戻る"
                >
                    <ArrowLeft size={18} strokeWidth={2.5} />
                </button>
            )}
            <div>
                <h1 className="text-2xl font-bold text-text-primary">{title}</h1>
                {subtitle && (
                    <p className="mt-0.5 text-sm text-text-secondary">{subtitle}</p>
                )}
            </div>
        </div>
    );
}
