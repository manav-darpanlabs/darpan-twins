#!/usr/bin/env python3
"""
Validate that the Streamlit app can import and run basic operations.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def validate_imports():
    """Validate all imports work."""
    print("=" * 60)
    print("VALIDATING STREAMLIT APP")
    print("=" * 60)

    print("\n1. Checking imports...")
    try:
        import streamlit as st
        print("   ✓ streamlit")

        from twins.twin_runtime import TwinRuntime
        print("   ✓ TwinRuntime")

        from twins.twin_profile import TwinProfile
        print("   ✓ TwinProfile")

        from twins.tools import DecisionTool
        print("   ✓ DecisionTool")

        from twins.prompts_llm import build_decider_prompt, build_analyst_prompt
        print("   ✓ build_decider_prompt")
        print("   ✓ build_analyst_prompt")

        print("\n✅ All imports successful!")
        return True

    except Exception as e:
        print(f"\n❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_profile_loading():
    """Validate profile loading works."""
    print("\n2. Checking profile loading...")
    try:
        from twins.twin_profile import TwinProfile

        # Check if profiles directory exists
        profiles_dir = Path("data/twin_profiles")
        if not profiles_dir.exists():
            print(f"   ❌ Profiles directory not found: {profiles_dir}")
            return False

        # Count profiles
        profiles = list(profiles_dir.glob("USER_*.json"))
        print(f"   ✓ Found {len(profiles)} user profiles")

        if len(profiles) == 0:
            print("   ❌ No profiles found!")
            return False

        # Try loading first profile
        first_profile = profiles[0]
        profile = TwinProfile.from_json(str(first_profile))
        print(f"   ✓ Loaded test profile: {profile.user_id}")
        print(f"     - Openness: {profile.openness:.2f}")
        print(f"     - Conscientiousness: {profile.conscientiousness:.2f}")

        print("\n✅ Profile loading works!")
        return True

    except Exception as e:
        print(f"\n❌ Profile loading error: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_rag_data():
    """Validate RAG data exists."""
    print("\n3. Checking RAG data...")
    try:
        rag_path = Path("data/rag_examples.json")
        if not rag_path.exists():
            print(f"   ⚠️  RAG examples not found: {rag_path}")
            print("      Run: python scripts/build_rag_examples.py")
            return False

        # Check file size
        size_mb = rag_path.stat().st_size / 1024 / 1024
        print(f"   ✓ RAG examples found: {size_mb:.1f} MB")

        # Check embeddings cache
        cache_path = Path("data/rag_embeddings.npy")
        if cache_path.exists():
            cache_mb = cache_path.stat().st_size / 1024 / 1024
            print(f"   ✓ Embeddings cache found: {cache_mb:.1f} MB")
        else:
            print(f"   ℹ️  Embeddings cache not found (will be generated on first use)")

        print("\n✅ RAG data ready!")
        return True

    except Exception as e:
        print(f"\n❌ RAG data error: {e}")
        return False


def validate_env():
    """Validate .env configuration."""
    print("\n4. Checking .env configuration...")
    try:
        import os
        from dotenv import load_dotenv

        # Load .env
        env_path = Path(".env")
        if not env_path.exists():
            print(f"   ❌ .env file not found!")
            print("      Create .env with OPENAI_API_KEY")
            return False

        load_dotenv()

        # Check provider
        provider = os.getenv("LLM_PROVIDER", "none")
        model = os.getenv("LLM_MODEL", "none")
        api_key = os.getenv("OPENAI_API_KEY", "")

        print(f"   ✓ LLM_PROVIDER: {provider}")
        print(f"   ✓ LLM_MODEL: {model}")

        if api_key:
            masked_key = api_key[:8] + "..." + api_key[-4:]
            print(f"   ✓ OPENAI_API_KEY: {masked_key}")
        else:
            print(f"   ❌ OPENAI_API_KEY not set!")
            return False

        print("\n✅ Environment configured!")
        return True

    except Exception as e:
        print(f"\n❌ Environment error: {e}")
        return False


def validate_decision_pipeline():
    """Validate decision pipeline works."""
    print("\n5. Testing decision pipeline...")
    try:
        from twins.twin_runtime import TwinRuntime

        # Load a test profile
        twin = TwinRuntime.from_profile_path("data/twin_profiles/USER_001.json")

        # Create simple test cards
        card_a = {
            "name": "Test Restaurant A",
            "cuisine": "italian",
            "rating_avg": 4.5,
            "delivery_time_min": 30,
            "distance_km": 3.0,
            "dish_price": 400,
            "delivery_fee": 20,
            "num_reviews": 2000,
            "coupon_text": "",
            "sponsored": 0,
            "coupon_available": 0
        }

        card_b = {
            "name": "Test Restaurant B",
            "cuisine": "chinese",
            "rating_avg": 4.3,
            "delivery_time_min": 25,
            "distance_km": 2.5,
            "dish_price": 350,
            "delivery_fee": 15,
            "num_reviews": 1500,
            "coupon_text": "SAVE20",
            "sponsored": 0,
            "coupon_available": 1
        }

        context = {
            "hour_of_day": 19,
            "is_weekend": 0,
            "temperature_c": 28,
            "precip_mm": 0
        }

        print("   ⏳ Running decision pipeline (this may take a few seconds)...")
        result = twin.choose_between_cards(card_a, card_b, context)

        # Validate result structure
        assert "action" in result, "Missing 'action' field"
        assert "rationale" in result, "Missing 'rationale' field"
        assert "meta" in result, "Missing 'meta' field"

        meta = result["meta"]
        assert "confidence" in meta, "Missing 'confidence' in meta"
        assert "key_factors" in meta, "Missing 'key_factors' in meta"
        assert "decider_response" in meta, "Missing 'decider_response' in meta"
        assert "analyst_extraction" in meta, "Missing 'analyst_extraction' in meta"
        assert "agent_pipeline" in meta, "Missing 'agent_pipeline' in meta"

        print(f"   ✓ Decision: Card {result['action']}")
        print(f"   ✓ Confidence: {meta['confidence']:.2f}")
        print(f"   ✓ Key factors: {', '.join(meta['key_factors'])}")

        # Check pipeline status
        pipeline = meta["agent_pipeline"]
        print(f"   ✓ Stage 1: {pipeline.get('stage_1', 'N/A')}")
        print(f"   ✓ Stage 2: {pipeline.get('stage_2', 'N/A')}")
        print(f"   ✓ Status: {pipeline.get('extraction_status', 'N/A')}")

        print("\n✅ Decision pipeline works!")
        return True

    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validations."""
    results = []

    results.append(("Imports", validate_imports()))
    results.append(("Profile Loading", validate_profile_loading()))
    results.append(("RAG Data", validate_rag_data()))
    results.append(("Environment", validate_env()))
    results.append(("Decision Pipeline", validate_decision_pipeline()))

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n🎉 ALL VALIDATIONS PASSED!")
        print("\n✅ Streamlit app is ready to run!")
        print("\nTo start the app:")
        print("  streamlit run app_streamlit.py")
    else:
        failed = [name for name, passed in results if not passed]
        print(f"\n⚠️  {len(failed)} validation(s) failed: {', '.join(failed)}")
        print("   Please fix the issues above before running the app")

    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
