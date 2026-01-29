/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#772B21',
          dark: '#381811',
          light: '#CFE3DA',
        },
        background: '#FFF8F3',
        card: '#ffffff',
        foreground: '#221B19',
        muted: '#5a4f4c',
        border: '#e5dcd7',
        success: {
          DEFAULT: '#10b981',
          light: '#d1fae5',
        },
        warning: {
          DEFAULT: '#f59e0b',
          light: '#fef3c7',
        },
        danger: {
          DEFAULT: '#AC3631',
          light: '#fee2e2',
        },
        info: {
          DEFAULT: '#3b82f6',
          light: '#dbeafe',
        },
        svn: {
          brown: '#8b4513',
          orange: '#dc7f37',
          green: '#6b8e23',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        btn: '8px',
        input: '8px',
        card: '12px',
      },
      boxShadow: {
        card: '0 1px 3px rgba(0, 0, 0, 0.08)',
        'card-hover': '0 4px 12px rgba(0, 0, 0, 0.12)',
        modal: '0 20px 40px rgba(0, 0, 0, 0.2)',
      },
    },
  },
  plugins: [],
}
