export type AlgorithmStatus =
  | 'planned'
  | 'in-progress'
  | 'documented'
  | 'implemented'
  | 'lab-ready'

export type Complexity = 'low' | 'medium' | 'high'

export type LabFramework = 'streamlit' | 'gradio' | ''

export interface AlgorithmFrontmatter {
  title: string
  slug: string
  category: string
  subcategory: string
  year: number
  author: string
  paper: string
  complexity: Complexity
  status: AlgorithmStatus
  compatibility: {
    tabular: boolean
    image: boolean
    text: boolean
    timeseries: boolean
    graph: boolean
  }
  tags: string[]
  lab_url: string
  lab_framework: LabFramework
  related: string[]
}

export interface AlgorithmPage {
  frontmatter: AlgorithmFrontmatter
  content: string
  readingTimeMinutes: number
}
