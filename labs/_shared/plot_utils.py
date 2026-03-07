"""Shared plotting utilities for ML Atlas labs."""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.figure


def create_scatter_plot(
    X: np.ndarray,
    labels: np.ndarray,
    title: str = "Scatter Plot",
    x_label: str = "Feature 1",
    y_label: str = "Feature 2",
    feature_indices: tuple[int, int] = (0, 1),
) -> matplotlib.figure.Figure:
    """Create a 2D scatter plot from two features of X, colored by labels."""
    fig, ax = plt.subplots(figsize=(8, 6))
    scatter = ax.scatter(
        X[:, feature_indices[0]],
        X[:, feature_indices[1]],
        c=labels,
        cmap="tab10",
        alpha=0.7,
        s=40,
    )
    plt.colorbar(scatter, ax=ax, label="Label")
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    plt.tight_layout()
    return fig


def create_decision_boundary_plot(
    model,
    X: np.ndarray,
    y: np.ndarray,
    title: str = "Decision Boundary",
    resolution: int = 200,
) -> matplotlib.figure.Figure:
    """Plot decision boundary for a 2-feature dataset."""
    x_min, x_max = X[:, 0].min() - 0.5, X[:, 0].max() + 0.5
    y_min, y_max = X[:, 1].min() - 0.5, X[:, 1].max() + 0.5

    xx, yy = np.meshgrid(
        np.linspace(x_min, x_max, resolution),
        np.linspace(y_min, y_max, resolution),
    )
    Z = model.predict(np.c_[xx.ravel(), yy.ravel()])
    Z = Z.reshape(xx.shape)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.contourf(xx, yy, Z, alpha=0.3, cmap="tab10")
    ax.scatter(X[:, 0], X[:, 1], c=y, cmap="tab10", edgecolors="k", s=40)
    ax.set_title(title)
    plt.tight_layout()
    return fig
