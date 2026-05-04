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
          50:  '#FFF0F3',
          100: '#FFE1E7',
          200: '#FFBFCC',
          300: '#FF8FA3',
          400: '#C94B6A',
          500: '#9B1C2E',
          600: '#7F1D1D',
          700: '#6B1414',
          800: '#5A1010',
          900: '#4A0B0B',
        },
      },
      keyframes: {
        'fade-in': {
          '0%':   { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in-left': {
          '0%':   { opacity: '0', transform: 'translateX(-20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        'scale-in': {
          '0%':   { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        'shimmer': {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      animation: {
        'fade-in':       'fade-in 0.4s ease-out both',
        'slide-in-left': 'slide-in-left 0.35s ease-out both',
        'scale-in':      'scale-in 0.3s ease-out both',
        'shimmer':       'shimmer 1.8s linear infinite',
      },
    },
  },
  plugins: [],
}
