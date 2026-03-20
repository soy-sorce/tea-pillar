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
                btn: "10px",
                "card-lg": "20px",
                "card-xl": "28px",
            },
            boxShadow: {
                card: "0 1px 4px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.04)",
                "card-selected": "0 0 0 2px #4D8C6F",
                "card-hover": "0 8px 24px rgba(0,0,0,0.10)",
                "btn-primary": "0 4px 14px rgba(77,140,111,0.35)",
                "btn-primary-hover": "0 6px 20px rgba(77,140,111,0.50)",
                glow: "0 0 20px rgba(77,140,111,0.25)",
                "inner-sm": "inset 0 1px 3px rgba(0,0,0,0.06)",
            },
            backgroundImage: {
                "gradient-hero": "radial-gradient(ellipse 100% 70% at 50% -10%, #E8F4EE 0%, #FAFAF8 65%)",
                "gradient-btn": "linear-gradient(135deg, #4D8C6F 0%, #3A6E56 100%)",
                "gradient-card": "linear-gradient(180deg, #FFFFFF 0%, #F9FAF8 100%)",
                "gradient-surface": "linear-gradient(135deg, rgba(232,244,238,0.6) 0%, rgba(255,255,255,0) 100%)",
            },
            animation: {
                "fadeIn": "fadeIn 0.35s ease-out",
                "slideUp": "slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1)",
                "pulse-ring": "pulseRing 2s ease-out infinite",
                "spin-slow": "spin 3s linear infinite",
                "bounce-gentle": "bounceGentle 1.4s ease-in-out infinite",
                "step-cycle": "stepCycle 6s ease-in-out infinite",
            },
            keyframes: {
                fadeIn: {
                    "0%": { opacity: "0" },
                    "100%": { opacity: "1" },
                },
                slideUp: {
                    "0%": { opacity: "0", transform: "translateY(20px)" },
                    "100%": { opacity: "1", transform: "translateY(0)" },
                },
                pulseRing: {
                    "0%": { transform: "scale(0.8)", opacity: "0.8" },
                    "100%": { transform: "scale(1.6)", opacity: "0" },
                },
                bounceGentle: {
                    "0%, 100%": { transform: "translateY(0)" },
                    "50%": { transform: "translateY(-10px)" },
                },
                stepCycle: {
                    "0%, 28%": { opacity: "1" },
                    "33%, 61%": { opacity: "0" },
                    "66%, 94%": { opacity: "0" },
                    "100%": { opacity: "1" },
                },
            },
        },
    },
    plugins: [],
} satisfies Config;
