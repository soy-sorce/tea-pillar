// src/components/ui/Button.tsx
import type { ButtonHTMLAttributes } from "react";

type ButtonVariant = "primary" | "secondary" | "text";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: ButtonVariant;
    size?: ButtonSize;
}

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
    primary: "bg-accent text-white hover:bg-accent-dark active:scale-95",
    secondary:
        "bg-surface border border-border text-text-primary hover:bg-surface-alt",
    text: "text-accent hover:underline bg-transparent",
};

const SIZE_CLASSES: Record<ButtonSize, string> = {
    sm: "px-3 py-1.5 text-sm",
    md: "px-5 py-2.5 text-base",
    lg: "px-6 py-3 text-base",
};

export function Button({
    variant = "primary",
    size = "md",
    className = "",
    children,
    disabled,
    ...props
}: ButtonProps): JSX.Element {
    return (
        <button
            className={[
                "inline-flex items-center justify-center rounded-btn font-medium transition-all",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
                "disabled:opacity-40 disabled:cursor-not-allowed",
                VARIANT_CLASSES[variant],
                SIZE_CLASSES[size],
                className,
            ].join(" ")}
            disabled={disabled}
            {...props}
        >
            {children}
        </button>
    );
}
