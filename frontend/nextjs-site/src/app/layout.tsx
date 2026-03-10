import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import './globals.css'
import { NavbarClient } from '@/components/layout/NavbarClient'
import { Footer } from '@/components/layout/Footer'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  display: 'swap',
})

export const metadata: Metadata = {
  title: {
    default: 'ML Atlas',
    template: '%s | ML Atlas',
  },
  description:
    'Documentation and interactive labs for 278 machine learning algorithms across 10 major categories.',
  keywords: [
    'machine learning',
    'algorithms',
    'documentation',
    'interactive labs',
    'ML reference',
  ],
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="flex min-h-screen flex-col bg-white font-sans text-slate-900 antialiased">
        <NavbarClient />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  )
}
