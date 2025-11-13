"""
Persona Assessor Module

This module uses LLM to generate detailed, insightful persona descriptions
based on cluster characteristics. The Assessor LLM analyzes demographic,
behavioral, and psychological data to create rich persona profiles from
a food delivery app's perspective.
"""

import os
import json
from typing import Dict, List, Optional
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class PersonaAssessor:
    """
    LLM-powered persona assessor that generates rich, contextual descriptions
    of customer segments based on clustering data.
    """

    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize the persona assessor.

        Args:
            model: The Anthropic model to use for assessment
        """
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = model

    def assess_persona(
        self,
        cluster_id: int,
        characteristics: Dict,
        context: str = "food delivery app"
    ) -> Dict[str, str]:
        """
        Generate a comprehensive persona assessment using LLM.

        Args:
            cluster_id: The cluster/persona ID
            characteristics: Dictionary containing cluster characteristics including:
                - size: number of users
                - percentage: percentage of total users
                - ocean_means: OCEAN personality traits
                - demographic_means: age, income, gender distribution
                - behavioral_means: novelty_seeking, budget_sensitivity, etc.
            context: Business context (default: food delivery app)

        Returns:
            Dictionary with:
                - name: Short, memorable persona name
                - tagline: One-line descriptor
                - description: Detailed 2-3 sentence description
                - motivations: What drives this persona
                - pain_points: What frustrates them
                - preferences: What they prefer
        """

        # Prepare the analysis prompt
        prompt = self._build_assessment_prompt(cluster_id, characteristics, context)

        try:
            # Call the LLM
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Parse the response
            response_text = response.content[0].text
            assessment = self._parse_assessment_response(response_text)

            return assessment

        except Exception as e:
            print(f"Error in persona assessment: {e}")
            return self._get_fallback_assessment(cluster_id, characteristics)

    def _build_assessment_prompt(
        self,
        cluster_id: int,
        characteristics: Dict,
        context: str
    ) -> str:
        """
        Build a detailed prompt for the LLM assessor.

        The prompt includes all available data and asks for structured output.
        """

        ocean = characteristics.get('ocean_means', {})
        demographics = characteristics.get('demographic_means', {})
        behavioral = characteristics.get('behavioral_means', {})
        size = characteristics.get('size', 0)
        percentage = characteristics.get('percentage', 0)

        prompt = f"""You are a Customer Insights Analyst specializing in user segmentation for a {context}.
You have discovered a distinct customer persona through clustering analysis. Your task is to create a rich,
insightful profile that helps the business understand and serve this segment better.

## CLUSTER DATA FOR PERSONA {cluster_id}

### Scale and Reach
- Size: {size} users ({percentage:.1f}% of total user base)

### OCEAN Personality Traits (0.0 to 1.0 scale)
- Openness: {ocean.get('openness', 0):.2f}
  (willingness to try new experiences, creativity, curiosity)
- Conscientiousness: {ocean.get('conscientiousness', 0):.2f}
  (organization, reliability, planning orientation)
- Extraversion: {ocean.get('extraversion', 0):.2f}
  (social energy, assertiveness, enthusiasm)
- Agreeableness: {ocean.get('agreeableness', 0):.2f}
  (cooperation, empathy, trust in others)
- Neuroticism: {ocean.get('neuroticism', 0):.2f}
  (emotional stability vs anxiety and mood variability)

### Demographics
- Average Age: {demographics.get('age', 0):.1f} years
- Average Income: ₹{demographics.get('income', 0):.0f}k per year
- Gender Distribution:
  * Male: {demographics.get('gender_distribution', {}).get('male', 0)*100:.1f}%
  * Female: {demographics.get('gender_distribution', {}).get('female', 0)*100:.1f}%
  * Other: {demographics.get('gender_distribution', {}).get('other', 0)*100:.1f}%

### Behavioral Patterns (0.0 to 1.0 scale)
- Novelty Seeking: {behavioral.get('novelty_seeking', 0):.2f}
  (tendency to explore new restaurants and cuisines)
- Budget Sensitivity: {behavioral.get('budget_sensitivity', 0):.2f}
  (how much price influences decisions)
- Distance Tolerance: {behavioral.get('distance_tolerance', 0):.2f}
  (willingness to order from farther restaurants)
- Rating Focus: {behavioral.get('rating_focus', 0):.2f}
  (importance of ratings and reviews in decision-making)

## YOUR TASK

Analyze this data holistically and generate a persona profile in the following JSON format:

{{
  "name": "A memorable 2-3 word name that captures the essence (e.g., 'Budget Explorer', 'Quality Seeker')",
  "tagline": "One compelling sentence that summarizes who they are and what they want",
  "description": "A rich 2-3 sentence narrative describing this persona's relationship with food delivery. Connect their personality, demographics, and behaviors into a cohesive story.",
  "motivations": "2-3 key drivers that motivate their food delivery choices",
  "pain_points": "2-3 main frustrations or challenges they face with food delivery",
  "preferences": "2-3 specific preferences for how they like to order food"
}}

## IMPORTANT GUIDELINES

