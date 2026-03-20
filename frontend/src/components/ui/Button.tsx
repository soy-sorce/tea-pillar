// src/components/ui/Button.tsx
import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "text";
type ButtonSize = "sm" | "md" | "lg" | "xl";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: ButtonVariant;
    size?: ButtonSize;
    leftIcon?: ReactNode;
    rightIcon?: ReactNode;
}

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
    primary: [
        "bg-gradient-btn text-white font-semibold",
        "shadow-btn-primary hover:shadow-btn-primary-hover",
        "hover:brightness-110 hover:scale-[1.02] active:scale-[0.98]",
    ].join(" "),
    secondary: [
        "bg-surface border border-border text-text-primary font-medium",
        "hover:bg-surface-alt hover:border-accent hover:text-accent",
        "hover:scale-[1.01] active:scale-[0.99]",
    ].join(" "),
    ghost: [
        "bg-accent-light text-accent font-medium",
        "hover:bg-accent hover:text-white",
        "hover:scale-[1.01] active:scale-[0.99]",
    ].join(" "),
    text: "text-accent hover:text-accent-dark hover:underline bg-transparent font-medium",
};

const SIZE_CLASSES: Record<ButtonSize, string> = {
    sm: "px-4 py-2 text-sm gap-1.5",
    md: "px-5 py-2.5 text-base gap-2",
    lg: "px-8 py-4 text-base gap-2",
    xl: "px-10 py-5 text-lg gap-2.5",
};

export function Button({
    variant = "primary",
    size = "md",
    className = "",
    children,
    disabled,
    leftIcon,
    rightIcon,
    ...props
}: ButtonProps): React.JSX.Element {
    return (
        <button
            className={[
                "inline-flex items-center justify-center rounded-btn transition-all duration-200",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2",
                "disabled:opacity-40 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none",
                VARIANT_CLASSES[variant],
                SIZE_CLASSES[size],
                className,
            ].join(" ")}
            disabled={disabled}
            {...props}
        >
            {leftIcon && <span className="flex-shrink-0">{leftIcon}</span>}
            {children}
            {rightIcon && <span className="flex-shrink-0">{rightIcon}</span>}
        </button>
    );
}
