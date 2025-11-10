import os
import re
import json
import random
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

    /* Properly style widget labels instead of hiding them */
    label[data-testid="stWidgetLabel"] {
      font-weight: 500;
      font-size: var(--text-sm);
      color: var(--text);
      margin-bottom: var(--space-2);
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
    /* Style expander labels properly */
    .stExpander summary > span {
      font-weight: 600;
      font-size: var(--text-base);
    }

    /* Weather Card */
    .weather-card {
      background: linear-gradient(135deg, hsl(0,0%,14%), hsl(0,0%,10%));
      border: 1px solid var(--brand2);
      border-radius: 16px;
      padding: var(--space-6);
      margin: var(--space-4) 0 var(--space-6) 0;
      box-shadow: var(--glowB);
      overflow: hidden;
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
      overflow: hidden;
      flex-wrap: nowrap;
    }
    .weather-icon {
      font-size: 48px;
      line-height: 1.2;
      flex-shrink: 0;
    }
    .weather-info {
      flex: 1;
      min-width: 0;
    }
    .weather-city {
      font-size: var(--text-xl);
      font-weight: 700;
      color: var(--text);
      margin-bottom: var(--space-1);
      line-height: 1.4;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
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

    /* Slider - Theme-appropriate colors */
    .stSlider > div > div > div > div {
      background: linear-gradient(90deg, #4CAF50, #2196F3) !important;
    }
    .stSlider > div > div > div {
      background: hsl(0, 0%, 15%) !important;
    }
    .stSlider label {
      color: var(--text) !important;
      font-size: var(--text-sm) !important;
      font-weight: 500 !important;
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
      font-size: var(--text-lg);
      color: var(--brand2);
      margin-top: var(--space-3);
      font-weight: 600;
      animation: pulse 2s ease-in-out infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.6; }
    }

    .loading-percentage {
      font-size: var(--text-3xl);
      font-weight: 700;
      color: var(--brand);
      margin-bottom: var(--space-2);
    }

    .loading-twin-info {
      margin-top: var(--space-6);
      padding-top: var(--space-6);
      border-top: 1px solid var(--divider);
      font-size: var(--text-sm);
      color: var(--muted);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def parse_card_form(prefix: str) -> Dict[str, Any]:
    cuisines = ["italian", "mexican", "sushi", "indian", "american", "chinese", "thai", "pizza", "burgers"]
    with st.expander(f"{prefix} card details"):
        name = st.text_input(f"{prefix} name", value=f"{prefix} Restaurant")
        cuisine = st.selectbox(f"{prefix} cuisine", cuisines, index=0, key=f"{prefix}_cuisine", label_visibility="collapsed")
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
        idx = st.selectbox("Results", list(range(len(labels))), format_func=lambda i: labels[i], label_visibility="collapsed")
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
    st.markdown(
        '''
        <div class="logo">
            Darpan <span class="logo-grad">Twins</span> Lab
        </div>
        <div class="tagline">AI-Powered Digital Twin Experiments</div>
        ''',
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
                f'<span class="step-pill {"active" if step==1 else ""}">1. Setup</span>'
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
3. **Select Twins:** Choose from all 1,000+ twins or filter by demographics/personality
4. **Run Simulation:** Your selected digital twins analyze and choose between options
5. **View Results:** See aggregate choices, top factors, and detailed reasoning
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
                        <div class="weather-info">
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
                    # Display image with constrained size
                    st.image(file_a, width=350)

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

                        # Show JSON data with checkbox toggle
                        st.markdown("")
                        if st.checkbox("📋 Show Full JSON Data", key="show_json_a", value=False):
                            st.json(card_a_data)

            with preview_cols[1]:
                if file_b:
                    st.markdown('<div class="section-subheader">Card B Preview</div>', unsafe_allow_html=True)
                    # Display image with constrained size
                    st.image(file_b, width=350)

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

                        # Show JSON data with checkbox toggle
                        st.markdown("")
                        if st.checkbox("📋 Show Full JSON Data", key="show_json_b", value=False):
                            st.json(card_b_data)

        # Twin Selection Section
        st.divider()
        st.markdown('<div class="section-header">👥 STEP 3: Twin Selection</div>', unsafe_allow_html=True)

        # Load all profile metadata if not already loaded
        if "all_profiles_data" not in st.session_state:
            profiles_dir = os.path.join("data", "twin_profiles")
            all_profiles_data = []
            try:
                files = sorted([f for f in os.listdir(profiles_dir) if f.endswith(".json")])
                for file in files[:]:  # Load all profiles
                    try:
                        with open(os.path.join(profiles_dir, file), 'r') as f:
                            profile_data = json.load(f)
                            profile_data['file_path'] = os.path.join(profiles_dir, file)
                            all_profiles_data.append(profile_data)
                    except:
                        continue
                st.session_state["all_profiles_data"] = all_profiles_data
            except:
                st.error("Could not load twin profiles")
                st.session_state["all_profiles_data"] = []

        all_profiles_data = st.session_state.get("all_profiles_data", [])

        # Display available twins count
        st.info(f"📊 **{len(all_profiles_data)} Digital Twins Available** - Each with unique OCEAN personality traits and demographics")

        # Twin selection method
        selection_method = st.radio(
            "Selection Method",
            ["Use All Twins (Full Dataset)", "Select Random Sample", "Apply Filters"],
            index=0,
            horizontal=True
        )

        selected_profiles = all_profiles_data.copy()

        if selection_method == "Select Random Sample":
            col1, col2, col3 = st.columns([1.5, 1.5, 1])

            # Quick select buttons
            with col1:
                st.markdown("**Quick Select:**")
                button_cols = st.columns(4)
                preset_values = [50, 100, 200, 500]
                for idx, val in enumerate(preset_values):
                    with button_cols[idx]:
                        if st.button(str(val), key=f"preset_{val}", use_container_width=True):
                            st.session_state["sample_size_input"] = val

            # Custom number input
            with col2:
                st.markdown("**Custom Count:**")
                sample_size = st.number_input(
                    "Number of twins",
                    min_value=1,
                    max_value=min(len(all_profiles_data), 1000),
                    value=st.session_state.get("sample_size_input", 50),
                    step=1,
                    key="sample_size_input",
                    label_visibility="collapsed",
                    help="Note: More twins = longer processing time (~3-6 seconds per twin)"
                )

            with col3:
                st.markdown("**Randomize:**")
                if st.button("🎲 Shuffle", use_container_width=True):
                    st.session_state["random_seed"] = random.randint(0, 10000)

            # Apply random sampling
            random.seed(st.session_state.get("random_seed", 42))
            selected_profiles = random.sample(all_profiles_data, min(sample_size, len(all_profiles_data)))

        elif selection_method == "Apply Filters":
            # Quick preset segments
            st.markdown("**🚀 Quick Presets**")
            preset_segments = {
                "All Twins": None,
                "Young Adults (18-30)": {"age": (18, 30)},
                "Middle Aged (31-50)": {"age": (31, 50)},
                "High Income (>₹500k)": {"income": (500000, float('inf'))},
                "Adventure Seekers": {"openness": "High"},
                "Quality Focused": {"conscientiousness": "High"},
                "Social Butterflies": {"extraversion": "High"},
                "Budget Conscious": {"income": (0, 300000)},
            }

            preset = st.selectbox(
                "Select a preset filter",
                options=list(preset_segments.keys()),
                index=0,
                help="Quick filters for common segments",
                label_visibility="collapsed"
            )

            # Advanced filters with checkbox toggle
            show_filters = st.checkbox("🎯 Show Advanced Filters", value=(preset == "All Twins"), key="show_advanced_filters")

            if show_filters:
                # Add tabs for better organization
                tab1, tab2, tab3 = st.tabs(["Demographics", "Personality", "Behavioral"])

                with tab1:
                    col1, col2 = st.columns(2)
                    with col1:
                        # Age filter - use groups instead of slider
                        st.markdown("**Age Groups**")
                        age_groups = ["18-25", "26-35", "36-45", "46-55", "56+"]
                        selected_age_groups = st.multiselect(
                            "Age Groups",
                            options=age_groups,
                            default=age_groups,
                            help="Select one or more age groups",
                            label_visibility="collapsed"
                        )

                        # Convert age groups to ranges
                        age_range = (18, 100)
                        if selected_age_groups and len(selected_age_groups) < len(age_groups):
                            min_ages = []
                            max_ages = []
                            for group in selected_age_groups:
                                if group == "18-25":
                                    min_ages.append(18)
                                    max_ages.append(25)
                                elif group == "26-35":
                                    min_ages.append(26)
                                    max_ages.append(35)
                                elif group == "36-45":
                                    min_ages.append(36)
                                    max_ages.append(45)
                                elif group == "46-55":
                                    min_ages.append(46)
                                    max_ages.append(55)
                                elif group == "56+":
                                    min_ages.append(56)
                                    max_ages.append(100)
                            age_range = (min(min_ages), max(max_ages))

                        # Gender filter
                        st.markdown("**Gender**")
                        gender_options = list(set([p['demographics']['gender'] for p in all_profiles_data]))
                        selected_genders = st.multiselect(
                            "Gender",
                            options=gender_options,
                            default=gender_options,
                            label_visibility="collapsed"
                        )

                    with col2:
                        # Income filter - use brackets instead of slider
                        st.markdown("**Income Brackets**")
                        income_brackets = ["<₹2L", "₹2-5L", "₹5-8L", "₹8-12L", "₹12L+"]
                        selected_income_brackets = st.multiselect(
                            "Income Brackets",
                            options=income_brackets,
                            default=income_brackets,
                            help="Select one or more income brackets",
                            label_visibility="collapsed"
                        )

                        # Convert income brackets to range
                        income_range = (0, float('inf'))
                        if selected_income_brackets and len(selected_income_brackets) < len(income_brackets):
                            min_incomes = []
                            max_incomes = []
                            for bracket in selected_income_brackets:
                                if bracket == "<₹2L":
                                    min_incomes.append(0)
                                    max_incomes.append(200000)
                                elif bracket == "₹2-5L":
                                    min_incomes.append(200000)
                                    max_incomes.append(500000)
                                elif bracket == "₹5-8L":
                                    min_incomes.append(500000)
                                    max_incomes.append(800000)
                                elif bracket == "₹8-12L":
                                    min_incomes.append(800000)
                                    max_incomes.append(1200000)
                                elif bracket == "₹12L+":
                                    min_incomes.append(1200000)
                                    max_incomes.append(float('inf'))
                            income_range = (min(min_incomes), max(max_incomes))

                with tab2:
                    # OCEAN trait filters - use select boxes instead of sliders
                    ocean_filters = {}
                    trait_levels = ["Any", "Low (0-0.4)", "Medium (0.4-0.7)", "High (0.7-1.0)"]

                    col1, col2 = st.columns(2)
                    traits_col1 = ['openness', 'conscientiousness', 'extraversion']
                    traits_col2 = ['agreeableness', 'neuroticism']

                    with col1:
                        for trait in traits_col1:
                            level = st.selectbox(
                                trait.capitalize(),
                                options=trait_levels,
                                index=0,
                                key=f"ocean_{trait}",
                                label_visibility="collapsed"
                            )

                            if level == "Low (0-0.4)":
                                ocean_filters[trait] = (0.0, 0.4)
                            elif level == "Medium (0.4-0.7)":
                                ocean_filters[trait] = (0.4, 0.7)
                            elif level == "High (0.7-1.0)":
                                ocean_filters[trait] = (0.7, 1.0)
                            else:  # Any
                                ocean_filters[trait] = (0.0, 1.0)

                    with col2:
                        for trait in traits_col2:
                            level = st.selectbox(
                                trait.capitalize(),
                                options=trait_levels,
                                index=0,
                                key=f"ocean_{trait}",
                                label_visibility="collapsed"
                            )

                            if level == "Low (0-0.4)":
                                ocean_filters[trait] = (0.0, 0.4)
                            elif level == "Medium (0.4-0.7)":
                                ocean_filters[trait] = (0.4, 0.7)
                            elif level == "High (0.7-1.0)":
                                ocean_filters[trait] = (0.7, 1.0)
                            else:  # Any
                                ocean_filters[trait] = (0.0, 1.0)

                with tab3:
                    st.markdown("**Behavioral Filters**")
                    col1, col2 = st.columns(2)

                    with col1:
                        # Birth place average income
                        birth_income_brackets = ["Low (<₹3L)", "Medium (₹3-5L)", "High (>₹5L)", "Any"]
                        selected_birth_income = st.selectbox(
                            "Birth Place Economic Status",
                            options=birth_income_brackets,
                            index=3,
                            help="Economic status of the place where the twin was born",
                            label_visibility="collapsed"
                        )

                        birth_income_range = (0, float('inf'))
                        if selected_birth_income == "Low (<₹3L)":
                            birth_income_range = (0, 300000)
                        elif selected_birth_income == "Medium (₹3-5L)":
                            birth_income_range = (300000, 500000)
                        elif selected_birth_income == "High (>₹5L)":
                            birth_income_range = (500000, float('inf'))

                    with col2:
                        # Food variety index
                        variety_levels = ["Low (0-0.3)", "Medium (0.3-0.6)", "High (0.6-1.0)", "Any"]
                        selected_variety = st.selectbox(
                            "Food Variety Preference",
                            options=variety_levels,
                            index=3,
                            help="Preference for food variety in the birth location",
                            label_visibility="collapsed"
                        )

                        variety_range = (0.0, 1.0)
                        if selected_variety == "Low (0-0.3)":
                            variety_range = (0.0, 0.3)
                        elif selected_variety == "Medium (0.3-0.6)":
                            variety_range = (0.3, 0.6)
                        elif selected_variety == "High (0.6-1.0)":
                            variety_range = (0.6, 1.0)

            # Apply preset if selected
            if preset != "All Twins" and preset_segments[preset]:
                preset_config = preset_segments[preset]
                if "age" in preset_config:
                    age_range = preset_config["age"]
                if "income" in preset_config:
                    income_range = preset_config["income"]
                if "openness" in preset_config:
                    if preset_config["openness"] == "High":
                        ocean_filters["openness"] = (0.7, 1.0)
                if "conscientiousness" in preset_config:
                    if preset_config["conscientiousness"] == "High":
                        ocean_filters["conscientiousness"] = (0.7, 1.0)
                if "extraversion" in preset_config:
                    if preset_config["extraversion"] == "High":
                        ocean_filters["extraversion"] = (0.7, 1.0)

            # Apply filters
            filtered_profiles = []
            for profile in all_profiles_data:
                # Check demographics
                if not (age_range[0] <= profile['demographics']['age'] <= age_range[1]):
                    continue
                if profile['demographics']['gender'] not in selected_genders:
                    continue
                if not (income_range[0] <= profile['demographics']['income'] <= income_range[1]):
                    continue

                # Check behavioral filters
                if 'birth_income_range' in locals():
                    birth_income = profile['demographics'].get('place_of_birth_avg_income', 0)
                    if not (birth_income_range[0] <= birth_income <= birth_income_range[1]):
                        continue

                if 'variety_range' in locals():
                    variety = profile['demographics'].get('place_of_birth_food_variety_index', 0)
                    if not (variety_range[0] <= variety <= variety_range[1]):
                        continue

                # Check OCEAN traits
                valid = True
                for trait, (min_val, max_val) in ocean_filters.items():
                    if not (min_val <= profile['OCEAN'][trait] <= max_val):
                        valid = False
                        break

                if valid:
                    filtered_profiles.append(profile)

            selected_profiles = filtered_profiles

            # Sample size for filtered results
            if len(selected_profiles) > 100:
                max_filtered = st.number_input(
                    f"Limit to (filtered {len(selected_profiles)} twins)",
                    min_value=1,
                    max_value=min(len(selected_profiles), 1000),
                    value=min(100, len(selected_profiles)),
                    step=1
                )
                random.seed(42)
                selected_profiles = random.sample(selected_profiles, min(max_filtered, len(selected_profiles)))

        # Display selection summary
        if selected_profiles:
            st.success(f"✅ **{len(selected_profiles)} twins selected** for the experiment")

            # Show preview with checkbox toggle
            st.markdown("")
            if st.checkbox(f"👥 Show Preview of Selected Twins ({len(selected_profiles)})", value=False, key="show_twin_preview"):
                st.markdown("---")
                st.markdown("**First 10 twins in the selection:**")
                preview_data = []
                for p in selected_profiles[:10]:  # Show first 10
                    preview_data.append({
                        "ID": p['user_id'],
                        "Age": p['demographics']['age'],
                        "Gender": p['demographics']['gender'],
                        "O": f"{p['OCEAN']['openness']:.1f}",
                        "C": f"{p['OCEAN']['conscientiousness']:.1f}",
                        "E": f"{p['OCEAN']['extraversion']:.1f}",
                        "A": f"{p['OCEAN']['agreeableness']:.1f}",
                        "N": f"{p['OCEAN']['neuroticism']:.1f}",
                    })
                st.dataframe(preview_data, hide_index=True)
                if len(selected_profiles) > 10:
                    st.info(f"... and {len(selected_profiles) - 10} more twins")
                st.markdown("---")
        else:
            st.warning("No twins match the selected criteria. Please adjust filters.")

        # Performance warning
        if len(selected_profiles) > 50:
            est_time = len(selected_profiles) * 4  # ~4 seconds per twin
            st.warning(f"⏱️ **Performance Note**: Processing {len(selected_profiles)} twins will take approximately {est_time//60} minutes {est_time%60} seconds")

        # Start button with better styling
        st.markdown("")
        st.markdown("")
        ready = bool(file_a and file_b and st.session_state.get("last_wx") and st.session_state.get("last_city") and selected_profiles)
        if st.button("▶️ Start Experiment", disabled=not ready, use_container_width=True, type="primary"):
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

            # Use selected profiles instead of hardcoded 10
            profile_paths = [p['file_path'] for p in selected_profiles]
            st.session_state["run_params"] = {
                "profiles": profile_paths,
                "k": 50,
                "n_samples": 3,
                "temperature": 0.3,
            }
            st.session_state["selected_twin_count"] = len(selected_profiles)
            st.session_state["pending_run"] = True
            st.session_state.step = 2
            st.rerun()

    # Page 2: Loading & run - Using Native Streamlit Components
    elif step == 2:
        # Create an anchor at the top for auto-scroll
        st.markdown('<a id="top"></a>', unsafe_allow_html=True)
        # JavaScript to scroll to top on page load
        st.markdown("""
        <script>
        window.onload = function() {
            window.scrollTo({top: 0, behavior: 'instant'});
            document.getElementById('top').scrollIntoView();
        }
        </script>
        """, unsafe_allow_html=True)

        # Validate twin count is properly set
        total_twins = st.session_state.get("selected_twin_count")
        if not total_twins:
            st.error("Error: Twin count not set properly. Please go back and select twins again.")
            if st.button("Go Back"):
                st.session_state.step = 1
                st.rerun()

        # Initialize progress tracking
        progress_pct = st.session_state.get("progress_pct", 0)
        current_twin_num = st.session_state.get("current_twin_num", 0)
        current_stage = st.session_state.get("current_stage", "Initializing...")

        # Create container for loading display
        with st.container():
            st.markdown("## 🤖 Experiment Running")
            st.markdown(f"### Processing {total_twins} Digital Twins")

            # Add stop button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("⏹️ Stop Experiment", key="stop_button", use_container_width=True):
                    st.session_state["stop_requested"] = True
                    st.warning("Stopping experiment... Please wait for current twin to complete.")

            st.markdown("---")

            # Progress bar
            progress_bar = st.progress(progress_pct / 100.0, text=f"Overall Progress: {progress_pct}%")

            # Twin counter and stage info
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Current Twin", f"{current_twin_num} of {total_twins}", delta=None)
            with col2:
                time_estimate = (total_twins - current_twin_num) * 4  # ~4 seconds per twin
                st.metric("Estimated Time Remaining", f"{time_estimate // 60}m {time_estimate % 60}s", delta=None)

            # Current stage display
            stage_container = st.empty()
            stage_container.info(f"**Current Stage:** {current_stage}")

            # Show processing details directly (no expander)
            st.markdown("")
            st.markdown("---")
            st.markdown("**📊 Processing Details:**")
            col_details1, col_details2, col_details3 = st.columns(3)
            with col_details1:
                st.markdown(f"**Total Twins:** {total_twins}")
                st.markdown(f"**Current Twin:** {current_twin_num}")
            with col_details2:
                st.markdown(f"**Progress:** {progress_pct}%")
                st.markdown(f"**Stage:** {current_stage}")
            with col_details3:
                st.markdown(f"**Speed:** ~3-6s per twin")
                est_remaining = (total_twins - current_twin_num) * 4
                st.markdown(f"**Est. Time:** {est_remaining//60}m {est_remaining%60}s")

            # Store containers in session state for updates
            st.session_state["progress_bar"] = progress_bar
            st.session_state["stage_container"] = stage_container

        # Progress callback function
        def on_progress(done: int, total: int, stage: str = "", twin_num: int = 0) -> None:
            # Check if stop was requested
            if st.session_state.get("stop_requested", False):
                st.stop()  # Stop execution

            # Calculate progress based on twins completed, not API calls
            # Each twin has ~9 API calls, so we calculate based on twin_num instead
            total_twins_count = st.session_state.get("selected_twin_count", 1)

            # Calculate percentage based on twins completed
            # If twin_num is 0, use the API call progress but scale it down
            if twin_num > 0:
                # Use twin progress (twin_num - 1 because it's 1-indexed)
                twins_completed = twin_num - 1
                # Add partial progress for current twin (done/total gives progress within current twin)
                within_twin_progress = (done % 9) / 9.0 if total > 0 else 0
                pct = int(round(100 * (twins_completed + within_twin_progress) / max(1, total_twins_count)))
            else:
                # Fallback to original calculation but scaled
                pct = int(round(100 * done / max(1, total)))

            st.session_state["progress_pct"] = pct
            st.session_state["current_twin_num"] = twin_num
            st.session_state["current_stage"] = stage

            # Parse stage to get cleaner display
            stage_display = stage
            if "Analyzing Card A" in stage:
                stage_display = "🔍 Analyzing Card A..."
            elif "Analyzing Card B" in stage:
                stage_display = "🔍 Analyzing Card B..."
            elif "Comparing options" in stage:
                stage_display = "⚖️ Making decision..."
            elif "Finalizing" in stage:
                stage_display = "📊 Finalizing decision..."
            elif stage == "":
                stage_display = "🤖 Processing..."

            # Update native components if they exist
            if "progress_bar" in st.session_state:
                st.session_state["progress_bar"].progress(pct / 100.0, text=f"Overall Progress: {pct}%")
            if "stage_container" in st.session_state:
                st.session_state["stage_container"].info(f"**Current Stage:** {stage_display}")

            # Force a rerun to update the display
            # Note: This is commented out to prevent infinite loops
            # st.rerun()
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

        # Summary stats
        st.markdown(f"**Experiment Summary**: {total} digital twins simulated")
        st.markdown("")

        # Aggregate results with fixed spacing
        st.markdown("**Aggregate Results**")
        st.markdown(f"**Card A:** {counts['A']} twins ({a_pct:.1f}%)")
        st.markdown(f'<div class="scorebar"><div style="width:{a_pct:.1f}%"></div></div>', unsafe_allow_html=True)
        st.markdown("")

        st.markdown(f"**Card B:** {counts['B']} twins ({b_pct:.1f}%)")
        st.markdown(f'<div class="scorebar"><div style="width:{b_pct:.1f}%"></div></div>', unsafe_allow_html=True)
        st.markdown("")

        st.markdown(f"**Tie:** {counts['tie']} twins ({t_pct:.1f}%)")
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

        # Detailed per-twin data with checkbox toggle
        if st.checkbox("📋 Show Detailed Per-Twin Data", value=False, key="show_detailed_data"):
            st.markdown("---")
            st.markdown("**Detailed Decision Data for Each Twin:**")
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


if __name__ == "__main__":
    main()
