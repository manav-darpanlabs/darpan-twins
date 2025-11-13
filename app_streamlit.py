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

/* Compact persona cards grid */
.persona-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 1rem;
    margin: 1.5rem 0;
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

.stButton > button[kind="primary"]:hover {
    background-color: #a8c424 !important;
    border-color: #a8c424 !important;
    box-shadow: 0 0 20px rgba(193, 227, 41, 0.4) !important;
}

.stButton > button[kind="primary"]:active {
    background-color: #8fa61f !important;
    border-color: #8fa61f !important;
}

/* Override red sliders with neon green */
.stSlider > div > div > div > div {
    background-color: #C1E329 !important;
}

.stSlider > div > div > div > div > div {
    background-color: #C1E329 !important;
}

.stSlider [role="slider"] {
    background-color: #C1E329 !important;
}

.stSlider [data-baseweb="slider"] > div > div {
    background-color: #C1E329 !important;
}

.stSlider [data-baseweb="slider"] [role="slider"] {
    background-color: #C1E329 !important;
    border: 2px solid #C1E329 !important;
}

/* Slider track (the filled part) */
.stSlider [data-baseweb="slider"] > div:first-child > div:first-child {
    background-color: #C1E329 !important;
}

/* Slider thumb */
.stSlider [data-baseweb="slider"] [role="slider"]:focus {
    box-shadow: 0 0 0 0.2rem rgba(193, 227, 41, 0.5) !important;
}

/* Override any other red accents */
[data-testid="stMarkdownContainer"] a {
    color: #3FB1F0 !important;
}

