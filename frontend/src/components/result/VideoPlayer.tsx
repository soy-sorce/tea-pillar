// src/components/result/VideoPlayer.tsx
import { useRef, useState } from "react";

interface VideoPlayerProps {
    src: string;
}

export function VideoPlayer({ src }: VideoPlayerProps): JSX.Element {
    const videoRef = useRef<HTMLVideoElement>(null);
    const [isMuted, setIsMuted] = useState(true);

    const toggleMute = (): void => {
        if (videoRef.current) {
            videoRef.current.muted = !videoRef.current.muted;
            setIsMuted(videoRef.current.muted);
        }
    };

    return (
        <div className="relative rounded-card overflow-hidden shadow-card">
            <video
                ref={videoRef}
                src={src}
                autoPlay
                loop
                muted={isMuted}
                playsInline
                className="w-full"
                aria-label="生成された動画"
            />
            <button
                onClick={toggleMute}
                className="absolute bottom-3 right-3 flex h-9 w-9 items-center justify-center rounded-full bg-black/50 text-white hover:bg-black/70 transition-colors"
                aria-label={isMuted ? "音量オン" : "音量オフ"}
            >
                {isMuted ? "🔇" : "🔊"}
            </button>
        </div>
    );
}
