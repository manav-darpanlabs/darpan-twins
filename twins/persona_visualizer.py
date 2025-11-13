"""
Persona Visualization Module

Creates interactive visualizations for persona clusters using Plotly.
"""

import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class PersonaVisualizer:
    """
    Creates interactive visualizations for persona analysis.
    """

    def __init__(self,
                 personas_file: str = "data/persona_definitions.json",
                 assignments_file: str = "data/persona_assignments.json",
                 umap_file: str = "data/umap_embeddings.npy"):
        """Initialize the visualizer with data files."""
        self.personas = self._load_personas(personas_file)
        self.assignments = self._load_assignments(assignments_file)
        self.umap_embeddings = self._load_umap(umap_file)

        # Create color palette for clusters
        self.colors = px.colors.qualitative.Plotly + px.colors.qualitative.Bold

    def _load_personas(self, file_path: str) -> Dict:
        """Load persona definitions."""
        with open(file_path, 'r') as f:
            return json.load(f)

    def _load_assignments(self, file_path: str) -> Dict:
        """Load persona assignments."""
        with open(file_path, 'r') as f:
            return json.load(f)

    def _load_umap(self, file_path: str) -> Optional[np.ndarray]:
        """Load UMAP embeddings if available."""
        path = Path(file_path)
        if path.exists():
            return np.load(file_path)
        return None

    def create_persona_distribution_chart(self, selected_twins: Optional[List[str]] = None) -> go.Figure:
        """
        Create a pie/sunburst chart showing persona distribution.

        Args:
            selected_twins: List of twin IDs to include (None = all)

        Returns:
            Plotly figure object
        """
        # Count twins per persona
        if selected_twins:
            assignments = {k: v for k, v in self.assignments.items() if k in selected_twins}
        else:
            assignments = self.assignments

        cluster_counts = {}
        for user_id, assignment in assignments.items():
            cluster_id = str(assignment['cluster_id'])
            if cluster_id not in cluster_counts:
                cluster_counts[cluster_id] = 0
            cluster_counts[cluster_id] += 1

        # Prepare data for sunburst
        labels = []
        parents = []
        values = []
        colors_list = []

        # Add root
        labels.append("All Personas")
        parents.append("")
        values.append(len(assignments))
        colors_list.append("#636EFA")

        # Add each persona
        for cluster_id, count in cluster_counts.items():
            persona = self.personas.get(cluster_id, {})
            labels.append(persona.get('name', f'Cluster {cluster_id}'))
            parents.append("All Personas")
            values.append(count)
            colors_list.append(self.colors[int(cluster_id) % len(self.colors)])

        fig = go.Figure(go.Sunburst(
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total",
            marker=dict(colors=colors_list),
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>%{percentParent}<extra></extra>',
            textinfo="label+percent parent"
        ))

        fig.update_layout(
            title="Persona Distribution",
            height=500,
            margin=dict(t=50, l=0, r=0, b=0)
        )

        return fig

    def create_ocean_radar_chart(self, cluster_ids: Optional[List[int]] = None) -> go.Figure:
        """
        Create radar charts comparing OCEAN traits across personas.

        Args:
            cluster_ids: List of cluster IDs to include (None = all)

        Returns:
            Plotly figure object
        """
        fig = go.Figure()

        if cluster_ids is None:
            cluster_ids = [int(k) for k in self.personas.keys()]

        categories = ['Openness', 'Conscientiousness', 'Extraversion',
                      'Agreeableness', 'Neuroticism']

        for cluster_id in cluster_ids[:5]:  # Limit to 5 for clarity
            persona = self.personas.get(str(cluster_id), {})
            ocean = persona.get('ocean_traits', {})

            values = [
                ocean.get('openness', 0),
                ocean.get('conscientiousness', 0),
                ocean.get('extraversion', 0),
                ocean.get('agreeableness', 0),
                ocean.get('neuroticism', 0)
            ]

            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name=persona.get('name', f'Cluster {cluster_id}'),
                line=dict(color=self.colors[cluster_id % len(self.colors)])
            ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title="OCEAN Personality Traits by Persona",
            height=500
        )

        return fig

    def create_umap_scatter(self, highlight_twins: Optional[List[str]] = None) -> go.Figure:
        """
        Create 2D UMAP projection scatter plot of all twins.

        Args:
            highlight_twins: List of twin IDs to highlight

        Returns:
            Plotly figure object
        """
        if self.umap_embeddings is None:
            return go.Figure().add_annotation(
                text="UMAP embeddings not available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )

        # Prepare data
        df_data = []
        for idx, (user_id, assignment) in enumerate(self.assignments.items()):
            cluster_id = str(assignment['cluster_id'])
            persona = self.personas.get(cluster_id, {})

            df_data.append({
                'user_id': user_id,
                'x': self.umap_embeddings[idx, 0],
                'y': self.umap_embeddings[idx, 1],
                'cluster_id': cluster_id,
                'persona_name': persona.get('name', f'Cluster {cluster_id}'),
                'confidence': assignment['confidence'],
                'highlighted': user_id in highlight_twins if highlight_twins else False
            })

        df = pd.DataFrame(df_data)

        # Create scatter plot
        fig = px.scatter(
            df,
            x='x',
            y='y',
            color='persona_name',
            hover_data=['user_id', 'confidence'],
            title="Twin Personas - UMAP Visualization",
            labels={'x': 'UMAP 1', 'y': 'UMAP 2'},
            color_discrete_sequence=self.colors
        )

        # Highlight selected twins
        if highlight_twins:
            highlighted = df[df['highlighted']]
            fig.add_trace(go.Scatter(
                x=highlighted['x'],
                y=highlighted['y'],
                mode='markers',
                marker=dict(size=15, color='red', symbol='star'),
                name='Selected Twins',
                hovertext=highlighted['user_id']
            ))

        fig.update_layout(height=600)
        return fig

    def create_demographic_heatmap(self) -> go.Figure:
        """
        Create heatmap showing age/income distribution by persona.

        Returns:
            Plotly figure object
        """
        # Prepare data matrix
        age_bins = ['18-25', '26-30', '31-35', '36-40', '41-45', '46+']
        income_bins = ['<300K', '300-500K', '500-700K', '700K-1M', '>1M']

        heatmap_data = []
        persona_names = []

        for cluster_id, persona in self.personas.items():
            persona_names.append(persona.get('name', f'Cluster {cluster_id}'))
            demographics = persona.get('demographics', {})

            # Simple representation based on averages
            avg_age = demographics.get('age', 30)
            avg_income = demographics.get('income', 500000)

            # Create simplified distribution
            row = []
            for income_bin in income_bins:
                # Simulate distribution around average
                if avg_income < 300000:
                    weights = [0.5, 0.3, 0.1, 0.05, 0.05]
                elif avg_income < 500000:
                    weights = [0.2, 0.4, 0.2, 0.1, 0.1]
                elif avg_income < 700000:
                    weights = [0.1, 0.2, 0.4, 0.2, 0.1]
                elif avg_income < 1000000:
                    weights = [0.05, 0.1, 0.2, 0.4, 0.25]
                else:
                    weights = [0.05, 0.05, 0.1, 0.3, 0.5]

                row.append(weights[income_bins.index(income_bin)] * persona['size'])

            heatmap_data.append(row)

        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=income_bins,
            y=persona_names,
            colorscale='Viridis',
            text=[[f'{val:.0f}' for val in row] for row in heatmap_data],
            texttemplate="%{text}",
            textfont={"size": 10},
            hovertemplate="Persona: %{y}<br>Income: %{x}<br>Count: %{z}<extra></extra>"
        ))

        fig.update_layout(
            title="Demographics: Income Distribution by Persona",
            xaxis_title="Income Range (₹)",
            yaxis_title="Persona",
            height=400
        )

        return fig

    def create_behavioral_comparison(self) -> go.Figure:
        """
        Create bar chart comparing behavioral traits across personas.

        Returns:
            Plotly figure object
        """
        traits = ['novelty_seeking', 'budget_sensitivity', 'distance_tolerance', 'rating_focus']
        trait_labels = ['Novelty Seeking', 'Budget Sensitivity', 'Distance Tolerance', 'Rating Focus']

        fig = go.Figure()

        for cluster_id, persona in self.personas.items():
            behavioral = persona.get('behavioral_traits', {})
            values = [behavioral.get(trait, 0) for trait in traits]

            fig.add_trace(go.Bar(
                name=persona.get('name', f'Cluster {cluster_id}'),
                x=trait_labels,
                y=values,
                marker_color=self.colors[int(cluster_id) % len(self.colors)]
            ))

        fig.update_layout(
            title="Behavioral Traits Comparison",
            xaxis_title="Behavioral Trait",
            yaxis_title="Score (0-1)",
            barmode='group',
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5
            )
        )

        return fig

    def create_decision_pattern_analysis(self, decisions_file: Optional[str] = None) -> go.Figure:
        """
        Analyze decision patterns by persona if decision data is available.

        Args:
            decisions_file: Path to decisions CSV file

        Returns:
            Plotly figure object
        """
        # For now, create a placeholder visualization
        # In production, this would analyze actual decision data

        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Choice Preference (A vs B)', 'Decision Confidence'),
            specs=[[{'type': 'bar'}, {'type': 'box'}]]
        )

        # Simulated data for demonstration
        for cluster_id, persona in self.personas.items():
            # Simulated choice preference
            a_preference = 0.5 + np.random.normal(0, 0.1)
            a_preference = max(0, min(1, a_preference))

            fig.add_trace(
                go.Bar(
                    name=persona.get('name', f'Cluster {cluster_id}'),
                    x=['Choice A', 'Choice B'],
                    y=[a_preference, 1 - a_preference],
                    marker_color=self.colors[int(cluster_id) % len(self.colors)],
                    showlegend=False
                ),
                row=1, col=1
            )

            # Simulated confidence distribution
            confidence_values = np.random.beta(5, 2, size=50)
            fig.add_trace(
                go.Box(
                    y=confidence_values,
                    name=persona.get('name', f'Cluster {cluster_id}'),
                    marker_color=self.colors[int(cluster_id) % len(self.colors)]
                ),
                row=1, col=2
            )

        fig.update_layout(
            title="Decision Pattern Analysis by Persona",
            height=400,
            showlegend=True
        )

        return fig

    def create_persona_summary_card(self, cluster_id: int) -> Dict:
        """
        Create a summary card for a specific persona.

        Args:
            cluster_id: Cluster ID

        Returns:
            Dictionary with persona summary information
        """
        persona = self.personas.get(str(cluster_id), {})

        return {
            'name': persona.get('name', f'Cluster {cluster_id}'),
            'tagline': persona.get('tagline', ''),
            'size': persona.get('size', 0),
            'percentage': persona.get('percentage', 0),
            'key_traits': persona.get('key_traits', []),
            'food_preferences': persona.get('food_preferences', ''),
            'decision_pattern': persona.get('decision_pattern', ''),
            'quote': persona.get('representative_quote', ''),
            'ocean_traits': persona.get('ocean_traits', {}),
            'demographics': persona.get('demographics', {}),
            'behavioral_traits': persona.get('behavioral_traits', {})
        }

    def get_cluster_statistics(self) -> pd.DataFrame:
        """
        Get statistical summary of all clusters.

        Returns:
            DataFrame with cluster statistics
        """
        stats = []

        for cluster_id, persona in self.personas.items():
            stats.append({
                'Persona': persona.get('name', f'Cluster {cluster_id}'),
                'Size': persona.get('size', 0),
                'Percentage': f"{persona.get('percentage', 0):.1f}%",
                'Avg Age': f"{persona.get('demographics', {}).get('age', 0):.1f}",
                'Avg Income': f"₹{persona.get('demographics', {}).get('income', 0):,.0f}",
                'Novelty': f"{persona.get('behavioral_traits', {}).get('novelty_seeking', 0):.2f}",
                'Budget': f"{persona.get('behavioral_traits', {}).get('budget_sensitivity', 0):.2f}",
                'Quality': f"{persona.get('behavioral_traits', {}).get('rating_focus', 0):.2f}"
            })

        return pd.DataFrame(stats)


if __name__ == "__main__":
    # Test the visualizer
    visualizer = PersonaVisualizer()

    # Create sample visualizations
    fig1 = visualizer.create_persona_distribution_chart()
    fig2 = visualizer.create_ocean_radar_chart()
    fig3 = visualizer.create_behavioral_comparison()

    # Display statistics
    stats_df = visualizer.get_cluster_statistics()
    print("\nCluster Statistics:")
    print(stats_df.to_string())

    print("\nVisualizations created successfully!")