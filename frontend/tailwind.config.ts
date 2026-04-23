import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        mist: "#e2e8f0",
        panel: "#111827",
        panelSoft: "#172033",
        accent: "#0ea5e9",
        success: "#22c55e",
        warning: "#f59e0b",
        danger: "#ef4444",
      },
      boxShadow: {
        panel: "0 12px 36px rgba(15, 23, 42, 0.14)",
      },
    },
  },
  plugins: [],
} satisfies Config;
