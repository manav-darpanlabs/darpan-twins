import os
import re
from typing import Dict, Any, List

import streamlit as st

from twins.prompt_simulator import run_dual_llm_for_users
from twins.card_parser import extract_from_image
from twins.weather import search_cities, fetch_current_weather


# Default Indian cities for quick selection
DEFAULT_CITIES = [
    {"name": "Mumbai", "country_code": "IN", "latitude": 19.0760, "longitude": 72.8777},
    {"name": "Delhi", "country_code": "IN", "latitude": 28.7041, "longitude": 77.1025},
    {"name": "Bangalore", "country_code": "IN", "latitude": 12.9716, "longitude": 77.5946},
    {"name": "Chennai", "country_code": "IN", "latitude": 13.0827, "longitude": 80.2707},
    {"name": "Kolkata", "country_code": "IN", "latitude": 22.5726, "longitude": 88.3639},
    {"name": "Hyderabad", "country_code": "IN", "latitude": 17.3850, "longitude": 78.4867},
    {"name": "Pune", "country_code": "IN", "latitude": 18.5204, "longitude": 73.8567},
    {"name": "Ahmedabad", "country_code": "IN", "latitude": 23.0225, "longitude": 72.5714},
]


st.set_page_config(page_title="Darpan Labs — Customer Twin MVP", page_icon="🍽️", layout="wide")

