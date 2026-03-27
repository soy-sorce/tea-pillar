import { useCallback, useEffect, useRef, useState, type RefObject } from "react";

import DiffCamEngine from "diff-cam-engine";

type MotionStatus = "idle" | "watching" | "detected" | "cooldown";

interface UseMotionDetectionOptions {
    videoRef: RefObject<HTMLVideoElement | null>;
    getStream: () => MediaStream | null;
    onTrigger: () => void;
    pixelDiffThreshold?: number;
    scoreThreshold?: number;
    consecutiveFrames?: number;
    cooldownMs?: number;
    /** カメラ起動直後の誤検知を防ぐウォームアップ期間 (ms)。デフォルト 0。 */
    warmupMs?: number;
}

interface MotionPayload {
    score?: number;
    hasMotion?: boolean;
}

interface DiffCamEngineLike {
    init: (options: Record<string, unknown>) => void;
    start: () => void;
    stop: () => void;
}

const MOTION_SETTLE_DELAY_MS = 500;

export function useMotionDetection({
    videoRef,
    getStream,
    onTrigger,
    pixelDiffThreshold = 30,
    scoreThreshold = 40,
    consecutiveFrames = 2,
    cooldownMs = 10_000,
    warmupMs = 0,
}: UseMotionDetectionOptions): {
    status: MotionStatus;
    motionScore: number;
    startDetection: () => void;
    stopDetection: () => void;
} {
    const engineRef = useRef<DiffCamEngineLike | null>(null);
    const consecutiveHitsRef = useRef(0);
    const cooldownUntilRef = useRef(0);
    const warmupUntilRef = useRef(0);
    const [status, setStatus] = useState<MotionStatus>("idle");
    const [motionScore, setMotionScore] = useState(0);

    const stopDetection = useCallback((): void => {
        engineRef.current?.stop();
        engineRef.current = null;
        consecutiveHitsRef.current = 0;
        setStatus("idle");
        setMotionScore(0);
    }, []);

    const startDetection = useCallback((): void => {
        const video = videoRef.current;
        if (!video) {
            return;
        }

        engineRef.current?.stop();
        consecutiveHitsRef.current = 0;
        warmupUntilRef.current = Date.now() + warmupMs;

        const engine = DiffCamEngine as unknown as DiffCamEngineLike;
        engine.init({
            video,
            stream: getStream() ?? undefined,
            captureIntervalTime: 120,
            captureWidth: 320,
            captureHeight: 180,
            pixelDiffThreshold,
            scoreThreshold,
            includeMotionBox: false,
            includeMotionPixels: false,
            captureCallback: (payload: MotionPayload) => {
                const now = Date.now();
                const score = payload.score ?? 0;
                setMotionScore(score);

                // ウォームアップ期間中は onTrigger を呼ばない
                if (now < warmupUntilRef.current) {
                    setStatus("watching");
                    return;
                }

                if (now < cooldownUntilRef.current) {
                    setStatus("cooldown");
                    return;
                }

                const hasMotion = Boolean(payload.hasMotion) || score >= scoreThreshold;
                if (!hasMotion) {
                    consecutiveHitsRef.current = 0;
                    setStatus("watching");
                    return;
                }

                consecutiveHitsRef.current += 1;
                if (consecutiveHitsRef.current < consecutiveFrames) {
                    setStatus("watching");
                    return;
                }

                consecutiveHitsRef.current = 0;
                cooldownUntilRef.current = now + cooldownMs;
                setStatus("detected");
                window.setTimeout(() => {
                    onTrigger();
                    setStatus("cooldown");
                }, MOTION_SETTLE_DELAY_MS);
            },
        });
        engine.start();
        engineRef.current = engine;
        setStatus("watching");
    }, [
        consecutiveFrames,
        cooldownMs,
        warmupMs,
        onTrigger,
        pixelDiffThreshold,
        scoreThreshold,
        getStream,
        videoRef,
    ]);

    useEffect(() => stopDetection, [stopDetection]);

    return { status, motionScore, startDetection, stopDetection };
}
