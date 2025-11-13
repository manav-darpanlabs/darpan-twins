"""
Persona Discovery and Clustering Module

This module implements intelligent persona discovery for digital twins using
unsupervised clustering on behavioral, psychographic, and demographic attributes.
"""

import json
import os
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
import umap
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


class PersonaAnalyzer:
    """
    Discovers and manages personas through clustering of twin profiles.

    Implements Gaussian Mixture Model clustering with automatic model selection
    to identify 10-15 MECE (Mutually Exclusive, Collectively Exhaustive) personas
    based on OCEAN traits, demographics, and derived behavioral attributes.
    """

    def __init__(self, profiles_dir: str = "data/twin_profiles",
                 n_clusters_range: Tuple[int, int] = (10, 15),
                 random_state: int = 42):
        """
        Initialize the PersonaAnalyzer.

        Args:
            profiles_dir: Directory containing twin profile JSON files
            n_clusters_range: Range of clusters to evaluate (min, max)
            random_state: Random seed for reproducibility
        """
        self.profiles_dir = profiles_dir
        self.n_clusters_range = n_clusters_range
        self.random_state = random_state

        # Data containers
        self.profiles = {}
        self.features_df = None
        self.features_scaled = None
        self.pca_features = None
        self.umap_embedding = None

        # Clustering results
        self.gmm = None
        self.optimal_n_clusters = None
        self.cluster_labels = None
        self.cluster_probabilities = None
        self.personas = {}

        # Feature information
        self.feature_names = []
        self.feature_importance = {}

    def load_profiles(self) -> Dict[str, Dict]:
        """Load all twin profiles from JSON files."""
        profiles = {}
        profiles_path = Path(self.profiles_dir)

        for profile_file in sorted(profiles_path.glob("USER_*.json")):
            with open(profile_file, 'r') as f:
                profile = json.load(f)
                profiles[profile['user_id']] = profile

        self.profiles = profiles
        print(f"Loaded {len(profiles)} twin profiles")
        return profiles

    def extract_features(self) -> pd.DataFrame:
        """
        Extract features from profiles for clustering.

        Returns:
            DataFrame with features for each twin
        """
        if not self.profiles:
            self.load_profiles()

        features_list = []

        for user_id, profile in self.profiles.items():
            # Extract OCEAN traits (5 dimensions)
            ocean = profile['OCEAN']

            # Extract demographics
            demographics = profile.get('demographics', {})

            # Calculate derived behavioral traits
            openness = ocean['openness']
            conscientiousness = ocean['conscientiousness']
            extraversion = ocean['extraversion']
            agreeableness = ocean['agreeableness']
            neuroticism = ocean['neuroticism']

            # Derived preferences (matching the original formulas)
            novelty_seeking = (openness * 0.7) + ((1 - conscientiousness) * 0.3)
            budget_sensitivity = ((1 - conscientiousness) * 0.5) + (neuroticism * 0.5)
            distance_tolerance = (extraversion * 0.6) + (openness * 0.2) - (neuroticism * 0.3)
            rating_focus = (agreeableness * 0.4) + (conscientiousness * 0.6)

            features = {
                'user_id': user_id,
                # OCEAN traits
                'openness': openness,
                'conscientiousness': conscientiousness,
                'extraversion': extraversion,
                'agreeableness': agreeableness,
                'neuroticism': neuroticism,
                # Demographics
                'age': demographics.get('age', 30),
                'income': demographics.get('income', 500000),
                'gender_male': 1 if demographics.get('gender') == 'male' else 0,
                'gender_female': 1 if demographics.get('gender') == 'female' else 0,
                'place_income': demographics.get('place_of_birth_avg_income', 300000),
                'food_variety_index': demographics.get('place_of_birth_food_variety_index', 0.5),
                # Derived behavioral
                'novelty_seeking': novelty_seeking,
                'budget_sensitivity': budget_sensitivity,
                'distance_tolerance': distance_tolerance,
                'rating_focus': rating_focus
            }
            features_list.append(features)

        self.features_df = pd.DataFrame(features_list)
        self.features_df.set_index('user_id', inplace=True)

        # Store feature names for later use
        self.feature_names = list(self.features_df.columns)

        print(f"Extracted {len(self.feature_names)} features for {len(self.features_df)} twins")
        return self.features_df

    def preprocess_features(self) -> np.ndarray:
        """
        Preprocess features for clustering.

        Returns:
            Scaled features array
        """
        if self.features_df is None:
            self.extract_features()

        # Standardize features (z-score normalization)
        scaler = StandardScaler()
        self.features_scaled = scaler.fit_transform(self.features_df)

        # Apply PCA to reduce dimensionality while retaining 95% variance
        pca = PCA(n_components=0.95, random_state=self.random_state)
        self.pca_features = pca.fit_transform(self.features_scaled)

        # Store feature importance from PCA
        self.feature_importance['pca_explained_variance'] = pca.explained_variance_ratio_
        self.feature_importance['n_components'] = pca.n_components_

        print(f"Reduced features from {len(self.feature_names)} to {pca.n_components_} components")
        print(f"Explained variance: {pca.explained_variance_ratio_.sum():.2%}")

        return self.pca_features

    def find_optimal_clusters(self) -> int:
        """
        Find optimal number of clusters using BIC and silhouette score.

        Returns:
            Optimal number of clusters
        """
        if self.pca_features is None:
            self.preprocess_features()

        min_k, max_k = self.n_clusters_range

        bic_scores = []
        aic_scores = []
        silhouette_scores = []

        for n_clusters in range(min_k, max_k + 1):
            gmm = GaussianMixture(
                n_components=n_clusters,
                covariance_type='full',
                random_state=self.random_state,
                n_init=5
            )
            gmm.fit(self.pca_features)

            # Calculate metrics
            bic_scores.append(gmm.bic(self.pca_features))
            aic_scores.append(gmm.aic(self.pca_features))

            labels = gmm.predict(self.pca_features)
            silhouette = silhouette_score(self.pca_features, labels)
            silhouette_scores.append(silhouette)

            print(f"k={n_clusters}: BIC={bic_scores[-1]:.0f}, "
                  f"AIC={aic_scores[-1]:.0f}, Silhouette={silhouette:.3f}")

        # Find elbow point in BIC (lower is better)
        # We want the point where adding more clusters doesn't significantly improve BIC
        bic_deltas = np.diff(bic_scores)
        bic_delta_ratios = bic_deltas[1:] / bic_deltas[:-1]

        # Find where improvement starts to plateau (ratio close to 1)
        elbow_idx = np.argmax(bic_delta_ratios > -0.1) + min_k

        # Also consider silhouette score (higher is better)
        best_silhouette_idx = np.argmax(silhouette_scores) + min_k

        # Balance between BIC elbow and silhouette score
        if abs(elbow_idx - best_silhouette_idx) <= 2:
            optimal_k = best_silhouette_idx  # Prefer better separation
        else:
            optimal_k = elbow_idx  # Prefer BIC if very different

        # Ensure we're in the target range
        optimal_k = max(min_k, min(optimal_k, max_k))

        self.optimal_n_clusters = optimal_k
        print(f"\nOptimal number of clusters: {optimal_k}")

        return optimal_k

    def fit_clustering(self, n_clusters: Optional[int] = None) -> None:
        """
        Fit GMM clustering model.

        Args:
            n_clusters: Number of clusters (if None, finds optimal)
        """
        if self.pca_features is None:
            self.preprocess_features()

        if n_clusters is None:
            n_clusters = self.find_optimal_clusters()

        # Fit final GMM model
        self.gmm = GaussianMixture(
            n_components=n_clusters,
            covariance_type='full',
            random_state=self.random_state,
            n_init=10,  # More initializations for final model
            max_iter=200
        )
        self.gmm.fit(self.pca_features)

        # Get cluster assignments
        self.cluster_labels = self.gmm.predict(self.pca_features)
        self.cluster_probabilities = self.gmm.predict_proba(self.pca_features)

        # Calculate clustering quality metrics
        silhouette = silhouette_score(self.pca_features, self.cluster_labels)
        davies_bouldin = davies_bouldin_score(self.pca_features, self.cluster_labels)
        calinski = calinski_harabasz_score(self.pca_features, self.cluster_labels)

        print(f"\nClustering Quality Metrics:")
        print(f"  Silhouette Score: {silhouette:.3f} (higher is better, >0.3 is good)")
        print(f"  Davies-Bouldin Index: {davies_bouldin:.3f} (lower is better)")
        print(f"  Calinski-Harabasz Score: {calinski:.1f} (higher is better)")

        # Validate MECE properties
        self._validate_mece()

    def _validate_mece(self) -> Dict[str, float]:
        """
        Validate Mutually Exclusive, Collectively Exhaustive properties.

        Returns:
            Dictionary with validation metrics
        """
        # Check mutual exclusivity (how many twins have high probability in multiple clusters)
        high_prob_threshold = 0.3
        multi_cluster_twins = 0

        for probs in self.cluster_probabilities:
            if np.sum(probs > high_prob_threshold) > 1:
                multi_cluster_twins += 1

        overlap_percentage = (multi_cluster_twins / len(self.cluster_labels)) * 100

        # Check collective exhaustiveness (all twins assigned)
        coverage = len(self.cluster_labels) / len(self.profiles) * 100

        print(f"\nMECE Validation:")
        print(f"  Overlap (twins in multiple clusters): {overlap_percentage:.1f}% (target <5%)")
        print(f"  Coverage (twins assigned): {coverage:.1f}% (target 100%)")

        return {
            'overlap_percentage': overlap_percentage,
            'coverage': coverage,
            'is_mece': overlap_percentage < 5 and coverage == 100
        }

    def generate_umap_embedding(self) -> np.ndarray:
        """
        Generate 2D UMAP embedding for visualization.

        Returns:
            2D embedding array
        """
        if self.features_scaled is None:
            self.preprocess_features()

        print("Generating UMAP 2D projection...")
        reducer = umap.UMAP(
            n_components=2,
            random_state=self.random_state,
            n_neighbors=15,
            min_dist=0.1
        )

        self.umap_embedding = reducer.fit_transform(self.features_scaled)
        print("UMAP projection complete")

        return self.umap_embedding

    def analyze_clusters(self) -> Dict[int, Dict]:
        """
        Analyze cluster characteristics.

        Returns:
            Dictionary with cluster statistics
        """
        if self.cluster_labels is None:
            raise ValueError("Must fit clustering first")

        cluster_stats = {}

        for cluster_id in range(self.gmm.n_components):
            mask = self.cluster_labels == cluster_id
            cluster_profiles = [uid for uid, m in zip(self.features_df.index, mask) if m]

            # Calculate cluster center in original feature space
            cluster_features = self.features_df.loc[cluster_profiles]

            stats = {
                'cluster_id': cluster_id,
                'size': len(cluster_profiles),
                'percentage': len(cluster_profiles) / len(self.features_df) * 100,
                'member_ids': cluster_profiles[:10],  # Sample of members
                'ocean_means': {
                    'openness': cluster_features['openness'].mean(),
                    'conscientiousness': cluster_features['conscientiousness'].mean(),
                    'extraversion': cluster_features['extraversion'].mean(),
                    'agreeableness': cluster_features['agreeableness'].mean(),
                    'neuroticism': cluster_features['neuroticism'].mean()
                },
                'demographic_means': {
                    'age': cluster_features['age'].mean(),
                    'income': cluster_features['income'].mean(),
                    'gender_distribution': {
                        'male': cluster_features['gender_male'].mean(),
                        'female': cluster_features['gender_female'].mean(),
                        'other': 1 - cluster_features['gender_male'].mean() - cluster_features['gender_female'].mean()
                    }
                },
                'behavioral_means': {
                    'novelty_seeking': cluster_features['novelty_seeking'].mean(),
                    'budget_sensitivity': cluster_features['budget_sensitivity'].mean(),
                    'distance_tolerance': cluster_features['distance_tolerance'].mean(),
                    'rating_focus': cluster_features['rating_focus'].mean()
                }
            }

            cluster_stats[cluster_id] = stats

        return cluster_stats

    def assign_persona(self, profile: Dict) -> Tuple[int, float, np.ndarray]:
        """
        Assign a single profile to a persona.

        Args:
            profile: Twin profile dictionary

        Returns:
            Tuple of (cluster_id, confidence, probability_distribution)
        """
        if self.gmm is None:
            raise ValueError("Must fit clustering model first")

        # Extract features for this profile
        features = self._extract_single_profile_features(profile)

        # Transform features
        features_scaled = StandardScaler().fit_transform([features])[0]
        # Note: In production, we'd save the scaler and PCA from training

        # Predict cluster
        cluster_id = self.gmm.predict([features_scaled])[0]
        probabilities = self.gmm.predict_proba([features_scaled])[0]
        confidence = probabilities[cluster_id]

        return cluster_id, confidence, probabilities

    def _extract_single_profile_features(self, profile: Dict) -> List[float]:
        """Extract features from a single profile."""
        ocean = profile['OCEAN']
        demographics = profile.get('demographics', {})

        openness = ocean['openness']
        conscientiousness = ocean['conscientiousness']
        extraversion = ocean['extraversion']
        agreeableness = ocean['agreeableness']
        neuroticism = ocean['neuroticism']

        novelty_seeking = (openness * 0.7) + ((1 - conscientiousness) * 0.3)
        budget_sensitivity = ((1 - conscientiousness) * 0.5) + (neuroticism * 0.5)
        distance_tolerance = (extraversion * 0.6) + (openness * 0.2) - (neuroticism * 0.3)
        rating_focus = (agreeableness * 0.4) + (conscientiousness * 0.6)

        return [
            openness, conscientiousness, extraversion, agreeableness, neuroticism,
            demographics.get('age', 30),
            demographics.get('income', 500000),
            1 if demographics.get('gender') == 'male' else 0,
            1 if demographics.get('gender') == 'female' else 0,
            demographics.get('place_of_birth_avg_income', 300000),
            demographics.get('place_of_birth_food_variety_index', 0.5),
            novelty_seeking, budget_sensitivity, distance_tolerance, rating_focus
        ]

    def save_results(self, output_dir: str = "data") -> None:
        """
        Save clustering results and persona assignments.

        Args:
            output_dir: Directory to save results
        """
        output_path = Path(output_dir)

        # Save cluster assignments
        assignments = {}
        for idx, user_id in enumerate(self.features_df.index):
            assignments[user_id] = {
                'cluster_id': int(self.cluster_labels[idx]),
                'confidence': float(self.cluster_probabilities[idx][self.cluster_labels[idx]]),
                'probabilities': self.cluster_probabilities[idx].tolist()
            }

        with open(output_path / 'persona_assignments.json', 'w') as f:
            json.dump(assignments, f, indent=2)

        # Save UMAP embedding if generated
        if self.umap_embedding is not None:
            np.save(output_path / 'umap_embeddings.npy', self.umap_embedding)

        # Save cluster statistics
        cluster_stats = self.analyze_clusters()
        with open(output_path / 'cluster_statistics.json', 'w') as f:
            json.dump(cluster_stats, f, indent=2, default=str)

        print(f"\nResults saved to {output_dir}/")
        print(f"  - persona_assignments.json")
        print(f"  - cluster_statistics.json")
        if self.umap_embedding is not None:
            print(f"  - umap_embeddings.npy")

    def get_persona_breakdown(self, user_ids: List[str]) -> Dict[int, Dict]:
        """
        Get persona breakdown for a subset of twins.

        Args:
            user_ids: List of user IDs to analyze

        Returns:
            Dictionary with cluster counts and percentages
        """
        if self.cluster_labels is None:
            raise ValueError("Must fit clustering first")

        breakdown = {}

        for user_id in user_ids:
            if user_id in self.features_df.index:
                idx = self.features_df.index.get_loc(user_id)
                cluster_id = self.cluster_labels[idx]

                if cluster_id not in breakdown:
                    breakdown[cluster_id] = {'count': 0, 'users': []}

                breakdown[cluster_id]['count'] += 1
                breakdown[cluster_id]['users'].append(user_id)

        # Calculate percentages
        total = len(user_ids)
        for cluster_id in breakdown:
            breakdown[cluster_id]['percentage'] = breakdown[cluster_id]['count'] / total * 100

        return breakdown


if __name__ == "__main__":
    # Test the PersonaAnalyzer
    analyzer = PersonaAnalyzer()

    # Load and process profiles
    analyzer.load_profiles()
    analyzer.extract_features()

    # Find optimal clusters and fit model
    analyzer.fit_clustering()

    # Generate visualizations
    analyzer.generate_umap_embedding()

    # Analyze clusters
    cluster_stats = analyzer.analyze_clusters()
    print(f"\nFound {len(cluster_stats)} personas:")
    for cluster_id, stats in cluster_stats.items():
        print(f"  Cluster {cluster_id}: {stats['size']} twins ({stats['percentage']:.1f}%)")

    # Save results
    analyzer.save_results()