1. **Be Specific and Contextual**: Don't just restate the numbers. Synthesize them into insights.
   - Bad: "This persona has high novelty seeking"
   - Good: "Always on the hunt for the next trending restaurant, they're the first to try new cuisines"

2. **Connect the Dots**: Show how traits interact
   - Example: High openness + low budget sensitivity → "Willing to pay premium for unique culinary experiences"
   - Example: High conscientiousness + high rating focus → "Meticulously researches restaurants, reads multiple reviews"

3. **Use Vivid Language**: Make the persona come alive
   - Include lifestyle implications from age/income
   - Reference real behaviors this persona would exhibit
   - Use active, present-tense language

4. **Business-Relevant Insights**: Focus on actionable understanding
   - What would make them order more?
   - What would frustrate them?
   - How should the app serve them?

5. **Realistic Nuance**: Real people are complex
   - Avoid stereotypes
   - Show both strengths and challenges
   - Acknowledge trade-offs in their behavior

Return ONLY the JSON object, no other text."""

        return prompt

    def _parse_assessment_response(self, response_text: str) -> Dict[str, str]:
        """
        Parse the LLM response into a structured assessment.

        Attempts to extract JSON from the response. Falls back to parsing
        if JSON extraction fails.
        """
        try:
            # Try to extract JSON from the response
            # Handle both cases: pure JSON and JSON wrapped in text
            start = response_text.find('{')
            end = response_text.rfind('}') + 1

            if start != -1 and end > start:
                json_str = response_text[start:end]
                assessment = json.loads(json_str)

                # Validate required fields
                required_fields = ['name', 'tagline', 'description', 'motivations', 'pain_points', 'preferences']
                if all(field in assessment for field in required_fields):
                    return assessment

        except json.JSONDecodeError:
            pass

        # Fallback: try to parse line by line
        return self._parse_fallback(response_text)

    def _parse_fallback(self, text: str) -> Dict[str, str]:
        """
        Fallback parser for when JSON parsing fails.
        Attempts to extract information from structured text.
        """
        lines = text.split('\n')
        assessment = {
            'name': 'Unknown Persona',
            'tagline': 'Customer segment',
            'description': 'A distinct customer group with unique characteristics.',
            'motivations': 'Seeking convenient food options',
            'pain_points': 'Delivery challenges',
            'preferences': 'Reliable service'
        }

        current_field = None
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for field markers
            if 'name' in line.lower() and ':' in line:
                current_field = 'name'
                assessment['name'] = line.split(':', 1)[1].strip().strip('"\'')
            elif 'tagline' in line.lower() and ':' in line:
                current_field = 'tagline'
                assessment['tagline'] = line.split(':', 1)[1].strip().strip('"\'')
            elif 'description' in line.lower() and ':' in line:
                current_field = 'description'
                assessment['description'] = line.split(':', 1)[1].strip().strip('"\'')
            elif 'motivation' in line.lower() and ':' in line:
                current_field = 'motivations'
                assessment['motivations'] = line.split(':', 1)[1].strip().strip('"\'')
            elif 'pain' in line.lower() and ':' in line:
                current_field = 'pain_points'
                assessment['pain_points'] = line.split(':', 1)[1].strip().strip('"\'')
            elif 'preference' in line.lower() and ':' in line:
                current_field = 'preferences'
                assessment['preferences'] = line.split(':', 1)[1].strip().strip('"\'')

        return assessment

    def _get_fallback_assessment(
        self,
        cluster_id: int,
        characteristics: Dict
    ) -> Dict[str, str]:
        """
        Generate a basic fallback assessment when LLM call fails.
        Uses rule-based logic based on the characteristics.
        """
        ocean = characteristics.get('ocean_means', {})
        behavioral = characteristics.get('behavioral_means', {})
        size = characteristics.get('size', 0)
        percentage = characteristics.get('percentage', 0)

        # Simple rule-based name generation
        if behavioral.get('novelty_seeking', 0) > 0.6:
            name = "adventurous explorer"
        elif behavioral.get('budget_sensitivity', 0) > 0.6:
            name = "budget-conscious diner"
        elif behavioral.get('rating_focus', 0) > 0.6:
            name = "quality seeker"
        elif ocean.get('conscientiousness', 0) > 0.6:
            name = "reliable regular"
        else:
            name = f"persona {cluster_id}"

        return {
            'name': name,
            'tagline': f"cluster with {size} users ({percentage:.1f}% of total)",
            'description': f"a distinct customer segment representing {percentage:.1f}% of the user base.",
            'motivations': "convenient food delivery",
            'pain_points': "service quality issues",
            'preferences': "reliable delivery"
        }

    def assess_all_personas(
        self,
        characteristics_dict: Dict[int, Dict],
        context: str = "food delivery app"
    ) -> Dict[int, Dict[str, str]]:
        """
        Assess all personas in a clustering result.

        Args:
            characteristics_dict: Dictionary mapping cluster_id to characteristics
            context: Business context

        Returns:
            Dictionary mapping cluster_id to assessment
        """
        assessments = {}

        for cluster_id, characteristics in characteristics_dict.items():
            print(f"Assessing persona {cluster_id}...")
            assessment = self.assess_persona(cluster_id, characteristics, context)
            assessments[cluster_id] = assessment

        return assessments
