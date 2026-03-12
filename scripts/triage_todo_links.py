#!/usr/bin/env python3
"""
ML Atlas — Triage todo-links.md items.

Reads documentation/todo-links.md (1,653 unlinked term items) and classifies
each entry as:

  FRAGMENT        — garbled sentence fragment (e.g. "The Theil", "For Lasso")
  INTERNAL        — matches an existing ML Atlas algorithm page
  WIKIPEDIA       — real person or recognized ML/math/stats concept with a Wikipedia page
  REVIEW          — ambiguous; needs human review

Outputs:
  documentation/todo-links-triaged.md   — full classified list
  documentation/todo-links-wikipedia.md — actionable list of WIKIPEDIA items with URLs

Usage:
    python scripts/triage_todo_links.py
"""

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent.parent
CONTENT_DIR = ROOT / "content" / "algorithms"
TODO_FILE = ROOT / "documentation" / "todo-links.md"
TRIAGED_FILE = ROOT / "documentation" / "todo-links-triaged.md"
WIKI_FILE = ROOT / "documentation" / "todo-links-wikipedia.md"

# ---------------------------------------------------------------------------
# Known ML/stats/math researchers — used for WIKIPEDIA_PERSON classification
# Wikipedia URL: https://en.wikipedia.org/wiki/First_Last (spaces → underscores)
# ---------------------------------------------------------------------------

