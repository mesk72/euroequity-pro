/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        bg:      '#07090d',
        surface: '#0d1017',
        border:  '#1e2840',
        gold:    '#c8982a',
        green:   '#22d48a',
        red:     '#e84560',
        text:    '#dde4f0',
        muted:   '#5a6880',
        sub:     '#8a9ab8',
      },
      fontFamily: {
        sans: ['Outfit', 'sans-serif'],
        mono: ['Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
