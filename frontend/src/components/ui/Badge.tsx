// src/components/ui/Badge.tsx
interface BadgeProps {
    children: React.ReactNode;
    className?: string;
}

export function Badge({ children, className = "" }: BadgeProps): JSX.Element {
    return (
        <span
            className={`inline-flex items-center rounded-full bg-accent-light px-2.5 py-0.5 text-xs font-medium text-accent-dark ${className}`}
        >
            {children}
        </span>
    );
}
