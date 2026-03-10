import { MDXRemote } from 'next-mdx-remote/rsc'
import remarkMath from 'remark-math'
import remarkGfm from 'remark-gfm'
import rehypeKatex from 'rehype-katex'
import rehypeHighlight from 'rehype-highlight'
import rehypeSlug from 'rehype-slug'
import { Callout } from './Callout'
import { CompatibilityMatrix } from './CompatibilityMatrix'
import { LabEmbed } from './LabEmbed'

interface MDXContentProps {
  source: string
}

const components = {
  Callout,
  CompatibilityMatrix,
  LabEmbed,
}

export function MDXContent({ source }: MDXContentProps) {
  return (
    <MDXRemote
      source={source}
      components={components}
      options={{
        mdxOptions: {
          remarkPlugins: [remarkMath, remarkGfm],
          rehypePlugins: [rehypeKatex, rehypeHighlight, rehypeSlug],
        },
      }}
    />
  )
}