KNOWN_RESEARCHERS: dict[str, str] = {
    # Statisticians / ML founders
    "Thomas Bayes": "https://en.wikipedia.org/wiki/Thomas_Bayes",
    "Andrey Markov": "https://en.wikipedia.org/wiki/Andrey_Markov",
    "Karl Pearson": "https://en.wikipedia.org/wiki/Karl_Pearson",
    "Ronald Fisher": "https://en.wikipedia.org/wiki/Ronald_Fisher",
    "George Box": "https://en.wikipedia.org/wiki/George_E._P._Box",
    "John Tukey": "https://en.wikipedia.org/wiki/John_Tukey",
    "David Cox": "https://en.wikipedia.org/wiki/David_Cox_(statistician)",
    # ML researchers
    "Leo Breiman": "https://en.wikipedia.org/wiki/Leo_Breiman",
    "Jerome Friedman": "https://en.wikipedia.org/wiki/Jerome_H._Friedman",
    "Vladimir Vapnik": "https://en.wikipedia.org/wiki/Vladimir_Vapnik",
    "Bernhard Scholkopf": "https://en.wikipedia.org/wiki/Bernhard_Schölkopf",
    "Yann LeCun": "https://en.wikipedia.org/wiki/Yann_LeCun",
    "Geoffrey Hinton": "https://en.wikipedia.org/wiki/Geoffrey_Hinton",
    "Yoshua Bengio": "https://en.wikipedia.org/wiki/Yoshua_Bengio",
    "Ian Goodfellow": "https://en.wikipedia.org/wiki/Ian_Goodfellow",
    "Alex Krizhevsky": "https://en.wikipedia.org/wiki/Alex_Krizhevsky",
    "Andrew Ng": "https://en.wikipedia.org/wiki/Andrew_Ng",
    "Michael Jordan": "https://en.wikipedia.org/wiki/Michael_I._Jordan",
    "Judea Pearl": "https://en.wikipedia.org/wiki/Judea_Pearl",
    "Peter Dayan": "https://en.wikipedia.org/wiki/Peter_Dayan",
    "Richard Sutton": "https://en.wikipedia.org/wiki/Richard_S._Sutton",
    "Andrew Barto": "https://en.wikipedia.org/wiki/Andrew_Barto",
    "Demis Hassabis": "https://en.wikipedia.org/wiki/Demis_Hassabis",
    "Ilya Sutskever": "https://en.wikipedia.org/wiki/Ilya_Sutskever",
    "Sam Altman": "https://en.wikipedia.org/wiki/Sam_Altman",
    "Fei-Fei Li": "https://en.wikipedia.org/wiki/Fei-Fei_Li",
    # Regression researchers
    "Arthur Hoerl": "https://en.wikipedia.org/wiki/Ridge_regression",
    "Robert Kennard": "https://en.wikipedia.org/wiki/Ridge_regression",
    "Robert Tibshirani": "https://en.wikipedia.org/wiki/Robert_Tibshirani",
    "Trevor Hastie": "https://en.wikipedia.org/wiki/Trevor_Hastie",
    "Bradley Efron": "https://en.wikipedia.org/wiki/Bradley_Efron",
    "Hui Zou": "https://en.wikipedia.org/wiki/Elastic_net_regularization",
    "Gilbert Bassett": "https://en.wikipedia.org/wiki/Quantile_regression",
    "Roger Koenker": "https://en.wikipedia.org/wiki/Roger_Koenker",
    "John Nelder": "https://en.wikipedia.org/wiki/John_Nelder",
    "Robert Wedderburn": "https://en.wikipedia.org/wiki/Generalized_linear_model",
    "Joseph Berkson": "https://en.wikipedia.org/wiki/Joseph_Berkson",
    "Harald Martens": "https://en.wikipedia.org/wiki/Partial_least_squares_regression",
    "Herman Wold": "https://en.wikipedia.org/wiki/Herman_Wold",
    "Svante Wold": "https://en.wikipedia.org/wiki/Partial_least_squares_regression",
    "Henri Theil": "https://en.wikipedia.org/wiki/Theil%E2%80%93Sen_estimator",
    "Pranab Kumar Sen": "https://en.wikipedia.org/wiki/Pranab_Kumar_Sen",
    "Charles Stone": "https://en.wikipedia.org/wiki/Charles_J._Stone",
    "Richard Olshen": "https://en.wikipedia.org/wiki/Classification_and_regression_tree",
    "Harold Hotelling": "https://en.wikipedia.org/wiki/Harold_Hotelling",
    "Ian Jolliffe": "https://en.wikipedia.org/wiki/Ian_Jolliffe",
    # Clustering
    "John MacQueen": "https://en.wikipedia.org/wiki/K-means_clustering",
    "Stuart Lloyd": "https://en.wikipedia.org/wiki/Lloyd%27s_algorithm",
    "Martin Ester": "https://en.wikipedia.org/wiki/DBSCAN",
    "Hans-Peter Kriegel": "https://en.wikipedia.org/wiki/DBSCAN",
    "Jorg Sander": "https://en.wikipedia.org/wiki/DBSCAN",
    "Xiaowei Xu": "https://en.wikipedia.org/wiki/DBSCAN",
    "Laurens van der Maaten": "https://en.wikipedia.org/wiki/T-distributed_stochastic_neighbor_embedding",
    "Geoffrey Hinton": "https://en.wikipedia.org/wiki/Geoffrey_Hinton",
    # Deep learning
    "Alex Smola": "https://en.wikipedia.org/wiki/Alex_Smola",
    "Bernhard Boser": "https://en.wikipedia.org/wiki/Support_vector_machine",
    "Corinna Cortes": "https://en.wikipedia.org/wiki/Corinna_Cortes",
    "Isabelle Guyon": "https://en.wikipedia.org/wiki/Isabelle_Guyon",
    "Sepp Hochreiter": "https://en.wikipedia.org/wiki/Sepp_Hochreiter",
    "Juergen Schmidhuber": "https://en.wikipedia.org/wiki/Jürgen_Schmidhuber",
    "Juho Kannala": "https://en.wikipedia.org/wiki/Juho_Kannala",
    "David Rumelhart": "https://en.wikipedia.org/wiki/David_Rumelhart",
    "James McClelland": "https://en.wikipedia.org/wiki/James_McClelland_(psychologist)",
    "Frank Rosenblatt": "https://en.wikipedia.org/wiki/Frank_Rosenblatt",
    "Warren McCulloch": "https://en.wikipedia.org/wiki/Warren_McCulloch",
    "Walter Pitts": "https://en.wikipedia.org/wiki/Walter_Pitts",
    "John Hopfield": "https://en.wikipedia.org/wiki/John_Hopfield",
    "Paul Werbos": "https://en.wikipedia.org/wiki/Paul_Werbos",
    "David Ackley": "https://en.wikipedia.org/wiki/Boltzmann_machine",
    # Boosting
    "Tianqi Chen": "https://en.wikipedia.org/wiki/XGBoost",
    "Carlos Guestrin": "https://en.wikipedia.org/wiki/Carlos_Guestrin",
    "Andy Liaw": "https://en.wikipedia.org/wiki/Random_forest",
    "Matthew Wiener": "https://en.wikipedia.org/wiki/Random_forest",
    "Tin Kam Ho": "https://en.wikipedia.org/wiki/Tin_Kam_Ho",
    "Pierre Geurts": "https://en.wikipedia.org/wiki/Extra-trees_algorithm",
    "Damien Ernst": "https://en.wikipedia.org/wiki/Extra-trees_algorithm",
    "Louis Wehenkel": "https://en.wikipedia.org/wiki/Extra-trees_algorithm",
    "Anna Prokhorenkova": "https://en.wikipedia.org/wiki/CatBoost",
    "Guido Ke": "https://en.wikipedia.org/wiki/LightGBM",
    "Carl Edward Rasmussen": "https://en.wikipedia.org/wiki/Gaussian_process",
    "Alex Gammerman": "https://en.wikipedia.org/wiki/Conformal_prediction",
    "Craig Saunders": "https://en.wikipedia.org/wiki/Kernel_methods",
    # Reinforcement learning
    "Christopher Watkins": "https://en.wikipedia.org/wiki/Q-learning",
    "Gerald Tesauro": "https://en.wikipedia.org/wiki/TD-Gammon",
    "Volodymyr Mnih": "https://en.wikipedia.org/wiki/Deep_Q-network",
    "David Silver": "https://en.wikipedia.org/wiki/David_Silver_(programmer)",
    "John Schulman": "https://en.wikipedia.org/wiki/John_Schulman",
    "Pieter Abbeel": "https://en.wikipedia.org/wiki/Pieter_Abbeel",
    "Sergey Levine": "https://en.wikipedia.org/wiki/Sergey_Levine",
    "Timothy Lillicrap": "https://en.wikipedia.org/wiki/Timothy_Lillicrap",
    # Generative models
    "Diederik Kingma": "https://en.wikipedia.org/wiki/Diederik_P._Kingma",
    "Max Welling": "https://en.wikipedia.org/wiki/Max_Welling",
    "Martin Arjovsky": "https://en.wikipedia.org/wiki/Wasserstein_GAN",
    "Jonathan Ho": "https://en.wikipedia.org/wiki/Denoising_diffusion_probabilistic_model",
    "Jascha Sohl-Dickstein": "https://en.wikipedia.org/wiki/Denoising_diffusion_probabilistic_model",
    # NLP
    "Tomas Mikolov": "https://en.wikipedia.org/wiki/Word2vec",
    "Jeffrey Pennington": "https://en.wikipedia.org/wiki/GloVe_(machine_learning)",
    "Matthew Peters": "https://en.wikipedia.org/wiki/ELMo",
    "Jacob Devlin": "https://en.wikipedia.org/wiki/BERT_(language_model)",
    "Ashish Vaswani": "https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture)",
    # Other
    "Evelyn Fix": "https://en.wikipedia.org/wiki/Evelyn_Fix",
    "Joseph Hodges": "https://en.wikipedia.org/wiki/Joseph_Hodges_Jr.",
    "Larry Rafsky": "https://en.wikipedia.org/wiki/Nearest_neighbor_search",
    "Hans-Peter Fischler": "https://en.wikipedia.org/wiki/RANSAC",
    "Robert Bolles": "https://en.wikipedia.org/wiki/RANSAC",
    "Crammer Koby": "https://en.wikipedia.org/wiki/Passive-aggressive_algorithm",
}

