import { useRef, useState } from "react";
import { Upload, Music, ImageIcon, FileText, Wand2, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useGenerate } from "@/hooks/useGenerate";
import { fileToBase64 } from "@/lib/imageUtils";
import { blobToBase64 } from "@/lib/audioUtils";
import {
    MAX_AUDIO_UPLOAD_BYTES,
    MAX_AUDIO_UPLOAD_LABEL,
    MAX_IMAGE_UPLOAD_BYTES,
    MAX_IMAGE_UPLOAD_LABEL,
} from "@/lib/uploadLimits";
import { MAX_RECORDING_SECONDS } from "@/hooks/useMicrophone";

interface DropZoneProps {
    label: string;
    sublabel?: string;
    required?: boolean;
    file: File | null;
    accept: string;
    icon: React.ReactNode;
    onFile: (file: File) => void;
    inputRef: React.RefObject<HTMLInputElement | null>;
    errorMessage?: string | null;
}

function DropZone({
    label,
    sublabel,
    required,
    file,
    accept,
    icon,
    onFile,
    inputRef,
    errorMessage,
}: DropZoneProps): React.JSX.Element {
    const [isDragging, setIsDragging] = useState(false);

    return (
        <div>
            <div className="mb-2 flex items-center gap-1.5">
                <span className="text-sm font-semibold text-text-primary">{label}</span>
                {required ? (
                    <span className="rounded-full bg-red-50 px-2 py-0.5 text-xs font-medium text-red-500">必須</span>
                ) : (
                    <span className="rounded-full bg-surface-alt px-2 py-0.5 text-xs text-text-muted">任意</span>
                )}
            </div>

            <div
                className={[
                    "relative flex min-h-[120px] cursor-pointer flex-col items-center justify-center gap-3 rounded-card-lg border-2 border-dashed p-6 text-center transition-all duration-200",
                    file
                        ? "border-accent bg-accent-light"
                        : isDragging
                            ? "border-accent bg-accent-light scale-[1.01]"
                            : "border-border bg-surface hover:border-accent hover:bg-accent-light/50",
                ].join(" ")}
                onClick={() => inputRef.current?.click()}
                onDragOver={(e) => {
                    e.preventDefault();
                    setIsDragging(true);
                }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={(e) => {
                    e.preventDefault();
                    setIsDragging(false);
                    const droppedFile = e.dataTransfer.files[0];
                    if (droppedFile) onFile(droppedFile);
                }}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                    if (e.key === "Enter") inputRef.current?.click();
                }}
            >
                {file ? (
                    <>
                        <CheckCircle2 size={32} className="text-accent" />
                        <span className="text-sm font-medium text-accent">{file.name}</span>
                        <span className="text-xs text-text-muted">クリックして変更</span>
                    </>
                ) : (
                    <>
                        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-surface-alt text-text-muted">
                            {icon}
                        </div>
                        <div>
                            <span className="text-sm font-medium text-text-secondary">ファイルを選択またはドロップ</span>
                            {sublabel && <p className="mt-0.5 text-xs text-text-muted">{sublabel}</p>}
                        </div>
                        <Upload size={14} className="text-text-muted" />
                    </>
                )}
            </div>

            <input
                ref={inputRef}
                type="file"
                accept={accept}
                className="hidden"
                onChange={(e) => {
                    const selectedFile = e.target.files?.[0];
                    if (selectedFile) onFile(selectedFile);
                }}
            />
            {errorMessage && <p className="mt-2 text-xs text-red-500">{errorMessage}</p>}
        </div>
    );
}

function validateFileSize(file: File, maxBytes: number, label: string): string | null {
    if (file.size <= maxBytes) {
        return null;
    }
    return `${label}は${(maxBytes / (1024 * 1024)).toFixed(0)}MB以下のファイルを選択してください`;
}

