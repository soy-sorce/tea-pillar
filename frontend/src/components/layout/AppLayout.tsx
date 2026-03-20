// src/components/layout/AppLayout.tsx
import { Outlet, Link } from "react-router-dom";
import { useToast } from "@/hooks/useToast";
import { Toast } from "@/components/ui/Toast";

export function AppLayout(): React.JSX.Element {
    const { toasts, removeToast } = useToast();

    return (
        <div className="min-h-screen bg-bg font-sans text-text-primary">
            {/* ナビバー */}
            <header className="sticky top-0 z-40 border-b border-border/60 bg-surface/80 backdrop-blur-md">
                <div className="mx-auto flex max-w-5xl items-center justify-between px-5 py-3">
                    <Link
                        to="/"
                        className="flex items-center gap-2 text-lg font-bold text-text-primary hover:text-accent transition-colors"
                    >
                        <span className="text-2xl">🐱</span>
                        <span>nekkoflix</span>
                    </Link>
                    <p className="hidden sm:block text-xs text-text-muted">
                        Powered by Veo3 × Gemini
                    </p>
                </div>
            </header>

            <main className="mx-auto max-w-5xl px-4 sm:px-6">
                <Outlet />
            </main>

            {/* トースト通知エリア */}
            <div className="fixed bottom-6 left-1/2 -translate-x-1/2 w-full max-w-sm space-y-2 px-4 z-50">
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
