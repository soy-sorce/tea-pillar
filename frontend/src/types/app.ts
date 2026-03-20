// src/types/app.ts
// アプリ内部型定義

export type ResultState = "idle" | "loading" | "done" | "error";
export type InputMode = "A" | "B";
export type Reaction = "good" | "neutral" | "bad";

export interface MeowSample {
    id: "brushing" | "waiting_for_food" | "isolation";
    emoji: string;
    label: string;
    url: string; // /samples/audio/*.wav
}

export interface PhotoSample {
    id: "cat-1" | "cat-2" | "cat-3";
    label: string;
    imageUrl: string; // /samples/cat-pictures/*.png
    url: string;      // urlToBase64 で使うため同値
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
    { id: "cat-1", label: "cat-1", imageUrl: "/samples/cat-pictures/cat-1.png", url: "/samples/cat-pictures/cat-1.png" },
    { id: "cat-2", label: "cat-2", imageUrl: "/samples/cat-pictures/cat-2.png", url: "/samples/cat-pictures/cat-2.png" },
    { id: "cat-3", label: "cat-3", imageUrl: "/samples/cat-pictures/cat-3.png", url: "/samples/cat-pictures/cat-3.png" },
];

// コンテキスト入力のサンプル例（クリックでtextareaにfill）
export const CONTEXT_EXAMPLES: string[] = [
    "魚が大好きで、遊び好きな活発な猫",
    "臆病でびっくりしやすい、内気な猫",
    "甘えたでのんびり屋、ゴロゴロが好き",
    "警戒心が強くツンデレ、でも実は寂しがり",
];
