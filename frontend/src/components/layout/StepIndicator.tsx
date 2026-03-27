// src/components/layout/StepIndicator.tsx
import { Check } from "lucide-react";

interface StepIndicatorProps {
    steps: string[];
    currentStep: number; // 0-indexed
}

export function StepIndicator({ steps, currentStep }: StepIndicatorProps): React.JSX.Element {
    return (
        <div className="flex items-center justify-center gap-0" aria-label="進捗ステップ">
            {steps.map((label, index) => {
                const isDone = index < currentStep;
                const isActive = index === currentStep;

                return (
                    <div key={index} className="flex items-center">
                        {/* Circle */}
                        <div className="flex flex-col items-center gap-1.5">
                            <div
                                className={[
                                    "flex h-9 w-9 items-center justify-center rounded-full border-2 text-sm font-bold transition-all duration-300",
                                    isDone
                                        ? "border-accent bg-accent text-white"
                                        : isActive
                                            ? "border-accent bg-white text-accent shadow-glow"
                                            : "border-border bg-surface-alt text-text-muted",
                                ].join(" ")}
                                aria-current={isActive ? "step" : undefined}
                            >
                                {isDone ? (
                                    <Check size={16} strokeWidth={3} />
                                ) : (
                                    <span>{index + 1}</span>
                                )}
                            </div>
                            <span
                                className={[
                                    "text-xs font-medium whitespace-nowrap",
                                    isActive ? "text-accent" : isDone ? "text-accent-dark" : "text-text-muted",
                                ].join(" ")}
                            >
                                {label}
                            </span>
                        </div>

                        {/* Connector line (not after last) */}
                        {index < steps.length - 1 && (
                            <div
                                className={[
                                    "mb-5 h-0.5 w-12 transition-all duration-500 sm:w-16",
                                    index < currentStep ? "bg-accent" : "bg-border",
                                ].join(" ")}
                            />
                        )}
                    </div>
                );
            })}
        </div>
    );
}
