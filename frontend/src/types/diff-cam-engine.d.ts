declare module "diff-cam-engine" {
    interface MotionPayload {
        score?: number;
        hasMotion?: boolean;
    }

    interface DiffCamEngineOptions {
        video: HTMLVideoElement;
        stream?: MediaStream;
        captureIntervalTime?: number;
        captureWidth?: number;
        captureHeight?: number;
        diffWidth?: number;
        diffHeight?: number;
        pixelDiffThreshold?: number;
        scoreThreshold?: number;
        includeMotionBox?: boolean;
        includeMotionPixels?: boolean;
        initSuccessCallback?: () => void;
        initErrorCallback?: () => void;
        startCompleteCallback?: () => void;
        captureCallback?: (payload: MotionPayload) => void;
    }

    interface DiffCamEngineModule {
        init: (options: DiffCamEngineOptions) => void;
        start: () => void;
        stop: () => void;
    }

    const DiffCamEngine: DiffCamEngineModule;
    export default DiffCamEngine;
}
