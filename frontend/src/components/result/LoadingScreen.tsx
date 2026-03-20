// src/components/result/LoadingScreen.tsx

const PAW_DELAYS = ["", "delay-150", "delay-300"] as const;

interface LoadingScreenProps {
    stateKey?: string;
    templateName?: string;
}

export function LoadingScreen({
    stateKey,
    templateName,
}: LoadingScreenProps): JSX.Element {
    return (
        <div className="flex min-h-[70vh] flex-col items-center justify-center gap-8 px-4">
            {/* 肉球アニメーション */}
            <div className="flex gap-4">
                {PAW_DELAYS.map((delay, i) => (
                    <span
                        key={i}
                        className={`text-4xl animate-bounce ${delay}`}
                        style={{ animationDuration: "1.2s" }}
                    >
                        🐾
                    </span>
                ))}
            </div>

            <div className="text-center">
                <p className="text-base text-text-secondary">Veo3 が動画を生成中です</p>
                <p className="mt-1 text-sm text-text-muted">
                    通常30秒〜3分かかります
                </p>
            </div>

            {(stateKey ?? templateName) && (
                <div className="rounded-card bg-surface-alt px-4 py-3 text-sm text-text-secondary space-y-1">
                    {stateKey && (
                        <p>
                            状態キー:{" "}
                            <span className="font-mono text-xs">{stateKey}</span>
                        </p>
                    )}
                    {templateName && <p>テンプレート: {templateName}</p>}
                </div>
            )}
        </div>
    );
}
