import plotly.graph_objects as go
from typing import List, Dict, Any
from core.models import QuestionEvaluation

def create_radar_chart(evaluations: List[QuestionEvaluation]) -> go.Figure:
    """Generates a radar chart displaying scores across the 4 key competencies."""
    if not evaluations:
        categories = ["Technical", "Structure", "Communication", "Confidence"]
        values = [0, 0, 0, 0]
    else:
        avg_tech = sum(e.technical_score for e in evaluations) / len(evaluations)
        avg_struct = sum(e.structure_score for e in evaluations) / len(evaluations)
        avg_comm = sum(e.communication_score for e in evaluations) / len(evaluations)
        avg_conf = sum(e.confidence_score for e in evaluations) / len(evaluations)

        categories = ["Technical Depth", "Structure & STAR", "Communication & Fluency", "Confidence"]
        values = [avg_tech, avg_struct, avg_comm, avg_conf]

    # Close radar loop
    radar_categories = categories + [categories[0]]
    radar_values = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=radar_values,
        theta=radar_categories,
        fill="toself",
        fillcolor="rgba(59, 130, 246, 0.25)",
        line=dict(color="#2563EB", width=2),
        name="Candidate Competency"
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10, color="#64748B"),
                gridcolor="#E2E8F0"
            )
        ),
        showlegend=False,
        margin=dict(l=40, r=40, t=30, b=30),
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig

def create_progression_bar_chart(evaluations: List[QuestionEvaluation]) -> go.Figure:
    """Displays question-by-question performance progression."""
    labels = [f"Q{i+1}" for i in range(len(evaluations))]
    scores = [e.overall_score for e in evaluations]

    colors = []
    for s in scores:
        if s >= 75:
            colors.append("#10B981") # Green
        elif s >= 50:
            colors.append("#F59E0B") # Amber
        else:
            colors.append("#EF4444") # Red

    fig = go.Figure(data=[
        go.Bar(
            x=labels, 
            y=scores, 
            marker_color=colors,
            text=[f"{s:.0f}%" for s in scores],
            textposition="auto"
        )
    ])

    fig.update_layout(
        title="Question-by-Question Score Progression",
        yaxis=dict(range=[0, 100], title="Score (%)"),
        xaxis=dict(title="Question"),
        margin=dict(l=30, r=30, t=40, b=30),
        height=280,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig
