import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
      },
    },
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: [
      {
        mytheme: {
          primary: "#ACF7C1",
          secondary: "#94BFBE",
          accent: "#C2E812",
          neutral: "#08605F",
          "base-100": "#ffffff",
          success: "#ACF7C1",
        },
      },
      "light",
      "dark",
      "cupcake",
      "business",
      "retro",
      "cyberpunk",
      "acid",
    ],
  },
};
export default config;
