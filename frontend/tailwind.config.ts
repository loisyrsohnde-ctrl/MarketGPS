import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // ═══════════════════════════════════════════════════════════════
      // MARKETGPS DESIGN SYSTEM - GLASSMORPHISM PREMIUM
      // ═══════════════════════════════════════════════════════════════
      colors: {
        // Background
        bg: {
          primary: "#070A0B",
          secondary: "#0A0E10",
          elevated: "#0D1214",
        },
        // Surface (glass cards)
        surface: {
          DEFAULT: "rgba(255, 255, 255, 0.04)",
          hover: "rgba(255, 255, 255, 0.06)",
          active: "rgba(255, 255, 255, 0.08)",
          dark: "rgba(0, 0, 0, 0.35)",
        },
        // Glass borders
        glass: {
          border: "rgba(255, 255, 255, 0.08)",
          "border-hover": "rgba(255, 255, 255, 0.12)",
          "border-active": "rgba(25, 211, 140, 0.4)",
        },
        // Accent Green
        accent: {
          DEFAULT: "#19D38C",
          light: "#4ADE80",
          dark: "#16A34A",
          dim: "rgba(25, 211, 140, 0.15)",
          glow: "rgba(25, 211, 140, 0.25)",
        },
        // Text
        text: {
          primary: "#EAF2EE",
          secondary: "rgba(234, 242, 238, 0.70)",
          muted: "rgba(234, 242, 238, 0.50)",
          dim: "rgba(234, 242, 238, 0.35)",
        },
        // Score colors
        score: {
          red: "#EF4444",
          yellow: "#F59E0B",
          "light-green": "#4ADE80",
          green: "#22C55E",
        },
        // Status
        status: {
          success: "#22C55E",
          warning: "#F59E0B",
          error: "#EF4444",
          info: "#3B82F6",
        },
      },
      // Typography
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["JetBrains Mono", "Menlo", "monospace"],
      },
      fontSize: {
        "2xs": ["0.625rem", { lineHeight: "0.875rem" }],
        xs: ["0.75rem", { lineHeight: "1rem" }],
        sm: ["0.875rem", { lineHeight: "1.25rem" }],
        base: ["1rem", { lineHeight: "1.5rem" }],
        lg: ["1.125rem", { lineHeight: "1.75rem" }],
        xl: ["1.25rem", { lineHeight: "1.75rem" }],
        "2xl": ["1.5rem", { lineHeight: "2rem" }],
        "3xl": ["1.875rem", { lineHeight: "2.25rem" }],
        "4xl": ["2.25rem", { lineHeight: "2.5rem" }],
        "5xl": ["3rem", { lineHeight: "1" }],
      },
      // Spacing (8px grid)
      spacing: {
        "18": "4.5rem",
        "22": "5.5rem",
        "30": "7.5rem",
        "34": "8.5rem",
      },
      // Border radius
      borderRadius: {
        "2xl": "16px",
        "3xl": "20px",
        "4xl": "24px",
      },
      // Box shadow
      boxShadow: {
        glass: "0 8px 32px rgba(0, 0, 0, 0.4)",
        "glass-sm": "0 4px 16px rgba(0, 0, 0, 0.3)",
        "glass-lg": "0 16px 48px rgba(0, 0, 0, 0.5)",
        glow: "0 0 20px rgba(25, 211, 140, 0.3)",
        "glow-sm": "0 0 10px rgba(25, 211, 140, 0.2)",
        "glow-lg": "0 0 40px rgba(25, 211, 140, 0.4)",
      },
      // Backdrop blur
      backdropBlur: {
        xs: "4px",
        glass: "16px",
        "glass-lg": "24px",
      },
      // Animations
      animation: {
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-up": "slideUp 0.3s ease-out",
        "slide-down": "slideDown 0.3s ease-out",
        "scale-in": "scaleIn 0.2s ease-out",
        pulse: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        shimmer: "shimmer 2s linear infinite",
        glow: "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideDown: {
          "0%": { opacity: "0", transform: "translateY(-10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        scaleIn: {
          "0%": { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        glow: {
          "0%": { boxShadow: "0 0 20px rgba(25, 211, 140, 0.2)" },
          "100%": { boxShadow: "0 0 30px rgba(25, 211, 140, 0.4)" },
        },
      },
      // Transitions
      transitionDuration: {
        "250": "250ms",
        "350": "350ms",
      },
      transitionTimingFunction: {
        glass: "cubic-bezier(0.4, 0, 0.2, 1)",
      },
    },
  },
  plugins: [],
};

export default config;