# Enhanced dark theme with modern SaaS aesthetic
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
      /* Core Brand Colors */
      --brand: #C1E329;           /* Neon green - primary */
      --brand2: #3fb1f0;          /* Neon blue - secondary */
      --bg: hsl(0, 0%, 8%);       /* Dark background */
      --panel: hsl(0, 0%, 12%);   /* Card background */
      --border: #1f232b;          /* Default borders */
      --text: hsl(0, 0%, 98%);    /* Primary text */
      --muted: #aab4c2;           /* Secondary text */

      /* Extended Palette */
      --success: #4ade80;         /* Success green */
      --warning: #fbbf24;         /* Warning yellow */
      --error: #f87171;           /* Error red */
      --divider: #2a2e35;         /* Section dividers */
      --input-bg: hsl(0, 0%, 10%); /* Input backgrounds */

      /* Glow Effects */
      --glowG: 0 0 20px rgba(193, 227, 41, 0.35);
      --glowB: 0 0 20px rgba(63, 177, 240, 0.35);
      --glowSuccess: 0 0 16px rgba(74, 222, 128, 0.3);

      /* Typography Scale */
      --text-xs: 12px;
      --text-sm: 13px;
      --text-base: 14px;
      --text-lg: 16px;
      --text-xl: 20px;
      --text-2xl: 24px;
      --text-3xl: 28px;

      /* Spacing Scale */
      --space-1: 4px;
      --space-2: 8px;
      --space-3: 12px;
      --space-4: 16px;
      --space-6: 24px;
      --space-8: 32px;
      --space-12: 48px;
    }

    /* Base Styles */
    html, body, [class^="css"], * {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif !important;
    }
    .block-container {
      padding-top: var(--space-3);
      padding-bottom: var(--space-6);
      max-width: 1400px;
    }
    body {
      background: var(--bg);
      color: var(--text);
    }

    /* Header Styles */
    .header-container {
      padding: var(--space-4) 0 var(--space-6) 0;
      border-bottom: 1px solid var(--divider);
      margin-bottom: var(--space-6);
    }
    .logo {
      font-weight: 800;
      font-size: var(--text-3xl);
      letter-spacing: -0.02em;
      line-height: 1.2;
    }
    .logo-grad {
      background: linear-gradient(135deg, var(--brand), var(--brand2));
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
      text-shadow: var(--glowG), var(--glowB);
    }
    .tagline {
      font-size: var(--text-base);
      color: var(--muted);
      margin-top: var(--space-1);
      font-weight: 400;
    }
    .xp {
      background: linear-gradient(180deg, hsl(0,0%,14%), hsl(0,0%,10%));
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: var(--space-3) var(--space-4);
      color: var(--text);
      box-shadow: var(--glowB);
      font-size: var(--text-sm);
    }

    /* Stepper Pills */
    .stepper {
      display: flex;
      gap: var(--space-2);
      margin: var(--space-6) 0 var(--space-8) 0;
      padding: var(--space-2) 0;
    }
    .step-pill {
      padding: var(--space-2) var(--space-4);
      border-radius: 999px;
      border: 1px solid var(--border);
      color: var(--muted);
      background: hsl(0,0%,10%);
      transition: all 0.25s cubic-bezier(0.22, 0.61, 0.36, 1);
      font-size: var(--text-sm);
      font-weight: 500;
    }
    .step-pill.active {
      color: var(--text);
      background: linear-gradient(180deg, hsl(0,0%,16%), hsl(0,0%,12%));
      border-color: var(--brand2);
      box-shadow: var(--glowB);
      font-weight: 600;
    }

    /* Panel & Cards */
    .panel {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: var(--space-6);
      color: var(--text);
      margin-bottom: var(--space-6);
    }
    .panel.ghost {
      background: transparent;
      border: none;
      padding: 0;
      margin-bottom: 0;
    }

    /* Section Headers */
    .section-header {
      font-size: var(--text-xl);
      font-weight: 700;
      color: var(--text);
      margin-bottom: var(--space-4);
      padding-bottom: var(--space-3);
      border-bottom: 1px solid var(--divider);
    }
    .section-subheader {
      font-size: var(--text-base);
      font-weight: 600;
      color: var(--text);
      margin-bottom: var(--space-3);
    }

    /* Buttons */
    .stButton>button {
      background: var(--brand);
      color: #0b0e14;
      border-radius: 12px;
      border: none;
      box-shadow: var(--glowG);
      font-weight: 700;
      font-size: var(--text-base);
      padding: var(--space-3) var(--space-6);
      min-height: 44px;
      transition: all 0.2s cubic-bezier(0.22, 0.61, 0.36, 1);
    }
    .stButton>button:hover {
      transform: translateY(-2px);
      box-shadow: 0 0 24px rgba(193, 227, 41, 0.5);
    }
    .stButton>button:active {
      transform: translateY(0px);
    }
    .stButton>button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      transform: none !important;
    }
    .secondary-zone .stButton>button {
      background: var(--brand2);
      box-shadow: var(--glowB);
    }
    .secondary-zone .stButton>button:hover {
      box-shadow: 0 0 24px rgba(63, 177, 240, 0.5);
    }

    /* Form Inputs */
    .stTextInput>div>div>input,
    .stSelectbox>div>div>div {
      background: var(--input-bg);
      color: var(--text);
      border-radius: 12px;
      border: 1px solid var(--border);
      box-shadow: none;
      font-size: var(--text-base);
      padding: var(--space-3);
      transition: border-color 0.2s;
    }
    .stTextInput>div>div>input:focus,
    .stSelectbox>div>div>div:focus {
      border-color: var(--brand2);
      box-shadow: 0 0 0 3px rgba(63, 177, 240, 0.1);
    }
    .stTextInput>label,
    .stSelectbox>label {
      font-weight: 500;
      font-size: var(--text-sm);
      color: var(--text);
      margin-bottom: var(--space-2);
    }
    .stTextInput input::placeholder {
      opacity: 0.6;
    }

    /* NUCLEAR OPTION: Hide ALL widget labels completely */
    label[data-testid="stWidgetLabel"] {
      display: none !important;
      visibility: hidden !important;
      opacity: 0 !important;
      width: 0 !important;
      height: 0 !important;
      position: absolute !important;
      left: -9999px !important;
    }

    /* File Uploader */
    .stFileUploader {
      border: 2px dashed var(--border);
      border-radius: 12px;
      padding: var(--space-6);
      background: var(--input-bg);
      transition: all 0.2s;
    }
    .stFileUploader:hover {
      border-color: var(--brand2);
      background: hsl(0,0%,11%);
    }

    /* Expanders */
    .stExpander {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 12px;
      margin-bottom: var(--space-4);
    }
    .stExpander summary {
      font-weight: 600;
      font-size: var(--text-base);
      padding: var(--space-4);
    }
    /* NUCLEAR: Remove ALL labels from expanders */
    .stExpander label,
    .stExpander > label,
    [data-testid="stExpander"] label,
    [data-testid="stExpander"] label[data-testid="stWidgetLabel"] {
      display: none !important;
      visibility: hidden !important;
      position: absolute !important;
      left: -9999px !important;
      width: 0 !important;
      height: 0 !important;
    }

    /* Expander wrapper to contain and clean up rendering */
    .expander-wrapper {
      position: relative;
    }
    .expander-wrapper label {
      display: none !important;
    }

    /* Weather Card */
    .weather-card {
      background: linear-gradient(135deg, hsl(0,0%,14%), hsl(0,0%,10%));
      border: 1px solid var(--brand2);
      border-radius: 16px;
      padding: var(--space-6);
      margin: var(--space-4) 0 var(--space-6) 0;
      box-shadow: var(--glowB);
      overflow: visible;
    }
    .weather-title {
      font-size: var(--text-sm);
      color: var(--muted);
      margin-bottom: var(--space-3);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-weight: 600;
    }
    .weather-content {
      display: flex;
      align-items: center;
      gap: var(--space-4);
      overflow: visible;
    }
    .weather-icon {
      font-size: 48px;
      line-height: 1.2;
      flex-shrink: 0;
    }
    .weather-city {
      font-size: var(--text-xl);
      font-weight: 700;
      color: var(--text);
      margin-bottom: var(--space-1);
      line-height: 1.4;
      overflow: visible;
    }
    .weather-temp {
      font-size: var(--text-base);
      color: var(--muted);
      line-height: 1.4;
    }
    .weather-status {
      margin-left: auto;
      color: var(--success);
      font-weight: 600;
      font-size: var(--text-sm);
      flex-shrink: 0;
    }

    /* Score Bars */
    .scorebar {
      height: 12px;
      border-radius: 8px;
      background: hsl(0,0%,10%);
      border: 1px solid var(--border);
      overflow: hidden;
      box-shadow: inset 0 0 8px rgba(0,0,0,0.45);
    }
    .scorebar > div {
      height: 100%;
      background: linear-gradient(90deg, var(--brand), var(--brand2));
      box-shadow: var(--glowG), var(--glowB);
      transition: width 0.5s cubic-bezier(0.22, 0.61, 0.36, 1);
    }

    /* Dividers */
    hr {
      border: none;
      border-top: 1px solid var(--divider);
      margin: var(--space-6) 0;
    }

    /* Typography */
    h1, h2, h3 {
      margin: 0 0 var(--space-3) 0;
      font-weight: 700;
    }
    h1 { font-size: var(--text-2xl); }
    h2 { font-size: var(--text-xl); }
    h3 { font-size: var(--text-lg); }

    p, label {
      margin-bottom: var(--space-2);
      line-height: 1.6;
    }

    .hint {
      color: var(--muted);
      font-size: var(--text-xs);
      font-weight: 400;
    }
    .mini {
      font-size: var(--text-xs);
      color: var(--muted);
    }

    /* Slider */
    .stSlider>div>div>div>div {
      background: var(--brand2) !important;
    }

    /* Hide debug text */
    [data-testid="stMarkdownContainer"] > p:empty {
      display: none;
    }

    /* Full-Screen Blur Overlay for Processing */
    .blur-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.85);
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
      z-index: 99999;
      display: flex;
      align-items: center;
      justify-content: center;
      animation: fadeIn 0.3s ease-in;
    }

    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    .loading-card {
      background: var(--panel);
      border: 2px solid var(--brand2);
      border-radius: 24px;
      padding: var(--space-12);
      max-width: 500px;
      width: 90%;
      box-shadow: var(--glowB), 0 20px 60px rgba(0, 0, 0, 0.8);
      text-align: center;
      animation: pulseGlow 2s ease-in-out infinite;
    }

    @keyframes pulseGlow {
      0%, 100% {
        box-shadow: var(--glowB), 0 20px 60px rgba(0, 0, 0, 0.8);
        transform: scale(1);
      }
      50% {
        box-shadow: 0 0 40px rgba(63, 177, 240, 0.6), 0 20px 60px rgba(0, 0, 0, 0.8);
        transform: scale(1.02);
      }
    }

    .loading-icon {
      font-size: 64px;
      margin-bottom: var(--space-6);
      animation: rotate 2s linear infinite;
    }

    @keyframes rotate {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }

    .loading-title {
      font-size: var(--text-2xl);
      font-weight: 700;
      color: var(--text);
      margin-bottom: var(--space-4);
    }

    .loading-status {
      font-size: var(--text-lg);
      color: var(--brand2);
      margin-bottom: var(--space-6);
      font-weight: 600;
    }

    .loading-progress-container {
      background: hsl(0, 0%, 10%);
      border-radius: 12px;
      height: 24px;
      overflow: hidden;
      border: 1px solid var(--border);
      margin-bottom: var(--space-4);
    }

    .loading-progress-bar {
      height: 100%;
      background: linear-gradient(90deg, var(--brand), var(--brand2));
      box-shadow: var(--glowG), var(--glowB);
      transition: width 0.5s cubic-bezier(0.22, 0.61, 0.36, 1);
      border-radius: 12px;
    }

    .loading-percentage {
      font-size: var(--text-xl);
      color: var(--text);
      font-weight: 700;
      margin-bottom: var(--space-3);
    }

    .loading-subtitle {
      font-size: var(--text-base);
      color: var(--muted);
      margin-top: var(--space-3);
    }

    .loading-twin-info {
      margin-top: var(--space-6);
      padding-top: var(--space-6);
      border-top: 1px solid var(--divider);
      font-size: var(--text-sm);
      color: var(--muted);
    }
    </style>
    <script>
    // Force remove all widget labels from DOM
    function removeWidgetLabels() {
      const labels = document.querySelectorAll('label[data-testid="stWidgetLabel"]');
      labels.forEach(label => {
        if (label && label.parentNode) {
          label.parentNode.removeChild(label);
        }
      });

      // Also remove any labels inside expanders
      const expanderLabels = document.querySelectorAll('[data-testid="stExpander"] label');
      expanderLabels.forEach(label => {
        if (label && label.parentNode) {
          label.parentNode.removeChild(label);
        }
      });
    }

    // Run on load
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', removeWidgetLabels);
    } else {
      removeWidgetLabels();
    }

    // Run periodically to catch dynamically added elements
    setInterval(removeWidgetLabels, 100);
    </script>
    """,
    unsafe_allow_html=True,
)


def parse_card_form(prefix: str) -> Dict[str, Any]:
    cuisines = ["italian", "mexican", "sushi", "indian", "american", "chinese", "thai", "pizza", "burgers"]
    with st.expander(f"{prefix} card details"):
        name = st.text_input(f"{prefix} name", value=f"{prefix} Restaurant")
        cuisine = st.selectbox(f"{prefix} cuisine", cuisines, index=0, key=f"{prefix}_cuisine")
        dish_price = st.number_input(
            f"{prefix} dish price (₹)",
            min_value=50.0,
            max_value=2000.0,
            value=250.0,
            step=10.0,
            key=f"{prefix}_price",
        )
        delivery_time_min = st.number_input(f"{prefix} delivery time (min)", min_value=5, max_value=120, value=35, step=1, key=f"{prefix}_dt")
        distance_km = st.number_input(f"{prefix} distance (km)", min_value=0.1, max_value=30.0, value=3.0, step=0.1, key=f"{prefix}_dist")
        delivery_fee = st.number_input(
            f"{prefix} delivery fee (₹)",
            min_value=0.0,
            max_value=200.0,
            value=25.0,
            step=5.0,
            key=f"{prefix}_fee",
        )
        rating_avg = st.number_input(f"{prefix} rating avg", min_value=3.0, max_value=5.0, value=4.2, step=0.1, key=f"{prefix}_rating")
        num_reviews = st.number_input(f"{prefix} number of reviews", min_value=0, max_value=100000, value=200, step=10, key=f"{prefix}_reviews")
        coupon_text = st.text_input(f"{prefix} coupon text", value="", key=f"{prefix}_coupon")
        friend_endorsements_count = st.number_input(f"{prefix} friend endorsements", min_value=0, max_value=1000, value=1, step=1, key=f"{prefix}_endorse")
        sponsored = st.checkbox(f"{prefix} sponsored", value=False, key=f"{prefix}_sponsored")

    card: Dict[str, Any] = {
        "name": name,
        "cuisine": cuisine,
        "dish_price": float(dish_price),
        "delivery_time_min": int(delivery_time_min),
        "distance_km": float(distance_km),
        "delivery_fee": float(delivery_fee),
        "rating_avg": float(rating_avg),
        "num_reviews": int(num_reviews),
        "coupon_text": coupon_text,
        "friend_endorsements_count": int(friend_endorsements_count),
        "sponsored": float(1.0 if sponsored else 0.0),
        "coupon_available": float(1.0 if coupon_text else 0.0),
    }
    for c in cuisines:
        card[f"cuisine_{c}"] = 1.0 if c == cuisine else 0.0
    return card


def format_factor(reason: str) -> str:
    """Extract 2-3 word factor from longer reason text."""
    reason = reason.strip()

    # Common patterns to extract key factors
    patterns = {
        r"(?:higher|better|good|excellent|great)\s+(?:average\s+)?rating": "Higher Rating",
        r"(?:lower|cheaper|less|reduced)\s+price": "Lower Price",
        r"(?:higher|expensive|more|increased)\s+price": "Higher Price",
        r"(?:more|greater|larger)\s+(?:number\s+of\s+)?reviews": "More Reviews",
        r"(?:fewer|less)\s+(?:number\s+of\s+)?reviews": "Fewer Reviews",
        r"(?:faster|quicker|shorter)\s+(?:delivery|eta)": "Faster Delivery",
        r"(?:slower|longer)\s+(?:delivery|eta)": "Slower Delivery",
        r"(?:closer|nearer|shorter)\s+distance": "Closer Distance",
        r"(?:farther|further|longer)\s+distance": "Farther Distance",
        r"coupon|discount|deal|offer": "Coupon Available",
        r"(?:novel|new|different|unique)\s+cuisine": "Novel Cuisine",
        r"(?:familiar|known|usual)\s+cuisine": "Familiar Cuisine",
        r"friend[s]?\s+(?:endorsed|recommended)|(?:endorsed|recommended)\s+(?:by\s+)?friend": "Friend Endorsed",
        r"sponsored": "Sponsored",
        r"(?:lower|cheaper|less)\s+(?:delivery\s+)?fee": "Lower Fee",
        r"trust|reliable|reputation": "Trust Factor",
    }

    reason_lower = reason.lower()
    for pattern, factor in patterns.items():
        if re.search(pattern, reason_lower):
            return factor

    # Fallback: take first 2-3 meaningful words
    words = reason.split()
    if len(words) <= 3:
        return reason.title()
    return " ".join(words[:3]).title()


def aggregate_results(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_twins = len(rows) if rows else 0
    totals = {"A": 0, "B": 0, "tie": 0}
    reasons_a: dict[str, int] = {}
    reasons_b: dict[str, int] = {}
    checks_breakdown = {
        "price": {"A": 0, "B": 0, "tie": 0},
        "delivery": {"A": 0, "B": 0, "tie": 0},
        "fit": {"A": 0, "B": 0, "tie": 0},
        "trust": {"A": 0, "B": 0, "tie": 0},
    }

    for r in rows or []:
        choice = r.get("action", "tie")
        if choice not in totals:
            choice = "tie"
        totals[choice] += 1

        # Aggregate reasons with formatted factors
        for reason in r.get("reasons", []) or []:
            formatted = format_factor(reason)
            if choice == "A":
                reasons_a[formatted] = reasons_a.get(formatted, 0) + 1
            elif choice == "B":
                reasons_b[formatted] = reasons_b.get(formatted, 0) + 1

        # Aggregate checks breakdown
        checks = r.get("checks", {}) or {}
        for check_type in ["price", "delivery", "fit", "trust"]:
            check_val = checks.get(check_type, "tie")
            if check_val in checks_breakdown[check_type]:
                checks_breakdown[check_type][check_val] += 1

    pct = {k: (v * 100.0 / total_twins if total_twins else 0.0) for k, v in totals.items()}

    # Get top 5 and bottom 5 factors for each option
    sorted_a = sorted(reasons_a.items(), key=lambda kv: kv[1], reverse=True)
    sorted_b = sorted(reasons_b.items(), key=lambda kv: kv[1], reverse=True)

    top_a_factors = [{"factor": r, "count": c, "pct": (c * 100.0 / max(1, totals["A"]))} for r, c in sorted_a[:5]]
    top_b_factors = [{"factor": r, "count": c, "pct": (c * 100.0 / max(1, totals["B"]))} for r, c in sorted_b[:5]]

    return {
        "total_twins": total_twins,
        "counts": totals,
        "percent": pct,
        "top_a_factors": top_a_factors,
        "top_b_factors": top_b_factors,
        "checks_breakdown": checks_breakdown,
    }


def context_controls() -> Dict[str, Any]:
    st.subheader("Context")
    hour = st.slider("🕒 Hour of day", min_value=0, max_value=23, value=13)
    weekend = st.checkbox("🎉 Weekend", value=False)

    # City search → Open-Meteo
    st.markdown("**City weather**")
    q = st.text_input("🔎 Search city", value=st.session_state.get("city_q", ""))
    if q != st.session_state.get("city_q"):
        st.session_state["city_q"] = q
        st.session_state["city_results"] = []
    if st.button("Search"):
        st.session_state["city_results"] = search_cities(q or "")
    results = st.session_state.get("city_results", [])
    choice = None
    if results:
        labels = [
            f"{r.get('name')}, {r.get('country_code','')} ({r.get('latitude'):.2f},{r.get('longitude'):.2f})"
            for r in results
        ]
        idx = st.selectbox("Results", list(range(len(labels))), format_func=lambda i: labels[i])
        choice = results[idx]

    fetched_temp = None
    fetched_precip = None
    if choice and st.button("Use current weather"):
        wx = fetch_current_weather(choice.get("latitude"), choice.get("longitude"))
        fetched_temp = wx.get("temperature_c")
        fetched_precip = wx.get("precip_mm")
        st.session_state["last_wx"] = wx
        st.session_state["last_city"] = choice
    if st.session_state.get("last_wx") and st.session_state.get("last_city"):
        wx = st.session_state["last_wx"]
        city = st.session_state["last_city"]
        st.markdown(
            f"Using weather for <b>{city.get('name')}</b>: {wx['temperature_c']:.0f}°C, {wx['precip_mm']:.1f} mm",
            unsafe_allow_html=True,
        )
        temp = float(wx["temperature_c"])
        precip = float(wx["precip_mm"])
        # Override hour/weekend with current local time from API when available
        if "hour_of_day" in wx:
            hour = int(wx["hour_of_day"])  # type: ignore[arg-type]
        if "is_weekend" in wx:
            weekend = bool(int(wx["is_weekend"]))  # type: ignore[arg-type]
    else:
        # Fun but classy manual fallback
        temp = st.slider("🌡️ Temperature (°C)", min_value=-5, max_value=45, value=24)
        precip = st.select_slider(
            "🌧️ Rain (mm)",
            options=[0.0, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0],
            value=0.0,
            format_func=lambda x: f"{x:g} mm",
        )

    # Compact visual preview
    def temp_icon(t: int) -> str:
        return "❄️" if t <= 5 else ("🌤️" if t <= 20 else ("☀️" if t <= 32 else "🔥"))

    def rain_icon(r: float) -> str:
        return "🌫️" if r == 0 else ("🌦️" if r <= 2 else ("🌧️" if r <= 10 else "⛈️"))

    colv1, colv2, colv3 = st.columns([1, 1, 2])
    with colv1:
        st.markdown(f"<div class='hint'>Temp</div><div style='font-size:28px'>{temp_icon(int(temp))}</div>", unsafe_allow_html=True)
    with colv2:
        st.markdown(f"<div class='hint'>Rain</div><div style='font-size:28px'>{rain_icon(float(precip))}</div>", unsafe_allow_html=True)
    with colv3:
        st.markdown(
            f"<div class='hint'>Summary</div><div>~{int(temp)}°C, {precip:g} mm, {'weekend' if weekend else 'weekday'} at {hour}:00</div>",
            unsafe_allow_html=True,
        )
    dem = {
        "hour_of_day": int(hour),
        "is_weekend": int(1 if weekend else 0),
        "temperature_c": float(temp),
        "precip_mm": float(precip),
    }
    return dem


def reset_experiment() -> None:
    """Clear experiment data while preserving XP."""
    keys_to_clear = [
        "cards_a", "cards_b", "cards_a_preview", "cards_b_preview",
        "ctx", "run_params", "pending_run", "dual_results",
        "city_q", "city_results", "last_wx", "last_city",
        "progress_pct", "current_twin"
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.step = 1


def main() -> None:
    # Header Section - Redesigned to prevent overlaps
    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    colH1, colH2 = st.columns([3,1])
    with colH1:
        st.markdown(
            '''
            <div class="logo">
                Darpan <span class="logo-grad">Twins</span> Lab
            </div>
            <div class="tagline">AI-Powered Digital Twin Experiments</div>
            ''',
            unsafe_allow_html=True
        )
    with colH2:
        xp = st.session_state.get("xp", 0)
        st.markdown(
            f'<div class="xp">XP: {xp} <span class="mini">• Complete runs to unlock badges</span></div>',
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # Quick Guide
    st.markdown("""
    ### 🍽️ About This Tool

    This tool simulates how **digital twins** (AI personas based on real user personalities) make restaurant choices between two options.

    **How to use:**
    1. **Select City & Weather** - Choose a city, weather is automatically fetched
    2. **Upload Restaurant Cards** - Upload screenshots of two restaurant options (PNG/JPG)
    3. **Run Experiment** - Simulate 10 digital twins making choices (~30-60 seconds)
    4. **View Results** - See which card wins and why (factors, percentages, reasoning)

    Each twin has unique **OCEAN personality traits** that influence their decisions based on factors like price, ratings, delivery time, weather, and more.
    """)

    st.divider()

    # Users picker (multi-select)
    profiles_dir = os.path.join("data", "twin_profiles")
    files = []
    try:
        files = sorted([f for f in os.listdir(profiles_dir) if f.endswith(".json")])
    except Exception:
        pass

    # Wizard step setup - Now with 4 steps including Introduction
    if "step" not in st.session_state:
        st.session_state.step = 0  # Start with introduction
    step = st.session_state.step
    st.markdown('<div class="stepper">'
                f'<span class="step-pill {"active" if step==0 else ""}">Welcome</span>'
                f'<span class="step-pill {"active" if step==1 else ""}">1. City & Upload</span>'
                f'<span class="step-pill {"active" if step==2 else ""}">2. Running</span>'
                f'<span class="step-pill {"active" if step==3 else ""}">3. Results</span>'
                '</div>', unsafe_allow_html=True)

    # Page 0: Introduction/Landing Page
    if step == 0:
        st.title("Welcome to Darpan Twins Lab")
        st.markdown("Experience the future of customer insights through AI-powered digital twin simulations")

        st.divider()

        # Feature cards in columns
        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("🧬 Digital Twins")
            st.write("1,000+ unique AI personas based on real personality traits (OCEAN model)")

        with col2:
            st.subheader("🎯 Real Decisions")
            st.write("Watch twins make restaurant choices based on personality, weather, and context")

        with col3:
            st.subheader("📊 Rich Analytics")
            st.write("Detailed insights into decision factors, confidence scores, and reasoning")

        st.divider()

        # How it works section
        st.subheader("🚀 How It Works")
        st.write("""
