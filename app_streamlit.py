"""
Darpan Twins Lab V3 - Dynamic Persona Discovery Platform
Fixed version with reliable Streamlit components
"""

import os
import json
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional

from twins.dynamic_persona_analyzer import DynamicPersonaAnalyzer
from twins.persona_visualizer import PersonaVisualizer
from twins.prompt_simulator import run_dual_llm_for_users
from twins.card_parser import extract_from_image
from twins.weather import fetch_current_weather

# Default Indian cities
DEFAULT_CITIES = [
    {"name": "Mumbai", "country_code": "IN", "latitude": 19.0760, "longitude": 72.8777},
    {"name": "Delhi", "country_code": "IN", "latitude": 28.7041, "longitude": 77.1025},
    {"name": "Bangalore", "country_code": "IN", "latitude": 12.9716, "longitude": 77.5946},
    {"name": "Chennai", "country_code": "IN", "latitude": 13.0827, "longitude": 80.2707},
    {"name": "Kolkata", "country_code": "IN", "latitude": 22.5726, "longitude": 88.3639},
]

st.set_page_config(
    page_title="🎭 Darpan Twins Lab V3",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Enhanced CSS with compact cards
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* {
    font-family: 'Inter', -apple-system, system-ui, sans-serif !important;
}

/* Force all text to lowercase globally */
* {
    text-transform: lowercase !important;
}

/* Compact persona cards grid */
.persona-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 1rem;
    margin: 1.5rem 0;
}

/* Container for card + checkbox positioning */
.persona-card-container {
    position: relative;
    margin-bottom: 1rem;
}

.persona-card {
    background: #141414;
    border: 2px solid #2a2a2a;
    border-radius: 16px;
    padding: 1.25rem;
    transition: all 0.3s ease;
    cursor: pointer;
    min-height: 180px;
}

.persona-card:hover {
    border-color: #C1E329;
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(193, 227, 41, 0.15);
}

