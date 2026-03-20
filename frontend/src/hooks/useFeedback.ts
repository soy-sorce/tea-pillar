// src/hooks/useFeedback.ts
import { useCallback, useState } from "react";
import { post, ApiError } from "@/lib/api";
import type { FeedbackRequest, FeedbackResponse } from "@/types/api";

interface UseFeedbackReturn {
    submitFeedback: (req: FeedbackRequest) => Promise<void>;
    submitted: boolean;
    isLoading: boolean;
}

export function useFeedback(): UseFeedbackReturn {
    const [submitted, setSubmitted] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    const submitFeedback = useCallback(
        async (req: FeedbackRequest): Promise<void> => {
            if (submitted) return;
            setIsLoading(true);
            try {
                await post<FeedbackResponse>("/feedback", req);
                setSubmitted(true);
            } catch (e) {
                // フィードバック送信失敗はUIに影響しない（サイレント処理）
                console.warn(
                    "Feedback submission failed:",
                    e instanceof ApiError ? e.message : e
                );
            } finally {
                setIsLoading(false);
            }
        },
        [submitted]
    );

    return { submitFeedback, submitted, isLoading };
}
