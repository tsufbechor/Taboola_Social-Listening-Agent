/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Sentiment colors
        sentiment: {
          positive: '#10b981',
          neutral: '#6b7280',
          negative: '#ef4444',
          mixed: '#f59e0b',
        },
        // Custom background colors
        bg: {
          primary: '#0f172a',
          secondary: '#1e293b',
          surface: '#334155',
          'surface-hover': '#475569',
        },
      },
    },
  },
  plugins: [],
}
