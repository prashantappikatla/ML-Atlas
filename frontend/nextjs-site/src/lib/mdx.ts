import fs from 'fs'
import path from 'path'
import matter from 'gray-matter'
import { AlgorithmFrontmatter, AlgorithmPage } from '@/types/mdx'

// Content root is at the monorepo level, two directories above nextjs-site
const CONTENT_ROOT = path.join(process.cwd(), '..', '..', 'content', 'algorithms')

function walkMdxFiles(dir: string): string[] {
  const results: string[] = []
  if (!fs.existsSync(dir)) return results
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      results.push(...walkMdxFiles(fullPath))
    } else if (entry.name.endsWith('.mdx')) {
      results.push(fullPath)
    }
  }
  return results
}

function estimateReadingTime(content: string): number {
  const words = content.split(/\s+/).length
  return Math.ceil(words / 200)
}

export function getAllAlgorithmSlugs(): Array<{ category: string; slug: string }> {
  const files = walkMdxFiles(CONTENT_ROOT)
  return files.map((filePath) => {
    const relative = path.relative(CONTENT_ROOT, filePath)
    const parts = relative.split(path.sep)
    // parts = [category, subcategory, slug.mdx] or [category, slug.mdx]
    const slug = parts[parts.length - 1].replace(/\.mdx$/, '')
    const category = parts[0]
    return { category, slug }
  })
}

export function getAlgorithmBySlug(category: string, slug: string): AlgorithmPage | null {
  const files = walkMdxFiles(path.join(CONTENT_ROOT, category))
  const filePath = files.find((f) => path.basename(f, '.mdx') === slug)
  if (!filePath) return null

  const raw = fs.readFileSync(filePath, 'utf-8')
  const { data, content } = matter(raw)

  return {
    frontmatter: data as AlgorithmFrontmatter,
    content,
    readingTimeMinutes: estimateReadingTime(content),
  }
}

export function getAlgorithmsByCategory(category: string): AlgorithmFrontmatter[] {
  const dir = path.join(CONTENT_ROOT, category)
  const files = walkMdxFiles(dir)
  return files.map((filePath) => {
    const raw = fs.readFileSync(filePath, 'utf-8')
    const { data } = matter(raw)
    return data as AlgorithmFrontmatter
  })
}

export function getAllAlgorithms(): AlgorithmFrontmatter[] {
  const files = walkMdxFiles(CONTENT_ROOT)
  return files.map((filePath) => {
    const raw = fs.readFileSync(filePath, 'utf-8')
    const { data } = matter(raw)
    return data as AlgorithmFrontmatter
  })
}
