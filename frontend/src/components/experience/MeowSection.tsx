// src/components/experience/MeowSection.tsx
import { useState } from "react";
import { SampleCard } from "./SampleCard";
import { MicButton } from "./MicButton";
import { useMicrophone } from "@/hooks/useMicrophone";
import { MEOW_SAMPLES, type MeowSample } from "@/types/app";

interface MeowSectionProps {
    selected: MeowSample | null;
    selectedAudioBase64: string | null;
    onSelect: (sample: MeowSample) => void;
    onAudioCapture: (base64: string) => void;
    onToast: (message: string, type?: "info" | "error") => void;
}

export function MeowSection({
    selected,
    selectedAudioBase64,
    onSelect,
    onAudioCapture,
    onToast,
}: MeowSectionProps): JSX.Element {
    const [inputMode, setInputMode] = useState<"A" | "B">("A");
    const { isRecording, audioBase64, startRecording, stopRecording, error } =
        useMicrophone();

    // エラー発生時にAモードへフォールバック
    const handleMicStart = async (): Promise<void> => {
        await startRecording();
        if (error) {
            onToast(
                "マイクが使用できませんでした。サンプル選択に切り替えます",
                "error"
            );
            setInputMode("A");
        }
    };

    const handleMicStop = (): void => {
        stopRecording();
    };

    // 録音完了後にBase64を親へ渡す
    const prevBase64 = selectedAudioBase64;
    if (audioBase64 && audioBase64 !== prevBase64 && inputMode === "B") {
        onAudioCapture(audioBase64);
    }

    return (
        <section aria-labelledby="meow-section-title">
            <h2
                id="meow-section-title"
                className="mb-3 text-lg font-medium text-text-primary"
            >
                Step 1 🎵 鳴き声
            </h2>

            {/* サンプル選択カード（方法A） */}
            <div className="grid grid-cols-3 gap-3 mb-3">
                {MEOW_SAMPLES.map((sample) => (
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

            {/* マイクボタン（方法B） */}
            <div className="flex items-center gap-3">
                <MicButton
                    isRecording={isRecording}
                    onStart={handleMicStart}
                    onStop={handleMicStop}
                />
                {inputMode === "B" && audioBase64 && (
                    <span className="text-xs text-accent font-medium">✓ 録音済み</span>
                )}
            </div>
        </section>
    );
}
