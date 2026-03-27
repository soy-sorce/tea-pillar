// src/pages/LandingPage.tsx
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { PawPrint, Clapperboard, ChevronRight, Sparkles } from "lucide-react";
import { useGenerationContext } from "@/contexts/GenerationContext";
import { Button } from "@/components/ui/Button";

export function LandingPage(): React.JSX.Element {
    const navigate = useNavigate();
    const { reset } = useGenerationContext();

    useEffect(() => {
        reset();
    }, [reset]);

    return (
        <div className="relative min-h-[calc(100vh-64px)] bg-gradient-hero">
            {/* 背景の装飾 */}
            <div className="pointer-events-none absolute inset-0 overflow-hidden">
                <div className="absolute -top-20 left-1/2 h-96 w-96 -translate-x-1/2 rounded-full bg-accent/10 blur-3xl" />
                <div className="absolute right-0 top-40 h-72 w-72 rounded-full bg-white/30 blur-3xl" />
                <div className="absolute bottom-20 left-0 h-64 w-64 rounded-full bg-accent/5 blur-3xl" />
            </div>

            <div className="relative mx-auto flex max-w-4xl flex-col gap-14 px-4 py-14 sm:px-6 sm:py-20">

                {/* ヒーローセクション */}
                <div className="animate-slideUp text-center">
                    <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-accent-light px-4 py-1.5 text-xs font-semibold text-accent-dark shadow-inner-sm">
                        <Sparkles size={13} />
                        Pets in the Loop
                    </div>
                    <h1 className="text-6xl font-black tracking-tight text-text-primary sm:text-7xl md:text-8xl">
                        nekko<span className="text-gradient">flix</span>
                    </h1>
                    <p className="mx-auto mt-5 max-w-xl text-lg font-semibold leading-relaxed text-text-secondary sm:text-2xl">
                        Pets in the Loopを先立って体験する。
                    </p>
                </div>

                {/* コンセプト説明 */}
                <section className="animate-slideUp delay-150">
                    <div className="rounded-[32px] border border-border/70 bg-white/75 p-6 shadow-card backdrop-blur-sm sm:p-8">
                        <div className="mx-auto max-w-3xl text-left">
                            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-accent sm:text-[11px]">
                                What is Pets in the Loop?
                            </p>
                            <h2 className="mt-3 text-xl font-bold tracking-tight text-text-primary sm:text-2xl">
                                Our Vision
                            </h2>
                            <div className="mt-4 space-y-3 text-sm leading-7 text-text-secondary sm:text-[15px]">
                                <p>
                                    「次はフィジカルAIだ」と語られる今、AIが身体を持って暮らしに入ってくる未来が現実味を帯びています。
                                    そのとき家の中にいるのは人間だけでなく、猫をはじめとするペットたちも含まれます。
                                </p>
                                <p>
                                    フィジカルAIが普及した未来には、ペットがロボットやデバイスを通じてAIと自然に関わり、
                                    その反応がモデル改善の手がかりになります。
                                    私たちはこの関係性を <span className="font-semibold text-text-primary">Pets in the Loop</span> と捉え、
                                    その入り口をWeb上で先取り体験できるプロダクトとして提案します。
                                </p>
                            </div>
                        </div>
                    </div>
                </section>

                {/* モード選択カード */}
                <section className="animate-slideUp delay-200">
                    <p className="mb-6 text-center text-sm font-semibold uppercase tracking-[0.14em] text-text-muted">
                        モードを選んでください
                    </p>
                    <div className="grid gap-5 sm:grid-cols-2">

                        {/* 体験モードカード */}
                        <div className="group flex flex-col rounded-[28px] border border-border bg-white/80 p-6 shadow-card backdrop-blur-sm transition-all duration-200 hover:shadow-card-hover sm:p-8">
                            <div className="flex items-center gap-3">
                                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-btn shadow-btn-primary">
                                    <PawPrint size={22} className="text-white" />
                                </div>
                                <div>
                                    <p className="text-xs font-semibold uppercase tracking-[0.14em] text-accent">
                                        あなたが猫になる
                                    </p>
                                    <h3 className="text-xl font-bold text-text-primary">体験モード</h3>
                                </div>
                            </div>

                            <p className="mt-5 flex-1 text-sm leading-7 text-text-secondary">
                                カメラの前で猫の真似をして動いてみましょう。
                                AIがあなたの動きと声を分析し、その「猫キャラクター」に合った動画をVeo3で生成します。
                            </p>

                            <ul className="mt-4 space-y-1.5 text-xs text-text-muted">
                                <li className="flex items-center gap-2">
                                    <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                                    動き検知 → 自動撮影
                                </li>
                                <li className="flex items-center gap-2">
                                    <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                                    3秒の鳴きマネ録音
                                </li>
                                <li className="flex items-center gap-2">
                                    <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                                    モデル更新なし（純粋な体験）
                                </li>
                            </ul>

                            <Button
                                id="btn-experience"
                                variant="primary"
                                size="lg"
                                className="mt-6 w-full"
                                rightIcon={<ChevronRight size={18} />}
                                onClick={() => void navigate("/experience")}
                            >
                                体験モードで試す
                            </Button>
                        </div>

                        {/* 本番モードカード */}
                        <div className="group flex flex-col rounded-[28px] border border-border bg-white/80 p-6 shadow-card backdrop-blur-sm transition-all duration-200 hover:shadow-card-hover sm:p-8">
                            <div className="flex items-center gap-3">
                                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-btn shadow-btn-primary">
                                    <Clapperboard size={22} className="text-white" />
                                </div>
                                <div>
                                    <p className="text-xs font-semibold uppercase tracking-[0.14em] text-accent">
                                        実際の猫で使う
                                    </p>
                                    <h3 className="text-xl font-bold text-text-primary">本番モード</h3>
                                </div>
                            </div>

                            <p className="mt-5 flex-1 text-sm leading-7 text-text-secondary">
                                実際の猫をカメラの前に連れてきましょう。
                                猫のリアルな動きや鳴き声を分析して最適な動画を生成し、
                                猫の反応を録画してAIモデルの改善に役立てます。
                            </p>

                            <ul className="mt-4 space-y-1.5 text-xs text-text-muted">
                                <li className="flex items-center gap-2">
                                    <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                                    猫の動き・鳴き声を自動取得
                                </li>
                                <li className="flex items-center gap-2">
                                    <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                                    動画再生と同時に反応を録画
                                </li>
                                <li className="flex items-center gap-2">
                                    <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                                    reaction videoでモデルを改善
                                </li>
                            </ul>

                            <Button
                                id="btn-production"
                                variant="secondary"
                                size="lg"
                                className="mt-6 w-full"
                                rightIcon={<ChevronRight size={18} />}
                                onClick={() => void navigate("/production")}
                            >
                                本番モードで使う
                            </Button>
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
