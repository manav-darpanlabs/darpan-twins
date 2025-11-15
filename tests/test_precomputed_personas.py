"""
Test Suite for Pre-computed Persona Loading

Tests the ability to load and use pre-computed persona assignments
without re-running clustering.
"""

import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pytest
from pathlib import Path
from twins.dynamic_persona_analyzer import DynamicPersonaAnalyzer


def test_load_precomputed_assignments():
    """Test loading pre-computed persona assignments from JSON file."""
    analyzer = DynamicPersonaAnalyzer()

    # Load pre-computed assignments
    assignments_path = "data/persona_assignments.json"
    analyzer.load_precomputed_assignments(assignments_path)

    # Verify assignments were loaded
    assert hasattr(analyzer, 'precomputed_assignments'), "Precomputed assignments not stored"
    assert analyzer.precomputed_assignments is not None, "Assignments should not be None"
    assert len(analyzer.precomputed_assignments) > 0, "Assignments should not be empty"

    # Verify structure of loaded data
    sample_user = list(analyzer.precomputed_assignments.keys())[0]
    sample_assignment = analyzer.precomputed_assignments[sample_user]

    assert 'cluster_id' in sample_assignment, "Assignment missing cluster_id"
    assert isinstance(sample_assignment['cluster_id'], int), "cluster_id should be int"


def test_load_precomputed_assignments_with_probabilities():
    """Test loading pre-computed assignments that include probabilities."""
    analyzer = DynamicPersonaAnalyzer()

    # Load pre-computed assignments
    assignments_path = "data/persona_assignments.json"
    analyzer.load_precomputed_assignments(assignments_path)

    # Check if probabilities exist in the data
    sample_user = list(analyzer.precomputed_assignments.keys())[0]
    sample_assignment = analyzer.precomputed_assignments[sample_user]

    if 'probabilities' in sample_assignment:
        assert isinstance(sample_assignment['probabilities'], list), "Probabilities should be a list"
        assert len(sample_assignment['probabilities']) > 0, "Probabilities should not be empty"


def test_load_precomputed_assignments_file_not_found():
    """Test error handling when assignment file doesn't exist."""
    analyzer = DynamicPersonaAnalyzer()

    with pytest.raises(FileNotFoundError):
        analyzer.load_precomputed_assignments("data/nonexistent_file.json")


def test_get_twins_by_cluster_with_precomputed():
    """Test getting twins by cluster using pre-computed assignments."""
    analyzer = DynamicPersonaAnalyzer()

    # Load pre-computed assignments
    assignments_path = "data/persona_assignments.json"
    analyzer.load_precomputed_assignments(assignments_path)

    # Try to get twins from cluster 0
    cluster_id = 0
    twins = analyzer.get_twins_by_cluster(cluster_id)

    # Verify results
    assert isinstance(twins, list), "Should return a list"
    assert len(twins) > 0, f"Cluster {cluster_id} should have at least one twin"

    # Verify all returned twins are actually in cluster 0
    for twin_id in twins:
        assert twin_id in analyzer.precomputed_assignments, f"{twin_id} not in assignments"
        assert analyzer.precomputed_assignments[twin_id]['cluster_id'] == cluster_id, \
            f"{twin_id} not in cluster {cluster_id}"


def test_get_twins_by_cluster_multiple_clusters():
    """Test getting twins from multiple different clusters."""
    analyzer = DynamicPersonaAnalyzer()

    # Load pre-computed assignments
    assignments_path = "data/persona_assignments.json"
    analyzer.load_precomputed_assignments(assignments_path)

    # Get all unique cluster IDs
    cluster_ids = set(
        assignment['cluster_id']
        for assignment in analyzer.precomputed_assignments.values()
    )

    # Test first 3 clusters
    for cluster_id in list(cluster_ids)[:3]:
        twins = analyzer.get_twins_by_cluster(cluster_id)
        assert len(twins) > 0, f"Cluster {cluster_id} should have twins"


def test_get_twins_by_cluster_without_loading():
    """Test that getting twins fails gracefully when nothing is loaded."""
    analyzer = DynamicPersonaAnalyzer()

    # Should raise error when no clustering or precomputed data exists
    with pytest.raises(ValueError, match="No clustering.*performed|No.*assignments.*loaded"):
        analyzer.get_twins_by_cluster(0)


def test_precomputed_vs_dynamic_consistency():
    """
    Test that precomputed assignments match the profile persona data.

    This verifies that twin profiles were updated with the same
    persona assignments that are in the precomputed file.
    """
    analyzer = DynamicPersonaAnalyzer()
    analyzer.load_precomputed_assignments("data/persona_assignments.json")

    # Sample 10 random twins
    import random
    sample_twins = random.sample(list(analyzer.precomputed_assignments.keys()), 10)

    for twin_id in sample_twins:
        # Get cluster from precomputed assignments
        precomputed_cluster = analyzer.precomputed_assignments[twin_id]['cluster_id']

        # Get cluster from profile (if exists)
        profile = analyzer.profiles.get(twin_id)
        if profile and 'persona' in profile:
            profile_cluster = profile['persona']['cluster_id']
            assert precomputed_cluster == profile_cluster, \
                f"{twin_id}: precomputed cluster {precomputed_cluster} != profile cluster {profile_cluster}"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