# ---------------------------------------------------------------------------
# Known ML/math/stats concepts with Wikipedia URLs
# ---------------------------------------------------------------------------

KNOWN_CONCEPTS: dict[str, str] = {
    # Core statistics
    "Bayesian Inference": "https://en.wikipedia.org/wiki/Bayesian_inference",
    "Bayes Theorem": "https://en.wikipedia.org/wiki/Bayes%27_theorem",
    "Maximum Likelihood Estimation": "https://en.wikipedia.org/wiki/Maximum_likelihood_estimation",
    "Ordinary Least Squares": "https://en.wikipedia.org/wiki/Ordinary_least_squares",
    "Markov Chain Monte Carlo": "https://en.wikipedia.org/wiki/Markov_chain_Monte_Carlo",
    "Monte Carlo Methods": "https://en.wikipedia.org/wiki/Monte_Carlo_method",
    "Monte Carlo Method": "https://en.wikipedia.org/wiki/Monte_Carlo_method",
    "Expectation Maximization": "https://en.wikipedia.org/wiki/Expectation%E2%80%93maximization_algorithm",
    "Stochastic Gradient Descent": "https://en.wikipedia.org/wiki/Stochastic_gradient_descent",
    "Gradient Descent": "https://en.wikipedia.org/wiki/Gradient_descent",
    "Backpropagation": "https://en.wikipedia.org/wiki/Backpropagation",
    "Cross Entropy": "https://en.wikipedia.org/wiki/Cross_entropy",
    "Cross-Entropy": "https://en.wikipedia.org/wiki/Cross_entropy",
    "Kullback-Leibler Divergence": "https://en.wikipedia.org/wiki/Kullback%E2%80%93Leibler_divergence",
    "KL Divergence": "https://en.wikipedia.org/wiki/Kullback%E2%80%93Leibler_divergence",
    "Information Gain": "https://en.wikipedia.org/wiki/Information_gain_(decision_tree)",
    "Entropy": "https://en.wikipedia.org/wiki/Entropy_(information_theory)",
    "Gini Impurity": "https://en.wikipedia.org/wiki/Decision_tree_learning#Gini_impurity",
    "Bootstrap Aggregating": "https://en.wikipedia.org/wiki/Bootstrap_aggregating",
    "Bagging": "https://en.wikipedia.org/wiki/Bootstrap_aggregating",
    "Boosting": "https://en.wikipedia.org/wiki/Boosting_(machine_learning)",
    "Kernel Methods": "https://en.wikipedia.org/wiki/Kernel_method",
    "Kernel Trick": "https://en.wikipedia.org/wiki/Kernel_method",
    "Radial Basis Function": "https://en.wikipedia.org/wiki/Radial_basis_function",
    "Radial Basis Functions": "https://en.wikipedia.org/wiki/Radial_basis_function",
    "Gaussian Process": "https://en.wikipedia.org/wiki/Gaussian_process",
    "Gaussian Processes": "https://en.wikipedia.org/wiki/Gaussian_process",
    "Generalized Linear Model": "https://en.wikipedia.org/wiki/Generalized_linear_model",
    "Generalized Linear Models": "https://en.wikipedia.org/wiki/Generalized_linear_model",
    "Support Vector Machines": "https://en.wikipedia.org/wiki/Support_vector_machine",
    "Support Vector Machine": "https://en.wikipedia.org/wiki/Support_vector_machine",
    "Principal Component Analysis": "https://en.wikipedia.org/wiki/Principal_component_analysis",
    "Singular Value Decomposition": "https://en.wikipedia.org/wiki/Singular_value_decomposition",
    "Non-Negative Matrix Factorization": "https://en.wikipedia.org/wiki/Non-negative_matrix_factorization",
    "Independent Component Analysis": "https://en.wikipedia.org/wiki/Independent_component_analysis",
    "Linear Discriminant Analysis": "https://en.wikipedia.org/wiki/Linear_discriminant_analysis",
    "Manifold Learning": "https://en.wikipedia.org/wiki/Nonlinear_dimensionality_reduction",
    "Dimensionality Reduction": "https://en.wikipedia.org/wiki/Dimensionality_reduction",
    "Random Forests": "https://en.wikipedia.org/wiki/Random_forest",
    "Random Forest": "https://en.wikipedia.org/wiki/Random_forest",
    "Decision Trees": "https://en.wikipedia.org/wiki/Decision_tree_learning",
    "Decision Tree": "https://en.wikipedia.org/wiki/Decision_tree_learning",
    "Gradient Boosting": "https://en.wikipedia.org/wiki/Gradient_boosting",
    "Gradient Boosting Machine": "https://en.wikipedia.org/wiki/Gradient_boosting",
    "Neural Network": "https://en.wikipedia.org/wiki/Neural_network_(machine_learning)",
    "Neural Networks": "https://en.wikipedia.org/wiki/Neural_network_(machine_learning)",
    "Convolutional Neural Network": "https://en.wikipedia.org/wiki/Convolutional_neural_network",
    "Recurrent Neural Network": "https://en.wikipedia.org/wiki/Recurrent_neural_network",
    "Long Short-Term Memory": "https://en.wikipedia.org/wiki/Long_short-term_memory",
    "Transformer": "https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture)",
    "Attention Mechanism": "https://en.wikipedia.org/wiki/Attention_(machine_learning)",
    "Self-Attention": "https://en.wikipedia.org/wiki/Attention_(machine_learning)",
    "Transfer Learning": "https://en.wikipedia.org/wiki/Transfer_learning",
    "Regularization": "https://en.wikipedia.org/wiki/Regularization_(mathematics)",
    "Overfitting": "https://en.wikipedia.org/wiki/Overfitting",
    "Underfitting": "https://en.wikipedia.org/wiki/Overfitting",
    "Bias-Variance Tradeoff": "https://en.wikipedia.org/wiki/Bias%E2%80%93variance_tradeoff",
    "Bias Variance Tradeoff": "https://en.wikipedia.org/wiki/Bias%E2%80%93variance_tradeoff",
    "Cross Validation": "https://en.wikipedia.org/wiki/Cross-validation_(statistics)",
    "Cross-Validation": "https://en.wikipedia.org/wiki/Cross-validation_(statistics)",
    "Confusion Matrix": "https://en.wikipedia.org/wiki/Confusion_matrix",
    "ROC Curve": "https://en.wikipedia.org/wiki/Receiver_operating_characteristic",
    "AUC-ROC": "https://en.wikipedia.org/wiki/Receiver_operating_characteristic",
    "Precision Recall": "https://en.wikipedia.org/wiki/Precision_and_recall",
    "F1 Score": "https://en.wikipedia.org/wiki/F-score",
    "Mean Squared Error": "https://en.wikipedia.org/wiki/Mean_squared_error",
    "RMSE": "https://en.wikipedia.org/wiki/Root_mean_square_deviation",
    "Softmax": "https://en.wikipedia.org/wiki/Softmax_function",
    "Softmax Function": "https://en.wikipedia.org/wiki/Softmax_function",
    "ReLU": "https://en.wikipedia.org/wiki/Rectifier_(neural_networks)",
    "Sigmoid Function": "https://en.wikipedia.org/wiki/Sigmoid_function",
    "Activation Function": "https://en.wikipedia.org/wiki/Activation_function",
    "Batch Normalization": "https://en.wikipedia.org/wiki/Batch_normalization",
    "Dropout": "https://en.wikipedia.org/wiki/Dropout_(neural_networks)",
    "Adam Optimizer": "https://en.wikipedia.org/wiki/Stochastic_gradient_descent#Adam",
    "Learning Rate": "https://en.wikipedia.org/wiki/Learning_rate",
    "Hyperparameter": "https://en.wikipedia.org/wiki/Hyperparameter_(machine_learning)",
    "Hyperparameter Optimization": "https://en.wikipedia.org/wiki/Hyperparameter_optimization",
    "Markov Decision Process": "https://en.wikipedia.org/wiki/Markov_decision_process",
    "Bellman Equation": "https://en.wikipedia.org/wiki/Bellman_equation",
    "Q-Learning": "https://en.wikipedia.org/wiki/Q-learning",
    "Policy Gradient": "https://en.wikipedia.org/wiki/Policy_gradient_method",
    "Reward Function": "https://en.wikipedia.org/wiki/Reward_function",
    "Monte Carlo Tree Search": "https://en.wikipedia.org/wiki/Monte_Carlo_tree_search",
    "Variational Autoencoder": "https://en.wikipedia.org/wiki/Variational_autoencoder",
    "Generative Adversarial Network": "https://en.wikipedia.org/wiki/Generative_adversarial_network",
    "Generative Adversarial Networks": "https://en.wikipedia.org/wiki/Generative_adversarial_network",
    "Diffusion Models": "https://en.wikipedia.org/wiki/Diffusion_model",
    "Word2Vec": "https://en.wikipedia.org/wiki/Word2vec",
    "BERT": "https://en.wikipedia.org/wiki/BERT_(language_model)",
    "GPT": "https://en.wikipedia.org/wiki/Generative_pre-trained_transformer",
    "Perceptron": "https://en.wikipedia.org/wiki/Perceptron",
    "Multilayer Perceptron": "https://en.wikipedia.org/wiki/Multilayer_perceptron",
    "Boltzmann Machine": "https://en.wikipedia.org/wiki/Boltzmann_machine",
    "Restricted Boltzmann Machine": "https://en.wikipedia.org/wiki/Restricted_Boltzmann_machine",
    "Autoencoder": "https://en.wikipedia.org/wiki/Autoencoder",
    "Autoencoders": "https://en.wikipedia.org/wiki/Autoencoder",
    "K-Means Clustering": "https://en.wikipedia.org/wiki/K-means_clustering",
    "DBSCAN": "https://en.wikipedia.org/wiki/DBSCAN",
    "Hierarchical Clustering": "https://en.wikipedia.org/wiki/Hierarchical_clustering",
    "Gaussian Mixture Model": "https://en.wikipedia.org/wiki/Mixture_model#Gaussian_mixture_model",
    "Gaussian Mixture Models": "https://en.wikipedia.org/wiki/Mixture_model#Gaussian_mixture_model",
    "Mean Shift": "https://en.wikipedia.org/wiki/Mean_shift",
    "Spectral Clustering": "https://en.wikipedia.org/wiki/Spectral_clustering",
    "Softmax Regression": "https://en.wikipedia.org/wiki/Multinomial_logistic_regression",
    "Statistical Learning Theory": "https://en.wikipedia.org/wiki/Statistical_learning_theory",
    "Nearest Neighbor": "https://en.wikipedia.org/wiki/Nearest_neighbor_search",
    "Iteratively Reweighted Least Squares": "https://en.wikipedia.org/wiki/Iteratively_reweighted_least_squares",
    "Pool Adjacent Violators Algorithm": "https://en.wikipedia.org/wiki/Isotonic_regression",
    "Bootstrap Aggregating": "https://en.wikipedia.org/wiki/Bootstrap_aggregating",
    "Bagging Predictors": "https://en.wikipedia.org/wiki/Bootstrap_aggregating",
    "Random Subspace Method": "https://en.wikipedia.org/wiki/Random_subspace_method",
    "Multivariate Adaptive Regression Splines": "https://en.wikipedia.org/wiki/Multivariate_adaptive_regression_splines",
    "Least Absolute Deviations": "https://en.wikipedia.org/wiki/Least_absolute_deviations",
    "Statistical Inference": "https://en.wikipedia.org/wiki/Statistical_inference",
    "Ordered Boosting": "https://en.wikipedia.org/wiki/CatBoost",
    "Passive Aggressive Algorithms": "https://en.wikipedia.org/wiki/Passive-aggressive_algorithm",
    "Aggressive Algorithms": "https://en.wikipedia.org/wiki/Passive-aggressive_algorithm",
    "Nearest Neighbor Pattern Classification": "https://en.wikipedia.org/wiki/K-nearest_neighbors_algorithm",
    "Order Restrictions": "https://en.wikipedia.org/wiki/Isotonic_regression",
    "Logit Model": "https://en.wikipedia.org/wiki/Logistic_regression",
    "Compound Poisson Model": "https://en.wikipedia.org/wiki/Compound_Poisson_distribution",
    "Exponential Dispersion Models": "https://en.wikipedia.org/wiki/Exponential_dispersion_model",
    "Inverse Gaussian": "https://en.wikipedia.org/wiki/Inverse_Gaussian_distribution",
    "Maximum Likelihood Sample Consensus": "https://en.wikipedia.org/wiki/RANSAC",
    "Progressive Sample Consensus": "https://en.wikipedia.org/wiki/RANSAC",
    "Random Sample Consensus": "https://en.wikipedia.org/wiki/RANSAC",
    "Repeated Median Estimator": "https://en.wikipedia.org/wiki/Repeated_median_estimator",
    "Machine Learning": "https://en.wikipedia.org/wiki/Machine_learning",
    "Deep Learning": "https://en.wikipedia.org/wiki/Deep_learning",
    "Natural Language Processing": "https://en.wikipedia.org/wiki/Natural_language_processing",
    "Computer Vision": "https://en.wikipedia.org/wiki/Computer_vision",
    "Reinforcement Learning": "https://en.wikipedia.org/wiki/Reinforcement_learning",
    "Semi-Supervised Learning": "https://en.wikipedia.org/wiki/Semi-supervised_learning",
    "Unsupervised Learning": "https://en.wikipedia.org/wiki/Unsupervised_learning",
    "Supervised Learning": "https://en.wikipedia.org/wiki/Supervised_learning",
    "Feature Engineering": "https://en.wikipedia.org/wiki/Feature_engineering",
    "Feature Selection": "https://en.wikipedia.org/wiki/Feature_selection",
    "Ensemble Learning": "https://en.wikipedia.org/wiki/Ensemble_learning",
    "Online Learning": "https://en.wikipedia.org/wiki/Online_machine_learning",
    "Time Series Analysis": "https://en.wikipedia.org/wiki/Time_series",
    "Anomaly Detection": "https://en.wikipedia.org/wiki/Anomaly_detection",
    "Clustering": "https://en.wikipedia.org/wiki/Cluster_analysis",
    "Classification": "https://en.wikipedia.org/wiki/Statistical_classification",
    "Regression Analysis": "https://en.wikipedia.org/wiki/Regression_analysis",
    "Regression": "https://en.wikipedia.org/wiki/Regression_analysis",
    "Lasso": "https://en.wikipedia.org/wiki/Lasso_(statistics)",
    "Ridge Regression": "https://en.wikipedia.org/wiki/Ridge_regression",
    "Elastic Net": "https://en.wikipedia.org/wiki/Elastic_net_regularization",
    "Logistic Regression": "https://en.wikipedia.org/wiki/Logistic_regression",
    "Linear Regression": "https://en.wikipedia.org/wiki/Linear_regression",
    "Biased Estimation": "https://en.wikipedia.org/wiki/Bias_of_an_estimator",
    "Greedy Function Approximation": "https://en.wikipedia.org/wiki/Gradient_boosting",
    "Scalable Tree Boosting System": "https://en.wikipedia.org/wiki/XGBoost",
    "Iterative Partial Least Squares": "https://en.wikipedia.org/wiki/Partial_least_squares_regression",
}

