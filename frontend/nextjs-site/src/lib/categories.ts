export interface CategoryMeta {
  slug: string
  name: string
  description: string
  color: string
  bgColor: string
  textColor: string
  count: number
}

export const CATEGORIES: CategoryMeta[] = [
  {
    slug: 'supervised',
    name: 'Supervised Learning',
    description: 'Regression, classification, and ranking algorithms trained on labeled data.',
    color: '#4f46e5',
    bgColor: 'bg-indigo-50',
    textColor: 'text-indigo-700',
    count: 64,
  },
  {
    slug: 'unsupervised',
    name: 'Unsupervised Learning',
    description: 'Clustering, dimensionality reduction, and anomaly detection.',
    color: '#0891b2',
    bgColor: 'bg-cyan-50',
    textColor: 'text-cyan-700',
    count: 50,
  },
  {
    slug: 'deep-learning',
    name: 'Deep Learning',
    description: 'Neural networks including CNNs, RNNs, and Transformers.',
    color: '#7c3aed',
    bgColor: 'bg-violet-50',
    textColor: 'text-violet-700',
    count: 57,
  },
  {
    slug: 'generative',
    name: 'Generative Models',
    description: 'GANs, VAEs, diffusion models and other generative architectures.',
    color: '#db2777',
    bgColor: 'bg-pink-50',
    textColor: 'text-pink-700',
    count: 17,
  },
  {
    slug: 'reinforcement',
    name: 'Reinforcement Learning',
    description: 'Q-learning, policy gradients, and model-based RL algorithms.',
    color: '#d97706',
    bgColor: 'bg-amber-50',
    textColor: 'text-amber-700',
    count: 27,
  },
  {
    slug: 'time-series',
    name: 'Time Series & Forecasting',
    description: 'ARIMA, GARCH, Prophet, and temporal modeling techniques.',
    color: '#059669',
    bgColor: 'bg-emerald-50',
    textColor: 'text-emerald-700',
    count: 18,
  },
  {
    slug: 'probabilistic',
    name: 'Probabilistic & Bayesian',
    description: 'Bayesian networks, HMMs, Kalman filters, and probabilistic graphical models.',
    color: '#0369a1',
    bgColor: 'bg-sky-50',
    textColor: 'text-sky-700',
    count: 18,
  },
  {
    slug: 'graph',
    name: 'Graph Machine Learning',
    description: 'GNNs, node embeddings, and learning on graph-structured data.',
    color: '#65a30d',
    bgColor: 'bg-lime-50',
    textColor: 'text-lime-700',
    count: 12,
  },
  {
    slug: 'meta-learning',
    name: 'Meta-Learning & AutoML',
    description: 'Few-shot learning, MAML, NAS, and automated machine learning.',
    color: '#9333ea',
    bgColor: 'bg-purple-50',
    textColor: 'text-purple-700',
    count: 15,
  },
  {
    slug: 'evolutionary',
    name: 'Evolutionary & Fuzzy',
    description: 'Genetic algorithms, evolutionary strategies, and fuzzy logic systems.',
    color: '#dc2626',
    bgColor: 'bg-red-50',
    textColor: 'text-red-700',
    count: 8,
  },
]

export function getCategoryMeta(slug: string): CategoryMeta | undefined {
  return CATEGORIES.find((c) => c.slug === slug)
}
