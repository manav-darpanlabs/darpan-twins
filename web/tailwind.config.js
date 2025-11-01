/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        bg: '#14161a',
        panel: '#1a1d23',
        brand: '#C1E329',
        brand2: '#3fb1f0',
      },
      fontFamily: {
        grotesk: ['Space Grotesk', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        glowG: '0 0 16px rgba(193,227,41,0.35)',
        glowB: '0 0 16px rgba(63,177,240,0.35)'
      }
    },
  },
  plugins: [],
}

