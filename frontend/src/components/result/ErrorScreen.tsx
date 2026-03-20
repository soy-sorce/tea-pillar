// src/components/result/ErrorScreen.tsx
import { Button } from "@/components/ui/Button";

interface ErrorScreenProps {
    code: string | null;
    message: string | null;
    onRetry: () => void;
    onBack: () => void;
}

export function ErrorScreen({
    code: _code,
    message,
    onRetry,
    onBack,
}: ErrorScreenProps): JSX.Element {
    return (
        <div className="flex min-h-[70vh] flex-col items-center justify-center gap-6 px-4 text-center">
            <span className="text-6xl">😿</span>

            <div>
                <h2 className="text-xl font-semibold text-text-primary">
                    動画の生成に失敗しました
                </h2>
                <p className="mt-2 text-sm text-text-secondary">
                    {message ?? "予期しないエラーが発生しました"}
                </p>
                <p className="mt-1 text-xs text-text-muted">
                    もう一度お試しください
                </p>
            </div>

            <div className="flex gap-3">
                <Button variant="primary" onClick={onRetry} id="retry-button">
                    🔄 もう一度試す
                </Button>
                <Button variant="secondary" onClick={onBack} id="back-button">
                    ← 戻る
                </Button>
            </div>
        </div>
    );
}
