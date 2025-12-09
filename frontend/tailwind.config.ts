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
          600: "#0d9488",
          700: "#0f766e",
          800: "#115e59",
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
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        display: ["var(--font-outfit)", "var(--font-inter)", "sans-serif"],
        mono: ["JetBrains Mono", "var(--font-inter)", "monospace"],
      },
      boxShadow: {
        glow: "0 0 20px rgba(13,148,136,0.3)",
      },
      borderRadius: {
        xl: "16px",
      },
      backgroundImage: {
        "lucide-grid":
          "radial-gradient(circle at 20% 20%, rgba(13,148,136,0.12), transparent 32%), radial-gradient(circle at 70% 0%, rgba(245,158,11,0.08), transparent 32%)",
      },
    },
  },
  plugins: [],
};
export default config;