.stAlert a {
    color: #3FB1F0 !important;
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
        top_traits.append("Adventurous")
    if behavioral.get('budget_sensitivity', 0) > 0.6:
        top_traits.append("Budget-conscious")
    if behavioral.get('rating_focus', 0) > 0.6:
        top_traits.append("Quality-focused")
    if behavioral.get('distance_tolerance', 0) > 0.6:
        top_traits.append("Distance-flexible")

    if not top_traits:
        top_traits = ["Balanced", "Contextual", "Adaptive"]
    top_traits = top_traits[:3]

    card_html = f"""
    <div class="persona-card {selected_class}">
        <div class="persona-name">{persona.get('name', f'Persona {cluster_id}')}</div>
        <div class="persona-tagline">{persona.get('tagline', 'Customer segment')}</div>
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
    st.markdown("### 🔬 Dynamic Persona Discovery")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        algorithm = st.selectbox(
            "Clustering Algorithm",
            options=["gmm", "kmeans", "hierarchical", "dbscan"],
            format_func=lambda x: {
                "gmm": "🔮 Gaussian Mixture",
                "kmeans": "🎯 K-Means",
                "hierarchical": "🌳 Hierarchical",
                "dbscan": "💫 DBSCAN"
            }[x],
            help="Choose clustering algorithm"
        )
        st.session_state.clustering_params["algorithm"] = algorithm

    with col2:
        n_clusters = st.slider(
            "Number of Personas",
            min_value=5,
            max_value=20,
            value=8,
            help="Target number of personas"
        )
        st.session_state.clustering_params["n_clusters"] = n_clusters

    with col3:
        min_size = st.slider(
            "Min Twins per Persona",
            min_value=20,
            max_value=100,
            value=50,
            step=10,
            help="Minimum cluster size"
        )
        st.session_state.clustering_params["min_cluster_size"] = min_size

    with col4:
        st.markdown("###")
        if st.button("🚀 Run Clustering", type="primary", use_container_width=True):
            st.markdown('</div>', unsafe_allow_html=True)
            return True

    st.markdown('</div>', unsafe_allow_html=True)
    return False

def perform_clustering():
    """Perform dynamic clustering"""
    with st.spinner("🔍 Discovering personas..."):
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
    st.markdown("# 🎭 Darpan Twins Lab")
    st.markdown("### AI-Powered Persona Discovery & Customer Simulation Platform")
    st.markdown("---")

    # Large, prominent tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎭 PERSONAS",
        "🧪 EXPERIMENT",
        "📊 ANALYTICS",
        "⚙️ SETTINGS"
    ])

    with tab1:  # Personas Tab
        st.markdown("## Discover Customer Personas")

        # Clustering controls
        should_cluster = render_clustering_controls()

        if should_cluster:
            if perform_clustering():
                st.success("✅ Clustering completed successfully!")
                st.balloons()

        # Display results if available
        if st.session_state.current_clustering:
            clustering = st.session_state.current_clustering

            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Personas Found", clustering["metrics"]["n_clusters"])
            with col2:
                st.metric("Coverage", f"{clustering['metrics']['coverage']:.1f}%")
            with col3:
                st.metric("Silhouette Score", f"{clustering['metrics']['silhouette']:.3f}")
            with col4:
                st.metric("Min Size", clustering["metrics"]["min_size"])

            st.markdown("---")
            st.markdown("### 🎯 Discovered Personas")
            st.info("💡 Click on personas to select them for experiments")

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
                            "name": f"Persona {cluster_id}",
                            "tagline": f"Cluster with {char['size']} twins",
                            "size": char["size"],
                            "percentage": char["percentage"],
                            "behavioral_traits": char["behavioral_means"]
                        }

                        st.markdown(render_compact_persona_card(cluster_id, persona_data, is_selected),
                                  unsafe_allow_html=True)

                        # Hidden checkbox for selection
                        if st.checkbox(f"Select Persona {cluster_id}",
                                     key=f"sel_{cluster_id}",
                                     value=is_selected,
                                     label_visibility="collapsed"):
                            if cluster_id not in st.session_state.selected_personas:
                                st.session_state.selected_personas.append(cluster_id)
                        else:
                            if cluster_id in st.session_state.selected_personas:
                                st.session_state.selected_personas.remove(cluster_id)

            # Visualizations
            st.markdown("---")
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 🎨 OCEAN Traits Comparison")
                if st.session_state.selected_personas:
                    fig = go.Figure()
                    for cluster_id in st.session_state.selected_personas[:5]:
                        if cluster_id in characteristics:
                            ocean = characteristics[cluster_id]["ocean_means"]
                            fig.add_trace(go.Scatterpolar(
                                r=[ocean['openness'], ocean['conscientiousness'],
                                   ocean['extraversion'], ocean['agreeableness'], ocean['neuroticism']],
                                theta=['Openness', 'Conscientiousness', 'Extraversion',
                                      'Agreeableness', 'Neuroticism'],
                                fill='toself',
                                name=f'Persona {cluster_id}'
                            ))

                    fig.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                        showlegend=True,
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("👆 Select personas to compare their traits")

            with col2:
                st.markdown("### 📊 Cluster Summary")
                st.dataframe(clustering["summary"], use_container_width=True, hide_index=True)

        else:
            # Load existing personas if available
            try:
                with open("data/persona_definitions.json", 'r') as f:
                    personas = json.load(f)

                st.markdown("### 📚 Pre-computed Personas")
                st.info("💡 Use the clustering controls above to discover new personas dynamically")

                # Show pre-computed personas in grid
                sorted_personas = sorted(personas.items(), key=lambda x: x[1]['size'], reverse=True)

                cols_per_row = 4
                for i in range(0, len(sorted_personas), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j, (cluster_id, persona) in enumerate(sorted_personas[i:i+cols_per_row]):
                        with cols[j]:
                            is_selected = cluster_id in st.session_state.selected_personas
                            st.markdown(render_compact_persona_card(cluster_id, persona, is_selected),
                                      unsafe_allow_html=True)

                            if st.checkbox(f"Select {persona['name']}",
                                         key=f"pre_{cluster_id}",
                                         value=is_selected,
                                         label_visibility="collapsed"):
                                if cluster_id not in st.session_state.selected_personas:
                                    st.session_state.selected_personas.append(cluster_id)
                            else:
                                if cluster_id in st.session_state.selected_personas:
                                    st.session_state.selected_personas.remove(cluster_id)
            except:
                st.info("👆 Configure clustering parameters and click 'Run Clustering' to discover personas")

    with tab2:  # Experiment Tab
        st.markdown("## 🧪 Persona-Based Experiments")

        if not st.session_state.selected_personas:
            st.warning("⚠️ Please select personas from the Personas tab first")
        else:
            st.success(f"✅ {len(st.session_state.selected_personas)} personas selected for experiment")

            # Experiment setup
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 📍 Location & Context")
                city_idx = st.selectbox(
                    "Select City",
                    range(len(DEFAULT_CITIES)),
                    format_func=lambda i: DEFAULT_CITIES[i]["name"]
                )

                if city_idx is not None:
                    city = DEFAULT_CITIES[city_idx]
                    weather = fetch_current_weather(city["latitude"], city["longitude"])
                    if weather and not weather.get("error"):
                        st.info(f"🌡️ {weather['temperature_c']:.0f}°C | 💧 {weather['precip_mm']:.1f}mm")

                st.markdown("### 🍽️ Restaurant Card A")
                file_a = st.file_uploader("Upload Card A", type=["png", "jpg", "jpeg"], key="card_a")
                if file_a:
                    st.image(file_a, width=250)

            with col2:
                st.markdown("### 🍽️ Restaurant Card B")
                file_b = st.file_uploader("Upload Card B", type=["png", "jpg", "jpeg"], key="card_b")
                if file_b:
                    st.image(file_b, width=250)

            if file_a and file_b:
                if st.button("🚀 Run Persona Experiment", type="primary", use_container_width=True):
                    with st.spinner("Running experiment on selected personas..."):
                        # Get twins from selected personas
                        selected_twins = []
                        for cluster_id in st.session_state.selected_personas:
                            try:
                                cluster_twins = st.session_state.analyzer.get_twins_by_cluster(int(cluster_id))
                                selected_twins.extend(cluster_twins[:10])
                            except:
                                pass

                        if selected_twins:
                            st.success(f"✅ Running experiment on {len(selected_twins)} twins from {len(st.session_state.selected_personas)} personas")
                            st.info("💡 Experiment functionality ready - integrate with actual LLM calls")
                        else:
                            st.warning("No twins found for selected personas")

    with tab3:  # Analytics Tab
        st.markdown("## 📊 Persona Analytics")

        if st.session_state.current_clustering:
            metrics = st.session_state.current_clustering["metrics"]

            st.markdown("### 🎯 Clustering Quality Metrics")

            # Metrics visualization
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=['Silhouette', 'Davies-Bouldin', 'Calinski-Harabasz'],
                y=[metrics['silhouette'],
                   1 / (1 + metrics['davies_bouldin']),
                   metrics['calinski_harabasz'] / 100],
                marker_color=['#C1E329', '#3fb1f0', '#fbbf24']
            ))

            fig.update_layout(
                title="Clustering Quality Indicators",
                yaxis_title="Score",
                showlegend=False,
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Run clustering from the Personas tab to see analytics")

    with tab4:  # Settings Tab
        st.markdown("## ⚙️ Configuration")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 💾 Export Options")
            if st.button("Export Personas (JSON)"):
                if st.session_state.current_clustering:
                    st.session_state.analyzer.save_current_clustering()
                    st.success("✅ Exported to data/dynamic_persona_assignments.json")
                else:
                    st.warning("No clustering results to export")

        with col2:
            st.markdown("### ℹ️ About")
            st.markdown("""
            **Darpan Twins Lab v3.0**

            Dynamic Persona Discovery Platform
            - Real-time clustering
            - Multiple algorithms
            - Minimum cluster size enforcement
            - Persona-based experimentation
            """)

if __name__ == "__main__":
    main()
