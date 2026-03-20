// src/components/layout/PageHeader.tsx
interface PageHeaderProps {
    title: string;
    onBack?: () => void;
}

export function PageHeader({ title, onBack }: PageHeaderProps): JSX.Element {
    return (
        <div className="flex items-center gap-3 py-2">
            {onBack && (
                <button
                    onClick={onBack}
                    className="flex h-9 w-9 items-center justify-center rounded-full text-text-secondary hover:bg-surface-alt transition-colors"
                    aria-label="戻る"
                >
                    ←
                </button>
            )}
            <h1 className="text-2xl font-semibold text-text-primary">{title}</h1>
        </div>
    );
}