.persona-card.selected {
    background: linear-gradient(135deg, #141414 0%, rgba(193, 227, 41, 0.05) 100%);
    border-color: #C1E329;
}

.persona-name {
    font-size: 1.1rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 0.25rem;
}

.persona-tagline {
    font-size: 0.8rem;
    color: #888888;
    margin-bottom: 0.75rem;
    line-height: 1.3;
    height: 2.6em;
    overflow: hidden;
}

.persona-stats {
    display: flex;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
    font-size: 0.85rem;
}

.persona-traits {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
}

.trait-chip {
    background: rgba(193, 227, 41, 0.1);
    color: #C1E329;
    padding: 0.2rem 0.6rem;
    border-radius: 8px;
    font-size: 0.75rem;
    font-weight: 600;
}

/* Clustering panel */
.clustering-panel {
    background: linear-gradient(135deg, #141414 0%, rgba(63, 177, 240, 0.05) 100%);
    border: 2px solid #2a2a2a;
    border-radius: 20px;
    padding: 2rem;
    margin: 2rem 0;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
}

.stTabs [data-baseweb="tab"] {
    height: 60px;
    padding: 0 2rem;
    background-color: transparent;
    border-radius: 12px;
    font-size: 1rem;
    font-weight: 600;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(193, 227, 41, 0.1) 0%, rgba(63, 177, 240, 0.05) 100%);
    border: 2px solid #C1E329;
}

/* Override Streamlit's red primary button with neon green */
.stButton > button[kind="primary"] {
    background-color: #C1E329 !important;
    border-color: #C1E329 !important;
    color: #000000 !important;
}

/* Force black text on primary buttons - higher specificity */
.stButton > button[kind="primary"] p,
.stButton > button[kind="primary"] span,
.stButton > button[kind="primary"] div {
    color: #000000 !important;
}

.stButton > button[kind="primary"]:hover {
    background-color: #a8c424 !important;
    border-color: #a8c424 !important;
    box-shadow: 0 0 20px rgba(193, 227, 41, 0.4) !important;
    color: #000000 !important;
}

.stButton > button[kind="primary"]:active {
    background-color: #8fa61f !important;
    border-color: #8fa61f !important;
    color: #000000 !important;
}

/* COMPLETE slider override - remove ALL red */
/* Slider background track (unfilled gray/black part AFTER selection) */
.stSlider [data-baseweb="slider"] > div:first-child {
    background: #1a1a1a !important;
}

/* Slider filled track (the green progress bar UP TO selection point) */
.stSlider [data-baseweb="slider"] > div:first-child > div {
    background: linear-gradient(90deg, #C1E329 0%, #C1E329 100%) !important;
}

/* Additional specificity - ensure unfilled portion is dark */
.stSlider [data-baseweb="slider"] [data-baseweb="tick-bar"] {
    background: #1a1a1a !important;
}

/* Slider thumb (the draggable circle) */
.stSlider [data-baseweb="slider"] [role="slider"] {
    background-color: #C1E329 !important;
    border: none !important;
    box-shadow: 0 0 0 0.2rem rgba(193, 227, 41, 0.3) !important;
}

/* Slider thumb on hover */
.stSlider [data-baseweb="slider"] [role="slider"]:hover {
    background-color: #a8c424 !important;
    box-shadow: 0 0 0 0.3rem rgba(193, 227, 41, 0.5) !important;
}

/* Slider thumb on focus/active */
.stSlider [data-baseweb="slider"] [role="slider"]:focus,
.stSlider [data-baseweb="slider"] [role="slider"]:active {
    background-color: #C1E329 !important;
    box-shadow: 0 0 0 0.3rem rgba(193, 227, 41, 0.6) !important;
}

/* Remove any red from slider containers */
.stSlider > div {
    background: transparent !important;
}

.stSlider > div > div {
    background: transparent !important;
}

/* Override any other red accents */
[data-testid="stMarkdownContainer"] a {
    color: #3FB1F0 !important;
}

.stAlert a {
    color: #3FB1F0 !important;
}

/* Override error/warning alert colors */
div[data-testid="stAlert"][data-baseweb="notification"] {
    background-color: rgba(193, 227, 41, 0.1) !important;
    border-left-color: #C1E329 !important;
}

/* Override error messages specifically */
div[data-testid="stException"] {
    background-color: rgba(193, 227, 41, 0.1) !important;
    border-left-color: #C1E329 !important;
    color: #ffffff !important;
}

/* Override st.error color */
.stAlert[data-baseweb="notification"] > div {
    background-color: rgba(193, 227, 41, 0.1) !important;
}

/* Remove red from any notification icons */
.stAlert svg {
    color: #C1E329 !important;
    fill: #C1E329 !important;
}

/* Override ALL Streamlit label colors - remove red text */
label, .stSelectbox label, .stSlider label, .stNumberInput label,
.stTextInput label, .stTextArea label, .stCheckbox label,
.stRadio label, .stMultiSelect label, .stDateInput label,
.stTimeInput label, .stFileUploader label {
    color: #ffffff !important;
}

/* Override widget label text */
[data-testid="stWidgetLabel"] {
    color: #ffffff !important;
}

[data-testid="stWidgetLabel"] p {
    color: #ffffff !important;
}

/* Override form labels */
[data-testid="stFormLabel"] {
    color: #ffffff !important;
}

/* Override selectbox and dropdown text */
.stSelectbox > div > div {
    color: #ffffff !important;
}

/* Override any remaining red text in the app */
.element-container {
    color: #ffffff !important;
}

/* Make sure slider labels are white */
.stSlider label {
    color: #ffffff !important;
}

/* Override the help text color */
[data-testid="stTooltipHoverTarget"] {
    color: #888888 !important;
}

/* === COMPREHENSIVE RED TEXT ELIMINATION === */

/* 1. ALL HEADINGS - Force white text */
h1, h2, h3, h4, h5, h6 {
    color: #ffffff !important;
}

[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] h5,
[data-testid="stMarkdownContainer"] h6 {
    color: #ffffff !important;
}

/* 2. TAB TEXT - Both active and inactive tabs */
.stTabs [data-baseweb="tab"] p,
.stTabs [data-baseweb="tab"] span,
.stTabs [data-baseweb="tab"] div {
    color: #ffffff !important;
}

.stTabs [aria-selected="true"] p,
.stTabs [aria-selected="true"] span {
    color: #ffffff !important;
}

/* 3. METRIC COMPONENTS - Stats numbers and labels */
[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] p,
[data-testid="stMetricLabel"] div,
[data-testid="stMetricLabel"] span {
    color: #ffffff !important;
}

[data-testid="stMetricValue"],
[data-testid="stMetricValue"] div,
[data-testid="stMetricValue"] span {
    color: #ffffff !important;
}

[data-testid="stMetricDelta"] {
    color: #C1E329 !important;
}

/* 4. ALERT/INFO BOX TEXT */
[data-testid="stAlert"] p,
[data-testid="stAlert"] span,
[data-testid="stAlert"] div,
[data-testid="stAlert"] li {
    color: #ffffff !important;
}

/* 5. DATAFRAME TEXT */
[data-testid="stDataFrame"] {
    color: #ffffff !important;
}

[data-testid="stDataFrame"] th {
    color: #ffffff !important;
    background-color: #2a2a2a !important;
}

[data-testid="stDataFrame"] td {
    color: #ffffff !important;
}

/* 6. CHECKBOX - Make prominent and visible */
.stCheckbox label span,
.stCheckbox > label > div,
.stCheckbox label p {
    color: #ffffff !important;
}

/* Style the checkbox itself - larger and neon green when checked */
.stCheckbox input[type="checkbox"] {
    width: 20px !important;
    height: 20px !important;
    cursor: pointer !important;
    accent-color: #C1E329 !important;
}

/* Position checkbox in top-right corner within persona-card-container */
.persona-card-container .stCheckbox[data-testid="stCheckbox"] {
    position: absolute !important;
    top: 1rem !important;
    right: 1rem !important;
    margin: 0 !important;
    z-index: 10 !important;
}

/* Ensure checkbox container within card doesn't take up space */
.persona-card-container .stCheckbox {
    position: absolute !important;
    top: 1rem !important;
    right: 1rem !important;
    margin: 0 !important;
}

/* 7. FILE UPLOADER TEXT */
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploader"] span {
    color: #ffffff !important;
}

/* 8. SPINNER TEXT */
[data-testid="stSpinner"],
[data-testid="stSpinner"] > div,
[data-testid="stSpinner"] p {
    color: #C1E329 !important;
}

/* 9. GENERAL PARAGRAPH TEXT */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] div {
    color: #ffffff !important;
}

