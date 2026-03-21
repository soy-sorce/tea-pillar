// src/pages/TopPage.tsx
import { useEffect, useState } from "react";
import { PawPrint, Clapperboard } from "lucide-react";
import { useGenerationContext } from "@/contexts/GenerationContext";
import { ExperienceForm } from "@/components/forms/ExperienceForm";
import { ProductionForm } from "@/components/forms/ProductionForm";

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
                    <h1 className="text-6xl font-black tracking-tight text-text-primary sm:text-7xl md:text-8xl">
                        nekko<span className="text-gradient">flix</span>
                    </h1>
                    <p className="mx-auto mt-5 max-w-2xl text-xl font-semibold leading-relaxed text-text-secondary sm:text-3xl">
                        Pets in the loopの実践
                    </p>
                </div>

                <section className="animate-slideUp delay-150">
                    <div className="rounded-[32px] border border-border/70 bg-white/75 p-6 shadow-card backdrop-blur-sm sm:p-8">
                        <div className="mx-auto max-w-3xl text-left">
                            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-accent sm:text-[13px]">
                                Pets in the loop
                            </p>
                            <h2 className="mt-3 text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
                                ペットもAIの進化のループに入る未来を、いま体験する
                            </h2>
                            <div className="mt-5 space-y-4 text-sm leading-7 text-text-secondary sm:text-[15px]">
                                <p>
                                    「次はフィジカルAIだ」と語られることが増え、AIが身体を持って暮らしに入ってくる未来が現実味を帯びています。
                                    そのとき家の中にいるのは人間だけではなく、猫をはじめとするペットたちも含まれます。
                                </p>
                                <p>
                                    私たちも当初は「人間とAI」の関係だけを前提に考えていましたが、そこで見落としていたのが動物の存在でした。
                                    人間にとってAIが身近な道具になっていく一方で、動物にとってAIはこれから日常の中に現れる新しい相手です。
                                </p>
                                <p>
                                    フィジカルAIが普及した未来には、ペットがロボットやデバイスを通じてAIと自然に関わり、その反応がモデル改善の手がかりになります。
                                    さらに、人間の知識やアノテーションが加わることで、はじめてAIはよりよく学習できます。
                                    私たちはこの関係性を <span className="font-semibold text-text-primary">Pets in the Loop</span> と捉え、
                                    その入り口をWeb上で先取り体験できる形としてこのプロダクトを提案しています。
                                </p>
                            </div>
                        </div>
                    </div>
                </section>

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
