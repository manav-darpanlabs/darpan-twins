"""
Simple test for pre-computed persona loading (without pytest dependency)
"""

import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from twins.dynamic_persona_analyzer import DynamicPersonaAnalyzer


def test_load_precomputed_assignments():
    """Test loading pre-computed persona assignments from JSON file."""
    print("\n🧪 Testing load_precomputed_assignments()...")

    analyzer = DynamicPersonaAnalyzer()

    # Load pre-computed assignments
    assignments_path = "data/persona_assignments.json"

    try:
        analyzer.load_precomputed_assignments(assignments_path)
        print("  ✅ Method exists and executes")
    except AttributeError as e:
        print(f"  ❌ Method doesn't exist: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

    # Verify assignments were loaded
    if not hasattr(analyzer, 'precomputed_assignments'):
        print("  ❌ Precomputed assignments not stored")
        return False

    if analyzer.precomputed_assignments is None:
        print("  ❌ Assignments should not be None")
        return False

    if len(analyzer.precomputed_assignments) == 0:
        print("  ❌ Assignments should not be empty")
        return False

    print(f"  ✅ Loaded {len(analyzer.precomputed_assignments)} assignments")

    # Verify structure of loaded data
    sample_user = list(analyzer.precomputed_assignments.keys())[0]
    sample_assignment = analyzer.precomputed_assignments[sample_user]

    if 'cluster_id' not in sample_assignment:
        print("  ❌ Assignment missing cluster_id")
        return False

    if not isinstance(sample_assignment['cluster_id'], int):
        print("  ❌ cluster_id should be int")
        return False

    print("  ✅ Assignment structure is correct")
    return True


def test_get_twins_by_cluster_with_precomputed():
    """Test getting twins by cluster using pre-computed assignments."""
    print("\n🧪 Testing get_twins_by_cluster() with precomputed...")

    analyzer = DynamicPersonaAnalyzer()

    # Load pre-computed assignments
    assignments_path = "data/persona_assignments.json"

    try:
        analyzer.load_precomputed_assignments(assignments_path)
    except Exception as e:
        print(f"  ❌ Failed to load assignments: {e}")
        return False

    # Try to get twins from cluster 0
    cluster_id = 0

    try:
        twins = analyzer.get_twins_by_cluster(cluster_id)
    except Exception as e:
        print(f"  ❌ Failed to get twins: {e}")
        return False

    # Verify results
    if not isinstance(twins, list):
        print("  ❌ Should return a list")
        return False

    if len(twins) == 0:
        print(f"  ❌ Cluster {cluster_id} should have at least one twin")
        return False

    print(f"  ✅ Retrieved {len(twins)} twins from cluster {cluster_id}")

    # Verify all returned twins are actually in cluster 0
    for twin_id in twins[:5]:  # Check first 5
        if twin_id not in analyzer.precomputed_assignments:
            print(f"  ❌ {twin_id} not in assignments")
            return False
        if analyzer.precomputed_assignments[twin_id]['cluster_id'] != cluster_id:
            print(f"  ❌ {twin_id} not in cluster {cluster_id}")
            return False

    print("  ✅ All twins belong to correct cluster")
    return True


def test_get_twins_by_cluster_without_loading():
    """Test that getting twins fails gracefully when nothing is loaded."""
    print("\n🧪 Testing get_twins_by_cluster() without loading...")

    analyzer = DynamicPersonaAnalyzer()

    # Should raise error when no clustering or precomputed data exists
    try:
        twins = analyzer.get_twins_by_cluster(0)
        print("  ❌ Should have raised ValueError")
        return False
    except ValueError as e:
        print(f"  ✅ Correctly raised ValueError: {e}")
        return True
    except Exception as e:
        print(f"  ⚠️  Raised different exception: {type(e).__name__}: {e}")
        return True


if __name__ == "__main__":
    print("=" * 60)
    print("PRE-COMPUTED PERSONA LOADING TEST SUITE")
    print("=" * 60)

    tests = [
        test_load_precomputed_assignments,
        test_get_twins_by_cluster_with_precomputed,
        test_get_twins_by_cluster_without_loading,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{len(tests)} passed, {failed}/{len(tests)} failed")
    print("=" * 60)

    if failed > 0:
        print("\n⚠️  Tests are failing as expected (RED phase)")
        print("   Now we'll implement the functionality to make them pass.")
