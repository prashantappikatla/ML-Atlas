"""K-Means Clustering - Interactive Lab for ML Atlas."""

import sys
from pathlib import Path

import numpy as np
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "_shared"))
from dataset_loader import load_dataset_with_names, AVAILABLE_DATASETS
from plot_utils import create_scatter_plot

# --- Page Config ---
st.set_page_config(
    page_title="K-Means Clustering Lab | ML Atlas",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Header ---
st.title("K-Means Clustering")
st.markdown(
    "[← Back to Algorithm Page](http://localhost:3000/algorithms/unsupervised/kmeans)"
)
st.markdown(
    "Experiment with K-Means clustering by adjusting parameters and exploring different datasets."
)

# --- Sidebar Controls ---
with st.sidebar:
    st.header("Dataset")
    dataset_name = st.selectbox("Dataset", AVAILABLE_DATASETS, index=0)

    st.header("Parameters")
    n_clusters = st.slider("Number of Clusters (k)", min_value=2, max_value=10, value=3)
    init_method = st.selectbox("Initialization", ["k-means++", "random"])
    max_iter = st.slider("Max Iterations", min_value=10, max_value=500, value=300, step=10)
    n_init = st.slider("Number of Initializations", min_value=1, max_value=20, value=10)
    random_state = st.number_input("Random Seed", value=42, min_value=0, max_value=9999)

    st.header("Visualization")
    scale_data = st.checkbox("Standardize Features", value=True)
    show_centroids = st.checkbox("Show Centroids", value=True)

# --- Load Data ---
X, y_true, feature_names, target_names = load_dataset_with_names(dataset_name)

if scale_data:
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
else:
    X_scaled = X

# --- Fit Model ---
model = KMeans(
    n_clusters=n_clusters,
    init=init_method,
    max_iter=max_iter,
    n_init=n_init,
    random_state=random_state,
)
labels = model.fit_predict(X_scaled)

# --- Metrics ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Clusters", n_clusters)
col2.metric("Inertia", f"{model.inertia_:.2f}")

if n_clusters > 1 and len(set(labels)) > 1:
    sil = silhouette_score(X_scaled, labels)
    db = davies_bouldin_score(X_scaled, labels)
    col3.metric("Silhouette Score", f"{sil:.3f}", help="Higher is better (range: -1 to 1)")
    col4.metric("Davies-Bouldin", f"{db:.3f}", help="Lower is better")

st.divider()

# --- Visualization (PCA to 2D) ---
col_plot, col_info = st.columns([3, 1])

with col_plot:
    st.subheader("Cluster Visualization (PCA 2D)")
    pca = PCA(n_components=2, random_state=42)
    X_2d = pca.fit_transform(X_scaled)

    fig = create_scatter_plot(
        X_2d,
        labels,
        title=f"K-Means Clusters (k={n_clusters}) on {dataset_name}",
        x_label=f"PC1 ({pca.explained_variance_ratio_[0]:.1%} variance)",
        y_label=f"PC2 ({pca.explained_variance_ratio_[1]:.1%} variance)",
    )
    st.pyplot(fig)

with col_info:
    st.subheader("Cluster Sizes")
    unique, counts = np.unique(labels, return_counts=True)
    for cluster_id, count in zip(unique, counts):
        st.metric(f"Cluster {cluster_id}", f"{count} samples")

# --- Elbow Method ---
with st.expander("Elbow Method — Find Optimal k"):
    st.write("Compare inertia across different values of k to find the 'elbow'.")
    k_range = range(2, min(11, len(X_scaled)))
    inertias = []
    for k in k_range:
        km = KMeans(n_clusters=k, n_init=5, random_state=42)
        km.fit(X_scaled)
        inertias.append(km.inertia_)

    import matplotlib.pyplot as plt
    fig_elbow, ax = plt.subplots(figsize=(8, 4))
    ax.plot(list(k_range), inertias, marker="o", linewidth=2)
    ax.axvline(x=n_clusters, color="red", linestyle="--", alpha=0.7, label=f"Current k={n_clusters}")
    ax.set_xlabel("Number of Clusters (k)")
    ax.set_ylabel("Inertia (Within-cluster Sum of Squares)")
    ax.set_title("Elbow Method")
    ax.legend()
    plt.tight_layout()
    st.pyplot(fig_elbow)
