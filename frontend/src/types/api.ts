// src/types/api.ts
// Backend API のリクエスト/レスポンス型定義

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

export interface FeedbackRequest {
    session_id: string;
    reaction: "good" | "neutral" | "bad";
}

export interface FeedbackResponse {
    reward: number;
    updated_template_id: string;
}
