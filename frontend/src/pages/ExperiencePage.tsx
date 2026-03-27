// src/pages/ExperiencePage.tsx
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Camera, Mic, FileText, Radar, ArrowLeft } from "lucide-react";

import { StepIndicator } from "@/components/layout/StepIndicator";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { useCamera } from "@/hooks/useCamera";
import { useGenerate } from "@/hooks/useGenerate";
import { useGenerationContext } from "@/contexts/GenerationContext";
import { useMicrophone } from "@/hooks/useMicrophone";
import { useMotionDetection } from "@/hooks/useMotionDetection";

type Step = 0 | 1 | 2;

const STEPS = ["撮影", "鳴きマネ録音", "コンテキスト"];
const CAPTURE_WAIT_MS = 1000;
const MIC_SECONDS = 3;


export function ExperiencePage(): React.JSX.Element {
    const navigate = useNavigate();
    const { reset } = useGenerationContext();
    const { generate, isLoading } = useGenerate();

    // ── ステップ状態 ──────────────────────────────
    const [step, setStep] = useState<Step>(0);
    const [capturedImage, setCapturedImage] = useState<string | null>(null);
    const [capturedAudio, setCapturedAudio] = useState<string | null>(null);
    const [userContext, setUserContext] = useState("");
    const [captureNotice, setCaptureNotice] = useState(false);
    const [micCountdown, setMicCountdown] = useState(MIC_SECONDS);
    const [isRecordingStarted, setIsRecordingStarted] = useState(false);

    // マウント時にコンテキストをリセット
    useEffect(() => { reset(); }, [reset]);

    // ── フック（常に呼ぶ） ────────────────────────
    const {
        videoRef, isReady, error: cameraError,
        startCamera, stopCamera, captureFrame, getStream,
    } = useCamera();

    const {
        startTimedRecording, resetAudio,
    } = useMicrophone();

    // ── motion detection トリガーハンドラ ─────────
    // stale closure を避けるため ref に最新のハンドラを持つ
    const triggerHandlerRef = useRef<() => void>(() => { });
    const isHandlingRef = useRef(false);

    // 毎レンダリングで ref を更新（deps 不要）
    triggerHandlerRef.current = () => {
        if (isHandlingRef.current) return;
        isHandlingRef.current = true;

        const image = captureFrame();
        if (!image) {
            isHandlingRef.current = false;
            return;
        }

        setCapturedImage(image);
        setCaptureNotice(true);

        // 1秒待機してからステップ遷移
        window.setTimeout(() => {
            setStep(1);
        }, CAPTURE_WAIT_MS);
    };

    // stable な onTrigger を一度だけ作成
    const stableOnTrigger = useCallback(() => {
        triggerHandlerRef.current();
    }, []);

    const { motionScore, status: motionStatus, startDetection, stopDetection } = useMotionDetection({
        videoRef,
        getStream,
        onTrigger: stableOnTrigger,
    });

    // ── カメラ起動（step 0 マウント時に一度だけ） ─
    const hasCameraStartedRef = useRef(false);
    useEffect(() => {
        if (step !== 0 || hasCameraStartedRef.current) return;
        hasCameraStartedRef.current = true;
        void startCamera().then(() => startDetection());
    }, [step, startCamera, startDetection]);

    // ── step 0 を離れたらカメラ・検知を停止 ───────
    useEffect(() => {
        if (step > 0) {
            stopDetection();
            stopCamera();
        }
    }, [step, stopDetection, stopCamera]);

    // ── アンマウント時クリーンアップ ───────────────
    useEffect(() => () => {
        stopDetection();
        stopCamera();
    }, [stopDetection, stopCamera]);

    // ── 録音開始ハンドラ (step 1, ボタン押下で呼ばれる) ──
    const handleStartRecording = useCallback((): void => {
        if (isRecordingStarted) return;
        setIsRecordingStarted(true);
        setMicCountdown(MIC_SECONDS);
        resetAudio();

        // カウントダウン
        let remaining = MIC_SECONDS;
        const intervalId = window.setInterval(() => {
            remaining -= 1;
            setMicCountdown(remaining);
            if (remaining <= 0) clearInterval(intervalId);
        }, 1000);

        // 録音開始 → 完了 → step 2 へ
        void startTimedRecording(MIC_SECONDS).then((audio) => {
            clearInterval(intervalId);
            setCapturedAudio(audio);
            setStep(2);
            setIsRecordingStarted(false);
        });
    }, [isRecordingStarted, resetAudio, startTimedRecording]);

    // ── 動画生成送信 ───────────────────────────────
    const handleGenerate = useCallback(async (): Promise<void> => {
        if (!capturedImage) return;
        await generate({
            mode: "experience",
            image_base64: capturedImage,
            audio_base64: capturedAudio ?? undefined,
            user_context: userContext.trim() || undefined,
        });
    }, [capturedImage, capturedAudio, generate, userContext]);

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
                    <p className="text-xs font-semibold uppercase tracking-[0.14em] text-accent">体験モード</p>
                    <h1 className="text-xl font-bold text-text-primary">あなたが猫になりきる</h1>
                </div>
            </div>

            {/* ステップインジケーター */}
            <div className="mb-8">
                <StepIndicator steps={STEPS} currentStep={step} />
            </div>

            {/* 各ステップ本体 */}
            {step === 0 && (
                <div className="animate-fadeIn space-y-5">
                    {/* 説明カード */}
                    <div className="rounded-card-lg border border-border bg-surface p-5 shadow-card">
                        <div className="mb-2 inline-flex items-center rounded-full bg-gradient-btn px-3 py-1 text-xs font-bold text-white shadow-btn-primary">
                            STEP 1 / 3 &nbsp;·&nbsp; 撮影
                        </div>
                        <p className="mt-3 text-sm leading-7 text-text-secondary">
                            カメラの前で猫のポーズをとったり動いてみてください。
                            AIがあなたの動きを自動で検知し、その瞬間を撮影します。
                            準備ができたらカメラの前に立ってください。
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
                            {/* 動き検知通知オーバーレイ */}
                            {captureNotice && (
                                <div className="absolute inset-0 flex items-center justify-center bg-accent/20 backdrop-blur-sm animate-fadeIn">
                                    <div className="rounded-2xl bg-white/90 px-6 py-4 text-center shadow-2xl">
                                        <p className="text-2xl">📸</p>
                                        <p className="mt-1 text-sm font-bold text-accent">動きを検知しました！</p>
                                        <p className="text-xs text-text-muted">次のステップへ移動します...</p>
                                    </div>
                                </div>
                            )}
                            {/* 未起動時のプレースホルダー */}
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
                        <div className="grid grid-cols-2 gap-3 border-t border-border px-4 py-4">
                            <div className="rounded-2xl border border-border bg-surface-alt px-4 py-3">
                                <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.12em] text-text-muted">
                                    <Camera size={13} />
                                    Camera
                                </div>
                                <p className="mt-2 text-sm font-semibold text-text-primary">
                                    {isReady ? "準備完了" : "起動中..."}
                                </p>
                            </div>
                            <div className="rounded-2xl border border-border bg-surface-alt px-4 py-3">
                                <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.12em] text-text-muted">
                                    <Radar size={13} />
                                    Motion
                                </div>
                                <p className="mt-2 text-sm font-semibold text-text-primary">
                                    {motionStatus === "watching"
                                        ? `検知中 (score: ${Math.round(motionScore)})`
                                        : motionStatus === "detected"
                                            ? "動きを検出！"
                                            : motionStatus === "cooldown"
                                                ? "クールダウン中"
                                                : "待機中"}
                                </p>
                            </div>
                        </div>
                    </div>

                    {cameraError && (
                        <p className="text-sm text-red-500">{cameraError}</p>
                    )}
                </div>
            )}

            {step === 1 && (
                <div className="animate-fadeIn space-y-5">
                    {/* 説明カード */}
                    <div className="rounded-card-lg border border-border bg-surface p-5 shadow-card">
                        <div className="mb-2 inline-flex items-center rounded-full bg-gradient-btn px-3 py-1 text-xs font-bold text-white shadow-btn-primary">
                            STEP 2 / 3 &nbsp;·&nbsp; 鳴きマネ録音
                        </div>
                        <p className="mt-3 text-sm leading-7 text-text-secondary">
                            猫が鳴くように声を出してみてください。
                            3秒間録音します。無音でも自動で次のステップに進みます。
                        </p>
                    </div>

                    {/* 録音UI */}
                    <div className="rounded-card-xl border border-border bg-surface p-8 shadow-card text-center">
                        {/* マイクアイコン + パルス */}
                        <div className="relative mx-auto mb-6 flex h-28 w-28 items-center justify-center">
                            {isRecordingStarted && (
                                <>
                                    <div className="absolute h-28 w-28 rounded-full bg-accent/20 animate-pulse-ring" />
                                    <div className="absolute h-28 w-28 rounded-full bg-accent/10 animate-pulse-ring delay-500" />
                                </>
                            )}
                            <div
                                className={[
                                    "relative flex h-20 w-20 items-center justify-center rounded-full transition-all duration-300",
                                    isRecordingStarted
                                        ? "bg-gradient-btn shadow-btn-primary"
                                        : "bg-surface-alt border-2 border-border",
                                ].join(" ")}
                            >
                                <Mic
                                    size={36}
                                    className={isRecordingStarted ? "text-white" : "text-text-muted"}
                                />
                            </div>
                        </div>

                        {isRecordingStarted ? (
                            <>
                                {/* カウントダウン */}
                                <div className="text-6xl font-black text-accent tabular-nums">
                                    {micCountdown}
                                </div>
                                <p className="mt-2 text-sm text-text-secondary">録音中です...</p>
                                <p className="mt-1 text-xs text-text-muted">「にゃあ」「みゃー」など、猫の鳴き声を真似してみよう！</p>
                            </>
                        ) : (
                            <>
                                <p className="text-base font-semibold text-text-primary">録音の準備ができたら</p>
                                <p className="mt-1 text-xs text-text-muted mb-5">ボタンを押すと <span className="font-bold text-accent">3秒間</span> 録音が始まります</p>
                                <Button
                                    id="btn-start-recording"
                                    variant="primary"
                                    size="lg"
                                    leftIcon={<Mic size={18} />}
                                    onClick={handleStartRecording}
                                    className="w-full max-w-xs"
                                >
                                    録音を開始する（3秒）
                                </Button>
                                <p className="mt-3 text-xs text-text-muted">
                                    ※ 録音なしで次へ進む場合は<button
                                        onClick={() => {
                                            setCapturedAudio(null);
                                            setStep(2);
                                        }}
                                        className="ml-1 text-accent underline hover:no-underline"
                                    >スキップ</button>
                                </p>
                            </>
                        )}
                    </div>

                    {/* キャプチャ済み写真のサムネイル */}
                    {capturedImage && (
                        <div className="flex items-center gap-3 rounded-card border border-border bg-surface-alt px-4 py-3 text-sm text-text-secondary">
                            <img
                                src={capturedImage}
                                alt="キャプチャした画像"
                                className="h-12 w-16 rounded-lg object-cover border border-border flex-shrink-0"
                            />
                            <span>ステップ1で撮影した画像を取得しました ✓</span>
                        </div>
                    )}
                </div>
            )}

            {step === 2 && (
                <div className="animate-fadeIn space-y-5">
                    {/* 説明カード */}
                    <div className="rounded-card-lg border border-border bg-surface p-5 shadow-card">
                        <div className="mb-2 inline-flex items-center rounded-full bg-gradient-btn px-3 py-1 text-xs font-bold text-white shadow-btn-primary">
                            STEP 3 / 3 &nbsp;·&nbsp; コンテキスト
                        </div>
                        <p className="mt-3 text-sm leading-7 text-text-secondary">
                            演じた猫の性格や好みを自由に書いてください。
                            入力した情報がAIのプロンプト構築に使われ、より個性のある動画が生成されます。
                            空欄のまま生成することもできます。
                        </p>
                    </div>

                    {/* 取得済み情報の確認 */}
                    <div className="grid gap-3 sm:grid-cols-2">
                        {capturedImage && (
                            <div className="flex items-center gap-3 rounded-card border border-border bg-surface-alt px-4 py-3 text-sm text-text-secondary">
                                <img
                                    src={capturedImage}
                                    alt="キャプチャした画像"
                                    className="h-12 w-16 rounded-lg object-cover border border-border flex-shrink-0"
                                />
                                <div>
                                    <p className="text-xs font-semibold text-accent">Step 1</p>
                                    <p className="text-xs">画像取得済み ✓</p>
                                </div>
                            </div>
                        )}
                        <div className="flex items-center gap-3 rounded-card border border-border bg-surface-alt px-4 py-3 text-sm text-text-secondary">
                            <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-lg bg-accent-light">
                                <Mic size={20} className="text-accent" />
                            </div>
                            <div>
                                <p className="text-xs font-semibold text-accent">Step 2</p>
                                <p className="text-xs">{capturedAudio ? "録音取得済み ✓" : "録音なし（無音）"}</p>
                            </div>
                        </div>
                    </div>

                    {/* コンテキスト入力 */}
                    <div className="rounded-card-lg border border-border bg-surface p-5 shadow-card">
                        <label htmlFor="exp-context" className="text-sm font-semibold text-text-primary">
                            <FileText size={14} className="mr-1.5 inline" />
                            猫の性格・好みを書く
                            <span className="ml-2 text-xs font-normal text-text-muted">（任意）</span>
                        </label>
                        <textarea
                            id="exp-context"
                            value={userContext}
                            onChange={(e) => setUserContext(e.target.value)}
                            maxLength={500}
                            rows={4}
                            placeholder="例: 魚が大好きで、少し臆病な性格。窓の外の鳥によく反応する。"
                            className="mt-3 w-full resize-none rounded-card border border-border bg-surface-alt px-4 py-3 text-sm text-text-primary placeholder:text-text-muted transition-colors focus:border-accent focus:bg-surface focus:outline-none focus:ring-1 focus:ring-accent"
                        />
                        <p className="mt-1 text-right text-xs text-text-muted">{userContext.length} / 500</p>
                    </div>

                    {/* 生成ボタン */}
                    <Button
                        id="btn-generate-experience"
                        variant="primary"
                        size="xl"
                        disabled={isLoading || !capturedImage}
                        onClick={() => void handleGenerate()}
                        className="w-full"
                    >
                        {isLoading ? "生成リクエスト送信中..." : "動画を生成する 🎬"}
                    </Button>
                </div>
            )}
        </div>
    );
}
