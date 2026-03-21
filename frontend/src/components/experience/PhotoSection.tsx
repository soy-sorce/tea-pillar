// src/components/experience/PhotoSection.tsx
import { ImageIcon } from "lucide-react";
import { SampleCard } from "./SampleCard";
import { PHOTO_SAMPLES, type PhotoSample } from "@/types/app";

interface PhotoSectionProps {
    selected: PhotoSample | null;
    onSelect: (sample: PhotoSample) => void;
}

export function PhotoSection({
    selected,
    onSelect,
}: PhotoSectionProps): React.JSX.Element {
    return (
        <section aria-labelledby="photo-section-title">
            <div className="mb-4 flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-light">
                    <ImageIcon size={16} className="text-accent" />
                </div>
                <h2 id="photo-section-title" className="font-semibold text-text-primary">
                    写真を選ぶ
                </h2>
            </div>

            <p className="mb-4 text-sm leading-6 text-text-secondary sm:text-[15px]">
                猫の表情や見た目がわかる写真を1枚選ぶことで、見た目の特徴を生成内容に反映しやすくします。
            </p>

            <div className="grid grid-cols-3 gap-3">
                {PHOTO_SAMPLES.map((sample) => (
                    <SampleCard
                        key={sample.id}
                        label={sample.label}
                        imageUrl={sample.imageUrl}
                        selected={selected?.id === sample.id}
                        onClick={() => onSelect(sample)}
                    />
                ))}
            </div>
        </section>
    );
}