# ---------------------------------------------------------------------------
# Fragment detection patterns
# These text patterns are garbled sentence fragments, not real linkable entities
# ---------------------------------------------------------------------------

FRAGMENT_PREFIXES = (
    "The ", "For ", "In ", "An ", "A ", "Unlike ", "Using ",
    "On ", "At ", "By ", "Of ", "To ", "And ", "But ",
    "With ", "From ", "As ", "Is ", "It ", "This ", "That ",
    "Are ", "Was ", "Not ",
)

FRAGMENT_PATTERNS = [
    # Starts with an article/preposition
    r"^(The|A|An|For|In|Unlike|Using|On|At|By|Of|To|And|With|From|Is|This)\s",
    # Paper citation fragments (e.g. "Regression Shrinkage", "Selection Operator")
    # Very short (1 word) — likely a fragment
    r"^\w+$",
    # Obvious paper title fragments — ends with common partial words
    r"\s+(And|Or|The|A|An)$",
    # Looks like a mid-sentence phrase (contains verb-like words)
    r"\b(appears|unlike|using|based|applied|derived|proposed|known as|called)\b",
]

# Single-word terms that are too vague to link
FRAGMENT_SINGLE_WORDS = {
    "Lambda", "Grid", "Capsules", "Liquid", "Reservoir", "Ants",
    "Strong", "Weak", "Stress", "Softness", "Topics", "Imagined",
    "Few", "Different", "Sigma", "Kernel", "Sigma Points",
}

