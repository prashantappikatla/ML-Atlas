import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: {
    default: 'ML Atlas',
    template: '%s | ML Atlas',
  },
  description:
    'A documentation and experimentation platform for 278 machine learning algorithms.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-white text-gray-900 antialiased">
        <main>{children}</main>
      </body>
    </html>
  )
}
