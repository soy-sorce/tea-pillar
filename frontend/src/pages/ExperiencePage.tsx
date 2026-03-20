// src/pages/ExperiencePage.tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/Button";
import { PageHeader } from "@/components/layout/PageHeader";
import { MeowSection } from "@/components/experience/MeowSection";
import { PhotoSection } from "@/components/experience/PhotoSection";
import { ContextSection } from "@/components/experience/ContextSection";
import { useGenerate } from "@/hooks/useGenerate";
import { useToast } from "@/hooks/useToast";
import { audioUrlToBase64 } from "@/lib/audioUtils";
import { urlToBase64 } from "@/lib/imageUtils";
import type { MeowSample, PersonalityType, PhotoSample } from "@/types/app";

export function ExperiencePage(): JSX.Element {
    const navigate = useNavigate();
    const { generate, isLoading } = useGenerate();
    const { showToast } = useToast();

    // サンプル選択状態（方法A）
    const [selectedMeow, setSelectedMeow] = useState<MeowSample | null>(null);
    const [selectedPhoto, setSelectedPhoto] = useState<PhotoSample | null>(null);
    const [selectedPersonality, setSelectedPersonality] =
        useState<PersonalityType | null>(null);

    // デバイス入力状態（方法B）
    const [capturedAudioBase64, setCapturedAudioBase64] = useState<string | null>(
        null
    );
    const [capturedImageBase64, setCapturedImageBase64] = useState<string | null>(
        null
    );

    // Step1/2 どちらかが揃っていれば送信可能
    const hasAudio = capturedAudioBase64 !== null || selectedMeow !== null;
    const hasImage = capturedImageBase64 !== null || selectedPhoto !== null;
    const canSubmit = hasAudio && hasImage;

    const handleSubmit = async (): Promise<void> => {
        if (!canSubmit) return;

        // Base64を解決
        let audioBase64: string | undefined;
        if (capturedAudioBase64) {
            audioBase64 = capturedAudioBase64;
        } else if (selectedMeow) {
            audioBase64 = await audioUrlToBase64(selectedMeow.url);
        }

        let imageBase64: string;
        if (capturedImageBase64) {
            imageBase64 = capturedImageBase64;
        } else if (selectedPhoto) {
            imageBase64 = await urlToBase64(selectedPhoto.url);
        } else {
            return;
        }

        // user_contextにPersonalityTypeをそのまま渡す
        await generate({
            mode: "experience",
            image_base64: imageBase64,
            audio_base64: audioBase64,
            user_context: selectedPersonality ?? undefined,
        });
    };

    return (
        <div className="mx-auto max-w-2xl space-y-10 px-4 py-8">
            <PageHeader
                title="あなたが猫になる"
                onBack={() => void navigate("/")}
            />

            <MeowSection
                selected={selectedMeow}
                selectedAudioBase64={capturedAudioBase64}
                onSelect={setSelectedMeow}
                onAudioCapture={setCapturedAudioBase64}
                onToast={showToast}
            />

            <hr className="border-border" />

            <PhotoSection
                selected={selectedPhoto}
                selectedImageBase64={capturedImageBase64}
                onSelect={setSelectedPhoto}
                onImageCapture={setCapturedImageBase64}
                onToast={showToast}
            />

            <hr className="border-border" />

            <ContextSection
                selected={selectedPersonality}
                onSelect={setSelectedPersonality}
            />

            <Button
                id="btn-generate-experience"
                variant="primary"
                size="lg"
                disabled={!canSubmit || isLoading}
                onClick={() => void handleSubmit()}
                className="w-full"
            >
                {isLoading ? "生成中..." : "🎬 動画を生成する"}
            </Button>
        </div>
    );
}
