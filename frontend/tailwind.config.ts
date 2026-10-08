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
        navy: {
          900: "#0a1726",
          800: "#0f2440",
          700: "#163257",
          600: "#1d4173",
          500: "#2a5696",
          400: "#4a7ab8",
          300: "#7fa0d4",
          200: "#a9c2e6",
          100: "#d4e2f5",
        },
        accent: {
          DEFAULT: "#ff6b2c",
          400: "#ff8a5c",
          500: "#ff6b2c",
          600: "#e85d22",
        },
        surface: {
          DEFAULT: "#ffffff",
          subtle: "#f5f8fc",
          line: "#e6edf6",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "Segoe UI", "Roboto", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