/* 10. BODY TEXT FALLBACK */
body {
    color: #ffffff !important;
}

p, span {
    color: #ffffff !important;
}

/* 11. PLOTLY CHART TEXT */
.js-plotly-plot .plotly text {
    fill: #ffffff !important;
}

.js-plotly-plot .plotly .xtick text,
.js-plotly-plot .plotly .ytick text {
    fill: #ffffff !important;
}

/* 12. SELECTBOX DROPDOWN TEXT */
.stSelectbox [data-baseweb="select"] span,
.stSelectbox [data-baseweb="select"] div {
    color: #ffffff !important;
}

/* 13. NUMBER INPUT TEXT */
.stNumberInput input {
    color: #ffffff !important;
}

/* 14. TEXT INPUT TEXT */
.stTextInput input,
.stTextArea textarea {
    color: #ffffff !important;
}

/* 15. CAPTION TEXT */
[data-testid="stCaptionContainer"],
.caption {
    color: #888888 !important;
}
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize session state variables"""
    if "selected_personas" not in st.session_state:
        st.session_state.selected_personas = []
    if "clustering_params" not in st.session_state:
        st.session_state.clustering_params = {
            "algorithm": "gmm",
            "n_clusters": 8,
            "min_cluster_size": 50
        }
    if "current_clustering" not in st.session_state:
        st.session_state.current_clustering = None
    if "analyzer" not in st.session_state:
        st.session_state.analyzer = DynamicPersonaAnalyzer()

def render_compact_persona_card(cluster_id, persona, is_selected):
    """Render a single compact persona card"""
    selected_class = "selected" if is_selected else ""

    # Get top 3 behavioral traits
    behavioral = persona.get('behavioral_traits', {})
    top_traits = []
    if behavioral.get('novelty_seeking', 0) > 0.6:
        top_traits.append("adventurous")
    if behavioral.get('budget_sensitivity', 0) > 0.6:
        top_traits.append("budget-conscious")
    if behavioral.get('rating_focus', 0) > 0.6:
        top_traits.append("quality-focused")
    if behavioral.get('distance_tolerance', 0) > 0.6:
        top_traits.append("distance-flexible")

    if not top_traits:
        top_traits = ["balanced", "contextual", "adaptive"]
    top_traits = top_traits[:3]

    card_html = f"""
    <div class="persona-card {selected_class}">
        <div class="persona-name">{persona.get('name', f'persona {cluster_id}')}</div>
        <div class="persona-tagline">{persona.get('tagline', 'customer segment')}</div>
        <div class="persona-stats">
            <span>👥 {persona.get('size', 0)}</span>
            <span>📊 {persona.get('percentage', 0):.1f}%</span>
        </div>
        <div class="persona-traits">
            {"".join([f'<span class="trait-chip">{trait}</span>' for trait in top_traits])}
        </div>
    </div>
    """
    return card_html

def render_clustering_controls():
    """Render dynamic clustering control panel"""
    st.markdown('<div class="clustering-panel">', unsafe_allow_html=True)
    st.markdown("### 🔬 dynamic persona discovery")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        algorithm = st.selectbox(
            "clustering algorithm",
            options=["gmm", "kmeans", "hierarchical", "dbscan"],
            format_func=lambda x: {
                "gmm": "🔮 gaussian mixture",
                "kmeans": "🎯 k-means",
                "hierarchical": "🌳 hierarchical",
                "dbscan": "💫 dbscan"
            }[x],
            help="choose clustering algorithm"
        )
        st.session_state.clustering_params["algorithm"] = algorithm

    with col2:
        n_clusters = st.slider(
            "number of personas",
            min_value=5,
            max_value=20,
            value=8,
            help="target number of personas"
        )
        st.session_state.clustering_params["n_clusters"] = n_clusters

    with col3:
        min_size = st.slider(
            "min twins per persona",
            min_value=20,
            max_value=100,
            value=50,
            step=10,
            help="minimum cluster size"
        )
        st.session_state.clustering_params["min_cluster_size"] = min_size

    with col4:
        # Add vertical spacing to align with sliders
        st.markdown('<div style="height: 28px;"></div>', unsafe_allow_html=True)
        if st.button("🚀 run clustering", type="primary", use_container_width=True):
            st.markdown('</div>', unsafe_allow_html=True)
            return True

    st.markdown('</div>', unsafe_allow_html=True)
    return False

def perform_clustering():
    """Perform dynamic clustering"""
    with st.spinner("🔍 discovering personas..."):
        analyzer = st.session_state.analyzer

        if analyzer.features_df is None:
            analyzer.extract_features()

        labels, metrics = analyzer.cluster_with_algorithm(
            algorithm=st.session_state.clustering_params["algorithm"],
            n_clusters=st.session_state.clustering_params["n_clusters"],
            min_cluster_size=st.session_state.clustering_params["min_cluster_size"]
        )

        characteristics = analyzer.get_cluster_characteristics(labels)

        if analyzer.umap_embedding is None:
            analyzer.generate_umap_embedding()

        st.session_state.current_clustering = {
            "labels": labels,
            "metrics": metrics,
            "characteristics": characteristics,
            "summary": analyzer.get_cluster_summary()
        }

        return True

def main():
    init_session_state()

    # Header
    st.markdown("# 🎭 darpan twins lab")
    st.markdown("### ai-powered persona discovery & customer simulation platform")
    st.markdown("---")

    # Large, prominent tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎭 personas",
        "🧪 experiment",
        "📊 analytics",
        "⚙️ settings"
    ])

    with tab1:  # Personas Tab
        st.markdown("## discover customer personas")

        # Clustering controls
        should_cluster = render_clustering_controls()

        if should_cluster:
            if perform_clustering():
                st.success("✅ clustering completed successfully!")
                st.balloons()

        # Show placeholder or results
        if not st.session_state.current_clustering:
            st.info("👆 click 'run clustering' above to discover customer personas dynamically")

        # Display results if available
        if st.session_state.current_clustering:
            clustering = st.session_state.current_clustering

            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("personas found", clustering["metrics"]["n_clusters"])
            with col2:
                st.metric("coverage", f"{clustering['metrics']['coverage']:.1f}%")
            with col3:
                st.metric("silhouette score", f"{clustering['metrics']['silhouette']:.3f}")
            with col4:
                st.metric("min size", clustering["metrics"]["min_size"])

            st.markdown("---")
            st.markdown("### 🎯 discovered personas")
            st.info("💡 click on personas to select them for experiments")

            # Render persona cards in grid
            characteristics = clustering["characteristics"]
            sorted_personas = sorted(characteristics.items(),
                                    key=lambda x: x[1]['size'],
                                    reverse=True)

            # Create grid using columns
            cols_per_row = 4
            for i in range(0, len(sorted_personas), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, (cluster_id, char) in enumerate(sorted_personas[i:i+cols_per_row]):
                    with cols[j]:
                        is_selected = str(cluster_id) in [str(x) for x in st.session_state.selected_personas]

                        # Create mock persona dict for card
                        persona_data = {
                            "name": f"persona {cluster_id}",
                            "tagline": f"cluster with {char['size']} twins",
                            "size": char["size"],
                            "percentage": char["percentage"],
                            "behavioral_traits": char["behavioral_means"]
                        }

                        # Wrap card and checkbox in container for positioning
                        st.markdown('<div class="persona-card-container">', unsafe_allow_html=True)

                        st.markdown(render_compact_persona_card(cluster_id, persona_data, is_selected),
                                  unsafe_allow_html=True)

                        # Checkbox positioned in top-right corner
                        if st.checkbox(f"select persona {cluster_id}",
                                     key=f"sel_{cluster_id}",
                                     value=is_selected,
                                     label_visibility="collapsed"):
                            if cluster_id not in st.session_state.selected_personas:
                                st.session_state.selected_personas.append(cluster_id)
                        else:
                            if cluster_id in st.session_state.selected_personas:
                                st.session_state.selected_personas.remove(cluster_id)

                        st.markdown('</div>', unsafe_allow_html=True)

            # Visualizations
            st.markdown("---")
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 🎨 ocean traits comparison")
                if st.session_state.selected_personas:
                    fig = go.Figure()
                    for cluster_id in st.session_state.selected_personas[:5]:
                        if cluster_id in characteristics:
                            ocean = characteristics[cluster_id]["ocean_means"]
                            fig.add_trace(go.Scatterpolar(
                                r=[ocean['openness'], ocean['conscientiousness'],
                                   ocean['extraversion'], ocean['agreeableness'], ocean['neuroticism']],
                                theta=['openness', 'conscientiousness', 'extraversion',
                                      'agreeableness', 'neuroticism'],
                                fill='toself',
                                name=f'persona {cluster_id}'
                            ))

                    fig.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                        showlegend=True,
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("👆 select personas to compare their traits")

            with col2:
                st.markdown("### 📊 cluster summary")
                st.dataframe(clustering["summary"], use_container_width=True, hide_index=True)

        else:
            # Load existing personas if available
            try:
                with open("data/persona_definitions.json", 'r') as f:
                    personas = json.load(f)

                st.markdown("### 📚 pre-computed personas")
                st.info("💡 use the clustering controls above to discover new personas dynamically")

                # Show pre-computed personas in grid
                sorted_personas = sorted(personas.items(), key=lambda x: x[1]['size'], reverse=True)

                cols_per_row = 4
                for i in range(0, len(sorted_personas), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j, (cluster_id, persona) in enumerate(sorted_personas[i:i+cols_per_row]):
                        with cols[j]:
                            is_selected = cluster_id in st.session_state.selected_personas

                            # Wrap card and checkbox in container for positioning
                            st.markdown('<div class="persona-card-container">', unsafe_allow_html=True)

                            st.markdown(render_compact_persona_card(cluster_id, persona, is_selected),
                                      unsafe_allow_html=True)

                            # Checkbox positioned in top-right corner
                            if st.checkbox(f"select {persona['name']}",
                                         key=f"pre_{cluster_id}",
                                         value=is_selected,
                                         label_visibility="collapsed"):
                                if cluster_id not in st.session_state.selected_personas:
                                    st.session_state.selected_personas.append(cluster_id)
                            else:
                                if cluster_id in st.session_state.selected_personas:
                                    st.session_state.selected_personas.remove(cluster_id)

                            st.markdown('</div>', unsafe_allow_html=True)
            except:
                st.info("👆 configure clustering parameters and click 'run clustering' to discover personas")

    with tab2:  # Experiment Tab
        st.markdown("## 🧪 persona-based experiments")

        if not st.session_state.selected_personas:
            st.warning("⚠️ please select personas from the personas tab first")
        else:
            st.success(f"✅ {len(st.session_state.selected_personas)} personas selected for experiment")

            # Experiment setup
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 📍 location & context")
                city_idx = st.selectbox(
                    "select city",
                    range(len(DEFAULT_CITIES)),
                    format_func=lambda i: DEFAULT_CITIES[i]["name"]
                )

                if city_idx is not None:
                    city = DEFAULT_CITIES[city_idx]
                    weather = fetch_current_weather(city["latitude"], city["longitude"])
                    if weather and not weather.get("error"):
                        st.info(f"🌡️ {weather['temperature_c']:.0f}°C | 💧 {weather['precip_mm']:.1f}mm")

                st.markdown("### 🍽️ restaurant card a")
                file_a = st.file_uploader("upload card a", type=["png", "jpg", "jpeg"], key="card_a")
                if file_a:
                    st.image(file_a, width=250)

            with col2:
                st.markdown("### 🍽️ restaurant card b")
                file_b = st.file_uploader("upload card b", type=["png", "jpg", "jpeg"], key="card_b")
                if file_b:
                    st.image(file_b, width=250)

            if file_a and file_b:
                if st.button("🚀 run persona experiment", type="primary", use_container_width=True):
                    with st.spinner("running experiment on selected personas..."):
                        # Get twins from selected personas
                        selected_twins = []
                        for cluster_id in st.session_state.selected_personas:
                            try:
                                cluster_twins = st.session_state.analyzer.get_twins_by_cluster(int(cluster_id))
                                selected_twins.extend(cluster_twins[:10])
                            except:
                                pass

                        if selected_twins:
                            st.success(f"✅ running experiment on {len(selected_twins)} twins from {len(st.session_state.selected_personas)} personas")
                            st.info("💡 experiment functionality ready - integrate with actual llm calls")
                        else:
                            st.warning("no twins found for selected personas")

    with tab3:  # Analytics Tab
        st.markdown("## 📊 persona analytics")

        if st.session_state.current_clustering:
            metrics = st.session_state.current_clustering["metrics"]

            st.markdown("### 🎯 clustering quality metrics")

            # Metrics visualization
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=['silhouette', 'davies-bouldin', 'calinski-harabasz'],
                y=[metrics['silhouette'],
                   1 / (1 + metrics['davies_bouldin']),
                   metrics['calinski_harabasz'] / 100],
                marker_color=['#C1E329', '#3fb1f0', '#fbbf24']
            ))

            fig.update_layout(
                title="clustering quality indicators",
                yaxis_title="score",
                showlegend=False,
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("run clustering from the personas tab to see analytics")

    with tab4:  # Settings Tab
        st.markdown("## ⚙️ configuration")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 💾 export options")
            if st.button("export personas (json)"):
                if st.session_state.current_clustering:
                    st.session_state.analyzer.save_current_clustering()
                    st.success("✅ exported to data/dynamic_persona_assignments.json")
                else:
                    st.warning("no clustering results to export")

        with col2:
            st.markdown("### ℹ️ about")
            st.markdown("""
            **darpan twins lab v3.0**

            dynamic persona discovery platform
            - real-time clustering
            - multiple algorithms
            - minimum cluster size enforcement
            - persona-based experimentation
            """)

if __name__ == "__main__":
    main()
