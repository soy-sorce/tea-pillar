// src/pages/ResultPage.tsx
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useGenerationContext } from "@/contexts/GenerationContext";
import { LoadingScreen } from "@/components/result/LoadingScreen";
import { VideoPlayer } from "@/components/result/VideoPlayer";
import { FeedbackButtons } from "@/components/result/FeedbackButtons";
import { ErrorScreen } from "@/components/result/ErrorScreen";
import { Button } from "@/components/ui/Button";

export function ResultPage(): JSX.Element {
    const navigate = useNavigate();
    const { resultState, response, errorCode, errorMessage, reset } =
        useGenerationContext();

    // idle状態（直接アクセス）はトップへリダイレクト
    useEffect(() => {
        if (resultState === "idle") {
            void navigate("/", { replace: true });
        }
    }, [resultState, navigate]);

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
            <div className="mx-auto max-w-2xl space-y-6 px-4 py-8">
                <VideoPlayer src={response.video_url} />

                <FeedbackButtons sessionId={response.session_id} />

                <div className="text-center">
                    <Button
                        id="btn-retry"
                        variant="text"
                        onClick={() => {
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
                code={errorCode}
                message={errorMessage}
                onRetry={() => void navigate(0)}
                onBack={() => void navigate(-1)}
            />
        );
    }

    // idle の場合は useEffect でリダイレクト済み
    return <></>;
}
