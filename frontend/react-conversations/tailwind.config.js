/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#772B21',
        'primary-dark': '#381811',
        'primary-light': '#CFE3DA',
        background: '#FFF8F3',
        card: '#ffffff',
        foreground: '#221B19',
        muted: '#5a4f4c',
        border: '#e5dcd7',
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#AC3631',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      borderRadius: {
        'btn': '8px',
        'input': '8px',
        'card': '16px',
      },
    },
  },
  plugins: [],
}
