export const MAX_IMAGE_UPLOAD_BYTES = 7 * 1024 * 1024;
export const MAX_AUDIO_UPLOAD_BYTES = 8 * 1024 * 1024;

function formatSize(bytes: number): string {
    const megabytes = bytes / (1024 * 1024);
    return `${megabytes.toFixed(0)}MB`;
}

export const MAX_IMAGE_UPLOAD_LABEL = formatSize(MAX_IMAGE_UPLOAD_BYTES);
export const MAX_AUDIO_UPLOAD_LABEL = formatSize(MAX_AUDIO_UPLOAD_BYTES);
