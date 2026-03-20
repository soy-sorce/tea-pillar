// src/pages/ExperiencePage.tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Wand2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { PageHeader } from "@/components/layout/PageHeader";
import { MeowSection } from "@/components/experience/MeowSection";
import { PhotoSection } from "@/components/experience/PhotoSection";
import { ContextSection } from "@/components/experience/ContextSection";
import { useGenerate } from "@/hooks/useGenerate";
import { useToast } from "@/hooks/useToast";
import { audioUrlToBase64 } from "@/lib/audioUtils";
import { urlToBase64 } from "@/lib/imageUtils";
import type { MeowSample, PhotoSample } from "@/types/app";

interface StepCardProps {
    step: number;
    children: React.ReactNode;
}

function StepCard({ step, children }: StepCardProps): React.JSX.Element {
    return (
        <div className="relative rounded-card-lg border border-border bg-surface p-6 shadow-card">
            {/* ステップバッジ */}
            <div className="absolute -top-3.5 left-6">
                <span className="inline-flex items-center rounded-full bg-gradient-btn px-3 py-1 text-xs font-bold text-white shadow-btn-primary">
                    STEP {step}
                </span>
            </div>
            <div className="mt-3">{children}</div>
        </div>
    );
}

export function ExperiencePage(): React.JSX.Element {
    const navigate = useNavigate();
    const { generate, isLoading } = useGenerate();
    const { showToast } = useToast();

    // Step1: 鳴き声（サンプル選択 or マイク録音）
    const [selectedMeow, setSelectedMeow] = useState<MeowSample | null>(null);
    const [capturedAudioBase64, setCapturedAudioBase64] = useState<string | null>(null);

    // Step2: 写真（3択サンプル画像から選択）
    const [selectedPhoto, setSelectedPhoto] = useState<PhotoSample | null>(null);

    // Step3: 性格・好み（フリーテキスト）
    const [userContext, setUserContext] = useState("");

    const hasAudio = capturedAudioBase64 !== null || selectedMeow !== null;
    const hasImage = selectedPhoto !== null;
    const canSubmit = hasAudio && hasImage;

    const handleSubmit = async (): Promise<void> => {
        if (!canSubmit) return;

        let audioBase64: string | undefined;
        if (capturedAudioBase64) {
            audioBase64 = capturedAudioBase64;
        } else if (selectedMeow) {
            audioBase64 = await audioUrlToBase64(selectedMeow.url);
        }

        let imageBase64: string;
        if (selectedPhoto) {
            imageBase64 = await urlToBase64(selectedPhoto.url);
        } else {
            return;
        }

        await generate({
            mode: "experience",
            image_base64: imageBase64,
            audio_base64: audioBase64,
            user_context: userContext.trim() || undefined,
        });
    };

    return (
        <div className="mx-auto max-w-2xl py-6">
            <div className="px-4">
                <PageHeader
                    title="あなたが猫になる"
                    subtitle="3ステップで猫の動画を生成します"
                    onBack={() => void navigate("/")}
                />
            </div>

            <div className="mt-6 space-y-6 px-4 pb-36">
                <StepCard step={1}>
                    <MeowSection
                        selected={selectedMeow}
                        selectedAudioBase64={capturedAudioBase64}
                        onSelect={setSelectedMeow}
                        onAudioCapture={setCapturedAudioBase64}
                        onToast={showToast}
                    />
                </StepCard>

                <StepCard step={2}>
                    <PhotoSection
                        selected={selectedPhoto}
                        onSelect={setSelectedPhoto}
                    />
                </StepCard>

                <StepCard step={3}>
                    <ContextSection
                        value={userContext}
                        onChange={setUserContext}
                    />
                </StepCard>
            </div>

            {/* スティッキー生成ボタン */}
            <div className="fixed bottom-0 left-0 right-0 z-30 border-t border-border/60 bg-surface/90 px-4 py-4 backdrop-blur-md">
                <div className="mx-auto max-w-2xl">
                    <Button
                        id="btn-generate-experience"
                        variant="primary"
                        size="lg"
                        disabled={!canSubmit || isLoading}
                        onClick={() => void handleSubmit()}
                        className="w-full"
                        leftIcon={<Wand2 size={18} />}
                    >
                        {isLoading ? "AIが生成しています..." : "動画を生成する"}
                    </Button>
                    {!canSubmit && (
                        <p className="mt-2 text-center text-xs text-text-muted">
                            鳴き声と写真を選択するとボタンが有効になります
                        </p>
                    )}
                </div>
            </div>
        </div>
    );
}
