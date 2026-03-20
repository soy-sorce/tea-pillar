// src/hooks/useToast.ts
import { useCallback, useState } from "react";

interface Toast {
    id: string;
    message: string;
    type: "info" | "error";
}

interface UseToastReturn {
    toasts: Toast[];
    showToast: (message: string, type?: "info" | "error") => void;
    removeToast: (id: string) => void;
}

export function useToast(): UseToastReturn {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const showToast = useCallback(
        (message: string, type: "info" | "error" = "info"): void => {
            const id = crypto.randomUUID();
            setToasts((prev) => [...prev, { id, message, type }]);
            setTimeout(() => {
                setToasts((prev) => prev.filter((t) => t.id !== id));
            }, 4000);
        },
        []
    );

    const removeToast = useCallback((id: string): void => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    }, []);

    return { toasts, showToast, removeToast };
}
