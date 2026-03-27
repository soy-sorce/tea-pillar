import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Camera, RefreshCw, UploadCloud, Video } from "lucide-react";

import { ErrorScreen } from "@/components/result/ErrorScreen";
import { LoadingScreen } from "@/components/result/LoadingScreen";
import { VideoPlayer } from "@/components/result/VideoPlayer";
import { Button } from "@/components/ui/Button";
import { useGenerationContext } from "@/contexts/GenerationContext";
import {
    ApiError,
    completeReactionUpload,
    issueReactionUploadUrl,
    putBinary,
} from "@/lib/api";
import { useCamera } from "@/hooks/useCamera";
import { useReactionRecorder } from "@/hooks/useReactionRecorder";

type ReactionUploadState =
    | "idle"
    | "recording"
    | "uploading"
    | "completed"
    | "error";

export function ResultPage(): React.JSX.Element {
    const navigate = useNavigate();
    const {
        input,
        resultState,
        response,
        errorMessage,
        reset,
    } = useGenerationContext();
    const isProduction = input?.mode === "production";
    const hasStartedReactionFlowRef = useRef(false);
    const [reactionUploadState, setReactionUploadState] = useState<ReactionUploadState>("idle");
    const [reactionError, setReactionError] = useState<string | null>(null);

    const {
        videoRef: reactionCameraRef,
        startCamera,
        stopCamera,
        getStream,
        isReady: isReactionCameraReady,
        error: reactionCameraError,
    } = useCamera();
    const {
        isRecording: isReactionRecording,
        recordedBlob,
        error: reactionRecorderError,
        startRecording,
        reset: resetReactionRecording,
    } = useReactionRecorder();

    useEffect(() => {
        if (resultState === "idle") {
            void navigate("/", { replace: true });
        }
    }, [resultState, navigate]);

    useEffect(() => {
        if (!isProduction || resultState !== "done") {
            return;
        }

        void startCamera();

        return () => {
            stopCamera();
        };
    }, [isProduction, resultState, startCamera, stopCamera]);

    const handleVideoPlay = useCallback((): void => {
        if (!isProduction || !response || hasStartedReactionFlowRef.current) {
            return;
        }
        const stream = getStream();
        if (!stream) {
            return;
        }

        hasStartedReactionFlowRef.current = true;
        setReactionError(null);
        setReactionUploadState("recording");
        startRecording(stream);
    }, [getStream, isProduction, response, startRecording]);

    useEffect(() => {
        if (!recordedBlob || !response || !isProduction) {
            return;
        }

        const uploadReaction = async (): Promise<void> => {
            setReactionError(null);
            setReactionUploadState("uploading");
            try {
                const uploadInfo = await issueReactionUploadUrl(response.session_id);
                await putBinary(uploadInfo.upload_url, recordedBlob, "video/mp4");
                await completeReactionUpload(response.session_id, {
                    reaction_video_gcs_uri: uploadInfo.reaction_video_gcs_uri,
                });
                setReactionUploadState("completed");
            } catch (error) {
                setReactionUploadState("error");
                if (error instanceof ApiError) {
                    setReactionError(error.message);
                } else {
                    setReactionError("反応動画の送信に失敗しました");
                }
            }
        };

        void uploadReaction();
    }, [isProduction, recordedBlob, response]);

    const reactionStatusLabel = useMemo(() => {
        if (!isProduction) {
            return "体験モードではreaction video録画は行いません";
        }
        if (reactionCameraError) {
            return reactionCameraError;
        }
        if (reactionRecorderError) {
            return reactionRecorderError;
        }
        if (reactionError) {
            return reactionError;
        }
        switch (reactionUploadState) {
            case "idle":
                return isReactionCameraReady ? "再生開始を待っています" : "カメラを準備しています";
            case "recording":
                return "猫の反応を録画しています";
            case "uploading":
                return "reaction video をアップロードしています";
            case "completed":
                return "reaction video の送信が完了しました";
            case "error":
                return "reaction video の送信に失敗しました";
            default:
                return "待機中です";
        }
    }, [
        isProduction,
        isReactionCameraReady,
        reactionCameraError,
        reactionError,
        reactionRecorderError,
        reactionUploadState,
    ]);

    if (resultState === "loading") {
        return (
            <LoadingScreen
                stateKey={response?.state_key}
                templateName={response?.template_name}
            />
        );
    }

    if (resultState === "done" && response) {
        return (
            <div className="mx-auto max-w-2xl space-y-8 px-4 py-8 animate-fadeIn">
                <VideoPlayer
                    src={response.video_url}
                    loop={!isProduction}
                    onPlay={handleVideoPlay}
                />

                <div className="rounded-card-lg border border-border bg-surface p-6 shadow-card">
                    <div className="flex items-center gap-2 text-sm font-semibold text-text-primary">
                        <UploadCloud size={16} />
                        Reaction Status
                    </div>
                    <p className="mt-3 text-sm leading-6 text-text-secondary">{reactionStatusLabel}</p>

                    {isProduction && (
                        <div className="mt-5 overflow-hidden rounded-card-lg border border-border bg-surface-alt">
                            <div className="aspect-[16/10] bg-black/90">
                                <video
                                    ref={reactionCameraRef}
                                    muted
                                    playsInline
                                    className="h-full w-full object-cover"
                                    aria-label="reaction camera preview"
                                />
                            </div>
                            <div className="grid gap-3 border-t border-border px-4 py-4 sm:grid-cols-3">
                                <div className="rounded-2xl border border-border bg-surface px-4 py-3 text-sm text-text-secondary">
                                    <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.12em] text-text-muted">
                                        <Camera size={14} />
                                        Camera
                                    </div>
                                    <p className="mt-2 font-semibold text-text-primary">
                                        {isReactionCameraReady ? "準備完了" : "起動中"}
                                    </p>
                                </div>
                                <div className="rounded-2xl border border-border bg-surface px-4 py-3 text-sm text-text-secondary">
                                    <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.12em] text-text-muted">
                                        <Video size={14} />
                                        Recording
                                    </div>
                                    <p className="mt-2 font-semibold text-text-primary">
                                        {isReactionRecording ? "録画中" : "待機中"}
                                    </p>
                                </div>
                                <div className="rounded-2xl border border-border bg-surface px-4 py-3 text-sm text-text-secondary">
                                    <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.12em] text-text-muted">
                                        <UploadCloud size={14} />
                                        Upload
                                    </div>
                                    <p className="mt-2 font-semibold text-text-primary">{reactionUploadState}</p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                <div className="text-center">
                    <Button
                        id="btn-retry"
                        variant="ghost"
                        size="md"
                        leftIcon={<RefreshCw size={15} />}
                        onClick={() => {
                            hasStartedReactionFlowRef.current = false;
                            resetReactionRecording();
                            stopCamera();
                            reset();
                            void navigate("/");
                        }}
                    >
                        もう一度試す
                    </Button>
                </div>
            </div>
        );
    }

    if (resultState === "error") {
        return (
            <ErrorScreen
                message={errorMessage}
                onRetry={() => void navigate(0)}
                onBack={() => void navigate(-1)}
            />
        );
    }

    return <></>;
}
