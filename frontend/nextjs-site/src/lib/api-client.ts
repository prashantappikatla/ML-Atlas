const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${path}`)
  }
  return res.json()
}

export const api = {
  algorithms: {
    list: (params?: Record<string, string>) => {
      const qs = params ? '?' + new URLSearchParams(params).toString() : ''
      return apiFetch(`/algorithms${qs}`)
    },
    byId: (id: number) => apiFetch(`/algorithms/${id}`),
    bySlug: (slug: string) => apiFetch(`/algorithms/by-slug/${slug}`),
  },
  categories: {
    list: () => apiFetch('/categories'),
    bySlug: (slug: string) => apiFetch(`/categories/${slug}`),
  },
  labs: {
    list: () => apiFetch('/labs'),
    byAlgorithmSlug: (slug: string) => apiFetch(`/labs/${slug}`),
  },
  notes: {
    byAlgorithmId: (algorithmId: number) => apiFetch(`/notes/${algorithmId}`),
    create: (body: object) =>
      apiFetch('/notes', { method: 'POST', body: JSON.stringify(body) }),
    update: (noteId: number, body: object) =>
      apiFetch(`/notes/${noteId}`, { method: 'PUT', body: JSON.stringify(body) }),
  },
  status: {
    list: () => apiFetch('/status'),
    byAlgorithmId: (algorithmId: number) => apiFetch(`/status/${algorithmId}`),
    update: (algorithmId: number, body: object) =>
      apiFetch(`/status/${algorithmId}`, { method: 'PUT', body: JSON.stringify(body) }),
  },
  search: (query: string) => apiFetch(`/search?q=${encodeURIComponent(query)}`),
}
