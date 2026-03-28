// src/components/result/LoadingScreen.tsx
import { useEffect, useState } from "react";

interface Phase {
    emoji: string;
    message: string;
}

const PHASES: Phase[] = [
    { emoji: "🔍", message: "猫の感情・状態を分析しています..." },
    { emoji: "🎯", message: "最適なテンプレートを選択しています..." },
    { emoji: "✨", message: "Gemini がプロンプトを拡張しています..." },
    { emoji: "🎬", message: "Veo が動画を生成しています..." },
];

// 各フェーズに遷移する累積時刻 (ms)。最終フェーズは止まる。
const PHASE_TRIGGER_MS = [5_000, 25_000, 30_000] as const;

export function LoadingScreen(): React.JSX.Element {
    const [phaseIndex, setPhaseIndex] = useState(0);

    useEffect(() => {
        const timers = PHASE_TRIGGER_MS.map((t, i) =>
            window.setTimeout(() => setPhaseIndex(i + 1), t)
        );
        return () => timers.forEach(clearTimeout);
    }, []);

    const { emoji, message } = PHASES[phaseIndex];

    // 光る肉球の数: フェーズ 0→1個, 1→2個, 2→3個, 3→3個（全点灯）
    const activePaws = Math.min(phaseIndex + 1, 3);

    return (
        <div className="flex min-h-[70vh] flex-col items-center justify-center gap-10 px-4 py-12 animate-fadeIn">

            {/* 円形スピナー + 中央肉球 */}
            <div className="relative flex items-center justify-center">
                <div className="absolute h-28 w-28 rounded-full bg-accent/20 animate-pulse-ring" />
                <div className="absolute h-28 w-28 rounded-full bg-accent/10 animate-pulse-ring delay-700" />
                <div className="h-24 w-24 rounded-full border-4 border-accent-light border-t-accent animate-spin-slow" />
                <div className="absolute text-4xl animate-bounce-gentle">🐾</div>
            </div>

            {/* フェーズメッセージ（切り替わるたびにフェードイン） */}
            <div className="text-center min-h-[56px]">
                <p
                    key={phaseIndex}
                    className="text-base font-medium text-text-secondary animate-fadeIn"
                >
                    {emoji} {message}
                </p>
                <p className="mt-1.5 text-xs text-text-muted">
                    通常30秒〜3分かかります
                </p>
            </div>

            {/* 進捗肉球ドット：フェーズが進むたびに点灯 */}
            <div className="flex items-center gap-4">
                {[0, 1, 2].map((i) => {
                    const lit = i < activePaws;
                    return (
                        <span
                            key={i}
                            style={{ animationDelay: `${i * 200}ms` }}
                            className={[
                                "text-2xl transition-all duration-700",
                                lit
                                    ? "opacity-100 animate-bounce-gentle drop-shadow-[0_0_6px_rgba(236,72,153,0.6)]"
                                    : "opacity-20 grayscale",
                            ].join(" ")}
                        >
                            🐾
                        </span>
                    );
                })}
            </div>
        </div>
    );
}
