// src/hooks/useGenerate.ts
import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { post, ApiError } from "@/lib/api";
import { useGenerationContext } from "@/contexts/GenerationContext";
import type { GenerateRequest, GenerateResponse } from "@/types/api";

interface UseGenerateReturn {
    generate: (req: GenerateRequest) => Promise<void>;
    isLoading: boolean;
}

export function useGenerate(): UseGenerateReturn {
    const navigate = useNavigate();
    const { setLoading, setDone, setError } = useGenerationContext();
    const [isLoading, setIsLoading] = useState(false);

    const generate = useCallback(
        async (req: GenerateRequest): Promise<void> => {
            setIsLoading(true);
            setLoading();
            void navigate("/result");

            try {
                const data = await post<GenerateResponse>("/generate", req);
                setDone(data);
            } catch (e) {
                if (e instanceof ApiError) {
                    setError(e.errorCode, e.message);
                } else {
                    setError("UNKNOWN_ERROR", "予期しないエラーが発生しました");
                }
            } finally {
                setIsLoading(false);
            }
        },
        [navigate, setLoading, setDone, setError]
    );

    return { generate, isLoading };
}
