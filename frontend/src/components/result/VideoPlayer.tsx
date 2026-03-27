// src/components/result/VideoPlayer.tsx
import { useRef, useState } from "react";
import { Volume2, VolumeX } from "lucide-react";

interface VideoPlayerProps {
    src: string;
    loop?: boolean;
    onPlay?: () => void;
}

export function VideoPlayer({
    src,
    loop = true,
    onPlay,
}: VideoPlayerProps): React.JSX.Element {
    const videoRef = useRef<HTMLVideoElement>(null);
    const [isMuted, setIsMuted] = useState(true);

    const toggleMute = (): void => {
        if (videoRef.current) {
            videoRef.current.muted = !videoRef.current.muted;
            setIsMuted(videoRef.current.muted);
        }
    };

    return (
        <div className="relative overflow-hidden rounded-card-xl shadow-2xl ring-1 ring-border animate-slideUp">
            <video
                ref={videoRef}
                src={src}
                autoPlay
                loop={loop}
                muted={isMuted}
                playsInline
                onPlay={onPlay}
                className="w-full"
                aria-label="生成された動画"
            />

            {/* ミュートボタン */}
            <button
                onClick={toggleMute}
                className={[
                    "absolute bottom-4 right-4 flex h-9 w-9 items-center justify-center rounded-full",
                    "text-white transition-all duration-200 hover:scale-110",
                    isMuted ? "bg-black/40 hover:bg-black/60" : "bg-accent/80 hover:bg-accent",
                ].join(" ")}
                aria-label={isMuted ? "音量オン" : "音量オフ"}
            >
                {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
            </button>
        </div>
    );
}
