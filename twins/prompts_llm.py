"""
LLM-based decision prompts for digital twins.

This module contains prompt builders for the LLM-only architecture where
the LLM makes decisions (not just generates rationales).
"""

from typing import Dict, List, Any


def build_decider_prompt(
    user_name: str,
    ocean: Dict[str, float],
    demographics: Dict[str, float],
    context_summary: str,
    card_a: Dict[str, Any],
    card_b: Dict[str, Any],
    past_decisions: List[Dict] = None
) -> str:
    """
    Build prompt for The Decider - generates natural text decision explanation.

    The Decider's role is to make a restaurant choice and explain reasoning
    naturally, without structured output requirements.

    Args:
        user_name: User's name/ID
        ocean: OCEAN personality traits
        demographics: Age, income, gender, etc.
        context_summary: Human-readable context (e.g., "19:00, sunny, 28°C")
        card_a: Restaurant card A details
        card_b: Restaurant card B details
        past_decisions: Retrieved similar past decisions (from RAG)

    Returns:
        Formatted prompt string for natural text response
    """
    # Extract demographics
    age = int(demographics.get('dem_age', 30))
    income = demographics.get('dem_income', 600000)
    gender = _get_gender(demographics)

    # Derived preferences
    novelty = demographics.get('ctx_novelty_seeking', demographics.get('novelty_seeking', 0.5))
    budget = demographics.get('ctx_budget_sensitivity', demographics.get('budget_sensitivity', 0.5))
    distance_tol = demographics.get('ctx_distance_tolerance', demographics.get('distance_tolerance', 0.5))
    rating_focus = demographics.get('ctx_rating_focus', demographics.get('rating_focus', 0.5))

    # Format past decisions
    past_examples = _format_past_decisions(past_decisions) if past_decisions else "No similar past decisions available."

    # Build prompt
    prompt = f"""[SYSTEM] You are simulating {user_name}, a food delivery customer. Based on their personality, demographics, and past behavior, decide which restaurant to choose.

## USER PROFILE

**Identity**: {user_name}

**Personality (OCEAN Traits)**:
  • Openness: {ocean['openness']:.2f} (0=traditional/conventional, 1=adventurous/creative)
  • Conscientiousness: {ocean['conscientiousness']:.2f} (0=spontaneous/flexible, 1=organized/careful)
  • Extraversion: {ocean['extraversion']:.2f} (0=introverted/reserved, 1=social/outgoing)
  • Agreeableness: {ocean['agreeableness']:.2f} (0=competitive/critical, 1=cooperative/compassionate)
  • Neuroticism: {ocean['neuroticism']:.2f} (0=calm/confident, 1=anxious/sensitive)

**Demographics**:
  • Age: {age} years old
  • Gender: {gender}
  • Annual Income: ₹{income:,.0f}

**Derived Preferences** (computed from personality):
  • Novelty seeking: {novelty:.2f} (willingness to try new cuisines/restaurants)
  • Budget sensitivity: {budget:.2f} (importance of price/value)
  • Distance tolerance: {distance_tol:.2f} (willingness to order from farther places)
  • Rating focus: {rating_focus:.2f} (importance of ratings/reviews)

## CURRENT CONTEXT

{context_summary}

## YOUR PAST BEHAVIOR

{past_examples}

## TODAY'S DECISION

Choose between these two restaurants:

{_format_card(card_a, "A")}

{_format_card(card_b, "B")}

## PERSONALITY-DRIVEN DECISION GUIDELINES

Consider how your personality influences your choice:

**High Openness ({ocean['openness']:.2f})**:
{_openness_guidance(ocean['openness'])}

**Conscientiousness ({ocean['conscientiousness']:.2f})**:
{_conscientiousness_guidance(ocean['conscientiousness'])}

**Neuroticism ({ocean['neuroticism']:.2f})**:
{_neuroticism_guidance(ocean['neuroticism'])}

**Budget Sensitivity ({budget:.2f})**:
{_budget_guidance(budget)}

## TASK

Based on your personality, demographics, context, and past behavior, which restaurant would you choose?

**Explain your decision naturally** in 2-3 paragraphs:

1. **State your choice clearly**: Which restaurant are you choosing (A or B) and why?

2. **Explain your reasoning**: What specific factors influenced your decision? Consider:
   - Card attributes (rating, price, delivery time, distance, coupons)
   - How these align with your personality traits
   - Your past behavior in similar situations
   - Current context (time of day, weather, etc.)

3. **Express your confidence**: How sure are you about this choice? Use natural language like:
   - "I'm very confident because..."
   - "I'm fairly certain, though..."
   - "I'm somewhat hesitant, but..."

**Important**:
- Stay in character as {user_name}
- Be specific about the factors that matter to YOU
- Reference actual card details (not generic statements)
- Show how your personality influences this choice
- Write naturally - no need for structured format

**Example response style**:
"I'd choose Card A - the Sushi Express. Even though it's a bit pricier at ₹450 and takes longer to deliver (35 minutes), the significantly better rating of 4.7 stars really appeals to me. Given my conscientious nature, I trust well-reviewed restaurants. Plus, as someone who scores high on openness, trying sushi sounds more exciting than the usual pizza option. I'm quite confident about this choice - probably 80% sure - because the rating difference is substantial and aligns with what I typically value."
"""

    return prompt


