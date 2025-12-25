import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        teal: {
          600: "#0ea5e9",
          700: "#0284c7",
          800: "#0369a1",
        },
        amber: {
          400: "#f59e0b",
          500: "#f59e0b",
          600: "#d97706",
        },
        slatebg: "#f8fafc",
        dark: "#0f172a",
      },
      fontFamily: {
        sans: ["var(--font-plex)", "system-ui", "sans-serif"],
        display: ["var(--font-space)", "var(--font-plex)", "sans-serif"],
        mono: ["JetBrains Mono", "var(--font-plex)", "monospace"],
      },
      boxShadow: {
        glow: "0 0 20px rgba(14,165,233,0.28)",
      },
      borderRadius: {
        xl: "16px",
      },
      backgroundImage: {
        "lucide-grid":
          "radial-gradient(circle at 15% 15%, rgba(14,165,233,0.14), transparent 32%), radial-gradient(circle at 80% 10%, rgba(245,158,11,0.10), transparent 30%)",
      },
    },
  },
  plugins: [],
};
export default config;
