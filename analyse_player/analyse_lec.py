import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os  # Added for path resolution
from plotly.subplots import make_subplots
from pathlib import Path

# === Function Wrapper for Global Dashboard === #
def show_leclerc_analysis():
    # === 1. Configuration & Professional Styling === #
    # st.set_page_config(
    #     page_title="F1 Insight - Charles Leclerc", 
    #     layout="wide", 
    #     initial_sidebar_state="expanded"
    # )

    def apply_custom_styles():
        st.markdown("""
            <style>
            .stApp { background-color: #0e1117; }
            h1, h2, h3 { font-family: 'Helvetica Neue', sans-serif; font-weight: 700 !important; color: #DC0000 !important; }
            [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 2rem !important; }
            [data-testid="stMetricLabel"] { color: #808080 !important; }
            hr { border: 0; height: 1px; background: linear-gradient(to right, #DC0000, transparent); margin: 2rem 0; }
            .reportview-container .main .block-container { padding-top: 2rem; }
            /* Styling for the statistical table */
            .stats-table { width: 100%; border-collapse: collapse; color: white; margin-top: 10px; }
            .stats-table th { background-color: #1f2937; color: #DC0000; text-align: left; padding: 8px; }
            .stats-table td { border-bottom: 1px solid #374151; padding: 8px; }
            </style>
        """, unsafe_allow_html=True)

    apply_custom_styles()

    # === 2. Core Logic & Robust Data Loading === #
    @st.cache_data
    def load_data():
        """
        Finds the CSV file using absolute pathing to prevent FileNotFoundError.
        """
        file_name = "Australia2025_LEC_cleaned_sorted.csv"
        
        # Get the absolute path of the directory where this script is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Build the path relative to this script: up one level, then into cleaned_Csv
        target_path = os.path.join(current_dir, "..", "cleaned_Csv", file_name)

        if not os.path.exists(target_path):
            st.error(f"Telemetry file not found at: {target_path}")
            return pd.DataFrame()

        df = pd.read_csv(target_path)
        if "DistanceToDriverAhead" in df.columns:
            df.rename(columns={"DistanceToDriverAhead": "Gap"}, inplace=True)
        return df

    def compute_lap_time_stats(df):
        def single_lap_time(lap_df):
            lap_df = lap_df.sort_values("Distance")
            dx = lap_df["Distance"].diff().fillna(0).values
            v_mps = np.clip(lap_df["Speed"].values / 3.6, 0.1, 100)
            return np.nansum(dx / v_mps)
        return df.groupby("LapNumber").apply(single_lap_time)

    def get_stats_row(data, label):
        return {
            "Metric": label,
            "Q1": f"{np.percentile(data, 25):.2f}",
            "Median (Q2)": f"{np.median(data):.2f}",
            "Q3": f"{np.percentile(data, 75):.2f}",
            "Std Dev": f"{np.std(data):.2f}",
            "Variance": f"{np.var(data):.2f}"
        }

    # === 3. Main Dashboard Construction === #
    def main():
        df = load_data()
        if df.empty:
            return

        st.title("🏎️ Leclerc Telemetry Analysis")
        st.markdown("### Formula 1 | Australia 2025 | Scuderia Ferrari Performance")

        # SIDEBAR
        st.sidebar.header("Session Control")
        all_laps = sorted(df["LapNumber"].unique().tolist())
        selected_lap = st.sidebar.selectbox("Active Analysis Lap", all_laps, index=0)
        st.sidebar.markdown("---")
        st.sidebar.subheader("Comparison Engine")
        
        lap_times = compute_lap_time_stats(df)
        best_lap_num = int(lap_times.idxmin())
        worst_lap_num = int(lap_times.idxmax())

        compare_target = st.sidebar.selectbox(
            "Compare Primary Lap With:", 
            ["None", f"Session Best (#{best_lap_num})", f"Session Worst (#{worst_lap_num})", "Specific Lap"]
        )
        
        custom_comp_lap = None
        if compare_target == "Specific Lap":
            custom_comp_lap = st.sidebar.selectbox("Reference Lap", all_laps, index=min(1, len(all_laps)-1))

        # --- SECTION 1: PRIMARY TELEMETRY ---
        lap_data = df[df["LapNumber"] == selected_lap]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Current Lap", f"#{selected_lap}")
        m2.metric("Top Speed", f"{int(lap_data['Speed'].max())} km/h")
        m3.metric("Avg RPM", f"{int(lap_data['RPM'].mean())}")
        m4.metric("Est. Lap Time", f"{lap_times[selected_lap]:.3f}s")

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            fig_speed = px.line(lap_data, x="Distance", y="Speed", title="Velocity Profile (LEC)", 
                                color_discrete_sequence=["#DC0000"], template="plotly_dark")
            st.plotly_chart(fig_speed, use_container_width=True)
        with c2:
            fig_rpm = px.line(lap_data, x="Distance", y="RPM", title="Power Unit Output (RPM)", 
                              color_discrete_sequence=["#FFF200"], template="plotly_dark")
            st.plotly_chart(fig_rpm, use_container_width=True)

        c3, c4 = st.columns([1, 1.2])
        with c3:
            fig_inputs = go.Figure()
            fig_inputs.add_trace(go.Scatter(x=lap_data["Distance"], y=lap_data["Throttle"], name="Throttle", line=dict(color="#00FF00")))
            fig_inputs.update_layout(title="Driver Inputs: Throttle", xaxis_title="Distance (m)", yaxis_title="Throttle (%)", template="plotly_dark")
            st.plotly_chart(fig_inputs, use_container_width=True)
        with c4:
            fig_map = px.scatter(lap_data, x="X", y="Y", color="Speed", title="Track Speed Heatmap (Leclerc)",
                                 color_continuous_scale="Reds", template="plotly_dark")
            st.plotly_chart(fig_map, use_container_width=True)

        # --- SECTION 2: 3D ENGINE ANALYSIS ---
        st.markdown("<hr>", unsafe_allow_html=True)
        st.header("⚡ Advanced 3D Engine Diagnostics")
        c5, c6 = st.columns(2)
        with c5:
            st.write("### Velocity Valley")
            fig_3d = go.Figure(data=[go.Scatter3d(x=lap_data['X'], y=lap_data['Y'], z=lap_data['Speed'],
                mode='lines', line=dict(color=lap_data['Speed'], colorscale='Reds', width=4))])
            fig_3d.update_layout(template="plotly_dark", height=500)
            st.plotly_chart(fig_3d, use_container_width=True)
        with c6:
            st.write("### PU Thermal / RPM Load")
            fig_3d_rpm = go.Figure(data=[go.Scatter3d(x=lap_data['X'], y=lap_data['Y'], z=lap_data['RPM'],
                mode='markers', marker=dict(size=2, color=lap_data['RPM'], colorscale='YlOrRd'))])
            fig_3d_rpm.update_layout(template="plotly_dark", height=500)
            st.plotly_chart(fig_3d_rpm, use_container_width=True)

        # --- SECTION 3: COMPARISON ANALYSIS ---
        if compare_target != "None":
            st.markdown("<hr>", unsafe_allow_html=True)
            if "Best" in compare_target: ref_num = best_lap_num
            elif "Worst" in compare_target: ref_num = worst_lap_num
            else: ref_num = custom_comp_lap
            
            st.header(f"🔍 Comparative Delta Analysis: Lap {selected_lap} vs Lap {ref_num}")
            ref_df = df[df["LapNumber"] == ref_num].sort_values("Distance")
            cur_df = df[df["LapNumber"] == selected_lap].sort_values("Distance")
            
            max_dist = min(ref_df["Distance"].max(), cur_df["Distance"].max())
            ref_distance = np.linspace(0, max_dist, 2000)
            v_ref_interp = np.interp(ref_distance, ref_df["Distance"], ref_df["Speed"])
            v_cur_interp = np.interp(ref_distance, cur_df["Distance"], cur_df["Speed"])
            
            delta_time = np.cumsum((1/(np.clip(v_cur_interp/3.6, 0.1, 100)) - 1/(np.clip(v_ref_interp/3.6, 0.1, 100))) * np.diff(ref_distance, prepend=0))

            fig_delta = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.3, 0.7])
            fig_delta.add_trace(go.Scatter(x=ref_distance, y=delta_time, name="Time Delta", fill='tozeroy', line=dict(color="#FFF200")), row=1, col=1)
            fig_delta.add_trace(go.Scatter(x=ref_distance, y=v_ref_interp, name=f"Ref Lap {ref_num}", line=dict(color="rgba(255,255,255,0.4)", dash='dot')), row=2, col=1)
            fig_delta.add_trace(go.Scatter(x=ref_distance, y=v_cur_interp, name=f"Lap {selected_lap}", line=dict(color="#DC0000")), row=2, col=1)
            fig_delta.update_layout(height=600, template="plotly_dark")
            st.plotly_chart(fig_delta, use_container_width=True)

            st.subheader("📊 Statistical Distribution & Variance")
            combined_comp = pd.concat([
                cur_df.assign(Lap=f"Lap {selected_lap}"),
                ref_df.assign(Lap=f"Lap {ref_num}")
            ])

            col_stats1, col_stats2 = st.columns(2)
            with col_stats1:
                fig_box_speed = px.box(combined_comp, x="Lap", y="Speed", color="Lap",
                                     title="Speed Distribution (Q1-Q3 & Outliers)",
                                     color_discrete_map={f"Lap {selected_lap}": "#DC0000", f"Lap {ref_num}": "#808080"},
                                     template="plotly_dark")
                st.plotly_chart(fig_box_speed, use_container_width=True)
            with col_stats2:
                fig_box_rpm = px.box(combined_comp, x="Lap", y="RPM", color="Lap",
                                    title="RPM Consistency Analysis",
                                    color_discrete_map={f"Lap {selected_lap}": "#FFF200", f"Lap {ref_num}": "#808080"},
                                    template="plotly_dark")
                st.plotly_chart(fig_box_rpm, use_container_width=True)

            st.write("#### Detailed Telemetry Metrics")
            stats_data = [
                get_stats_row(cur_df["Speed"], f"Lap {selected_lap} Speed"),
                get_stats_row(ref_df["Speed"], f"Lap {ref_num} Speed"),
                get_stats_row(cur_df["RPM"], f"Lap {selected_lap} RPM"),
                get_stats_row(ref_df["RPM"], f"Lap {ref_num} RPM")
            ]
            st.table(pd.DataFrame(stats_data).set_index("Metric"))

        # --- SECTION 4: GLOBAL REPORT ---
        if st.sidebar.button("Generate Full Global Report"):
            st.markdown("<hr>", unsafe_allow_html=True)
            st.header(f"🏁 Global Session Comparison: Best (#{best_lap_num}) vs Worst (#{worst_lap_num})")
            
            col_a, col_b = st.columns(2)
            best_df = df[df["LapNumber"] == best_lap_num]
            worst_df = df[df["LapNumber"] == worst_lap_num]
            
            with col_a:
                fig_g_speed = go.Figure()
                fig_g_speed.add_trace(go.Scatter(x=best_df["Distance"], y=best_df["Speed"], name="Best", line=dict(color="#00FF7F")))
                fig_g_speed.add_trace(go.Scatter(x=worst_df["Distance"], y=worst_df["Speed"], name="Worst", line=dict(color="#FF6F61")))
                fig_g_speed.update_layout(title="Speed Profile Comparison", xaxis_title="Distance (m)", yaxis_title="Speed (km/h)", template="plotly_dark")
                st.plotly_chart(fig_g_speed, use_container_width=True)
                
            with col_b:
                fig_g_rpm = go.Figure()
                fig_g_rpm.add_trace(go.Scatter(x=best_df["Distance"], y=best_df["RPM"], name="Best", line=dict(color="#00FF7F")))
                fig_g_rpm.add_trace(go.Scatter(x=worst_df["Distance"], y=worst_df["RPM"], name="Worst", line=dict(color="#FF6F61")))
                fig_g_rpm.update_layout(title="RPM Load Comparison", xaxis_title="Distance (m)", yaxis_title="RPM", template="plotly_dark")
                st.plotly_chart(fig_g_rpm, use_container_width=True)

            st.subheader("📊 Global Statistical Distribution")
            combined_global = pd.concat([
                best_df.assign(Lap="Session Best"),
                worst_df.assign(Lap="Session Worst")
            ])
            
            ga, gb = st.columns(2)
            with ga:
                fig_box_g_speed = px.box(combined_global, x="Lap", y="Speed", color="Lap",
                                        title="Speed Variance: Best vs Worst",
                                        color_discrete_map={"Session Best": "#00FF7F", "Session Worst": "#FF6F61"},
                                        template="plotly_dark")
                st.plotly_chart(fig_box_g_speed, use_container_width=True)
            with gb:
                fig_box_g_rpm = px.box(combined_global, x="Lap", y="RPM", color="Lap",
                                      title="RPM Variance: Best vs Worst",
                                      color_discrete_map={"Session Best": "#00FF7F", "Session Worst": "#FF6F61"},
                                      template="plotly_dark")
                st.plotly_chart(fig_box_g_rpm, use_container_width=True)
                
            global_stats_data = [
                get_stats_row(best_df["Speed"], "Session Best Speed"),
                get_stats_row(worst_df["Speed"], "Session Worst Speed"),
                get_stats_row(best_df["RPM"], "Session Best RPM"),
                get_stats_row(worst_df["RPM"], "Session Worst RPM")
            ]
            st.table(pd.DataFrame(global_stats_data).set_index("Metric"))

    main()

# if __name__ == "__main__":
#     main()