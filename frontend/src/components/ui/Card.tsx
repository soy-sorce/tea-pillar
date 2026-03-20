// src/components/ui/Card.tsx
import type { HTMLAttributes } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
    selected?: boolean;
}

export function Card({
    selected = false,
    className = "",
    children,
    ...props
}: CardProps): JSX.Element {
    return (
        <div
            className={[
                "rounded-card bg-surface p-4 transition-all",
                selected
                    ? "shadow-card-selected border-2 border-border-selected"
                    : "shadow-card border border-border",
                className,
            ].join(" ")}
            {...props}
        >
            {children}
        </div>
    );
}
