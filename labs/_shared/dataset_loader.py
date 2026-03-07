"""Shared dataset loader for ML Atlas labs."""

from sklearn import datasets
import numpy as np

AVAILABLE_DATASETS = ["iris", "digits", "wine", "breast_cancer", "diabetes"]

DATASET_INFO = {
    "iris": {"task": "classification", "n_classes": 3, "description": "Iris flower species"},
    "digits": {"task": "classification", "n_classes": 10, "description": "Handwritten digits (0-9)"},
    "wine": {"task": "classification", "n_classes": 3, "description": "Wine cultivar recognition"},
    "breast_cancer": {"task": "classification", "n_classes": 2, "description": "Breast cancer diagnosis"},
    "diabetes": {"task": "regression", "n_classes": None, "description": "Diabetes progression"},
}


def load_dataset(name: str) -> tuple[np.ndarray, np.ndarray]:
    """Load a sklearn built-in dataset. Returns (X, y)."""
    loaders = {
        "iris": datasets.load_iris,
        "digits": datasets.load_digits,
        "wine": datasets.load_wine,
        "breast_cancer": datasets.load_breast_cancer,
        "diabetes": datasets.load_diabetes,
    }
    if name not in loaders:
        raise ValueError(f"Unknown dataset: {name}. Choose from {AVAILABLE_DATASETS}")
    data = loaders[name](return_X_y=False)
    return data.data, data.target


def load_dataset_with_names(name: str):
    """Load a sklearn dataset and return (X, y, feature_names, target_names)."""
    loaders = {
        "iris": datasets.load_iris,
        "digits": datasets.load_digits,
        "wine": datasets.load_wine,
        "breast_cancer": datasets.load_breast_cancer,
        "diabetes": datasets.load_diabetes,
    }
    data = loaders[name](return_X_y=False)
    feature_names = list(getattr(data, "feature_names", [f"feature_{i}" for i in range(data.data.shape[1])]))
    target_names = list(getattr(data, "target_names", []))
    return data.data, data.target, feature_names, target_names