async function validateAudioDuration(file: File): Promise<string | null> {
    const objectUrl = URL.createObjectURL(file);

    try {
        const duration = await new Promise<number>((resolve, reject) => {
            const audio = document.createElement("audio");

            audio.preload = "metadata";
            audio.onloadedmetadata = () => resolve(audio.duration);
            audio.onerror = () => reject(new Error("audio metadata load failed"));
            audio.src = objectUrl;
        });

        if (!Number.isFinite(duration)) {
            return "鳴き声ファイルの長さを確認できませんでした";
        }

        if (duration > MAX_RECORDING_SECONDS) {
            return `鳴き声ファイルは${MAX_RECORDING_SECONDS}秒以下にしてください`;
        }

        return null;
    } catch {
        return "鳴き声ファイルの読み込みに失敗しました";
    } finally {
        URL.revokeObjectURL(objectUrl);
    }
}

export function ProductionForm(): React.JSX.Element {
    const { generate, isLoading } = useGenerate();
    const [audioFile, setAudioFile] = useState<File | null>(null);
    const [imageFile, setImageFile] = useState<File | null>(null);
    const [audioError, setAudioError] = useState<string | null>(null);
    const [imageError, setImageError] = useState<string | null>(null);
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

    const handleAudioFile = async (file: File): Promise<void> => {
        const error = validateFileSize(file, MAX_AUDIO_UPLOAD_BYTES, "鳴き声ファイル");
        if (error) {
            setAudioFile(null);
            setAudioError(error);
            return;
        }

        const durationError = await validateAudioDuration(file);
        if (durationError) {
            setAudioFile(null);
            setAudioError(durationError);
            return;
        }

        setAudioError(null);
        setAudioFile(file);
    };

    const handleImageFile = (file: File): void => {
        const error = validateFileSize(file, MAX_IMAGE_UPLOAD_BYTES, "顔・全身写真");
        if (error) {
            setImageFile(null);
            setImageError(error);
            return;
        }

        setImageError(null);
        setImageFile(file);
    };

    return (
        <div className="space-y-5">
            <div className="space-y-6 rounded-card-lg border border-border bg-surface p-6 shadow-card">
                <DropZone
                    label="鳴き声ファイル"
                    sublabel={`.wav 形式 / ${MAX_AUDIO_UPLOAD_LABEL}以下 / 最大${MAX_RECORDING_SECONDS}秒`}
                    file={audioFile}
                    accept="audio/wav,.wav"
                    icon={<Music size={22} />}
                    onFile={(file) => {
                        void handleAudioFile(file);
                    }}
                    inputRef={audioInputRef}
                    errorMessage={audioError}
                />
                <div className="border-t border-border" />
                <DropZone
                    label="顔・全身写真"
                    sublabel={`.jpg / .png 形式 / ${MAX_IMAGE_UPLOAD_LABEL}以下`}
                    required
                    file={imageFile}
                    accept="image/jpeg,image/png,.jpg,.png"
                    icon={<ImageIcon size={22} />}
                    onFile={handleImageFile}
                    inputRef={imageInputRef}
                    errorMessage={imageError}
                />
            </div>

            <div className="rounded-card-lg border border-border bg-surface p-6 shadow-card">
                <div className="mb-3 flex items-center gap-2">
                    <FileText size={16} className="text-text-secondary" />
                    <label htmlFor="user-context-input" className="text-sm font-semibold text-text-primary">
                        猫の性格・好み
                    </label>
                    <span className="rounded-full bg-surface-alt px-2 py-0.5 text-xs text-text-muted">
                        任意・最大500文字
                    </span>
                </div>
                <textarea
                    id="user-context-input"
                    value={userContext}
                    onChange={(e) => setUserContext(e.target.value)}
                    maxLength={500}
                    rows={4}
                    placeholder="例：魚が好き、臆病な性格、外を眺めるのが趣味"
                    className="w-full resize-none rounded-card border border-border bg-surface-alt px-4 py-3 text-sm text-text-primary placeholder:text-text-muted transition-colors focus:border-accent focus:bg-surface focus:outline-none focus:ring-1 focus:ring-accent"
                />
                <p className="mt-1 text-right text-xs text-text-muted">{userContext.length} / 500</p>
            </div>

            <div className="rounded-card-lg border border-border bg-surface p-5 shadow-card">
                <Button
                    id="btn-generate-production"
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
                    <p className="mt-2 text-center text-xs text-text-muted">写真ファイルは必須です</p>
                )}
            </div>
        </div>
    );
}
