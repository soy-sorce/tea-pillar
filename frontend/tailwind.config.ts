import type { Config } from "tailwindcss";

export default {
    content: ["./index.html", "./src/**/*.{ts,tsx}"],
    theme: {
        extend: {
            colors: {
                bg: "#FAFAF8",
                surface: "#FFFFFF",
                "surface-alt": "#F4F4F0",
                accent: {
                    DEFAULT: "#4D8C6F",
                    light: "#E8F4EE",
                    dark: "#3A6E56",
                },
                text: {
                    primary: "#1C1C1A",
                    secondary: "#6B7280",
                    muted: "#9CA3AF",
                },
                border: {
                    DEFAULT: "#E5E7EB",
                    selected: "#4D8C6F",
                },
            },
            fontFamily: {
                sans: ["Inter", "Noto Sans JP", "sans-serif"],
            },
            borderRadius: {
                card: "12px",
                btn: "8px",
            },
            boxShadow: {
                card: "0 1px 4px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.04)",
                "card-selected": "0 0 0 2px #4D8C6F",
            },
            animationDelay: {
                "150": "150ms",
                "300": "300ms",
            },
        },
    },
    plugins: [],
} satisfies Config;
