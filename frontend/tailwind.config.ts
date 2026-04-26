import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter Variable", "sans-serif"],
        serif: ["Lora", "serif"],
        lora: ["Lora", "serif"],
        lexend: ["Lexend Variable", "sans-serif"],
      },
      colors: {
        "deep-space-blue": {
          "50": "#e5f6ff", "100": "#ccedff", "200": "#99dbff", "300": "#66c9ff",
          "400": "#33b8ff", "500": "#00a6ff", "600": "#0085cc", "700": "#006399",
          "800": "#004266", "900": "#002133", "950": "#001724"
        },
        "flag-red": {
          "50": "#fbe9e9", "100": "#f7d4d4", "200": "#efa9a9", "300": "#e77e7e",
          "400": "#df5353", "500": "#d72828", "600": "#ac2020", "700": "#811818",
          "800": "#561010", "900": "#2b0808", "950": "#1e0606"
        },
        "vivid-tangerine": {
          "50": "#fff3e5", "100": "#ffe6cc", "200": "#ffce99", "300": "#ffb566",
          "400": "#ff9c33", "500": "#ff8400", "600": "#cc6900", "700": "#994f00",
          "800": "#663500", "900": "#331a00", "950": "#241200"
        },
        "sunflower-gold": {
          "50": "#fff6e6", "100": "#feeecd", "200": "#fddc9b", "300": "#fdcb68",
          "400": "#fcba36", "500": "#fba904", "600": "#c98703", "700": "#976502",
          "800": "#644302", "900": "#322201", "950": "#231801"
        },
        "vanilla-custard": {
          "50": "#f9f7eb", "100": "#f4efd7", "200": "#e8e0b0", "300": "#ddd088",
          "400": "#d1c061", "500": "#c6b139", "600": "#9e8d2e", "700": "#776a22",
          "800": "#4f4717", "900": "#28230b", "950": "#1c1908"
        }
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic":
          "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
      },
    },
  },
  plugins: [],
};
export default config;
