// src/types/app.ts
// アプリ内部型定義

export type ResultState = "idle" | "loading" | "done" | "error";
export type InputMode = "A" | "B";
export type PersonalityType = "curious" | "relaxed" | "timid" | "capricious";
export type Reaction = "good" | "neutral" | "bad";

export interface MeowSample {
    id: "brushing" | "waiting_for_food" | "isolation";
    emoji: string;
    label: string;
    url: string; // /samples/audio/*.wav
}

export interface PhotoSample {
    id: "happy" | "sad" | "angry";
    emoji: string;
    label: string;
    url: string; // /samples/images/*.jpg
}

// 体験モードのサンプルデータ定数
export const MEOW_SAMPLES: MeowSample[] = [
    {
        id: "waiting_for_food",
        emoji: "🍚",
        label: "ごはん待ちのにゃー",
        url: "/samples/audio/waiting_for_food.wav",
    },
    {
        id: "brushing",
        emoji: "😺",
        label: "なでられてゴロゴロ",
        url: "/samples/audio/brushing.wav",
    },
    {
        id: "isolation",
        emoji: "😿",
        label: "ひとりぼっちの声",
        url: "/samples/audio/isolation.wav",
    },
];

export const PHOTO_SAMPLES: PhotoSample[] = [
    { id: "happy", emoji: "😊", label: "happy", url: "/samples/images/happy.jpg" },
    { id: "sad", emoji: "😢", label: "sad", url: "/samples/images/sad.jpg" },
    { id: "angry", emoji: "😠", label: "angry", url: "/samples/images/angry.jpg" },
];

export const PERSONALITY_OPTIONS: {
    type: PersonalityType;
    emoji: string;
    label: string;
}[] = [
        { type: "curious", emoji: "🌟", label: "好奇心旺盛" },
        { type: "relaxed", emoji: "😴", label: "のんびり屋" },
        { type: "timid", emoji: "😱", label: "ビビりな猫" },
        { type: "capricious", emoji: "👑", label: "気まぐれ" },
    ];
