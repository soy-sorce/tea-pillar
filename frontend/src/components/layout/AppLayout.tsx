// src/components/layout/AppLayout.tsx
import { Outlet } from "react-router-dom";
import { useToast } from "@/hooks/useToast";
import { Toast } from "@/components/ui/Toast";

export function AppLayout(): JSX.Element {
    const { toasts, removeToast } = useToast();

    return (
        <div className="min-h-screen bg-bg font-sans text-text-primary">
            <main className="mx-auto max-w-2xl">
                <Outlet />
            </main>

            {/* トースト通知エリア */}
            <div className="fixed bottom-4 left-1/2 -translate-x-1/2 w-full max-w-sm space-y-2 px-4 z-50">
                {toasts.map((t) => (
                    <Toast
                        key={t.id}
                        message={t.message}
                        type={t.type}
                        onClose={() => removeToast(t.id)}
                    />
                ))}
            </div>
        </div>
    );
}
