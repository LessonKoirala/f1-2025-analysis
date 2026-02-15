import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
from plotly.subplots import make_subplots

def show_comparison_analysis(driver1_name, driver2_name):
    # === 1. Configuration & Styling === #
    def apply_custom_styles():
        st.markdown("""
            <style>
            .stApp { background-color: #0e1117; }
            h1, h2, h3 { font-family: 'Helvetica Neue', sans-serif; font-weight: 700; color: #FFF200 !important; }
            [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.8rem !important; }
            hr { border: 0; height: 1px; background: linear-gradient(to right, #FFF200, transparent); margin: 2rem 0; }
            </style>
        """, unsafe_allow_html=True)

    apply_custom_styles()

    # === 2. Dynamic Data Loading === #
    def load_driver_data(name):
        file_name = f"Australia2025_{name}_cleaned_sorted.csv"
        current_dir = os.path.dirname(os.path.abspath(__file__))
        target_path = os.path.join(current_dir, "cleaned_Csv", file_name)
        return pd.read_csv(target_path) if os.path.exists(target_path) else pd.DataFrame()

    df1, df2 = load_driver_data(driver1_name), load_driver_data(driver2_name)
    if df1.empty or df2.empty:
        st.error(f"Missing data for {driver1_name} or {driver2_name}.")
        return

    # === 3. Lap Selection === #
    st.title(f"⚔️ {driver1_name} vs {driver2_name}")
    st.markdown(f"### Head-to-Head Telemetry | Australia 2025")

    col_sel1, col_sel2 = st.columns(2)
    lap1 = col_sel1.selectbox(f"{driver1_name} Lap", sorted(df1['LapNumber'].unique()), index=0)
    lap2 = col_sel2.selectbox(f"{driver2_name} Lap", sorted(df2['LapNumber'].unique()), index=0)

    d1 = df1[df1['LapNumber'] == lap1].sort_values("Distance")
    d2 = df2[df2['LapNumber'] == lap2].sort_values("Distance")

    # === 4. Distance Alignment & Delta Calculation === #
    max_dist = min(d1['Distance'].max(), d2['Distance'].max())
    dist_common = np.linspace(0, max_dist, 2000)
    
    # Interpolating channels for 1:1 comparison
    v1_interp = np.interp(dist_common, d1['Distance'], d1['Speed'])
    v2_interp = np.interp(dist_common, d2['Distance'], d2['Speed'])
    thr1_interp = np.interp(dist_common, d1['Distance'], d1['Throttle'])
    thr2_interp = np.interp(dist_common, d2['Distance'], d2['Throttle'])
    
    # Delta Time: Cumulative difference in time taken to cover each meter
    delta_time = np.cumsum((1/(np.clip(v1_interp/3.6, 1, 100)) - 1/(np.clip(v2_interp/3.6, 1, 100))) * np.diff(dist_common, prepend=0))

    # === 5. Multi-Plot Telemetry === #
    st.markdown("---")
    fig_comp = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                              row_heights=[0.25, 0.5, 0.25], vertical_spacing=0.05,
                              subplot_titles=("Time Delta (Negative = Driver 1 Leads)", "Speed Trace Overlay", "Throttle Application"))

    # Delta Plot
    fig_comp.add_trace(go.Scatter(x=dist_common, y=delta_time, name="Delta", fill='tozeroy', line=dict(color='gold')), row=1, col=1)
    
    # Speed Trace
    fig_comp.add_trace(go.Scatter(x=dist_common, y=v1_interp, name=f"{driver1_name}", line=dict(color='#00A19B')), row=2, col=1)
    fig_comp.add_trace(go.Scatter(x=dist_common, y=v2_interp, name=f"{driver2_name}", line=dict(color='#DC0000', dash='dot')), row=2, col=1)
    
    # Throttle Trace
    fig_comp.add_trace(go.Scatter(x=dist_common, y=thr1_interp, name=f"{driver1_name} Throttle", line=dict(color='#00A19B', width=1)), row=3, col=1)
    fig_comp.add_trace(go.Scatter(x=dist_common, y=thr2_interp, name=f"{driver2_name} Throttle", line=dict(color='#DC0000', width=1, dash='dot')), row=3, col=1)

    fig_comp.update_layout(height=800, template="plotly_dark", hovermode="x unified")
    st.plotly_chart(fig_comp, use_container_width=True)

    # === 6. Track Comparison Heatmaps === #
    st.markdown("<hr>", unsafe_allow_html=True)
    c_map1, c_map2 = st.columns(2)
    with c_map1:
        st.write(f"#### {driver1_name} Speed Map")
        fig_m1 = px.scatter(d1, x="X", y="Y", color="Speed", color_continuous_scale="Viridis", template="plotly_dark")
        st.plotly_chart(fig_m1, use_container_width=True)
    with c_map2:
        st.write(f"#### {driver2_name} Speed Map")
        fig_m2 = px.scatter(d2, x="X", y="Y", color="Speed", color_continuous_scale="Viridis", template="plotly_dark")
        st.plotly_chart(fig_m2, use_container_width=True)

    # === 7. 3D Engine Load Comparison === #
    st.header("🧊 3D Performance Comparison")
    c_3d1, c_3d2 = st.columns(2)
    with c_3d1:
        st.write(f"**{driver1_name} RPM Profile**")
        fig_3d1 = go.Figure(data=[go.Scatter3d(x=d1['X'], y=d1['Y'], z=d1['RPM'], mode='lines', line=dict(color=d1['RPM'], colorscale='Plasma'))])
        fig_3d1.update_layout(template="plotly_dark", height=450)
        st.plotly_chart(fig_3d1, use_container_width=True)
    with c_3d2:
        st.write(f"**{driver2_name} RPM Profile**")
        fig_3d2 = go.Figure(data=[go.Scatter3d(x=d2['X'], y=d2['Y'], z=d2['RPM'], mode='lines', line=dict(color=d2['RPM'], colorscale='Plasma'))])
        fig_3d2.update_layout(template="plotly_dark", height=450)
        st.plotly_chart(fig_3d2, use_container_width=True)