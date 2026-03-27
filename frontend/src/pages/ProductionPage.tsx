// src/pages/ProductionPage.tsx
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Camera, FileText, Radar, Mic, ArrowLeft } from "lucide-react";

import { StepIndicator } from "@/components/layout/StepIndicator";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { useCamera } from "@/hooks/useCamera";
import { useGenerate } from "@/hooks/useGenerate";
import { useGenerationContext } from "@/contexts/GenerationContext";
import { useMicrophone } from "@/hooks/useMicrophone";
import { useMotionDetection } from "@/hooks/useMotionDetection";

type Step = 0 | 1;

const STEPS = ["コンテキスト入力", "撮影・録音"];

export function ProductionPage(): React.JSX.Element {
    const navigate = useNavigate();
    const { reset } = useGenerationContext();
    const { generate, isLoading } = useGenerate();

    // ── ステップ状態 ──────────────────────────────
    const [step, setStep] = useState<Step>(0);
    const [userContext, setUserContext] = useState("");
    const [flowLabel, setFlowLabel] = useState("カメラの前で猫を準備してください");
    const [lastTriggerAt, setLastTriggerAt] = useState<string | null>(null);

    useEffect(() => { reset(); }, [reset]);

    // ── フック（常に呼ぶ） ────────────────────────
    const {
        videoRef, isReady, error: cameraError,
        startCamera, stopCamera, captureFrame, getStream,
    } = useCamera();

    const { startTimedRecording, resetAudio } = useMicrophone();

    // ── motion detection トリガーハンドラ ─────────
    const triggerHandlerRef = useRef<() => void>(() => { });
    const isHandlingRef = useRef(false);

    // 毎レンダリングで ref を更新（userContext などの最新値を使用）
    triggerHandlerRef.current = () => {
        if (isHandlingRef.current || isLoading) return;
        isHandlingRef.current = true;

        const image = captureFrame();
        if (!image) {
            isHandlingRef.current = false;
            return;
        }

        setLastTriggerAt(new Date().toLocaleTimeString("ja-JP"));
        setFlowLabel("動きを検知しました。3秒間音声を録音しています...");

        void (async () => {
            const audio = await startTimedRecording(3);
            setFlowLabel("生成リクエストを送信しています...");
            await generate({
                mode: "production",
                image_base64: image,
                audio_base64: audio ?? undefined,
                user_context: userContext.trim() || undefined,
            });
        })();
    };

    const stableOnTrigger = useCallback(() => {
        triggerHandlerRef.current();
    }, []);

    const { motionScore, status: motionStatus, startDetection, stopDetection } = useMotionDetection({
        videoRef,
        getStream,
        onTrigger: stableOnTrigger,
        warmupMs: 1000,
    });

    // ── step 1 でカメラ + 検知を自動起動 ──────────
    const hasCameraStartedRef = useRef(false);
    useEffect(() => {
        if (step !== 1 || hasCameraStartedRef.current) return;
        hasCameraStartedRef.current = true;
        resetAudio();
        void startCamera().then(() => startDetection());
    }, [step, startCamera, startDetection, resetAudio]);

    // ── アンマウント時クリーンアップ ───────────────
    useEffect(() => () => {
        stopDetection();
        stopCamera();
    }, [stopDetection, stopCamera]);

    // ── レンダリング ───────────────────────────────
    return (
        <div className="mx-auto max-w-2xl px-4 py-8">
            {/* ページヘッダー */}
            <div className="mb-8 flex items-center gap-4">
                <button
                    onClick={() => void navigate("/")}
                    className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full border border-border bg-surface text-text-secondary shadow-card hover:border-accent hover:text-accent transition-all duration-200"
                    aria-label="トップへ戻る"
                >
                    <ArrowLeft size={16} />
                </button>
                <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.14em] text-accent">本番モード</p>
                    <h1 className="text-xl font-bold text-text-primary">実際の猫でAIを鍛える</h1>
                </div>
            </div>

            {/* ステップインジケーター */}
            <div className="mb-8">
                <StepIndicator steps={STEPS} currentStep={step} />
            </div>

            {/* Step 0: コンテキスト入力 */}
            {step === 0 && (
                <div className="animate-fadeIn space-y-5">
                    {/* 説明カード */}
                    <div className="rounded-card-lg border border-border bg-surface p-5 shadow-card">
                        <div className="mb-2 inline-flex items-center rounded-full bg-gradient-btn px-3 py-1 text-xs font-bold text-white shadow-btn-primary">
                            STEP 1 / 2 &nbsp;·&nbsp; コンテキスト入力
                        </div>
                        <p className="mt-3 text-sm leading-7 text-text-secondary">
                            撮影する猫の性格や好みを入力してください。
                            入力した情報はAIのプロンプト構築に使用され、その猫らしい動画の生成に役立ちます。
                            空欄のままでも次のステップに進めます。
                        </p>
                    </div>

                    {/* テキストエリア */}
                    <div className="rounded-card-lg border border-border bg-surface p-5 shadow-card">
                        <label htmlFor="prod-context" className="text-sm font-semibold text-text-primary">
                            <FileText size={14} className="mr-1.5 inline" />
                            猫の性格・好みを書く
                            <span className="ml-2 text-xs font-normal text-text-muted">（任意）</span>
                        </label>
                        <p className="mt-1.5 text-xs text-text-muted">
                            例: 「好奇心旺盛でおもちゃへの反応が早い」「窓際で日向ぼっこが好き、外の鳥に反応する」
                        </p>
                        <textarea
                            id="prod-context"
                            value={userContext}
                            onChange={(e) => setUserContext(e.target.value)}
                            maxLength={500}
                            rows={5}
                            placeholder="猫の性格・好みを自由に入力..."
                            className="mt-3 w-full resize-none rounded-card border border-border bg-surface-alt px-4 py-3 text-sm text-text-primary placeholder:text-text-muted transition-colors focus:border-accent focus:bg-surface focus:outline-none focus:ring-1 focus:ring-accent"
                        />
                        <p className="mt-1 text-right text-xs text-text-muted">{userContext.length} / 500</p>
                    </div>

                    <Button
                        id="btn-next-production"
                        variant="primary"
                        size="xl"
                        className="w-full"
                        onClick={() => setStep(1)}
                    >
                        次へ →
                    </Button>
                </div>
            )}

            {/* Step 1: カメラ + 動き検知 + 録音 */}
            {step === 1 && (
                <div className="animate-fadeIn space-y-5">
                    {/* 説明カード */}
                    <div className="rounded-card-lg border border-border bg-surface p-5 shadow-card">
                        <div className="mb-2 inline-flex items-center rounded-full bg-gradient-btn px-3 py-1 text-xs font-bold text-white shadow-btn-primary">
                            STEP 2 / 2 &nbsp;·&nbsp; 撮影・録音
                        </div>
                        <p className="mt-3 text-sm leading-7 text-text-secondary">
                            猫がカメラの前を素早く横切ったり動いたりする瞬間を待ちます。
                            AIが動きを検知すると自動で撮影と3秒間の録音を開始します。
                            録音・撮影が完了すると自動で動画生成が始まります。
                        </p>
                    </div>

                    {/* カメラプレビュー */}
                    <div className="rounded-card-xl border border-border bg-surface shadow-card overflow-hidden">
                        <div className="relative aspect-[16/10] bg-black/90">
                            <video
                                ref={videoRef}
                                muted
                                playsInline
                                className="h-full w-full object-cover"
                                aria-label="カメラプレビュー"
                            />
                            {/* 未起動プレースホルダー */}
                            {!isReady && !cameraError && (
                                <div className="absolute inset-0 flex items-center justify-center">
                                    <div className="text-center text-white/60">
                                        <Spinner />
                                        <p className="mt-3 text-sm">カメラを起動しています...</p>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* ステータスバッジ */}
                        <div className="grid grid-cols-3 gap-3 border-t border-border px-4 py-4">
                            <div className="rounded-2xl border border-border bg-surface-alt px-3 py-3">
                                <div className="flex items-center gap-1 text-xs font-semibold uppercase tracking-[0.1em] text-text-muted">
                                    <Camera size={12} />
                                    Camera
                                </div>
                                <p className="mt-1.5 text-xs font-semibold text-text-primary">
                                    {isReady ? "準備完了" : "起動中..."}
                                </p>
                            </div>
                            <div className="rounded-2xl border border-border bg-surface-alt px-3 py-3">
                                <div className="flex items-center gap-1 text-xs font-semibold uppercase tracking-[0.1em] text-text-muted">
                                    <Radar size={12} />
                                    Motion
                                </div>
                                <p className="mt-1.5 text-xs font-semibold text-text-primary">
                                    {motionStatus === "watching"
                                        ? `score ${Math.round(motionScore)}`
                                        : motionStatus === "detected"
                                            ? "検知！"
                                            : motionStatus === "cooldown"
                                                ? "CD中"
                                                : "待機中"}
                                </p>
                            </div>
                            <div className="rounded-2xl border border-border bg-surface-alt px-3 py-3">
                                <div className="flex items-center gap-1 text-xs font-semibold uppercase tracking-[0.1em] text-text-muted">
                                    <Mic size={12} />
                                    Flow
                                </div>
                                <p className="mt-1.5 text-xs font-semibold text-text-primary">
                                    {isLoading ? "生成中..." : "検知待ち"}
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* フローステータス */}
                    <div className="rounded-card border border-border bg-surface-alt px-4 py-3 text-sm text-text-secondary">
                        <p className="font-medium">{flowLabel}</p>
                        {lastTriggerAt && (
                            <p className="mt-1 text-xs text-text-muted">直近の検知時刻: {lastTriggerAt}</p>
                        )}
                    </div>

                    {cameraError && (
                        <p className="text-sm text-red-500">{cameraError}</p>
                    )}

                    {/* 戻るボタン */}
                    <button
                        onClick={() => {
                            stopDetection();
                            stopCamera();
                            setStep(0);
                            hasCameraStartedRef.current = false;
                        }}
                        className="text-sm text-text-muted hover:text-accent transition-colors"
                    >
                        ← コンテキスト入力に戻る
                    </button>
                </div>
            )}
        </div>
    );
}
