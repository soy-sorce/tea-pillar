// src/contexts/GenerationContext.tsx
/* eslint-disable react-refresh/only-export-components */
import {
    createContext,
    useCallback,
    useContext,
    useMemo,
    useState,
    type ReactNode,
} from "react";
import type { GenerateRequest, GenerateResponse } from "@/types/api";
import type { ResultState } from "@/types/app";

interface GenerationContextValue {
    input: GenerateRequest | null;
    response: GenerateResponse | null;
    resultState: ResultState; // "idle" | "loading" | "done" | "error"
    errorCode: string | null;
    errorMessage: string | null;
    setInput: (input: GenerateRequest) => void;
    setLoading: () => void;
    setDone: (response: GenerateResponse) => void;
    setError: (code: string, message: string) => void;
    reset: () => void;
}

const GenerationContext = createContext<GenerationContextValue | null>(null);

export function GenerationContextProvider({
    children,
}: {
    children: ReactNode;
}): React.JSX.Element {
    const [input, setInputState] = useState<GenerateRequest | null>(null);
    const [response, setResponse] = useState<GenerateResponse | null>(null);
    const [resultState, setResultState] = useState<ResultState>("idle");
    const [errorCode, setErrorCode] = useState<string | null>(null);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    const setInput = useCallback((v: GenerateRequest) => setInputState(v), []);
    const setLoading = useCallback(() => {
        setResultState("loading");
        setErrorCode(null);
        setErrorMessage(null);
    }, []);
    const setDone = useCallback((res: GenerateResponse) => {
        setResponse(res);
        setResultState("done");
    }, []);
    const setError = useCallback((code: string, message: string) => {
        setErrorCode(code);
        setErrorMessage(message);
        setResultState("error");
    }, []);
    const reset = useCallback(() => {
        setInputState(null);
        setResponse(null);
        setResultState("idle");
        setErrorCode(null);
        setErrorMessage(null);
    }, []);

    const value = useMemo(
        () => ({
            input,
            response,
            resultState,
            errorCode,
            errorMessage,
            setInput,
            setLoading,
            setDone,
            setError,
            reset,
        }),
        [
            input,
            response,
            resultState,
            errorCode,
            errorMessage,
            setInput,
            setLoading,
            setDone,
            setError,
            reset,
        ]
    );

    return (
        <GenerationContext.Provider value={value}>
            {children}
        </GenerationContext.Provider>
    );
}

export function useGenerationContext(): GenerationContextValue {
    const ctx = useContext(GenerationContext);
    if (!ctx)
        throw new Error(
            "useGenerationContext must be inside GenerationContextProvider"
        );
    return ctx;
}
