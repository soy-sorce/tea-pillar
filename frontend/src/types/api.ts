export interface GenerateRequest {
    mode: "experience" | "production";
    image_base64: string;
    audio_base64?: string;
    user_context?: string;
}

export interface GenerateResponse {
    session_id: string;
    video_url: string;
    state_key: string;
    template_id: string;
    template_name: string;
}

export interface ReactionUploadUrlResponse {
    session_id: string;
    upload_url: string;
    reaction_video_gcs_uri: string;
    expires_in_seconds: number;
}

export interface ReactionUploadCompleteRequest {
    reaction_video_gcs_uri: string;
}

export interface ReactionUploadResponse {
    session_id: string;
    status: "accepted";
    reaction_video_gcs_uri: string;
}