# ---------------------------------------------------------------------------
# Parse todo-links.md
# ---------------------------------------------------------------------------


def parse_todo_file(path: Path) -> list[tuple[str, list[str]]]:
    """
    Parse todo-links.md and return list of (algorithm_name, [term, ...]).
    """
    sections: list[tuple[str, list[str]]] = []
    current_algo: str | None = None
    current_terms: list[str] = []

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.rstrip()
        # Section header: ### Algorithm Name (date)
        if line.startswith("### "):
            if current_algo is not None:
                sections.append((current_algo, current_terms))
            # Strip the date suffix "(2026-03-11)"
            header = re.sub(r"\s*\(\d{4}-\d{2}-\d{2}\)\s*$", "", line[4:]).strip()
            current_algo = header
            current_terms = []
        # Item: - [ ] `Term` — ...
        elif line.startswith("- [ ] `") or line.startswith("- [x] `"):
            m = re.match(r"^- \[.\] `([^`]+)`", line)
            if m:
                current_terms.append(m.group(1))

    if current_algo is not None:
        sections.append((current_algo, current_terms))

    return sections


# ---------------------------------------------------------------------------
# Classify a term
# ---------------------------------------------------------------------------

# Map algorithm name → MDX slug (used for slug lookups)
def slugify(text: str) -> str:
    """Simple slugification: lowercase, replace spaces/punctuation with hyphens."""
    s = text.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s