def build_analyst_prompt(decider_text: str) -> str:
    """
    Build prompt for The Analyst - extracts structured data from natural text.

    The Analyst's role is to parse The Decider's natural language response
    and extract: choice, confidence level, reasoning summary, and key factors.

    Args:
        decider_text: The Decider's natural text response

    Returns:
        Formatted extraction prompt
    """
    prompt = f"""You are The Analyst - an information extraction specialist. Your task is to analyze a restaurant decision explanation and extract structured data.

## INPUT TEXT (from The Decider)

{decider_text}

## YOUR TASK

Extract the following information from the text above and return it as valid JSON:

1. **choice**: Which card did they choose? Return "A" or "B"
   - Look for phrases like "I'd choose Card A", "Card B is better", "going with A", etc.

2. **confidence**: How confident are they? Return a number between 0.0 and 1.0
   - Analyze confidence language:
     - Very confident / definitely / certain / sure → 0.8-0.95
     - Fairly confident / quite sure / likely → 0.65-0.79
     - Somewhat confident / moderately sure → 0.5-0.64
     - Hesitant / uncertain / maybe → 0.3-0.49
     - Very uncertain / not sure → 0.1-0.29
   - Look for explicit percentages (e.g., "80% sure" → 0.8)
   - Consider hedging words (but, though, however) which lower confidence

3. **reasoning**: Summarize the main reasoning in 1-2 sentences
   - Focus on the PRIMARY reasons for the choice
   - Keep it concise and clear

4. **key_factors**: List the main factors that influenced the decision (3-5 factors max)
   - Common factors: "rating", "price", "delivery_time", "distance", "cuisine", "coupon", "personality_fit", "reviews", "novelty", "familiarity"
   - Extract only factors explicitly mentioned or strongly implied

## OUTPUT FORMAT

Return ONLY valid JSON in this exact format:

{{
  "choice": "A",
  "confidence": 0.8,
  "reasoning": "Chose Card A because of significantly better rating and novel cuisine that matches adventurous personality.",
  "key_factors": ["rating", "cuisine", "personality_fit"]
}}

## IMPORTANT RULES

- Return ONLY the JSON object, nothing else
- If choice is unclear, default to "A"
- If confidence is not mentioned, infer from language strength (default: 0.5)
- Reasoning should be objective and concise
- Key factors should be from the standard list above
- Do not make up information - only extract what's in the text
"""

    return prompt


def _get_gender(demographics: Dict) -> str:
    """Extract gender from one-hot or string format."""
    if 'gender' in demographics:
        return demographics['gender']

    if demographics.get('dem_gender_male', 0) == 1:
        return "male"
    elif demographics.get('dem_gender_female', 0) == 1:
        return "female"
    else:
        return "other"


def _format_card(card: Dict[str, Any], label: str) -> str:
    """Format restaurant card details for prompt."""
    name = card.get('name', 'Unknown Restaurant')
    cuisine = card.get('cuisine', 'N/A')
    rating = card.get('rating_avg', 0.0)
    reviews = card.get('num_reviews', 0)
    time = card.get('delivery_time_min', 0)
    distance = card.get('distance_km', 0.0)
    price = card.get('dish_price', 0.0)
    fee = card.get('delivery_fee', 0.0)
    coupon = card.get('coupon_text', '') or 'None'
    sponsored = card.get('sponsored', 0)

    return f"""**🅰️ CARD {label}: {name}**
  • Cuisine: {cuisine}
  • Rating: {rating:.1f}⭐ ({int(reviews):,} reviews)
  • Delivery Time: {int(time)} minutes
  • Distance: {distance:.1f} km away
  • Dish Price: ₹{price:.0f}
  • Delivery Fee: ₹{fee:.0f}
  • Coupon/Offer: {coupon}
  • Sponsored: {'Yes' if sponsored > 0 else 'No'}"""


