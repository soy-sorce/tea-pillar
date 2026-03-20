// src/components/result/LoadingScreen.tsx
import { useEffect, useState } from "react";

const STEPS = [
    "🔍 猫の感情を分析しています...",
    "✍️ AIがプロンプトを構築しています...",
    "🎬 Veo3が動画を生成中です...",
] as const;

const PAW_DELAYS = ["", "delay-200", "delay-500"] as const;

interface LoadingScreenProps {
    stateKey?: string;
    templateName?: string;
}

export function LoadingScreen({
    stateKey,
    templateName,
}: LoadingScreenProps): React.JSX.Element {
    const [stepIndex, setStepIndex] = useState(0);

    useEffect(() => {
        const interval = setInterval(() => {
            setStepIndex((prev) => (prev + 1) % STEPS.length);
        }, 4000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="flex min-h-[70vh] flex-col items-center justify-center gap-10 px-4 py-12 animate-fadeIn">
            {/* 円形プログレスプレースホルダー + 肉球 */}
            <div className="relative flex items-center justify-center">
                {/* 外側のパルスリング */}
                <div className="absolute h-28 w-28 rounded-full bg-accent/20 animate-pulse-ring" />
                <div className="absolute h-28 w-28 rounded-full bg-accent/10 animate-pulse-ring delay-700" />

                {/* 内側の回転リング */}
                <div className="h-24 w-24 rounded-full border-4 border-accent-light border-t-accent animate-spin-slow" />

                {/* 中央の肉球 */}
                <div className="absolute text-4xl animate-bounce-gentle">🐾</div>
            </div>

            {/* ステップテキスト */}
            <div className="text-center min-h-[56px]">
                <p
                    key={stepIndex}
                    className="text-base font-medium text-text-secondary animate-fadeIn"
                >
                    {STEPS[stepIndex]}
                </p>
                <p className="mt-1.5 text-xs text-text-muted">
                    通常30秒〜3分かかります
                </p>
            </div>

            {/* 下部の小さな肉球 */}
            <div className="flex gap-3">
                {PAW_DELAYS.map((delay, i) => (
                    <span
                        key={i}
                        className={`text-lg animate-bounce-gentle opacity-60 ${delay}`}
                    >
                        🐾
                    </span>
                ))}
            </div>

            {/* デバッグ情報 */}
            {(stateKey ?? templateName) && (
                <div className="rounded-card-lg bg-surface border border-border px-5 py-4 text-sm text-text-secondary shadow-card space-y-1.5 w-full max-w-md">
                    {stateKey && (
                        <p>
                            状態キー:{" "}
                            <span className="font-mono text-xs bg-surface-alt px-1.5 py-0.5 rounded text-accent">{stateKey}</span>
                        </p>
                    )}
                    {templateName && (
                        <p>テンプレート: <span className="font-medium">{templateName}</span></p>
                    )}
                </div>
            )}
        </div>
    );
}
