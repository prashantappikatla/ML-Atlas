'use client'

import { useState } from 'react'
import { Check, Copy } from 'lucide-react'

interface CodeBlockProps {
  children: string
  language?: string
}

export function CodeBlock({ children, language }: CodeBlockProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(children).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <div className="not-prose group relative my-4">
      {language && (
        <div className="flex items-center justify-between rounded-t-lg border border-b-0 border-slate-700 bg-slate-800 px-4 py-2">
          <span className="text-xs font-medium text-slate-400">{language}</span>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 rounded px-2 py-1 text-xs text-slate-400 hover:bg-slate-700 hover:text-slate-200"
            aria-label="Copy code"
          >
            {copied ? (
              <>
                <Check className="h-3.5 w-3.5" />
                Copied
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5" />
                Copy
              </>
            )}
          </button>
        </div>
      )}
      <div className="relative">
        {!language && (
          <button
            onClick={handleCopy}
            className="absolute right-3 top-3 z-10 flex items-center gap-1 rounded px-2 py-1 text-xs text-slate-400 opacity-0 transition-opacity group-hover:opacity-100 hover:bg-slate-700 hover:text-slate-200"
            aria-label="Copy code"
          >
            {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
          </button>
        )}
        <pre
          className={`overflow-x-auto bg-slate-950 p-4 text-sm text-slate-100 ${language ? 'rounded-b-lg' : 'rounded-lg'}`}
        >
          <code>{children}</code>
        </pre>
      </div>
    </div>
  )
}
