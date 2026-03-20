// src/pages/TopPage.tsx
import { useEffect, useState } from "react";
import { Sparkles, PawPrint, Clapperboard } from "lucide-react";
import { useGenerationContext } from "@/contexts/GenerationContext";
import { ExperienceForm } from "@/components/forms/ExperienceForm";
import { ProductionForm } from "@/components/forms/ProductionForm";
import { FlowDiagram } from "@/components/home/FlowDiagram";

type TabKey = "experience" | "production";

export function TopPage(): React.JSX.Element {
    const { reset } = useGenerationContext();
    const [activeTab, setActiveTab] = useState<TabKey>("experience");

    useEffect(() => {
        reset();
    }, [reset]);

    const handleTabChange = (tab: TabKey): void => {
        reset();
        setActiveTab(tab);
    };

    return (
        <div className="relative min-h-[calc(100vh-64px)] bg-gradient-hero">
            <div className="pointer-events-none absolute inset-0 overflow-hidden">
                <div className="absolute -top-20 left-1/2 h-96 w-96 -translate-x-1/2 rounded-full bg-accent/10 blur-3xl" />
                <div className="absolute right-0 top-40 h-72 w-72 rounded-full bg-white/30 blur-3xl" />
            </div>

            <div className="relative mx-auto flex max-w-4xl flex-col gap-12 px-1 py-12 sm:px-3 sm:py-20">
                <div className="animate-slideUp text-center">
                    <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent-light px-4 py-1.5 text-sm font-medium text-accent">
                        <Sparkles size={14} />
                        AIが猫のための動画を生成します
                    </div>
                    <h1 className="text-6xl font-black tracking-tight text-text-primary sm:text-7xl md:text-8xl">
                        nekko<span className="text-gradient">flix</span>
                    </h1>
                    <p className="mx-auto mt-5 max-w-2xl text-lg leading-relaxed text-text-secondary sm:text-2xl">
                        猫の鳴き声・表情・性格から、最高の動画を。
                    </p>
                </div>

                <div className="animate-slideUp delay-150">
                    <FlowDiagram />
                </div>

                <section className="animate-slideUp delay-200">
                    <div className="rounded-[36px] border border-border/70 bg-white/70 p-4 shadow-card backdrop-blur-md sm:p-6">
                        <div
                            role="tablist"
                            aria-label="動画生成モード"
                            className="grid grid-cols-1 gap-3 rounded-[28px] bg-surface-alt p-2 sm:grid-cols-2"
                        >
                            <button
                                id="btn-experience-mode"
                                type="button"
                                role="tab"
                                aria-selected={activeTab === "experience"}
                                aria-controls="panel-experience"
                                onClick={() => handleTabChange("experience")}
                                className={[
                                    "flex items-center justify-center gap-2 rounded-[22px] px-5 py-4 text-sm font-semibold transition-all",
                                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
                                    activeTab === "experience"
                                        ? "bg-gradient-btn text-white shadow-btn-primary"
                                        : "bg-transparent text-text-secondary hover:text-text-primary",
                                ].join(" ")}
                            >
                                <PawPrint size={18} />
                                体験モード
                            </button>
                            <button
                                id="btn-production-mode"
                                type="button"
                                role="tab"
                                aria-selected={activeTab === "production"}
                                aria-controls="panel-production"
                                onClick={() => handleTabChange("production")}
                                className={[
                                    "flex items-center justify-center gap-2 rounded-[22px] px-5 py-4 text-sm font-semibold transition-all",
                                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
                                    activeTab === "production"
                                        ? "bg-gradient-btn text-white shadow-btn-primary"
                                        : "bg-transparent text-text-secondary hover:text-text-primary",
                                ].join(" ")}
                            >
                                <Clapperboard size={18} />
                                本番モード
                            </button>
                        </div>

                        <div className="mt-6">
                            <div
                                id="panel-experience"
                                role="tabpanel"
                                hidden={activeTab !== "experience"}
                            >
                                {activeTab === "experience" && <ExperienceForm />}
                            </div>
                            <div
                                id="panel-production"
                                role="tabpanel"
                                hidden={activeTab !== "production"}
                            >
                                {activeTab === "production" && <ProductionForm />}
                            </div>
                        </div>
                    </div>
                </section>

                <p className="animate-fadeIn text-center text-xs text-text-muted">
                    Powered by <span className="font-semibold text-text-secondary">Veo3</span> ×{" "}
                    <span className="font-semibold text-text-secondary">Gemini</span> ×{" "}
                    <span className="font-semibold text-text-secondary">Vertex AI</span>
                </p>
            </div>
        </div>
    );
}
