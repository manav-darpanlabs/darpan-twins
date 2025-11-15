"""
Dynamic Persona Discovery and Clustering Module

This module implements real-time, configurable clustering with multiple algorithms
and user-defined parameters for persona discovery.
"""

import json
import os
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
import umap
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


class DynamicPersonaAnalyzer:
    """
    Dynamic persona discovery with real-time clustering and user controls.
    """

    CLUSTERING_ALGORITHMS = {
        'gmm': 'Gaussian Mixture Model (Soft clustering)',
        'kmeans': 'K-Means (Hard clustering)',
        'hierarchical': 'Hierarchical (Tree-based)',
        'dbscan': 'DBSCAN (Density-based)'
    }

    def __init__(self, profiles_dir: str = "data/twin_profiles"):
        """Initialize the dynamic analyzer."""
        self.profiles_dir = profiles_dir
        self.profiles = {}
        self.features_df = None
        self.features_scaled = None
        self.pca_features = None
        self.umap_embedding = None
        self.current_model = None
        self.current_labels = None
        self.current_params = {}
        self.precomputed_assignments = None

        # Load profiles on initialization
        self.load_profiles()

    def load_profiles(self) -> Dict[str, Dict]:
        """Load all twin profiles from JSON files."""
        profiles = {}
        profiles_path = Path(self.profiles_dir)

        for profile_file in sorted(profiles_path.glob("user_*.json")):
            with open(profile_file, 'r') as f:
                profile = json.load(f)
                profiles[profile['user_id']] = profile

        self.profiles = profiles
        return profiles

    def load_precomputed_assignments(self, filepath: str) -> Dict[str, Dict]:
        """
        Load pre-computed persona assignments from a JSON file.

        This allows using pre-computed persona assignments without
        re-running the clustering algorithm.

        Args:
            filepath: Path to the persona assignments JSON file

        Returns:
            Dictionary mapping user_id to assignment data

        Raises:
            FileNotFoundError: If the assignments file doesn't exist
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Assignments file not found: {filepath}")

        with open(filepath, 'r') as f:
            assignments_raw = json.load(f)

        assignments = {}
        for user_id, assignment_data in assignments_raw.items():
            cluster_id = assignment_data.get('cluster_id')

            if isinstance(cluster_id, str):
                cluster_id = int(cluster_id)

            assignments[user_id] = {
                'cluster_id': cluster_id,
                'probabilities': assignment_data.get('probabilities', [])
            }

        self.precomputed_assignments = assignments
        return assignments

    def extract_features(self) -> pd.DataFrame:
        """Extract features from profiles for clustering."""
        if not self.profiles:
            self.load_profiles()

        features_list = []

        for user_id, profile in self.profiles.items():
            ocean = profile['OCEAN']
            demographics = profile.get('demographics', {})

            # Extract all features
            openness = ocean['openness']
            conscientiousness = ocean['conscientiousness']
            extraversion = ocean['extraversion']
            agreeableness = ocean['agreeableness']
            neuroticism = ocean['neuroticism']

            # Derived preferences
            novelty_seeking = (openness * 0.7) + ((1 - conscientiousness) * 0.3)
            budget_sensitivity = ((1 - conscientiousness) * 0.5) + (neuroticism * 0.5)
            distance_tolerance = (extraversion * 0.6) + (openness * 0.2) - (neuroticism * 0.3)
            rating_focus = (agreeableness * 0.4) + (conscientiousness * 0.6)

            features = {
                'user_id': user_id,
                'openness': openness,
                'conscientiousness': conscientiousness,
                'extraversion': extraversion,
                'agreeableness': agreeableness,
                'neuroticism': neuroticism,
                'age': demographics.get('age', 30),
                'income': demographics.get('income', 500000),
                'gender_male': 1 if demographics.get('gender') == 'male' else 0,
                'gender_female': 1 if demographics.get('gender') == 'female' else 0,
                'place_income': demographics.get('place_of_birth_avg_income', 300000),
                'food_variety_index': demographics.get('place_of_birth_food_variety_index', 0.5),
                'novelty_seeking': novelty_seeking,
                'budget_sensitivity': budget_sensitivity,
                'distance_tolerance': distance_tolerance,
                'rating_focus': rating_focus
            }
            features_list.append(features)

        self.features_df = pd.DataFrame(features_list)
        self.features_df.set_index('user_id', inplace=True)

        # Standardize features
        scaler = StandardScaler()
        self.features_scaled = scaler.fit_transform(self.features_df)

        # Apply PCA
        pca = PCA(n_components=0.95, random_state=42)
        self.pca_features = pca.fit_transform(self.features_scaled)

        return self.features_df

    def cluster_with_algorithm(self,
                              algorithm: str = 'gmm',
                              n_clusters: int = 8,
                              min_cluster_size: int = 50,
                              random_state: int = 42) -> Tuple[np.ndarray, Dict]:
        """
        Perform clustering with specified algorithm and parameters.

        Args:
            algorithm: Clustering algorithm to use
            n_clusters: Target number of clusters
            min_cluster_size: Minimum twins per cluster
            random_state: Random seed for reproducibility

        Returns:
            Tuple of (cluster labels, metrics)
        """
        if self.pca_features is None:
            self.extract_features()

        # Store parameters
        self.current_params = {
            'algorithm': algorithm,
            'n_clusters': n_clusters,
            'min_cluster_size': min_cluster_size,
            'random_state': random_state
        }

        # Initial clustering
        labels = self._apply_algorithm(algorithm, n_clusters, random_state)

        # Merge small clusters
        labels = self._merge_small_clusters(labels, min_cluster_size)

        # Calculate metrics
        metrics = self._calculate_metrics(labels)

        self.current_labels = labels
        return labels, metrics

    def _apply_algorithm(self, algorithm: str, n_clusters: int, random_state: int) -> np.ndarray:
        """Apply the selected clustering algorithm."""

        if algorithm == 'gmm':
            model = GaussianMixture(
                n_components=n_clusters,
                covariance_type='full',
                random_state=random_state,
                n_init=5
            )
            model.fit(self.pca_features)
            labels = model.predict(self.pca_features)
            self.current_model = model

        elif algorithm == 'kmeans':
            model = KMeans(
                n_clusters=n_clusters,
                random_state=random_state,
                n_init=10
            )
            labels = model.fit_predict(self.pca_features)
            self.current_model = model

        elif algorithm == 'hierarchical':
            model = AgglomerativeClustering(
                n_clusters=n_clusters,
                linkage='ward'
            )
            labels = model.fit_predict(self.pca_features)
            self.current_model = model

        elif algorithm == 'dbscan':
            # For DBSCAN, we need to tune eps parameter
            # Using a heuristic based on data
            from sklearn.neighbors import NearestNeighbors
            neighbors = NearestNeighbors(n_neighbors=50)
            neighbors_fit = neighbors.fit(self.pca_features)
            distances, indices = neighbors_fit.kneighbors(self.pca_features)
            distances = np.sort(distances[:, -1], axis=0)

            # Find elbow point
            eps = np.percentile(distances, 95)

            model = DBSCAN(
                eps=eps,
                min_samples=20
            )
            labels = model.fit_predict(self.pca_features)

            # Handle noise points (-1 labels)
            noise_mask = labels == -1
            if noise_mask.any():
                # Assign noise points to nearest cluster
                from sklearn.neighbors import KNeighborsClassifier
                clean_mask = ~noise_mask
                if clean_mask.any():
                    knn = KNeighborsClassifier(n_neighbors=5)
                    knn.fit(self.pca_features[clean_mask], labels[clean_mask])
                    labels[noise_mask] = knn.predict(self.pca_features[noise_mask])

            self.current_model = model

        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

        return labels

    def _merge_small_clusters(self, labels: np.ndarray, min_size: int) -> np.ndarray:
        """Merge clusters smaller than min_size with their nearest neighbors."""
        unique_labels, counts = np.unique(labels, return_counts=True)

        # Identify small clusters
        small_clusters = unique_labels[counts < min_size]

        if len(small_clusters) == 0:
            return labels

        # Calculate cluster centers
        cluster_centers = {}
        for label in unique_labels:
            mask = labels == label
            cluster_centers[label] = np.mean(self.pca_features[mask], axis=0)

        # Merge small clusters with nearest large cluster
        new_labels = labels.copy()
        for small_label in small_clusters:
            # Find nearest large cluster
            min_dist = float('inf')
            merge_target = None

            for large_label in unique_labels:
                if large_label != small_label and counts[unique_labels == large_label][0] >= min_size:
                    dist = np.linalg.norm(
                        cluster_centers[small_label] - cluster_centers[large_label]
                    )
                    if dist < min_dist:
                        min_dist = dist
                        merge_target = large_label

            if merge_target is not None:
                new_labels[labels == small_label] = merge_target

        # Renumber clusters to be sequential
        unique_new = np.unique(new_labels)
        label_map = {old: new for new, old in enumerate(unique_new)}
        final_labels = np.array([label_map[label] for label in new_labels])

        return final_labels

    def _calculate_metrics(self, labels: np.ndarray) -> Dict:
        """Calculate clustering quality metrics."""
        metrics = {}

        n_clusters = len(np.unique(labels))

        if n_clusters > 1:
            metrics['silhouette'] = silhouette_score(self.pca_features, labels)
            metrics['davies_bouldin'] = davies_bouldin_score(self.pca_features, labels)
            metrics['calinski_harabasz'] = calinski_harabasz_score(self.pca_features, labels)
        else:
            metrics['silhouette'] = 0
            metrics['davies_bouldin'] = 0
            metrics['calinski_harabasz'] = 0

        # Cluster sizes
        unique_labels, counts = np.unique(labels, return_counts=True)
        metrics['n_clusters'] = n_clusters
        metrics['cluster_sizes'] = dict(zip(unique_labels.tolist(), counts.tolist()))
        metrics['min_size'] = int(counts.min())
        metrics['max_size'] = int(counts.max())
        metrics['avg_size'] = float(counts.mean())

        # MECE validation
        metrics['coverage'] = len(labels) / len(self.profiles) * 100

        return metrics

    def get_cluster_characteristics(self, labels: np.ndarray) -> Dict:
        """Get detailed characteristics for each cluster."""
        characteristics = {}

        for cluster_id in np.unique(labels):
            mask = labels == cluster_id
            cluster_profiles = self.features_df.index[mask].tolist()
            cluster_features = self.features_df.loc[cluster_profiles]

            characteristics[int(cluster_id)] = {
                'size': int(mask.sum()),
                'percentage': float(mask.sum() / len(labels) * 100),
                'members': cluster_profiles[:10],  # Sample members
                'ocean_means': {
                    'openness': float(cluster_features['openness'].mean()),
                    'conscientiousness': float(cluster_features['conscientiousness'].mean()),
                    'extraversion': float(cluster_features['extraversion'].mean()),
                    'agreeableness': float(cluster_features['agreeableness'].mean()),
                    'neuroticism': float(cluster_features['neuroticism'].mean())
                },
                'demographic_means': {
                    'age': float(cluster_features['age'].mean()),
                    'income': float(cluster_features['income'].mean()),
                    'gender_distribution': {
                        'male': float(cluster_features['gender_male'].mean()),
                        'female': float(cluster_features['gender_female'].mean()),
                        'other': float(1 - cluster_features['gender_male'].mean() -
                                      cluster_features['gender_female'].mean())
                    }
                },
                'behavioral_means': {
                    'novelty_seeking': float(cluster_features['novelty_seeking'].mean()),
                    'budget_sensitivity': float(cluster_features['budget_sensitivity'].mean()),
                    'distance_tolerance': float(cluster_features['distance_tolerance'].mean()),
                    'rating_focus': float(cluster_features['rating_focus'].mean())
                }
            }

        return characteristics

    def generate_umap_embedding(self, n_neighbors: int = 15) -> np.ndarray:
        """Generate 2D UMAP embedding for visualization."""
        if self.features_scaled is None:
            self.extract_features()

        reducer = umap.UMAP(
            n_components=2,
            random_state=42,
            n_neighbors=n_neighbors,
            min_dist=0.1
        )

        self.umap_embedding = reducer.fit_transform(self.features_scaled)
        return self.umap_embedding

    def get_twins_by_cluster(self, cluster_id: int) -> List[str]:
        """
        Get list of twin IDs in a specific cluster.

        Uses dynamic clustering results if available, otherwise falls back
        to pre-computed assignments if loaded.

        Args:
            cluster_id: The cluster ID to get twins for

        Returns:
            List of twin user IDs in the specified cluster

        Raises:
            ValueError: If neither clustering nor precomputed assignments exist
        """
        if self.current_labels is not None:
            mask = self.current_labels == cluster_id
            return self.features_df.index[mask].tolist()

        if self.precomputed_assignments is not None:
            twins = [
                user_id
                for user_id, assignment in self.precomputed_assignments.items()
                if assignment['cluster_id'] == cluster_id
            ]
            return twins

        raise ValueError(
            "No clustering performed yet and no precomputed assignments loaded. "
            "Either run clustering or load precomputed assignments first."
        )

    def get_cluster_summary(self) -> pd.DataFrame:
        """Get a summary dataframe of all clusters."""
        if self.current_labels is None:
            raise ValueError("No clustering performed yet")

        characteristics = self.get_cluster_characteristics(self.current_labels)

        summary_data = []
        for cluster_id, char in characteristics.items():
            summary_data.append({
                'Cluster': cluster_id,
                'Size': char['size'],
                'Percentage': f"{char['percentage']:.1f}%",
                'Avg Age': f"{char['demographic_means']['age']:.1f}",
                'Avg Income': f"₹{char['demographic_means']['income']/100000:.1f}L",
                'Openness': f"{char['ocean_means']['openness']:.2f}",
                'Conscientiousness': f"{char['ocean_means']['conscientiousness']:.2f}",
                'Novelty': f"{char['behavioral_means']['novelty_seeking']:.2f}",
                'Budget': f"{char['behavioral_means']['budget_sensitivity']:.2f}"
            })

        return pd.DataFrame(summary_data)

    def save_current_clustering(self, output_dir: str = "data") -> None:
        """Save current clustering results."""
        if self.current_labels is None:
            raise ValueError("No clustering performed yet")

        output_path = Path(output_dir)

        # Save assignments
        assignments = {}
        for idx, user_id in enumerate(self.features_df.index):
            assignments[user_id] = {
                'cluster_id': int(self.current_labels[idx]),
                'algorithm': self.current_params.get('algorithm', 'unknown')
            }

        with open(output_path / 'dynamic_persona_assignments.json', 'w') as f:
            json.dump(assignments, f, indent=2)

        # Save cluster characteristics
        characteristics = self.get_cluster_characteristics(self.current_labels)
        with open(output_path / 'dynamic_cluster_statistics.json', 'w') as f:
            json.dump(characteristics, f, indent=2)

        # Save UMAP if exists
        if self.umap_embedding is not None:
            np.save(output_path / 'dynamic_umap_embeddings.npy', self.umap_embedding)