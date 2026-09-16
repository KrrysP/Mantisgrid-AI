import streamlit as st


def render_header(status: str):
    """Renders the dashboard top header with status badge."""
    col1, col2 = st.columns([3, 1])

    with col1:
        st.title("MantisGuard")
        st.caption("AI Infrastructure Reliability Investigator")

    with col2:
        st.write("##")
        if status == "Healthy":
            st.success("System Status: HEALTHY")
        else:
            st.error("System Status: CRITICAL")


def render_metric_card(
    label: str,
    val_a: str,
    val_b: str,
    status_a: str = "green",
    status_b: str = "green",
):
    """Renders a custom dual-cluster comparative metric card."""
    color_map = {"green": "#28a745", "orange": "#fd7e14", "red": "#dc3545"}

    st.markdown(
        f"""
        <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 12px; margin-bottom: 12px; background-color: #f8f9fa;">
            <div style="font-weight: 600; font-size: 14px; color: #555; margin-bottom: 8px;">{label}</div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 12px; color: #777;">Cluster A:</span>
                    <span style="font-weight: bold; font-size: 16px; color: {color_map.get(status_a, '#000')}; margin-left: 4px;">{val_a}</span>
                </div>
                <div>
                    <span style="font-size: 12px; color: #777;">Cluster B:</span>
                    <span style="font-weight: bold; font-size: 16px; color: {color_map.get(status_b, '#000')}; margin-left: 4px;">{val_b}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )