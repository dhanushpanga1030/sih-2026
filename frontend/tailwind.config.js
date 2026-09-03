/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        risk: {
          immediate: '#dc2626',
          short_term: '#ea580c',
          medium_term: '#ca8a04',
          monitor: '#16a34a',
        },
      },
    },
  },
  plugins: [],
}
