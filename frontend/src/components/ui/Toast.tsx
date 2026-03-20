// src/components/ui/Toast.tsx
interface ToastProps {
    message: string;
    type?: "info" | "error";
    onClose: () => void;
}

export function Toast({
    message,
    type = "info",
    onClose,
}: ToastProps): JSX.Element {
    const bg =
        type === "error"
            ? "bg-red-50 border-red-200 text-red-700"
            : "bg-accent-light border-accent text-accent-dark";
    return (
        <div
            className={`flex items-center gap-3 rounded-card border px-4 py-3 shadow-card ${bg}`}
        >
            <span className="flex-1 text-sm">{message}</span>
            <button onClick={onClose} className="text-xs opacity-60 hover:opacity-100">
                ✕
            </button>
        </div>
    );
}
