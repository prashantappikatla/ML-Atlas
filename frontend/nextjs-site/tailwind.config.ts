import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-sans)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'ui-monospace', 'monospace'],
      },
      colors: {
        // Indigo as primary accent
        primary: {
          50: '#eef2ff',
          100: '#e0e7ff',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          900: '#312e81',
        },
      },
      typography: {
        DEFAULT: {
          css: {
            maxWidth: 'none',
            color: '#1e293b',
            a: { color: '#4f46e5', textDecoration: 'underline' },
            'h1, h2, h3, h4': { color: '#0f172a', fontWeight: '700' },
            strong: { color: '#0f172a' },
            blockquote: {
              borderLeftColor: '#6366f1',
              backgroundColor: '#eef2ff',
              padding: '0.5rem 1rem',
              borderRadius: '0.25rem',
              color: '#312e81',
            },
          },
        },
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
}

export default config
