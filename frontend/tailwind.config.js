/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        serif:  ['"Instrument Serif"', 'Georgia', 'serif'],
        sans:   ['"Geist"', 'system-ui', 'sans-serif'],
        mono:   ['"Geist Mono"', 'monospace'],
      },
      colors: {
        zinc: { 950: '#09090b' },
        violet: { 450: '#9b6dff' },
      },
      animation: {
        'fade-up':   'fadeUp 0.4s ease forwards',
        'fade-in':   'fadeIn 0.3s ease forwards',
        'slide-in':  'slideIn 0.35s ease forwards',
        'pulse-dot': 'pulseDot 1.4s ease-in-out infinite',
      },
      keyframes: {
        fadeUp:   { from: { opacity: 0, transform: 'translateY(12px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
        fadeIn:   { from: { opacity: 0 }, to: { opacity: 1 } },
        slideIn:  { from: { opacity: 0, transform: 'translateX(16px)' }, to: { opacity: 1, transform: 'translateX(0)' } },
        pulseDot: { '0%,100%': { opacity: 0.4, transform: 'scale(0.8)' }, '50%': { opacity: 1, transform: 'scale(1)' } },
      },
    },
  },
  plugins: [],
}