def get_all_valid_slugs() -> set[str]:
    slugs: set[str] = set()
    for f in CONTENT_DIR.rglob("*.mdx"):
        slugs.add(f.stem)
    return slugs


# Cache valid slugs at module level for performance
_valid_slugs: set[str] | None = None


def valid_slugs() -> set[str]:
    global _valid_slugs
    if _valid_slugs is None:
        _valid_slugs = get_all_valid_slugs()
    return _valid_slugs


def is_fragment(term: str) -> bool:
    """Return True if the term looks like a garbled sentence fragment."""
    if term in FRAGMENT_SINGLE_WORDS:
        return True
    for pat in FRAGMENT_PATTERNS:
        if re.search(pat, term, re.IGNORECASE):
            return True
    return False


def classify_term(term: str) -> tuple[str, str]:
    """
    Returns (category, wiki_url_or_path).
    Categories: FRAGMENT | INTERNAL | WIKIPEDIA | REVIEW
    """
    if is_fragment(term):
        return "FRAGMENT", ""

    # Check known researcher list
    if term in KNOWN_RESEARCHERS:
        return "WIKIPEDIA", KNOWN_RESEARCHERS[term]

    # Check known concept list
    if term in KNOWN_CONCEPTS:
        return "WIKIPEDIA", KNOWN_CONCEPTS[term]

    # Check if slugified term matches an existing ML Atlas algorithm
    slug = slugify(term)
    if slug in valid_slugs():
        # Find the category for the slug
        for f in CONTENT_DIR.rglob("*.mdx"):
            if f.stem == slug:
                # path: content/algorithms/{category}/{subcategory}/{slug}.mdx
                parts = f.relative_to(CONTENT_DIR).parts
                if len(parts) >= 3:
                    cat = parts[0]
                    return "INTERNAL", f"/algorithms/{cat}/{slug}"
                elif len(parts) >= 1:
                    return "INTERNAL", f"/algorithms/{slug}"
        return "INTERNAL", f"/algorithms/{slug}"

    # Try partial slugifications (e.g. "Random Forests" → "random-forest-classifier")
    CONCEPT_TO_SLUG: dict[str, str] = {
        "Random Forests": "random-forest-classifier",
        "Random Forest": "random-forest-classifier",
        "Decision Trees": "decision-tree-classifier",
        "Decision Tree": "decision-tree-classifier",
        "Gradient Boosting": "gradient-boosting-classifier",
        "Support Vector Machines": "support-vector-machine",
        "Support Vector Machine": "support-vector-machine",
        "Neural Networks": "multilayer-perceptron",
        "Neural Network": "multilayer-perceptron",
        "Gaussian Mixture Models": "gaussian-mixture-model",
        "Gaussian Mixture Model": "gaussian-mixture-model",
        "K-Means Clustering": "k-means",
        "Softmax Regression": "multinomial-logistic-regression",
        "Nearest Neighbor": "k-nearest-neighbors",
        "Nearest Neighbor Pattern Classification": "k-nearest-neighbors",
        "Backpropagation": "backpropagation",
        "Gradient Descent": "gradient-descent",
        "Stochastic Gradient Descent": "sgd",
        "Lasso": "lasso-regression",
        "Ridge Regression": "ridge-regression",
        "Elastic Net": "elastic-net",
        "Logistic Regression": "logistic-regression",
        "Linear Regression": "linear-regression",
        "DBSCAN": "dbscan",
        "Autoencoder": "autoencoder",
        "Autoencoders": "autoencoder",
        "Transformer": "transformer",
        "BERT": "bert",
        "GPT": "gpt",
        "Q-Learning": "q-learning",
        "Perceptron": "perceptron",
        "Multilayer Perceptron": "multilayer-perceptron",
        "Monte Carlo Tree Search": "monte-carlo-tree-search",
        "Variational Autoencoder": "variational-autoencoder",
        "Generative Adversarial Network": "generative-adversarial-network",
        "Generative Adversarial Networks": "generative-adversarial-network",
    }
    if term in CONCEPT_TO_SLUG:
        target_slug = CONCEPT_TO_SLUG[term]
        if target_slug in valid_slugs():
            for f in CONTENT_DIR.rglob("*.mdx"):
                if f.stem == target_slug:
                    parts = f.relative_to(CONTENT_DIR).parts
                    if len(parts) >= 3:
                        cat = parts[0]
                        return "INTERNAL", f"/algorithms/{cat}/{target_slug}"
            return "INTERNAL", f"/algorithms/{target_slug}"

    return "REVIEW", ""


