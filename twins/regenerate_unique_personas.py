"""
Script to regenerate personas with unique, meaningful names
"""

import json
import os
from typing import Dict
from dotenv import load_dotenv
import openai

load_dotenv()


def generate_unique_persona_name(cluster_stats: Dict, existing_names: list) -> Dict:
    """Generate a unique persona name that doesn't exist in the list"""

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OpenAI API key not found")

    client = openai.OpenAI(api_key=api_key)

    ocean = cluster_stats['ocean_means']
    demographics = cluster_stats['demographic_means']
    behavioral = cluster_stats['behavioral_means']

    # Create a more detailed prompt to ensure uniqueness
    prompt = f"""
You are creating a unique customer persona name for a food delivery platform segment.

CLUSTER CHARACTERISTICS:
Personality Traits (OCEAN, 0-1 scale):
- Openness: {ocean['openness']:.2f}
- Conscientiousness: {ocean['conscientiousness']:.2f}
- Extraversion: {ocean['extraversion']:.2f}
- Agreeableness: {ocean['agreeableness']:.2f}
- Neuroticism: {ocean['neuroticism']:.2f}

Demographics:
- Average Age: {demographics['age']:.1f} years
- Average Income: ₹{demographics['income']:,.0f}
- Gender: {demographics['gender_distribution']['male']:.0%} male, {demographics['gender_distribution']['female']:.0%} female

Behavioral Preferences:
- Novelty Seeking: {behavioral['novelty_seeking']:.2f}
- Budget Sensitivity: {behavioral['budget_sensitivity']:.2f}
- Distance Tolerance: {behavioral['distance_tolerance']:.2f}
- Rating Focus: {behavioral['rating_focus']:.2f}

Size: {cluster_stats['size']} people ({cluster_stats['percentage']:.1f}% of population)

ALREADY USED NAMES (DO NOT USE THESE OR SIMILAR):
{', '.join(existing_names)}

Based on the PRIMARY distinguishing characteristics of this cluster, create a persona with:

1. A UNIQUE, SPECIFIC name (2-3 words) that captures their key trait. Examples of the style (but create new ones):
   - For high openness + low budget: "Thrifty Adventurers"
   - For high conscientiousness + high income: "Premium Planners"
   - For high neuroticism + budget focus: "Anxious Savers"
   - For high extraversion + novelty: "Social Explorers"
   - For high agreeableness + quality: "Harmony Seekers"

2. A one-sentence description (max 15 words)
3. Key behavioral traits (3-4 bullet points)
4. Typical food preferences
5. Decision-making pattern
6. A representative quote

IMPORTANT: The name must be DIFFERENT from any existing names and should reflect the MOST DOMINANT trait combination.

Format as JSON:
{{
    "name": "Unique Persona Name",
    "tagline": "One-sentence description",
    "key_traits": ["trait1", "trait2", "trait3"],
    "food_preferences": "Description",
    "decision_pattern": "How they choose",
    "representative_quote": "What they might say"
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert in consumer segmentation. Create unique, non-overlapping persona names."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,  # Higher temperature for more creativity
            response_format={"type": "json_object"}
        )

        persona_def = json.loads(response.choices[0].message.content)

        # Verify the name is actually unique
        if persona_def['name'] in existing_names:
            # Try again with even more emphasis
            persona_def['name'] = f"{persona_def['name']} Plus"  # Fallback modification

        return persona_def

    except Exception as e:
        print(f"Error generating persona: {e}")
        # Fallback name generation based on top traits
        if behavioral['budget_sensitivity'] > 0.6:
            base = "Budget"
        elif behavioral['novelty_seeking'] > 0.6:
            base = "Adventure"
        elif behavioral['rating_focus'] > 0.6:
            base = "Quality"
        else:
            base = "Balanced"

        # Add modifiers based on demographics
        if demographics['age'] < 25:
            modifier = "Young"
        elif demographics['age'] > 45:
            modifier = "Mature"
        elif demographics['income'] > 700000:
            modifier = "Premium"
        else:
            modifier = "Smart"

        name = f"{modifier} {base} Seekers {cluster_stats['cluster_id']}"

        return {
            "name": name,
            "tagline": f"A unique customer segment",
            "key_traits": ["Diverse preferences", "Value-conscious", "Quality-aware"],
            "food_preferences": "Varied based on context",
            "decision_pattern": "Context-dependent choices",
            "representative_quote": "I choose what fits my needs"
        }


def regenerate_all_personas():
    """Regenerate all personas with unique names"""

    # Load cluster statistics
    with open("data/cluster_statistics.json", 'r') as f:
        cluster_stats = json.load(f)

    # Generate new personas with unique names
    personas = {}
    existing_names = []

    print("Regenerating personas with unique names...")
    print("=" * 60)

    # Sort clusters by size for consistent ordering
    sorted_clusters = sorted(cluster_stats.items(),
                           key=lambda x: x[1]['size'],
                           reverse=True)

    for cluster_id, stats in sorted_clusters:
        print(f"\nGenerating persona for cluster {cluster_id} (size: {stats['size']})...")

        # Try up to 3 times to get a unique name
        for attempt in range(3):
            persona_def = generate_unique_persona_name(stats, existing_names)

            if persona_def['name'] not in existing_names:
                break

            print(f"  Attempt {attempt + 1}: Name collision, retrying...")

        # Add cluster statistics
        persona_def['cluster_id'] = stats['cluster_id']
        persona_def['size'] = stats['size']
        persona_def['percentage'] = stats['percentage']
        persona_def['ocean_traits'] = stats['ocean_means']
        persona_def['demographics'] = stats['demographic_means']
        persona_def['behavioral_traits'] = stats['behavioral_means']

        personas[cluster_id] = persona_def
        existing_names.append(persona_def['name'])

        print(f"  ✓ Created: {persona_def['name']}")
        print(f"    Tagline: {persona_def['tagline']}")

    # Save new personas
    with open("data/persona_definitions.json", 'w') as f:
        json.dump(personas, f, indent=2)

    print("\n" + "=" * 60)
    print("PERSONA GENERATION COMPLETE")
    print("=" * 60)
    print("\nUnique Personas Created:")
    for cluster_id, persona in personas.items():
        print(f"  • {persona['name']} ({persona['size']} twins, {persona['percentage']:.1f}%)")

    return personas


def update_profiles_with_new_personas():
    """Update twin profiles with new persona names"""

    # Load new personas
    with open("data/persona_definitions.json", 'r') as f:
        personas = json.load(f)

    # Load assignments
    with open("data/persona_assignments.json", 'r') as f:
        assignments = json.load(f)

    # Update each profile
    profiles_dir = "data/twin_profiles"
    updated_count = 0

    print("\nUpdating twin profiles with new persona names...")

    for user_id, assignment in assignments.items():
        profile_file = os.path.join(profiles_dir, f"{user_id}.json")

        if os.path.exists(profile_file):
            with open(profile_file, 'r') as f:
                profile = json.load(f)

            cluster_id = str(assignment['cluster_id'])
            persona = personas.get(cluster_id, {})

            profile['persona'] = {
                'cluster_id': assignment['cluster_id'],
                'persona_name': persona.get('name', f'Cluster {cluster_id}'),
                'persona_tagline': persona.get('tagline', ''),
                'assignment_confidence': assignment['confidence'],
                'cluster_probabilities': assignment['probabilities']
            }

            with open(profile_file, 'w') as f:
                json.dump(profile, f, indent=2)

            updated_count += 1

    print(f"  ✓ Updated {updated_count} profiles")


if __name__ == "__main__":
    # Regenerate personas with unique names
    personas = regenerate_all_personas()

    # Update profiles
    update_profiles_with_new_personas()

    print("\n✅ All personas regenerated with unique names!")
    print("   Restart the Streamlit app to see the new personas.")