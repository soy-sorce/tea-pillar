// src/components/experience/MeowSection.tsx
import { useEffect, useState } from "react";
import { Music } from "lucide-react";
import { SampleCard } from "./SampleCard";
import { MicButton } from "./MicButton";
import { MAX_RECORDING_SECONDS, useMicrophone } from "@/hooks/useMicrophone";
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
}: MeowSectionProps): React.JSX.Element {
    const [inputMode, setInputMode] = useState<"A" | "B">("A");
    const { isRecording, audioBase64, startRecording, stopRecording, error } = useMicrophone();

    const handleMicStart = async (): Promise<void> => {
        await startRecording();
    };

    if (audioBase64 && audioBase64 !== selectedAudioBase64 && inputMode === "B") {
        onAudioCapture(audioBase64);
    }

    useEffect(() => {
        if (!error) {
            return;
        }

        if (error.includes("最大")) {
            onToast(`録音は最大${MAX_RECORDING_SECONDS}秒です`, "info");
            return;
        }

        onToast("マイクが使用できませんでした。サンプル選択に切り替えます", "error");
        setInputMode("A");
    }, [error, onToast]);

    return (
        <section aria-labelledby="meow-section-title">
            <div className="mb-4 flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-light">
                    <Music size={16} className="text-accent" />
                </div>
                <h2 id="meow-section-title" className="font-semibold text-text-primary">
                    鳴き声を選ぶ
                </h2>
            </div>

            <p className="mb-4 text-sm leading-6 text-text-secondary sm:text-[15px]">
                音声を選択するか、ご自身で猫の鳴きまねを録音することで、独自AIモデルが感情や状態のヒントを分析し、
                動画生成に役立てます。
            </p>

            <div className="grid grid-cols-3 gap-3 mb-4">
                {MEOW_SAMPLES.map((sample) => (
                    <SampleCard
                        key={sample.id}
                        emoji={sample.emoji}
                        label={sample.label}
                        selected={inputMode === "A" && selected?.id === sample.id}
                        onClick={() => { setInputMode("A"); onSelect(sample); }}
                    />
                ))}
            </div>

            <div className="flex items-center gap-3">
                <div className="h-px flex-1 bg-border" />
                <span className="text-xs text-text-muted">または</span>
                <div className="h-px flex-1 bg-border" />
            </div>

            <div className="mt-3 flex items-center gap-3">
                <MicButton
                    isRecording={isRecording}
                    onStart={() => void handleMicStart()}
                    onStop={stopRecording}
                />
                {inputMode === "B" && audioBase64 && (
                    <span className="flex items-center gap-1 text-xs text-accent font-semibold">
                        ✓ 録音済み
                    </span>
                )}
            </div>
            <p className="mt-2 text-xs text-text-muted">
                録音は最大{MAX_RECORDING_SECONDS}秒です
            </p>
        </section>
    );
}
