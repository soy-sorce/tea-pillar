// src/hooks/useGenerate.ts
import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, generateVideo } from "@/lib/api";
import { useGenerationContext } from "@/contexts/GenerationContext";
import type { GenerateRequest } from "@/types/api";

interface UseGenerateReturn {
    generate: (req: GenerateRequest) => Promise<void>;
    isLoading: boolean;
}

export function useGenerate(): UseGenerateReturn {
    const navigate = useNavigate();
    const { setInput, setLoading, setDone, setError } = useGenerationContext();
    const [isLoading, setIsLoading] = useState(false);

    const generate = useCallback(
        async (req: GenerateRequest): Promise<void> => {
            setIsLoading(true);
            setInput(req);
            setLoading();
            void navigate("/result");

            try {
                const data = await generateVideo(req);
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
        [navigate, setInput, setLoading, setDone, setError]
    );

    return { generate, isLoading };
}