1. **Select Location:** Choose a city, weather data is fetched automatically
2. **Upload Cards:** Upload images of two restaurant options (PNG/JPG)
3. **Run Simulation:** 10 digital twins analyze and choose between options
4. **View Results:** See aggregate choices, top factors, and detailed reasoning
        """)

        st.divider()

        # Stats section
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Digital Twins", "1,000+")
        with col2:
            st.metric("Training Examples", "10K+")
        with col3:
            st.metric("Avg. Runtime", "30s")

        # CTA Button
        st.markdown("<br>", unsafe_allow_html=True)
        col_center = st.columns([1, 2, 1])
        with col_center[1]:
            if st.button("🚀 Start Your First Experiment", use_container_width=True, type="primary"):
                st.session_state.step = 1
                st.rerun()
        st.markdown("<br><br>", unsafe_allow_html=True)

    # Page 1: City + Upload only
    elif step == 1:
        # STEP 1: LOCATION & CONTEXT
        st.markdown('<div class="section-header">📍 STEP 1: Location & Context</div>', unsafe_allow_html=True)

        # City selection with defaults
        st.markdown('<div class="section-subheader">Select City</div>', unsafe_allow_html=True)
        st.markdown('<div style="margin-bottom: 16px;"></div>', unsafe_allow_html=True)
        city_labels = [f"{c['name']}" for c in DEFAULT_CITIES]
        selected_default_idx = st.selectbox(
            "Choose from major Indian cities",
            list(range(len(city_labels))),
            format_func=lambda i: city_labels[i],
            key="city_selector_main",
            label_visibility="collapsed"
        )

        # Auto-fetch weather when city selected
        if selected_default_idx is not None:
            selected_city = DEFAULT_CITIES[selected_default_idx]
            # Auto-fetch weather if not already fetched for this city
            if (not st.session_state.get("last_city") or
                st.session_state.get("last_city", {}).get("name") != selected_city["name"]):
                with st.spinner("Fetching weather..."):
                    wx = fetch_current_weather(selected_city["latitude"], selected_city["longitude"])
                    st.session_state["last_wx"] = wx
                    st.session_state["last_city"] = selected_city

        # Display current weather with new design
        if st.session_state.get("last_wx") and st.session_state.get("last_city"):
            wx = st.session_state["last_wx"]
            city = st.session_state["last_city"]

            # Check if weather fetch had an error
            if wx.get("error"):
                st.warning(f"⚠️ {wx.get('error_message', 'Weather unavailable')} - Using default values")
                wx["temperature_c"] = 24.0
                wx["precip_mm"] = 0.0

            def temp_icon(t: float) -> str:
                return "❄️" if t <= 5 else ("🌤️" if t <= 20 else ("☀️" if t <= 32 else "🔥"))

            def rain_icon(r: float) -> str:
                return "🌫️" if r == 0 else ("🌦️" if r <= 2 else ("🌧️" if r <= 10 else "⛈️"))

            # Redesigned weather card using CSS classes
            st.markdown(
                f'''
                <div class="weather-card">
                    <div class="weather-title">Current Weather</div>
                    <div class="weather-content">
                        <div class="weather-icon">{temp_icon(wx['temperature_c'])}</div>
                        <div class="weather-icon">{rain_icon(wx['precip_mm'])}</div>
                        <div>
                            <div class="weather-city">{city['name']}</div>
                            <div class="weather-temp">{wx['temperature_c']:.0f}°C • {wx['precip_mm']:.1f}mm rain</div>
                        </div>
                        <div class="weather-status">✓ Updated</div>
                    </div>
                </div>
                ''',
                unsafe_allow_html=True
            )

        # Custom city search removed for simplicity

        # STEP 2: UPLOAD CARDS
        st.divider()
        st.markdown('<div class="section-header">🖼️ STEP 2: Upload Restaurant Cards</div>', unsafe_allow_html=True)

        upA, upB = st.columns(2)
        with upA:
            st.markdown('<div class="section-subheader">Card A</div>', unsafe_allow_html=True)
            file_a = st.file_uploader(
                "Upload Card A",
                type=["png", "jpg", "jpeg"],
                key="upload_card_a",
                label_visibility="collapsed"
            )
        with upB:
            st.markdown('<div class="section-subheader">Card B</div>', unsafe_allow_html=True)
            file_b = st.file_uploader(
                "Upload Card B",
                type=["png", "jpg", "jpeg"],
                key="upload_card_b",
                label_visibility="collapsed"
            )

        # Image Preview and Extracted Data Display
        if file_a or file_b:
            st.divider()
            st.markdown('<div class="section-header">📸 Preview & Extracted Data</div>', unsafe_allow_html=True)

            preview_cols = st.columns(2)

            with preview_cols[0]:
                if file_a:
                    st.markdown('<div class="section-subheader">Card A Preview</div>', unsafe_allow_html=True)
                    # Display image
                    st.image(file_a, use_container_width=True)

                    # Extract data if not already done
                    if "cards_a_preview" not in st.session_state:
                        with st.spinner("Analyzing Card A..."):
                            file_a.seek(0)  # Reset file pointer
                            card_a_data = extract_from_image(file_a.read())
                            st.session_state["cards_a_preview"] = card_a_data
                    else:
                        card_a_data = st.session_state["cards_a_preview"]

                    # Display extracted data in a nice format
                    if card_a_data:
                        st.markdown("""<div class="panel" style="margin-top: var(--space-3);">
                            <div style="font-weight: 600; margin-bottom: var(--space-2);">Extracted Information:</div>
                        """, unsafe_allow_html=True)

                        # Key information display
                        if card_a_data.get("name"):
                            st.markdown(f"**🏪 Name:** {card_a_data['name']}")
                        if card_a_data.get("cuisine"):
                            st.markdown(f"**🍽️ Cuisine:** {card_a_data['cuisine']}")
                        if card_a_data.get("dish_price"):
                            st.markdown(f"**💰 Price:** ₹{card_a_data['dish_price']}")
                        if card_a_data.get("rating_avg"):
                            st.markdown(f"**⭐ Rating:** {card_a_data['rating_avg']} ({card_a_data.get('num_reviews', 0)} reviews)")
                        if card_a_data.get("delivery_time_min"):
                            st.markdown(f"**⏱️ Delivery:** {card_a_data['delivery_time_min']} mins")
                        if card_a_data.get("distance_km"):
                            st.markdown(f"**📍 Distance:** {card_a_data['distance_km']} km")
                        if card_a_data.get("coupon_text"):
                            st.markdown(f"**🎟️ Offer:** {card_a_data['coupon_text']}")

                        st.markdown("</div>", unsafe_allow_html=True)

                        # Expandable JSON view
                        with st.expander("View Full JSON Data"):
                            st.json(card_a_data)

            with preview_cols[1]:
                if file_b:
                    st.markdown('<div class="section-subheader">Card B Preview</div>', unsafe_allow_html=True)
                    # Display image
                    st.image(file_b, use_container_width=True)

                    # Extract data if not already done
                    if "cards_b_preview" not in st.session_state:
                        with st.spinner("Analyzing Card B..."):
                            file_b.seek(0)  # Reset file pointer
                            card_b_data = extract_from_image(file_b.read())
                            st.session_state["cards_b_preview"] = card_b_data
                    else:
                        card_b_data = st.session_state["cards_b_preview"]

                    # Display extracted data in a nice format
                    if card_b_data:
                        st.markdown("""<div class="panel" style="margin-top: var(--space-3);">
                            <div style="font-weight: 600; margin-bottom: var(--space-2);">Extracted Information:</div>
                        """, unsafe_allow_html=True)

                        # Key information display
                        if card_b_data.get("name"):
                            st.markdown(f"**🏪 Name:** {card_b_data['name']}")
                        if card_b_data.get("cuisine"):
                            st.markdown(f"**🍽️ Cuisine:** {card_b_data['cuisine']}")
                        if card_b_data.get("dish_price"):
                            st.markdown(f"**💰 Price:** ₹{card_b_data['dish_price']}")
                        if card_b_data.get("rating_avg"):
                            st.markdown(f"**⭐ Rating:** {card_b_data['rating_avg']} ({card_b_data.get('num_reviews', 0)} reviews)")
                        if card_b_data.get("delivery_time_min"):
                            st.markdown(f"**⏱️ Delivery:** {card_b_data['delivery_time_min']} mins")
                        if card_b_data.get("distance_km"):
                            st.markdown(f"**📍 Distance:** {card_b_data['distance_km']} km")
                        if card_b_data.get("coupon_text"):
                            st.markdown(f"**🎟️ Offer:** {card_b_data['coupon_text']}")

                        st.markdown("</div>", unsafe_allow_html=True)

                        # Expandable JSON view
                        with st.expander("View Full JSON Data"):
                            st.json(card_b_data)

        # Start button with better styling
        st.markdown("")
        st.markdown("")
        ready = bool(file_a and file_b and st.session_state.get("last_wx") and st.session_state.get("last_city"))
        if st.button("▶️ Start Experiment", disabled=not ready, use_container_width=True):
            # Use already extracted data from preview
            card_a = st.session_state.get("cards_a_preview", {})
            card_b = st.session_state.get("cards_b_preview", {})

            # If preview data doesn't exist, extract now
            if not card_a and file_a:
                file_a.seek(0)
                card_a = extract_from_image(file_a.read())
            if not card_b and file_b:
                file_b.seek(0)
                card_b = extract_from_image(file_b.read())

            st.session_state["cards_a"] = card_a
            st.session_state["cards_b"] = card_b
            wx = st.session_state.get("last_wx", {})
            st.session_state["ctx"] = {
                "hour_of_day": int(wx.get("hour_of_day", 13)),
                "is_weekend": int(wx.get("is_weekend", 0)),
                "temperature_c": float(wx.get("temperature_c", 24.0)),
                "precip_mm": float(wx.get("precip_mm", 0.0)),
            }
            st.session_state["run_params"] = {
                "profiles": [os.path.join(profiles_dir, f) for f in (files[:10] if len(files) >= 10 else files)],
                "k": 50,
                "n_samples": 3,
                "temperature": 0.3,
            }
            st.session_state["pending_run"] = True
            st.session_state.step = 2
            st.rerun()

    # Page 2: Loading & run with Full-Screen Blur Overlay
    elif step == 2:
        # Display the blur overlay with loading animation
        progress_pct = st.session_state.get("progress_pct", 0)
        current_twin = st.session_state.get("current_twin", "Initializing...")

        st.markdown(f"""
        <div class="blur-overlay">
            <div class="loading-card">
                <div class="loading-icon">🤖</div>
                <div class="loading-title">Experiment Running</div>
                <div class="loading-status">Processing Digital Twins</div>

                <div class="loading-progress-container">
                    <div class="loading-progress-bar" style="width: {progress_pct}%"></div>
                </div>

                <div class="loading-percentage">{progress_pct}%</div>
                <div class="loading-subtitle">Analyzing restaurant choices...</div>

                <div class="loading-twin-info">
                    <div>Current Twin: {current_twin}</div>
                    <div style="margin-top: var(--space-2); color: var(--brand2);">
                        10 digital twins are making decisions based on their unique personalities
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Also keep a progress bar for functionality
        prog = st.progress(0, text="")
        def on_progress(done: int, total: int) -> None:
            pct = int(round(100 * done / max(1, total)))
            st.session_state["progress_pct"] = pct
            # Update current twin info
            if done > 0:
                st.session_state["current_twin"] = f"USER_{done:03d}"
            prog.progress(min(pct, 100), text="")
        if st.session_state.get("pending_run"):
            params = st.session_state.get("run_params", {})
            dual_results = run_dual_llm_for_users(
                params.get("profiles", []),
                choices_csv=os.path.join("data", "choices.csv"),
                runtime_context=st.session_state.get("ctx", {}),
                card_a=st.session_state.get("cards_a", {}),
                card_b=st.session_state.get("cards_b", {}),
                k=int(params.get("k", 50)),
                n_samples=int(params.get("n_samples", 3)),
                temperature=float(params.get("temperature", 0.3)),
                progress_cb=on_progress,
            )
            st.session_state["dual_results"] = dual_results
            st.session_state["pending_run"] = False
            st.session_state["xp"] = st.session_state.get("xp", 0) + 10
            st.session_state.step = 3
            st.rerun()
        else:
            st.info("Preparing…")

    # Page 3: Results
    elif step == 3:
        st.subheader("Results")
        dual_results = st.session_state.get("dual_results", [])
        agg = aggregate_results(dual_results)

        total = agg["total_twins"]
        counts = agg["counts"]
        pct = agg["percent"]
        a_pct = pct['A']
        b_pct = pct['B']
        t_pct = pct['tie']

        st.markdown('<div class="panel ghost">', unsafe_allow_html=True)

        # Summary stats
        st.markdown(f"**Experiment Summary**: {total} digital twins simulated")
        st.markdown("")

        # Aggregate results with fixed spacing
        st.markdown("**Aggregate Results**")
        st.markdown(f"<b>Card A:</b> {counts['A']} twins ({a_pct:.1f}%)", unsafe_allow_html=True)
        st.markdown(f'<div class="scorebar"><div style="width:{a_pct:.1f}%"></div></div>', unsafe_allow_html=True)
        st.markdown("")

        st.markdown(f"<b>Card B:</b> {counts['B']} twins ({b_pct:.1f}%)", unsafe_allow_html=True)
        st.markdown(f'<div class="scorebar"><div style="width:{b_pct:.1f}%"></div></div>', unsafe_allow_html=True)
        st.markdown("")

        st.markdown(f"<b>Tie:</b> {counts['tie']} twins ({t_pct:.1f}%)", unsafe_allow_html=True)
        st.markdown(f'<div class="scorebar"><div style="width:{t_pct:.1f}%"></div></div>', unsafe_allow_html=True)
        st.markdown("")
        st.markdown("")

        # Top factors for A and B
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Top Factors for Card A**")
            if agg["top_a_factors"]:
                for item in agg["top_a_factors"]:
                    st.markdown(f"• **{item['factor']}** - {item['count']} twins ({item['pct']:.0f}%)")
            else:
                st.markdown("—")

        with col_b:
            st.markdown("**Top Factors for Card B**")
            if agg["top_b_factors"]:
                for item in agg["top_b_factors"]:
                    st.markdown(f"• **{item['factor']}** - {item['count']} twins ({item['pct']:.0f}%)")
            else:
                st.markdown("—")

        st.markdown("")

        # Checks breakdown
        st.markdown("**Decision Criteria Breakdown**")
        checks = agg["checks_breakdown"]
        check_cols = st.columns(4)
        for idx, (check_name, check_data) in enumerate(checks.items()):
            with check_cols[idx]:
                st.markdown(f"**{check_name.title()}**")
                st.markdown(f"A: {check_data['A']}")
                st.markdown(f"B: {check_data['B']}")
                st.markdown(f"Tie: {check_data['tie']}")

        st.markdown("")
        st.markdown("")

        # Reset button
        if st.button("🔄 Run Another Experiment"):
            reset_experiment()
            st.rerun()

        # Detailed per-twin data
        with st.expander("Detailed Per-Twin Data"):
            st.dataframe([
                {
                    "user_id": r.get("user_id"),
                    "name": r.get("name"),
                    "action": r.get("action"),
                    "reasons": "; ".join(r.get("reasons", [])),
                    "price": r.get("checks", {}).get("price"),
                    "delivery": r.get("checks", {}).get("delivery"),
                    "fit": r.get("checks", {}).get("fit"),
                    "trust": r.get("checks", {}).get("trust"),
                    "likert": r.get("likert"),
                    "response_A": r.get("response_A"),
                    "response_B": r.get("response_B"),
                } for r in dual_results
            ])
        st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
