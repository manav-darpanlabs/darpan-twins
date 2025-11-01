import os
from typing import Dict, Any, List

import streamlit as st

from twins.prompt_simulator import run_dual_llm_for_users
from twins.card_parser import extract_from_image
from twins.weather import search_cities, fetch_current_weather


st.set_page_config(page_title="Darpan Labs — Customer Twin MVP", page_icon="🍽️", layout="wide")

# Minimal dark style to approximate dashboard look
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');
    :root {
      /* Theme palette */
      --brand: #C1E329;      /* neon green */
      --brand2: #3fb1f0;     /* neon blue */
      --bg: hsl(0, 0%, 8%);  /* 8% lightness */
      --panel: hsl(0, 0%, 12%); /* 12% lightness */
      --border: #1f232b;
      --text: hsl(0, 0%, 98%);
      --muted: #aab4c2;
      --glowG: 0 0 16px rgba(193, 227, 41, 0.35);
      --glowB: 0 0 16px rgba(63, 177, 240, 0.35);
    }
    html, body, [class^="css"], * { font-family: 'Space Grotesk', system-ui, -apple-system, Segoe UI, Roboto, sans-serif !important; }
    .block-container {padding-top: 0.25rem; padding-bottom: 1.5rem;}
    body {background: var(--bg); color: var(--text);} 
    .hero {display:flex; align-items:center; justify-content:space-between; padding: 8px 0 16px 0;}
    .logo {font-weight:800; font-size:20px; letter-spacing:0.8px;}
    .logo-grad {background: linear-gradient(90deg, var(--brand), var(--brand2)); -webkit-background-clip:text; background-clip:text; color:transparent; text-shadow: var(--glowG), var(--glowB)}
    .xp {background: linear-gradient(180deg, hsl(0,0%,14%), hsl(0,0%,10%)); border:1px solid var(--border); border-radius:10px; padding:8px 12px; color:var(--text); box-shadow: var(--glowB)}
    .stepper {display:flex; gap:8px; margin: 4px 0 14px 0;}
    .step-pill {padding: 6px 10px; border-radius: 999px; border:1px solid var(--border); color: var(--muted); background: hsl(0,0%,10%); transition: all .25s cubic-bezier(.22,.61,.36,1)}
    .step-pill.active {color: var(--text); background: linear-gradient(180deg, hsl(0,0%,14%), hsl(0,0%,10%)); border-color: var(--brand2); box-shadow: none}
    .panel {background: var(--panel); border:1px solid var(--border); border-radius:12px; padding:12px; color:var(--text)}
    .panel.ghost { background: transparent; border: none; padding: 0; }
    .cta {background: var(--brand); color:#0b0e14; padding:10px 14px; border-radius:12px; font-weight:700; border:none; box-shadow: var(--glowG); transition: transform .15s cubic-bezier(.22,.61,.36,1)}
    .cta:hover { transform: translateY(-1px); }
    .mini {font-size:12px; color: var(--muted)}
    .scorebar {height:8px; border-radius:6px; background:hsl(0,0%,10%); border:1px solid var(--border); overflow:hidden; box-shadow: inset 0 0 8px rgba(0,0,0,.45)}
    .scorebar > div {height:100%; background: linear-gradient(90deg, var(--brand), var(--brand2)); box-shadow: var(--glowG), var(--glowB)}
    .card-preview {font-size:13px; color:var(--muted);}
    .hint {color: var(--muted); font-size:12px}
    /* Streamlit control tweaks */
    /* Primary buttons (default) */
    .stButton>button { background: var(--brand); color:#0b0e14; border-radius:12px; border:none; box-shadow: var(--glowG); font-weight:700; }
    /* Secondary buttons only inside .secondary-zone containers */
    .secondary-zone .stButton>button { background: var(--brand2); color:#0b0e14; box-shadow: var(--glowB); }
    .stTextInput>div>div>input, .stSelectbox>div>div>div { background: hsl(0,0%,10%); color: var(--text); border-radius:10px; border:1px solid var(--border); box-shadow:none; }
    /* Prevent label/placeholder overlap */
    .stTextInput>label { position: static !important; display:block; margin-bottom:6px; }
    .stTextInput input::placeholder { opacity:.6; }
    /* tighten headings and labels */
    h1,h2,h3 { margin: 0 0 10px 0; }
    label, .stMarkdown p { margin-bottom: 6px; }
    .stSlider>div>div>div>div { background: var(--brand2) !important; }
    </style>
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


def aggregate_results(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    totals = {"A": 0, "B": 0, "tie": 0}
    reasons_a: dict[str, int] = {}
    reasons_b: dict[str, int] = {}
    n = len(rows) if rows else 0
    for r in rows or []:
        choice = r.get("action", "tie")
        if choice not in totals:
            choice = "tie"
        totals[choice] += 1
        for reason in r.get("reasons", []) or []:
            if choice == "A":
                reasons_a[reason] = reasons_a.get(reason, 0) + 1
            elif choice == "B":
                reasons_b[reason] = reasons_b.get(reason, 0) + 1
    pct = {k: (v * 100.0 / n if n else 0.0) for k, v in totals.items()}
    top_a = [r for r, _ in sorted(reasons_a.items(), key=lambda kv: kv[1], reverse=True)[:3]]
    top_b = [r for r, _ in sorted(reasons_b.items(), key=lambda kv: kv[1], reverse=True)[:3]]
    return {"counts": totals, "percent": pct, "top_a": top_a, "top_b": top_b}


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


def main() -> None:
    # Header
    colH1, colH2 = st.columns([3,1])
    with colH1:
        st.markdown('<div class="hero"><div class="logo">Darpan <span class="logo-grad">Twins</span> Lab</div></div>', unsafe_allow_html=True)
    with colH2:
        xp = st.session_state.get("xp", 0)
        st.markdown(f'<div class="xp">XP: {xp} <span class="mini">• Complete runs to unlock badges</span></div>', unsafe_allow_html=True)

    # Users picker (multi-select)
    profiles_dir = os.path.join("data", "twin_profiles")
    files = []
    try:
        files = sorted([f for f in os.listdir(profiles_dir) if f.endswith(".json")])
    except Exception:
        pass

    # Wizard step setup
    if "step" not in st.session_state:
        st.session_state.step = 1
    step = st.session_state.step
    st.markdown('<div class="stepper">'
                f'<span class="step-pill {"active" if step==1 else ""}">1. City & Upload</span>'
                f'<span class="step-pill {"active" if step==2 else ""}">2. Running</span>'
                f'<span class="step-pill {"active" if step==3 else ""}">3. Results</span>'
                '</div>', unsafe_allow_html=True)

    # Page 1: City + Upload only
    if step == 1:
        st.subheader("Select city & upload cards")
        st.markdown('<div class="panel ghost">', unsafe_allow_html=True)
        q = st.text_input("🔎 Search city", value=st.session_state.get("city_q", ""))
        if q != st.session_state.get("city_q"):
            st.session_state["city_q"] = q
            st.session_state["city_results"] = []
        colc1, colc2 = st.columns([1,3])
        with colc1:
            st.markdown('<div class="secondary-zone">', unsafe_allow_html=True)
            if st.button("Search"):
                st.session_state["city_results"] = search_cities(q or "")
            st.markdown('</div>', unsafe_allow_html=True)
        with colc2:
            results = st.session_state.get("city_results", [])
            choice = None
            if results:
                labels = [
                    f"{r.get('name')}, {r.get('country_code','')} ({r.get('latitude'):.2f},{r.get('longitude'):.2f})"
                    for r in results
                ]
                idx = st.selectbox("Results", list(range(len(labels))), format_func=lambda i: labels[i])
                choice = results[idx]
            if choice:
                st.markdown('<div class="secondary-zone">', unsafe_allow_html=True)
                if st.button("Use current weather"):
                    wx = fetch_current_weather(choice.get("latitude"), choice.get("longitude"))
                    st.session_state["last_wx"] = wx
                    st.session_state["last_city"] = choice
                st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="panel ghost">', unsafe_allow_html=True)
        upA, upB = st.columns(2)
        with upA:
            file_a = st.file_uploader("Card A screenshot", type=["png", "jpg", "jpeg"], key="upload_a")
        with upB:
            file_b = st.file_uploader("Card B screenshot", type=["png", "jpg", "jpeg"], key="upload_b")
        st.markdown('</div>', unsafe_allow_html=True)

        ready = bool(file_a and file_b and st.session_state.get("last_wx") and st.session_state.get("last_city"))
        if st.button("Start experiment", disabled=not ready):
            # Parse and stash
            card_a = extract_from_image(file_a.read()) if file_a else {}
            card_b = extract_from_image(file_b.read()) if file_b else {}
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

    # Page 2: Loading & run
    if step == 2:
        st.subheader("Running experiment")
        prog = st.progress(0, text="Fetching LLM responses… 0%")
        def on_progress(done: int, total: int) -> None:
            pct = int(round(100 * done / max(1, total)))
            prog.progress(min(pct, 100), text=f"Fetching LLM responses… {pct}%")
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
    if step == 3:
        st.subheader("Results")
        dual_results = st.session_state.get("dual_results", [])
        agg = aggregate_results(dual_results)
        a = agg['percent']['A']
        b = agg['percent']['B']
        t = agg['percent']['tie']
        st.markdown('<div class="panel ghost">', unsafe_allow_html=True)
        st.markdown("**Aggregate results**")
        st.write(f"Card A: {a:.1f}%")
        st.markdown(f'<div class="scorebar"><div style="width:{a:.1f}%"></div></div>', unsafe_allow_html=True)
        st.write(f"Card B: {b:.1f}%")
        st.markdown(f'<div class="scorebar"><div style="width:{b:.1f}%"></div></div>', unsafe_allow_html=True)
        st.write(f"Tie: {t:.1f}%")
        st.markdown(f'<div class="scorebar"><div style="width:{t:.1f}%"></div></div>', unsafe_allow_html=True)
        st.markdown("**Top reasons**")
        st.markdown("**For A:** " + (", ".join(agg["top_a"]) or "—"))
        st.markdown("**For B:** " + (", ".join(agg["top_b"]) or "—"))
        with st.expander("More info (per-user)"):
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
