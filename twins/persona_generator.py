"""
LLM-based Persona Name and Description Generator

This module generates meaningful persona names and descriptions based on
cluster characteristics using OpenAI's GPT models.
"""

import json
import os
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv
import openai

load_dotenv()


class PersonaGenerator:
    """
    Generates interpretable persona names and descriptions using LLM analysis
    of cluster characteristics.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the PersonaGenerator with OpenAI API key."""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY in .env file")

        self.client = openai.OpenAI(api_key=self.api_key)
        self.personas = {}

    def generate_persona_definition(self, cluster_stats: Dict) -> Dict:
        """
        Generate persona name and description for a cluster.

        Args:
            cluster_stats: Statistics for a cluster from PersonaAnalyzer

        Returns:
            Dictionary with persona definition
        """
        # Prepare cluster characteristics for the prompt
        ocean = cluster_stats['ocean_means']
        demographics = cluster_stats['demographic_means']
        behavioral = cluster_stats['behavioral_means']

        prompt = f"""
You are analyzing a customer segment from a food delivery platform to create a meaningful persona.

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
- Gender Distribution: {demographics['gender_distribution']['male']:.0%} male, {demographics['gender_distribution']['female']:.0%} female

Behavioral Preferences (0-1 scale):
- Novelty Seeking: {behavioral['novelty_seeking']:.2f} (tendency to try new cuisines)
- Budget Sensitivity: {behavioral['budget_sensitivity']:.2f} (focus on price and deals)
- Distance Tolerance: {behavioral['distance_tolerance']:.2f} (willingness to order from far)
- Rating Focus: {behavioral['rating_focus']:.2f} (importance of restaurant ratings)

Cluster Size: {cluster_stats['size']} people ({cluster_stats['percentage']:.1f}% of population)

Based on these characteristics, create a persona with:

1. A catchy, memorable name (2-3 words max, like "Quality Seekers" or "Budget Adventurers")
2. A one-sentence description (max 15 words)
3. Key behavioral traits (3-4 bullet points)
4. Typical food preferences
5. Decision-making pattern when choosing restaurants
6. A representative quote this persona might say

Format your response as JSON with the following structure:
{{
    "name": "Persona Name",
    "tagline": "One-sentence description",
    "key_traits": ["trait1", "trait2", "trait3"],
    "food_preferences": "Description of typical food choices",
    "decision_pattern": "How they typically choose restaurants",
    "representative_quote": "Something they might say about food delivery"
}}
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert in consumer segmentation and persona creation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            persona_def = json.loads(response.choices[0].message.content)

            # Add cluster statistics to the persona definition
            persona_def['cluster_id'] = cluster_stats['cluster_id']
            persona_def['size'] = cluster_stats['size']
            persona_def['percentage'] = cluster_stats['percentage']
            persona_def['ocean_traits'] = ocean
            persona_def['demographics'] = demographics
            persona_def['behavioral_traits'] = behavioral

            return persona_def

        except Exception as e:
            print(f"Error generating persona for cluster {cluster_stats['cluster_id']}: {e}")
            # Fallback to template-based naming
            return self._generate_fallback_persona(cluster_stats)

    def _generate_fallback_persona(self, cluster_stats: Dict) -> Dict:
        """Generate a template-based persona as fallback."""
        cluster_id = cluster_stats['cluster_id']
        behavioral = cluster_stats['behavioral_means']

        # Simple rule-based naming
        if behavioral['budget_sensitivity'] > 0.6:
            name = f"Budget Conscious Group {cluster_id}"
            focus = "price-sensitive"
        elif behavioral['novelty_seeking'] > 0.6:
            name = f"Adventurous Foodies {cluster_id}"
            focus = "variety-seeking"
        elif behavioral['rating_focus'] > 0.6:
            name = f"Quality Seekers {cluster_id}"
            focus = "quality-focused"
        else:
            name = f"Balanced Diners {cluster_id}"
            focus = "balanced"

        return {
            "name": name,
            "tagline": f"A {focus} customer segment",
            "key_traits": [
                f"Novelty: {behavioral['novelty_seeking']:.1%}",
                f"Budget: {behavioral['budget_sensitivity']:.1%}",
                f"Quality: {behavioral['rating_focus']:.1%}"
            ],
            "food_preferences": "Varied based on individual preferences",
            "decision_pattern": f"Primarily {focus} in their restaurant choices",
            "representative_quote": "I choose restaurants that fit my needs",
            "cluster_id": cluster_id,
            "size": cluster_stats['size'],
            "percentage": cluster_stats['percentage'],
            "ocean_traits": cluster_stats['ocean_means'],
            "demographics": cluster_stats['demographic_means'],
            "behavioral_traits": behavioral
        }

    def generate_all_personas(self, cluster_stats_file: str = "data/cluster_statistics.json") -> Dict:
        """
        Generate personas for all clusters.

        Args:
            cluster_stats_file: Path to cluster statistics JSON file

        Returns:
            Dictionary of all persona definitions
        """
        # Load cluster statistics
        with open(cluster_stats_file, 'r') as f:
            cluster_stats = json.load(f)

        personas = {}
        print(f"Generating personas for {len(cluster_stats)} clusters...")

        for cluster_id, stats in cluster_stats.items():
            print(f"  Generating persona for cluster {cluster_id}...")
            persona = self.generate_persona_definition(stats)
            personas[cluster_id] = persona
            print(f"    Created: {persona['name']}")

        self.personas = personas
        return personas

    def save_personas(self, output_file: str = "data/persona_definitions.json") -> None:
        """Save persona definitions to JSON file."""
        if not self.personas:
            raise ValueError("No personas to save. Run generate_all_personas() first.")

        with open(output_file, 'w') as f:
            json.dump(self.personas, f, indent=2)

        print(f"\nPersona definitions saved to {output_file}")

    def get_persona_summary(self) -> str:
        """Get a text summary of all personas."""
        if not self.personas:
            return "No personas generated yet."

        summary = "PERSONA SUMMARY\n" + "=" * 50 + "\n\n"

        for cluster_id, persona in self.personas.items():
            summary += f"**{persona['name']}** ({persona['size']} twins, {persona['percentage']:.1f}%)\n"
            summary += f"  {persona['tagline']}\n"
            summary += f"  Key Traits: {', '.join(persona['key_traits'])}\n"
            summary += f"  Quote: \"{persona['representative_quote']}\"\n\n"

        return summary


def update_profiles_with_personas(
    profiles_dir: str = "data/twin_profiles",
    assignments_file: str = "data/persona_assignments.json",
    personas_file: str = "data/persona_definitions.json"
) -> None:
    """
    Update twin profile JSON files with persona assignments.

    Args:
        profiles_dir: Directory containing twin profiles
        assignments_file: Persona assignments JSON file
        personas_file: Persona definitions JSON file
    """
    # Load assignments and personas
    with open(assignments_file, 'r') as f:
        assignments = json.load(f)

    with open(personas_file, 'r') as f:
        personas = json.load(f)

    profiles_path = Path(profiles_dir)
    updated_count = 0

    print(f"Updating {len(assignments)} twin profiles with persona assignments...")

    for user_id, assignment in assignments.items():
        profile_file = profiles_path / f"{user_id}.json"

        if profile_file.exists():
            with open(profile_file, 'r') as f:
                profile = json.load(f)

            # Add persona information
            cluster_id = str(assignment['cluster_id'])
            persona = personas.get(cluster_id, {})

            profile['persona'] = {
                'cluster_id': assignment['cluster_id'],
                'persona_name': persona.get('name', f'Cluster {cluster_id}'),
                'persona_tagline': persona.get('tagline', ''),
                'assignment_confidence': assignment['confidence'],
                'cluster_probabilities': assignment['probabilities']
            }

            # Save updated profile
            with open(profile_file, 'w') as f:
                json.dump(profile, f, indent=2)

            updated_count += 1

    print(f"Updated {updated_count} profiles with persona information")


if __name__ == "__main__":
    # Generate personas for all clusters
    generator = PersonaGenerator()

    # Generate persona definitions
    personas = generator.generate_all_personas()

    # Save persona definitions
    generator.save_personas()

    # Print summary
    print("\n" + generator.get_persona_summary())

    # Update profiles with persona assignments
    update_profiles_with_personas()