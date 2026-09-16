import numpy as np
import pandas as pd
import plotly.graph_objects as go


def generate_timeline_data(incident_active: bool) -> pd.DataFrame:
    """Generates time-series data for Cluster A and Cluster B."""
    timestamps = pd.date_range(end=pd.Timestamp.now(), periods=20, freq="1min")

    if not incident_active:
        # Healthy baseline for both clusters
        data = {
            "Timestamp": timestamps,
            "Cluster A Latency": np.random.normal(200, 10, 20),
            "Cluster B Latency": np.random.normal(190, 8, 20),
            "Cluster A Error Rate": np.random.normal(1.0, 0.1, 20),
            "Cluster B Error Rate": np.random.normal(0.5, 0.05, 20),
            "Cluster A GPU Util": np.random.normal(60, 2, 20),
            "Cluster B GPU Util": np.random.normal(58, 2, 20),
            "Cluster A Queue Depth": np.random.normal(20, 2, 20),
            "Cluster B Queue Depth": np.random.normal(25, 2, 20),
        }
    else:
        # Cluster A degrades over time while Cluster B remains healthy
        ramp_a_gpu = np.linspace(60, 96, 20) + np.random.normal(0, 1, 20)
        ramp_a_queue = np.linspace(20, 180, 20) + np.random.normal(0, 5, 20)
        ramp_a_latency = np.linspace(200, 500, 20) + np.random.normal(0, 15, 20)
        ramp_a_error = np.linspace(1.0, 15.0, 20) + np.random.normal(0, 0.5, 20)

        data = {
            "Timestamp": timestamps,
            "Cluster A Latency": ramp_a_latency,
            "Cluster B Latency": np.random.normal(190, 8, 20),
            "Cluster A Error Rate": ramp_a_error,
            "Cluster B Error Rate": np.random.normal(0.5, 0.05, 20),
            "Cluster A GPU Util": ramp_a_gpu,
            "Cluster B GPU Util": np.random.normal(58, 2, 20),
            "Cluster A Queue Depth": ramp_a_queue,
            "Cluster B Queue Depth": np.random.normal(25, 2, 20),
        }

    return pd.DataFrame(data)


def create_timeline_chart(
    df: pd.DataFrame,
    col_a: str,
    col_b: str,
    title: str,
    unit: str,
    color_a: str = "#EF553B",
    color_b: str = "#636EFA",
) -> go.Figure:
    """Helper to create a dual-cluster Plotly line chart."""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["Timestamp"],
            y=df[col_a],
            mode="lines+markers",
            name="Cluster A",
            line=dict(color=color_a, width=2.5),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["Timestamp"],
            y=df[col_b],
            mode="lines+markers",
            name="Cluster B",
            line=dict(color=color_b, width=2.5, dash="dash"),
        )
    )

    fig.update_layout(
        title=dict(text=title, font=dict(size=14)),
        margin=dict(l=20, r=20, t=40, b=20),
        height=260,
        yaxis=dict(title=unit),
        xaxis=dict(title="Time"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_white",
    )

    return fig