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
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#AC3631',
        info: '#3b82f6',
        'svn-brown': '#8b4513',
        'svn-orange': '#dc7f37',
        'svn-green': '#6b8e23',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        card: '12px',
        btn: '8px',
        input: '8px',
      },
      boxShadow: {
        card: '0 1px 3px rgba(0, 0, 0, 0.1)',
        modal: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
      },
    },
  },
  plugins: [],
}