def _format_past_decisions(past_decisions: List[Dict]) -> str:
    """Format past decisions for prompt context."""
    if not past_decisions:
        return "No similar past decisions available."

    lines = ["Here are similar situations where you or similar users made choices:\n"]

    for i, ex in enumerate(past_decisions[:5]):  # Limit to 5 for prompt length
        ocean = ex.get('ocean', {})
        demo = ex.get('demographics', {})
        dec = ex.get('decision', {})

        lines.append(f"""
**{i+1}.** User (O={ocean.get('openness', 0.5):.2f}, C={ocean.get('conscientiousness', 0.5):.2f}, E={ocean.get('extraversion', 0.5):.2f}, A={ocean.get('agreeableness', 0.5):.2f}, N={ocean.get('neuroticism', 0.5):.2f})
   Age: {demo.get('age', 'N/A')}, Income: ₹{demo.get('income', 0):,.0f}
   Context: {ex.get('context_summary', 'N/A')}
   → Chose {dec.get('action', 'N/A')}: {ex.get('reasoning', 'N/A')}""")

    return "\n".join(lines)


def _openness_guidance(score: float) -> str:
    """Generate openness-specific guidance."""
    if score >= 0.7:
        return "• You're highly adventurous - novel cuisines (sushi, Thai, etc.) strongly appeal to you\n  • You're willing to try less-reviewed places for unique experiences\n  • Sponsored ads don't bother you much"
    elif score <= 0.3:
        return "• You prefer familiar, traditional options\n  • You stick to well-known cuisines (pizza, burgers, Indian)\n  • You value consistency over novelty"
    else:
        return "• You balance familiar and new cuisines\n  • Moderately open to trying different restaurants"


def _conscientiousness_guidance(score: float) -> str:
    """Generate conscientiousness-specific guidance."""
    if score >= 0.7:
        return "• You highly value reliability - ratings and reviews matter a lot\n  • You plan ahead - prefer predictable delivery times\n  • You're detail-oriented about quality indicators"
    elif score <= 0.3:
        return "• You're spontaneous - don't overthink the choice\n  • Ratings are less important than immediate appeal\n  • You're flexible about delivery time and quality"
    else:
        return "• You consider ratings but don't obsess over them\n  • Balanced approach to planning vs spontaneity"


def _neuroticism_guidance(score: float) -> str:
    """Generate neuroticism-specific guidance."""
    if score >= 0.7:
        return "• You're risk-averse - high ratings (4.5+) reduce anxiety\n  • Closer distance and faster delivery feel safer\n  • Uncertainty about quality stresses you - prefer well-reviewed options"
    elif score <= 0.3:
        return "• You're calm and confident - ratings matter less\n  • You're comfortable with longer delivery and farther distance\n  • You take risks on new or lesser-known places"
    else:
        return "• You balance risk and reward\n  • Moderate concern about ratings and reliability"


def _budget_guidance(score: float) -> str:
    """Generate budget sensitivity guidance."""
    if score >= 0.7:
        return "• Price is a major factor - coupons/discounts are highly attractive\n  • You weigh cost vs quality tradeoffs carefully\n  • Delivery fees add up - you prefer free or low-fee options"
    elif score <= 0.3:
        return "• Budget is less of a concern - you prioritize quality/experience\n  • Price differences under ₹200 don't sway your decision much\n  • You're willing to pay for better ratings or unique cuisines"
    else:
        return "• You consider price but don't let it dominate your decision\n  • Good deals are nice but not essential"


# Backward compatibility: Keep old function names
def build_decision_prompt(*args, **kwargs) -> str:
    """
    BACKWARD COMPATIBILITY WRAPPER

    Old code may call build_decision_prompt() - redirect to build_decider_prompt()
    """
    return build_decider_prompt(*args, **kwargs)


def build_llm_prompt(user_name: str, ocean: Dict[str, float], values_top3: List[str],
                      context_summary: str, action: str, drivers: List[str]) -> str:
    """
    DEPRECATED: Old rationale-only prompt.
    Kept for backward compatibility during migration.
    """
    return (
        f"You are {user_name}'s digital twin.\n"
        f"Traits (OCEAN): O={ocean.get('openness', 0.5):.2f}, C={ocean.get('conscientiousness', 0.5):.2f}, "
        f"E={ocean.get('extraversion', 0.5):.2f}, A={ocean.get('agreeableness', 0.5):.2f}, N={ocean.get('neuroticism', 0.5):.2f}.\n"
        f"You usually value: {', '.join(values_top3) if values_top3 else '—'}.\n"
        f"Current context: {context_summary}.\n"
        f"Predicted action: {action}.\n"
        f"Drivers: {', '.join(drivers)}.\n"
        "Task: Write ONE short sentence about why this restaurant card is the better pick."
        " Mention 1–2 drivers above. Keep it under 20 words."
        " Stay strictly on the food/restaurant/delivery domain."
    )
