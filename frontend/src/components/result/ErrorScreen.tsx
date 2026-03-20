// src/components/result/ErrorScreen.tsx
import { AlertCircle, RefreshCw, ArrowLeft } from "lucide-react";
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
}: ErrorScreenProps): React.JSX.Element {
    return (
        <div className="flex min-h-[70vh] flex-col items-center justify-center gap-8 px-4 text-center animate-fadeIn">
            {/* エラーアイコン */}
            <div className="relative">
                <div className="absolute inset-0 rounded-full bg-red-100 scale-125 animate-pulse-ring" />
                <div className="relative flex h-20 w-20 items-center justify-center rounded-full bg-red-50 border border-red-200">
                    <AlertCircle size={36} className="text-red-400" />
                </div>
            </div>

            <div className="space-y-2">
                <h2 className="text-xl font-bold text-text-primary">
                    動画の生成に失敗しました
                </h2>
                <p className="text-sm text-text-secondary max-w-sm">
                    {message ?? "予期しないエラーが発生しました"}
                </p>
                <p className="text-xs text-text-muted">
                    もう一度お試しください
                </p>
            </div>

            <div className="flex gap-3">
                <Button
                    variant="primary"
                    size="lg"
                    onClick={onRetry}
                    id="retry-button"
                    leftIcon={<RefreshCw size={16} />}
                >
                    もう一度試す
                </Button>
                <Button
                    variant="secondary"
                    size="lg"
                    onClick={onBack}
                    id="back-button"
                    leftIcon={<ArrowLeft size={16} />}
                >
                    戻る
                </Button>
            </div>
        </div>
    );
}