# ---------------------------------------------------------------------------
# Build output files
# ---------------------------------------------------------------------------


def build_triaged(sections: list[tuple[str, list[str]]]) -> str:
    """Build the content of todo-links-triaged.md."""
    lines = [
        "# ML Atlas — Todo Links (Triaged)",
        "",
        "Generated by `scripts/triage_todo_links.py`.",
        "",
        "## Legend",
        "- `[FRAGMENT]` — Garbled sentence fragment; remove from tracking.",
        "- `[INTERNAL]` — Matches an existing ML Atlas algorithm page.",
        "- `[WIKIPEDIA]` — Real person or recognized concept; link to Wikipedia.",
        "- `[REVIEW]`   — Ambiguous; needs manual review.",
        "",
        "---",
        "",
    ]
    for algo, terms in sections:
        lines.append(f"### {algo}")
        for term in terms:
            cat, url = classify_term(term)
            if cat == "FRAGMENT":
                lines.append(f"- [FRAGMENT]  ~~`{term}`~~ — garbled fragment, remove")
            elif cat == "INTERNAL":
                lines.append(f"- [INTERNAL]  `{term}` → [{url}]({url})")
            elif cat == "WIKIPEDIA":
                lines.append(f"- [WIKIPEDIA] `{term}` → [{url}]({url})")
            else:
                lines.append(f"- [REVIEW]    `{term}` — no clear mapping found")
        lines.append("")
    return "\n".join(lines)


