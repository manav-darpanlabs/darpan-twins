"""
Test Suite for Dynamic Persona Clustering

Tests the real-time clustering with user controls and minimum cluster size enforcement.
"""

import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from twins.dynamic_persona_analyzer import DynamicPersonaAnalyzer


def test_minimum_cluster_size_enforcement():
    """Test that minimum cluster size is enforced properly."""
    print("\n🧪 Testing Minimum Cluster Size Enforcement...")

    analyzer = DynamicPersonaAnalyzer()
    analyzer.extract_features()

    # Test with min_cluster_size = 50
    labels, metrics = analyzer.cluster_with_algorithm(
        algorithm='gmm',
        n_clusters=10,
        min_cluster_size=50
    )

    print(f"  Target clusters: 10")
    print(f"  Actual clusters: {metrics['n_clusters']}")
    print(f"  Min size: {metrics['min_size']}")
    print(f"  Max size: {metrics['max_size']}")
    print(f"  Avg size: {metrics['avg_size']:.1f}")

    # Verify all clusters meet minimum size
    assert metrics['min_size'] >= 50, f"Found cluster with only {metrics['min_size']} twins (minimum: 50)"

    print(f"  ✅ All clusters have at least 50 twins")
    return True


def test_multiple_algorithms():
    """Test that all clustering algorithms work correctly."""
    print("\n🧪 Testing Multiple Clustering Algorithms...")

    analyzer = DynamicPersonaAnalyzer()
    analyzer.extract_features()

    algorithms = ['gmm', 'kmeans', 'hierarchical', 'dbscan']
    results = {}

    for algorithm in algorithms:
        print(f"\n  Testing {algorithm.upper()}...")

        labels, metrics = analyzer.cluster_with_algorithm(
            algorithm=algorithm,
            n_clusters=8,
            min_cluster_size=50
        )

        results[algorithm] = {
            'n_clusters': metrics['n_clusters'],
            'silhouette': metrics['silhouette'],
            'min_size': metrics['min_size'],
            'coverage': metrics['coverage']
        }

        print(f"    Clusters: {metrics['n_clusters']}")
        print(f"    Min size: {metrics['min_size']}")
        print(f"    Silhouette: {metrics['silhouette']:.3f}")
        print(f"    Coverage: {metrics['coverage']:.1f}%")

        # Basic validations
        assert metrics['coverage'] == 100.0, f"{algorithm}: Coverage not 100%"
        assert metrics['min_size'] >= 50, f"{algorithm}: Cluster too small"

    print(f"\n  ✅ All {len(algorithms)} algorithms working correctly")

    # Compare results
    print("\n  Algorithm Comparison:")
    print(f"  {'Algorithm':<15} {'Clusters':<10} {'Silhouette':<12} {'Min Size':<10}")
    print("  " + "-" * 50)
    for algo, result in results.items():
        print(f"  {algo.upper():<15} {result['n_clusters']:<10} {result['silhouette']:<12.3f} {result['min_size']:<10}")

    return True


def test_cluster_characteristics():
    """Test that cluster characteristics are computed correctly."""
    print("\n🧪 Testing Cluster Characteristics...")

    analyzer = DynamicPersonaAnalyzer()
    analyzer.extract_features()

    labels, metrics = analyzer.cluster_with_algorithm(
        algorithm='gmm',
        n_clusters=8,
        min_cluster_size=50
    )

    characteristics = analyzer.get_cluster_characteristics(labels)

    print(f"  Computed characteristics for {len(characteristics)} clusters")

    # Verify each cluster has required fields
    required_fields = ['size', 'percentage', 'members', 'ocean_means',
                      'demographic_means', 'behavioral_means']

    for cluster_id, char in characteristics.items():
        for field in required_fields:
            assert field in char, f"Cluster {cluster_id} missing field: {field}"

        # Verify OCEAN traits
        ocean = char['ocean_means']
        for trait in ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']:
            assert 0 <= ocean[trait] <= 1, f"OCEAN trait {trait} out of range: {ocean[trait]}"

        # Verify behavioral traits
        behavioral = char['behavioral_means']
        for trait in ['novelty_seeking', 'budget_sensitivity', 'distance_tolerance', 'rating_focus']:
            assert 0 <= behavioral[trait] <= 1.5, f"Behavioral trait {trait} out of range: {behavioral[trait]}"

    print(f"  ✅ All cluster characteristics valid")

    # Show sample cluster
    sample_cluster = list(characteristics.keys())[0]
    char = characteristics[sample_cluster]
    print(f"\n  Sample Cluster {sample_cluster}:")
    print(f"    Size: {char['size']} ({char['percentage']:.1f}%)")
    print(f"    Avg Age: {char['demographic_means']['age']:.1f}")
    print(f"    Avg Income: ₹{char['demographic_means']['income']:,.0f}")
    print(f"    Novelty Seeking: {char['behavioral_means']['novelty_seeking']:.2f}")
    print(f"    Budget Sensitivity: {char['behavioral_means']['budget_sensitivity']:.2f}")

    return True


