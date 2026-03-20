import { ChevronRight, Mic, Camera, PencilLine, Clapperboard } from "lucide-react";

const steps = [
    { icon: Mic, label: "鳴き声を選ぶ" },
    { icon: Camera, label: "写真を選ぶ" },
    { icon: PencilLine, label: "性格を入力" },
    { icon: Clapperboard, label: "動画生成" },
] as const;

export function FlowDiagram(): React.JSX.Element {
    return (
        <div className="rounded-[32px] border border-border/70 bg-white/75 p-6 shadow-card backdrop-blur-sm sm:p-8">
            <div className="mb-6 flex items-center justify-center gap-4">
                <div className="h-px flex-1 bg-border/80" />
                <p className="text-sm font-semibold uppercase tracking-[0.24em] text-text-muted">
                    How it works
                </p>
                <div className="h-px flex-1 bg-border/80" />
            </div>

            <div className="flex flex-col items-center justify-center gap-3 md:flex-row md:gap-0">
                {steps.map((step, index) => {
                    const Icon = step.icon;
                    const isLast = index === steps.length - 1;

                    return (
                        <div key={step.label} className="flex flex-col items-center gap-3 md:flex-row md:gap-0">
                            <div className="flex min-w-[150px] flex-col items-center gap-3 text-center">
                                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-accent-light text-accent">
                                    <Icon size={26} />
                                </div>
                                <div className="space-y-1">
                                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-muted">
                                        {String(index + 1).padStart(2, "0")}
                                    </p>
                                    <p className="text-sm font-semibold text-text-primary">{step.label}</p>
                                </div>
                            </div>
                            {!isLast && (
                                <ChevronRight
                                    size={22}
                                    className="rotate-90 text-text-muted md:mx-2 md:rotate-0"
                                />
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
