// src/pages/TopPage.tsx
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/Button";
import { useGenerationContext } from "@/contexts/GenerationContext";

export function TopPage(): JSX.Element {
    const navigate = useNavigate();
    const { reset } = useGenerationContext();

    const handleMode = (mode: "experience" | "production"): void => {
        reset();
        void navigate(`/${mode}`);
    };

    return (
        <div className="flex min-h-[80vh] flex-col items-center justify-center gap-10 px-4">
            <div className="text-center">
                <h1 className="text-3xl font-semibold text-text-primary">
                    🐱 nekkoflix
                </h1>
                <p className="mt-2 text-lg text-text-secondary">猫に、最高の動画を。</p>
            </div>

            <div className="flex w-full max-w-sm flex-col gap-4">
                <Button
                    id="btn-experience-mode"
                    variant="primary"
                    size="lg"
                    className="w-full"
                    onClick={() => handleMode("experience")}
                >
                    🐾 体験モード（あなたが猫になる）
                </Button>
                <Button
                    id="btn-production-mode"
                    variant="secondary"
                    size="lg"
                    className="w-full"
                    onClick={() => handleMode("production")}
                >
                    📹 本番モード（実際の猫データ）
                </Button>
            </div>
        </div>
    );
}
