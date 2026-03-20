// src/components/experience/PhotoSection.tsx
import { useState } from "react";
import { SampleCard } from "./SampleCard";
import { Button } from "@/components/ui/Button";
import { useCamera } from "@/hooks/useCamera";
import { PHOTO_SAMPLES, type PhotoSample } from "@/types/app";

interface PhotoSectionProps {
    selected: PhotoSample | null;
    selectedImageBase64: string | null;
    onSelect: (sample: PhotoSample) => void;
    onImageCapture: (base64: string) => void;
    onToast: (message: string, type?: "info" | "error") => void;
}

export function PhotoSection({
    selected,
    selectedImageBase64,
    onSelect,
    onImageCapture,
    onToast,
}: PhotoSectionProps): JSX.Element {
    const [inputMode, setInputMode] = useState<"A" | "B">("A");
    const { imageBase64, capturePhoto, error } = useCamera();

    const handleCapture = async (): Promise<void> => {
        await capturePhoto();
        if (error) {
            onToast(
                "カメラが使用できませんでした。サンプル選択に切り替えます",
                "error"
            );
            setInputMode("A");
            return;
        }
        if (imageBase64) {
            setInputMode("B");
            onImageCapture(imageBase64);
        }
    };

    // カメラキャプチャ後のBase64を親へ渡す
    const prevBase64 = selectedImageBase64;
    if (imageBase64 && imageBase64 !== prevBase64 && inputMode === "B") {
        onImageCapture(imageBase64);
    }

    return (
        <section aria-labelledby="photo-section-title">
            <h2
                id="photo-section-title"
                className="mb-3 text-lg font-medium text-text-primary"
            >
                Step 2 📸 表情
            </h2>

            {/* サンプル選択カード（方法A） */}
            <div className="grid grid-cols-3 gap-3 mb-3">
                {PHOTO_SAMPLES.map((sample) => (
                    <SampleCard
                        key={sample.id}
                        emoji={sample.emoji}
                        label={sample.label}
                        selected={inputMode === "A" && selected?.id === sample.id}
                        onClick={() => {
                            setInputMode("A");
                            onSelect(sample);
                        }}
                    />
                ))}
            </div>

            {/* カメラボタン（方法B） */}
            <div className="flex items-center gap-3">
                <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => void handleCapture()}
                >
                    📷 カメラで撮影する
                </Button>
                {inputMode === "B" && imageBase64 && (
                    <span className="text-xs text-accent font-medium">✓ 撮影済み</span>
                )}
            </div>
        </section>
    );
}
