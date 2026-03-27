import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Camera, Mic, Radar, Wand2, Video } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { useCamera } from "@/hooks/useCamera";
import { useGenerate } from "@/hooks/useGenerate";
import { useMicrophone } from "@/hooks/useMicrophone";
import { useMotionDetection } from "@/hooks/useMotionDetection";

type Mode = "experience" | "production";

interface MotionCaptureFormProps {
    mode: Mode;
}

type FlowState =
    | "idle"
    | "starting"
    | "watching"
    | "capturing"
    | "recording"
    | "submitting";

const MODE_TEXT: Record<
    Mode,
    {
        title: string;
        description: string;
        note: string;
    }
> = {
    experience: {
        title: "体験モード",
        description:
            "カメラの前で猫の真似をして動くと、その瞬間を切り取って動画生成を開始します。",
        note: "reaction video 録画やモデル更新は行いません。",
    },
    production: {
        title: "本番モード",
        description:
            "実猫の素早い動きを検知した瞬間に静止画と音声を取得し、猫向けの動画生成を開始します。",
        note: "生成後は result 画面で reaction video を録画し、モデル更新に使います。",
    },
};

function StatusBadge({
    icon,
    label,
    value,
}: {
    icon: ReactNode;
    label: string;
    value: string;
}): React.JSX.Element {
    return (
        <div className="rounded-2xl border border-border bg-surface-alt px-4 py-3">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.14em] text-text-muted">
                {icon}
                {label}
            </div>
            <p className="mt-2 text-sm font-semibold text-text-primary">{value}</p>
        </div>
    );
}