def test_umap_generation():
    """Test UMAP embedding generation."""
    print("\n🧪 Testing UMAP Embedding Generation...")

    analyzer = DynamicPersonaAnalyzer()
    analyzer.extract_features()

    # Generate UMAP
    umap_embedding = analyzer.generate_umap_embedding(n_neighbors=15)

    print(f"  UMAP shape: {umap_embedding.shape}")
    assert umap_embedding.shape[0] == 1000, "UMAP should have 1000 points"
    assert umap_embedding.shape[1] == 2, "UMAP should be 2D"

    print(f"  X range: [{umap_embedding[:, 0].min():.2f}, {umap_embedding[:, 0].max():.2f}]")
    print(f"  Y range: [{umap_embedding[:, 1].min():.2f}, {umap_embedding[:, 1].max():.2f}]")

    print(f"  ✅ UMAP embedding generated successfully")
    return True


def test_get_twins_by_cluster():
    """Test retrieval of twins by cluster."""
    print("\n🧪 Testing Twin Retrieval by Cluster...")

    analyzer = DynamicPersonaAnalyzer()
    analyzer.extract_features()

    labels, metrics = analyzer.cluster_with_algorithm(
        algorithm='gmm',
        n_clusters=8,
        min_cluster_size=50
    )

    # Get twins from first cluster
    cluster_id = 0
    twins = analyzer.get_twins_by_cluster(cluster_id)

    print(f"  Cluster {cluster_id} has {len(twins)} twins")
    print(f"  Sample twins: {twins[:5]}")

    assert len(twins) >= 50, f"Cluster {cluster_id} has fewer than 50 twins"
    assert all(isinstance(twin, str) for twin in twins), "All twins should be strings"
    assert all(twin.startswith("USER_") for twin in twins), "All twins should start with USER_"

    print(f"  ✅ Twin retrieval working correctly")
    return True


def test_cluster_summary():
    """Test cluster summary dataframe."""
    print("\n🧪 Testing Cluster Summary DataFrame...")

    analyzer = DynamicPersonaAnalyzer()
    analyzer.extract_features()

    labels, metrics = analyzer.cluster_with_algorithm(
        algorithm='gmm',
        n_clusters=8,
        min_cluster_size=50
    )

    summary = analyzer.get_cluster_summary()

    print(f"  Summary shape: {summary.shape}")
    print(f"\n{summary.to_string()}")

    assert len(summary) == metrics['n_clusters'], "Summary should have one row per cluster"
    assert 'Cluster' in summary.columns, "Summary should have Cluster column"
    assert 'Size' in summary.columns, "Summary should have Size column"

    print(f"\n  ✅ Cluster summary generated successfully")
    return True


def test_save_dynamic_clustering():
    """Test saving dynamic clustering results."""
    print("\n🧪 Testing Save Dynamic Clustering...")

    analyzer = DynamicPersonaAnalyzer()
    analyzer.extract_features()

    labels, metrics = analyzer.cluster_with_algorithm(
        algorithm='kmeans',
        n_clusters=10,
        min_cluster_size=50
    )

    # Generate UMAP
    analyzer.generate_umap_embedding()

    # Save
    analyzer.save_current_clustering(output_dir="data")

    # Verify files exist
    import os
    assert os.path.exists("data/dynamic_persona_assignments.json"), "Assignments file not created"
    assert os.path.exists("data/dynamic_cluster_statistics.json"), "Statistics file not created"
    assert os.path.exists("data/dynamic_umap_embeddings.npy"), "UMAP file not created"

    # Load and verify assignments
    with open("data/dynamic_persona_assignments.json", 'r') as f:
        assignments = json.load(f)

    print(f"  Saved {len(assignments)} assignments")
    assert len(assignments) == 1000, "Should have 1000 assignments"

    # Verify assignment structure
    sample_user = list(assignments.keys())[0]
    assert 'cluster_id' in assignments[sample_user], "Assignment should have cluster_id"
    assert 'algorithm' in assignments[sample_user], "Assignment should have algorithm"
    assert assignments[sample_user]['algorithm'] == 'kmeans', "Algorithm should be kmeans"

    print(f"  ✅ Clustering results saved successfully")
    return True


def run_all_tests():
    """Run all dynamic clustering tests."""
    print("=" * 60)
    print("DYNAMIC PERSONA CLUSTERING TEST SUITE")
    print("=" * 60)

    tests = [
        ("Minimum Cluster Size", test_minimum_cluster_size_enforcement),
        ("Multiple Algorithms", test_multiple_algorithms),
        ("Cluster Characteristics", test_cluster_characteristics),
        ("UMAP Generation", test_umap_generation),
        ("Twin Retrieval", test_get_twins_by_cluster),
        ("Cluster Summary", test_cluster_summary),
        ("Save Clustering", test_save_dynamic_clustering)
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
        except AssertionError as e:
            failed += 1
            print(f"  ❌ {test_name} FAILED: {e}")
        except Exception as e:
            failed += 1
            print(f"  ❌ {test_name} ERROR: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"TEST SUMMARY: {passed}/{len(tests)} passed, {failed}/{len(tests)} failed")
    print("=" * 60)

    if failed == 0:
        print("\n🎉 All tests passed! Dynamic clustering is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Review the output above.")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