def build_wikipedia_list(sections: list[tuple[str, list[str]]]) -> str:
    """Build the content of todo-links-wikipedia.md (actionable Wikipedia list)."""
    lines = [
        "# ML Atlas — Wikipedia Link Targets",
        "",
        "Generated by `scripts/triage_todo_links.py`.",
        "These items have been classified as `[WIKIPEDIA]` and are ready for",
        "`scripts/apply_wiki_links.py` to insert into MDX files.",
        "",
        "Format: `algorithm-slug | Term | Wikipedia URL`",
        "",
        "---",
        "",
    ]

    count = 0
    for algo, terms in sections:
        algo_slug = slugify(algo)
        wiki_items = []
        for term in terms:
            cat, url = classify_term(term)
            if cat == "WIKIPEDIA" and url:
                wiki_items.append((term, url))
        if wiki_items:
            lines.append(f"### {algo}")
            for term, url in wiki_items:
                lines.append(f"- `{algo_slug}` | `{term}` | {url}")
                count += 1
            lines.append("")

    lines.append("---")
    lines.append(f"Total: {count} Wikipedia link targets")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    if not TODO_FILE.exists():
        print(f"ERROR: {TODO_FILE} not found")
        sys.exit(1)

    print(f"Parsing {TODO_FILE} …")
    sections = parse_todo_file(TODO_FILE)

    # Load valid slugs
    _ = valid_slugs()
    print(f"Loaded {len(valid_slugs())} valid algorithm slugs.")
    print(f"Found {len(sections)} algorithm sections.")

    # Count items
    total_items = sum(len(terms) for _, terms in sections)
    print(f"Total items: {total_items}")
    print()

    # Classify all
    counts: dict[str, int] = {"FRAGMENT": 0, "INTERNAL": 0, "WIKIPEDIA": 0, "REVIEW": 0}
    for _, terms in sections:
        for term in terms:
            cat, _ = classify_term(term)
            counts[cat] += 1

    print("Classification summary:")
    for cat, n in counts.items():
        print(f"  {cat:12s} {n:5d}")
    print()

    # Write outputs
    triaged_content = build_triaged(sections)
    TRIAGED_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRIAGED_FILE.write_text(triaged_content, encoding="utf-8")
    print(f"✓ Wrote {TRIAGED_FILE}")

    wiki_content = build_wikipedia_list(sections)
    WIKI_FILE.write_text(wiki_content, encoding="utf-8")
    print(f"✓ Wrote {WIKI_FILE}")


if __name__ == "__main__":
    main()
