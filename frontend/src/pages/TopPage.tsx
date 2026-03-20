// src/pages/TopPage.tsx
import { useNavigate } from "react-router-dom";
import { Sparkles, Video, ChevronRight } from "lucide-react";
import { useGenerationContext } from "@/contexts/GenerationContext";

interface ModeCardProps {
    id: string;
    icon: React.ReactNode;
    title: string;
    description: string;
    tag: string;
    onClick: () => void;
    variant: "primary" | "secondary";
}

function ModeCard({ id, icon, title, description, tag, onClick, variant }: ModeCardProps): React.JSX.Element {
    const isP = variant === "primary";
    return (
        <button
            id={id}
            onClick={onClick}
            className={[
                "group relative flex flex-col items-start gap-4 rounded-card-xl p-7 text-left",
                "border transition-all duration-300",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
                "hover:scale-[1.02] hover:shadow-card-hover",
                isP
                    ? "bg-gradient-btn border-transparent text-white shadow-btn-primary"
                    : "bg-surface border-border text-text-primary shadow-card hover:border-accent",
            ].join(" ")}
        >
            {/* タグ */}
            <span
                className={[
                    "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold",
                    isP ? "bg-white/20 text-white" : "bg-accent-light text-accent",
                ].join(" ")}
            >
                {tag}
            </span>

            {/* アイコン */}
            <div
                className={[
                    "flex h-14 w-14 items-center justify-center rounded-2xl",
                    isP ? "bg-white/20" : "bg-accent-light",
                ].join(" ")}
            >
                <span className={isP ? "text-white" : "text-accent"}>{icon}</span>
            </div>

            {/* テキスト */}
            <div className="space-y-1.5">
                <h2 className={["text-xl font-bold", isP ? "text-white" : "text-text-primary"].join(" ")}>
                    {title}
                </h2>
                <p className={["text-sm leading-relaxed", isP ? "text-white/80" : "text-text-secondary"].join(" ")}>
                    {description}
                </p>
            </div>

            {/* 矢印 */}
            <ChevronRight
                size={20}
                className={[
                    "absolute right-6 top-1/2 -translate-y-1/2 transition-transform duration-200 group-hover:translate-x-1",
                    isP ? "text-white/70" : "text-text-muted",
                ].join(" ")}
            />
        </button>
    );
}

export function TopPage(): React.JSX.Element {
    const navigate = useNavigate();
    const { reset } = useGenerationContext();

    const handleMode = (mode: "experience" | "production"): void => {
        reset();
        void navigate(`/${mode}`);
    };

    return (
        <div className="relative min-h-[calc(100vh-64px)] bg-gradient-hero">
            {/* 背景装飾 */}
            <div className="pointer-events-none absolute inset-0 overflow-hidden">
                <div className="absolute -top-20 left-1/2 h-96 w-96 -translate-x-1/2 rounded-full bg-accent/10 blur-3xl" />
            </div>

            <div className="relative mx-auto flex max-w-3xl flex-col items-center gap-14 px-5 py-20">
                {/* ヒーロー */}
                <div className="animate-slideUp text-center">
                    <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent-light px-4 py-1.5 text-sm font-medium text-accent">
                        <Sparkles size={14} />
                        AIが猫のための動画を生成します
                    </div>
                    <h1 className="text-5xl font-black tracking-tight text-text-primary sm:text-6xl">
                        neko<span className="text-gradient">flix</span>
                    </h1>
                    <p className="mt-4 text-lg text-text-secondary">
                        猫の鳴き声・表情・性格から、最高の動画を。
                    </p>
                </div>

                {/* モード選択カード */}
                <div className="grid w-full grid-cols-1 gap-5 sm:grid-cols-2 animate-slideUp delay-150">
                    <ModeCard
                        id="btn-experience-mode"
                        icon={<span className="text-3xl">🐾</span>}
                        title="体験モード"
                        description="あなたが猫になって、サンプル鳴き声・表情を選ぶだけで試せます。"
                        tag="おすすめ"
                        onClick={() => handleMode("experience")}
                        variant="primary"
                    />
                    <ModeCard
                        id="btn-production-mode"
                        icon={<Video size={28} />}
                        title="本番モード"
                        description="実際の猫の音声・画像ファイルをアップロードして動画を生成します。"
                        tag="ファイルアップロード"
                        onClick={() => handleMode("production")}
                        variant="secondary"
                    />
                </div>

                {/* フッター */}
                <p className="animate-fadeIn delay-300 text-xs text-text-muted">
                    Powered by{" "}
                    <span className="font-semibold text-text-secondary">Veo3</span>
                    {" × "}
                    <span className="font-semibold text-text-secondary">Gemini</span>
                    {" × "}
                    <span className="font-semibold text-text-secondary">Vertex AI</span>
                </p>
            </div>
        </div>
    );
}