export function MotionCaptureForm({ mode }: MotionCaptureFormProps): React.JSX.Element {
    const { title, description, note } = MODE_TEXT[mode];
    const { generate, isLoading } = useGenerate();
    const {
        videoRef,
        isReady,
        error: cameraError,
        startCamera,
        stopCamera,
        captureFrame,
        getStream,
    } = useCamera();
    const {
        audioBase64,
        isRecording,
        error: microphoneError,
        startTimedRecording,
        resetAudio,
    } = useMicrophone();

    const [flowState, setFlowState] = useState<FlowState>("idle");
    const [userContext, setUserContext] = useState("");
    const [started, setStarted] = useState(false);
    const [lastTriggerAt, setLastTriggerAt] = useState<string | null>(null);
    const isHandlingTriggerRef = useRef(false);

    const handleTriggered = useCallback(async (): Promise<void> => {
        if (isHandlingTriggerRef.current || isLoading) {
            return;
        }

        isHandlingTriggerRef.current = true;
        setFlowState("capturing");

        const imageBase64 = captureFrame();
        if (!imageBase64) {
            isHandlingTriggerRef.current = false;
            setFlowState("watching");
            return;
        }

        setLastTriggerAt(new Date().toLocaleTimeString("ja-JP"));
        setFlowState("recording");
        const recordedAudio = await startTimedRecording();

        setFlowState("submitting");
        await generate({
            mode,
            image_base64: imageBase64,
            audio_base64: recordedAudio ?? undefined,
            user_context: userContext.trim() || undefined,
        });
    }, [captureFrame, generate, isLoading, mode, startTimedRecording, userContext]);

    const { motionScore, status: motionStatus, startDetection, stopDetection } = useMotionDetection({
        videoRef,
        getStream,
        onTrigger: () => {
            void handleTriggered();
        },
    });

    const startFlow = useCallback(async (): Promise<void> => {
        resetAudio();
        stopDetection();
        if (isReady) {
            setStarted(true);
            startDetection();
            setFlowState("watching");
            return;
        }
        setFlowState("starting");
        await startCamera();
        setStarted(true);
        startDetection();
        setFlowState("watching");
    }, [isReady, resetAudio, startCamera, startDetection, stopDetection]);

    useEffect(() => {
        return () => {
            stopDetection();
            stopCamera();
        };
    }, [stopCamera, stopDetection]);

    const flowLabel = useMemo(() => {
        if (isLoading) return "AIが動画を生成しています";
        switch (flowState) {
            case "idle":
                return "開始ボタンでカメラ待機を始めます";
            case "starting":
                return "カメラを起動しています";
            case "watching":
                return "素早い動きを検知中です";
            case "capturing":
                return "動きを検知しました。静止画を取得しています";
            case "recording":
                return "3秒だけ音声を録音しています";
            case "submitting":
                return "生成リクエストを送信しています";
            default:
                return "待機中です";
        }
    }, [flowState, isLoading]);

    return (
        <div className="space-y-5">
            <div className="rounded-card-lg border border-border bg-surface p-6 shadow-card">
                <div className="mb-3 inline-flex items-center rounded-full bg-gradient-btn px-3 py-1 text-xs font-bold text-white shadow-btn-primary">
                    LIVE CAPTURE
                </div>
                <h3 className="text-xl font-bold tracking-tight text-text-primary">{title}</h3>
                <p className="mt-3 text-sm leading-7 text-text-secondary sm:text-[15px]">{description}</p>
                <p className="mt-2 text-xs text-text-muted">{note}</p>

                <div className="mt-5 overflow-hidden rounded-card-xl border border-border bg-surface-alt">
                    <div className="aspect-[16/10] bg-black/90">
                        <video
                            ref={videoRef}
                            muted
                            playsInline
                            className="h-full w-full object-cover"
                            aria-label="カメラプレビュー"
                        />
                    </div>
                </div>

                <div className="mt-5 grid gap-3 sm:grid-cols-3">
                    <StatusBadge
                        icon={<Radar size={14} />}
                        label="Motion"
                        value={`${motionStatus} / score ${Math.round(motionScore)}`}
                    />
                    <StatusBadge
                        icon={<Mic size={14} />}
                        label="Audio"
                        value={isRecording ? "録音中" : audioBase64 ? "録音完了" : "待機中"}
                    />
                    <StatusBadge
                        icon={<Video size={14} />}
                        label="Flow"
                        value={flowLabel}
                    />
                </div>

                {(cameraError || microphoneError) && (
                    <p className="mt-4 text-sm text-red-500">{cameraError ?? microphoneError}</p>
                )}

                {lastTriggerAt && (
                    <p className="mt-3 text-xs text-text-muted">直近の検知時刻: {lastTriggerAt}</p>
                )}
            </div>

            <div className="rounded-card-lg border border-border bg-surface p-6 shadow-card">
                <div className="mb-3 inline-flex items-center rounded-full bg-gradient-btn px-3 py-1 text-xs font-bold text-white shadow-btn-primary">
                    CONTEXT
                </div>
                <label htmlFor={`${mode}-user-context`} className="text-sm font-semibold text-text-primary">
                    文脈テキスト
                </label>
                <p className="mt-2 text-sm leading-6 text-text-secondary">
                    性格やその場の状況を補足したい場合だけ入力します。空でも生成できます。
                </p>
                <textarea
                    id={`${mode}-user-context`}
                    value={userContext}
                    onChange={(event) => setUserContext(event.target.value)}
                    maxLength={500}
                    rows={4}
                    placeholder="例: 魚に反応しやすい、今日は少し眠そう"
                    className="mt-4 w-full resize-none rounded-card border border-border bg-surface-alt px-4 py-3 text-sm text-text-primary placeholder:text-text-muted transition-colors focus:border-accent focus:bg-surface focus:outline-none focus:ring-1 focus:ring-accent"
                />
                <p className="mt-1 text-right text-xs text-text-muted">{userContext.length} / 500</p>
            </div>

            <div className="rounded-card-lg border border-border bg-surface p-5 shadow-card">
                <div className="flex flex-col gap-3 sm:flex-row">
                    <Button
                        id={`btn-start-${mode}`}
                        variant="primary"
                        size="lg"
                        disabled={isLoading}
                        onClick={() => void startFlow()}
                        className="flex-1"
                        leftIcon={<Camera size={18} />}
                    >
                        {started ? "カメラ待機を再開する" : "カメラを起動して始める"}
                    </Button>
                    <Button
                        id={`btn-stop-${mode}`}
                        variant="ghost"
                        size="lg"
                        onClick={() => {
                            stopDetection();
                            stopCamera();
                            setStarted(false);
                            setFlowState("idle");
                        }}
                        className="flex-1"
                        leftIcon={<Wand2 size={18} />}
                    >
                        停止する
                    </Button>
                </div>
            </div>
        </div>
    );
}
