/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        midnight: {
          900: '#0f172a', // Slate 900
          950: '#020617', // Slate 950
        },
        electric: {
          400: '#a78bfa', // Violet 400
          500: '#8b5cf6', // Violet 500
          600: '#7c3aed', // Violet 600
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'mesh': 'radial-gradient(at 40% 20%, hsla(258,90%,66%,0.15) 0px, transparent 50%), radial-gradient(at 80% 0%, hsla(258,90%,66%,0.1) 0px, transparent 50%), radial-gradient(at 0% 50%, hsla(258,90%,66%,0.1) 0px, transparent 50%)',
      }
    },
  },
  plugins: [],
}
