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
          50: '#f0f4f8',
          100: '#d9e2ec',
          200: '#bcccdc',
          300: '#9fb3c8',
          400: '#829ab1',
          500: '#627d98',
          600: '#486581',
          700: '#334e68',
          800: '#102a43',
          900: '#0b1d3a',
          950: '#060f1e',
        },
        brand: {
          blue: '#1d4ed8',
          indigo: '#4338ca',
          cyan: '#0891b2',
          emerald: '#059669',
          amber: '#d97706',
          rose: '#e11d48',
        }
      },
    },
  },
  plugins: [],
};
export default config;
