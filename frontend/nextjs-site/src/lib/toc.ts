export interface TocItem {
  id: string
  text: string
  level: number
}

/**
 * Extracts headings from raw MDX/markdown content to build a table of contents.
 * Converts heading text to slug IDs (matching how rehype generates them).
 */
export function extractHeadings(content: string): TocItem[] {
  const headingRegex = /^(#{2,4})\s+(.+)$/gm
  const headings: TocItem[] = []
  let match

  while ((match = headingRegex.exec(content)) !== null) {
    const level = match[1].length
    const text = match[2].replace(/\*\*|__|`/g, '').trim()
    const id = text
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '')

    headings.push({ id, text, level })
  }

  return headings
}
