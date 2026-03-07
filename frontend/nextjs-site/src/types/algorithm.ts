export interface Algorithm {
  id: number
  name: string
  slug: string
  category: string
  subcategory: string
  year: number | null
  author: string | null
  paper_reference: string | null
  complexity: 'low' | 'medium' | 'high'
  best_use_case: string | null
  description: string | null
  compatibility_tabular: boolean
  compatibility_image: boolean
  compatibility_text: boolean
  compatibility_graph: boolean
  compatibility_timeseries: boolean
}

export interface AlgorithmListResponse {
  data: Algorithm[]
  meta: {
    total: number
    page: number
  }
}

export interface CategorySummary {
  slug: string
  name: string
  count: number
  documented: number
  implemented: number
  lab_ready: number
}
