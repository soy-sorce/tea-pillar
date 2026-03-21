import { useState } from "react";
import { Wand2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { MeowSection } from "@/components/experience/MeowSection";
import { PhotoSection } from "@/components/experience/PhotoSection";
import { ContextSection } from "@/components/experience/ContextSection";
import { useGenerate } from "@/hooks/useGenerate";
import { useToast } from "@/hooks/useToast";
import { urlToBase64 } from "@/lib/imageUtils";
import type { MeowSample, PhotoSample } from "@/types/app";

interface StepCardProps {
    step: number;
    children: React.ReactNode;
}

function StepCard({ step, children }: StepCardProps): React.JSX.Element {
    return (
        <div className="relative rounded-card-lg border border-border bg-surface p-6 shadow-card">
            <div className="absolute -top-3.5 left-6">
                <span className="inline-flex items-center rounded-full bg-gradient-btn px-3 py-1 text-xs font-bold text-white shadow-btn-primary">
                    STEP {step}
                </span>
            </div>
            <div className="mt-3">{children}</div>
        </div>
    );
}

export function ExperienceForm(): React.JSX.Element {
    const { generate, isLoading } = useGenerate();
    const { showToast } = useToast();

    const [selectedMeow, setSelectedMeow] = useState<MeowSample | null>(null);
    const [capturedAudioBase64, setCapturedAudioBase64] = useState<string | null>(null);
    const [selectedPhoto, setSelectedPhoto] = useState<PhotoSample | null>(null);
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
            // Temporary fallback: sample audio assets are not deployed yet, and the current
            // /samples/audio/*.wav URLs can resolve to index.html. Until real wav files are
            // added under frontend/public/samples/audio/, keep sample selection enabled in
            // experience mode but send no audio payload to the backend/model.
            //
            // Follow-up: once the wav files exist, replace this branch by sending a
            // pre-converted base64 string for each sample, instead of fetching the asset
            // during submit time.
            audioBase64 = undefined;
        }

        if (!selectedPhoto) return;
        const imageBase64 = await urlToBase64(selectedPhoto.url);

        await generate({
            mode: "experience",
            image_base64: imageBase64,
            audio_base64: audioBase64,
            user_context: userContext.trim() || undefined,
        });
    };

    return (
        <div className="space-y-6">
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
                <PhotoSection selected={selectedPhoto} onSelect={setSelectedPhoto} />
            </StepCard>

            <StepCard step={3}>
                <ContextSection value={userContext} onChange={setUserContext} />
            </StepCard>

            <div className="rounded-card-lg border border-border bg-surface p-5 shadow-card">
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
    );
}
