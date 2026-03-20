// src/pages/ProductionPage.tsx
import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/Button";
import { PageHeader } from "@/components/layout/PageHeader";
import { useGenerate } from "@/hooks/useGenerate";
import { fileToBase64 } from "@/lib/imageUtils";
import { blobToBase64 } from "@/lib/audioUtils";

export function ProductionPage(): JSX.Element {
    const navigate = useNavigate();
    const { generate, isLoading } = useGenerate();

    const [audioFile, setAudioFile] = useState<File | null>(null);
    const [imageFile, setImageFile] = useState<File | null>(null);
    const [userContext, setUserContext] = useState("");

    const audioInputRef = useRef<HTMLInputElement>(null);
    const imageInputRef = useRef<HTMLInputElement>(null);

    const canSubmit = imageFile !== null;

    const handleSubmit = async (): Promise<void> => {
        if (!canSubmit || !imageFile) return;

        const imageBase64 = await fileToBase64(imageFile);
        const audioBase64 = audioFile ? await blobToBase64(audioFile) : undefined;

        await generate({
            mode: "production",
            image_base64: imageBase64,
            audio_base64: audioBase64,
            user_context: userContext.trim() || undefined,
        });
    };

    return (
        <div className="mx-auto max-w-2xl space-y-8 px-4 py-8">
            <PageHeader
                title="猫のデータを入力"
                onBack={() => void navigate("/")}
            />

            {/* 音声ファイルアップロード */}
            <section aria-labelledby="audio-upload-label">
                <label
                    id="audio-upload-label"
                    className="mb-2 block text-sm font-medium text-text-primary"
                >
                    🎵 鳴き声ファイル（.wav）
                    <span className="ml-1 text-xs text-text-muted">（任意）</span>
                </label>
                <div
                    className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-card border-2 border-dashed border-border p-6 text-center transition-colors hover:border-accent hover:bg-accent-light"
                    onClick={() => audioInputRef.current?.click()}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                        e.preventDefault();
                        const file = e.dataTransfer.files[0];
                        if (file?.type.includes("audio")) setAudioFile(file);
                    }}
                    role="button"
                    tabIndex={0}
                    aria-label="音声ファイルを選択またはドロップ"
                    onKeyDown={(e) => {
                        if (e.key === "Enter") audioInputRef.current?.click();
                    }}
                >
                    <span className="text-2xl">🎤</span>
                    <span className="text-sm text-text-secondary">
                        {audioFile ? audioFile.name : "ファイルを選択 or ドロップ"}
                    </span>
                    <span className="text-xs text-text-muted">.wav 形式</span>
                </div>
                <input
                    ref={audioInputRef}
                    type="file"
                    accept="audio/wav,.wav"
                    className="hidden"
                    onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) setAudioFile(file);
                    }}
                />
            </section>

            {/* 画像ファイルアップロード */}
            <section aria-labelledby="image-upload-label">
                <label
                    id="image-upload-label"
                    className="mb-2 block text-sm font-medium text-text-primary"
                >
                    📸 顔・全身写真（.jpg / .png）
                    <span className="ml-1 text-xs text-red-500">（必須）</span>
                </label>
                <div
                    className={[
                        "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-card border-2 border-dashed p-6 text-center transition-colors",
                        imageFile
                            ? "border-accent bg-accent-light"
                            : "border-border hover:border-accent hover:bg-accent-light",
                    ].join(" ")}
                    onClick={() => imageInputRef.current?.click()}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                        e.preventDefault();
                        const file = e.dataTransfer.files[0];
                        if (file?.type.startsWith("image/")) setImageFile(file);
                    }}
                    role="button"
                    tabIndex={0}
                    aria-label="画像ファイルを選択またはドロップ"
                    onKeyDown={(e) => {
                        if (e.key === "Enter") imageInputRef.current?.click();
                    }}
                >
                    <span className="text-2xl">{imageFile ? "✅" : "🖼️"}</span>
                    <span className="text-sm text-text-secondary">
                        {imageFile ? imageFile.name : "ファイルを選択 or ドロップ"}
                    </span>
                    <span className="text-xs text-text-muted">.jpg / .png 形式</span>
                </div>
                <input
                    ref={imageInputRef}
                    type="file"
                    accept="image/jpeg,image/png,.jpg,.png"
                    className="hidden"
                    onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) setImageFile(file);
                    }}
                />
            </section>

            {/* コンテキスト入力 */}
            <section aria-labelledby="context-label">
                <label
                    id="context-label"
                    htmlFor="user-context-input"
                    className="mb-2 block text-sm font-medium text-text-primary"
                >
                    🐱 猫の性格・好み
                    <span className="ml-1 text-xs text-text-muted">（任意・最大500文字）</span>
                </label>
                <textarea
                    id="user-context-input"
                    value={userContext}
                    onChange={(e) => setUserContext(e.target.value)}
                    maxLength={500}
                    rows={4}
                    placeholder="例：魚が好き、臆病な性格、外を眺めるのが趣味"
                    className="w-full rounded-card border border-border bg-surface-alt px-4 py-3 text-sm text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent resize-none"
                />
                <p className="mt-1 text-right text-xs text-text-muted">
                    {userContext.length}/500
                </p>
            </section>

            <Button
                id="btn-generate-production"
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
