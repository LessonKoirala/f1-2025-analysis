import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os  # Added for path resolution
from plotly.subplots import make_subplots

# === Function Wrapper for Global Dashboard === #
def show_str_analysis():
    # === 1. Configuration & Professional Styling === #
    # st.set_page_config(
    #     page_title="F1 insight", 
    #     layout="wide", 
    #     initial_sidebar_state="expanded"
    # )

    def apply_custom_styles():
        st.markdown("""
            <style>
            .stApp { background-color: #0e1117; }
            h1, h2, h3 { font-family: 'Helvetica Neue', sans-serif; font-weight: 700 !important; color: #00A19B !important; }
            [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 2rem !important; }
            [data-testid="stMetricLabel"] { color: #808080 !important; }
            hr { border: 0; height: 1px; background: linear-gradient(to right, #00A19B, transparent); margin: 2rem 0; }
            .reportview-container .main .block-container { padding-top: 2rem; }
            /* Styling for the statistical table */
            .stats-table { width: 100%; border-collapse: collapse; color: white; margin-top: 10px; }
            .stats-table th { background-color: #1f2937; color: #00A19B; text-align: left; padding: 8px; }
            .stats-table td { border-bottom: 1px solid #374151; padding: 8px; }
            </style>
        """, unsafe_allow_html=True)

    apply_custom_styles()

    # === 2. Core Logic & Data Loading === #
    @st.cache_data
    def load_data():
        # Get the absolute path of the directory where this script is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Build the path relative to this script: up one level, then into cleaned_Csv
        DATA_PATH = os.path.join(current_dir, "..", "cleaned_Csv", "Australia2025_STR_cleaned_sorted.csv")
        
        if not os.path.exists(DATA_PATH):
            st.error(f"Telemetry file not found at: {DATA_PATH}")
            return pd.DataFrame()
            
        df = pd.read_csv(DATA_PATH)
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
            st.error("Telemetry database is inaccessible.")
            return

        st.title("🏎️ STR Telemetry Analysis")
        st.markdown("### Formula 1 | Australia 2025 |  Performance Insight")

        # SIDEBAR
        st.sidebar.header("Session Control")
        all_laps = sorted(df["LapNumber"].unique().tolist())
        selected_lap = st.sidebar.selectbox("Active Analysis Lap", all_laps, index=0)
        st.sidebar.markdown("---")
        st.sidebar.subheader("Comparison Engine")
        
        lap_times = compute_lap_time_stats(df)
        best_lap_num = int(lap_times.idxmin())
        worst_lap_num = int(lap_times.idxmax())
        
        # Calculate 2nd Best and 2nd Worst
        sorted_times = lap_times.sort_values()
        second_best_lap_num = int(sorted_times.index[1]) if len(sorted_times) > 1 else best_lap_num
        second_worst_lap_num = int(sorted_times.index[-2]) if len(sorted_times) > 1 else worst_lap_num

        compare_target = st.sidebar.selectbox(
            "Compare Primary Lap With:", 
            [
                "None", 
                f"Session Best (#{best_lap_num})", 
                f"2nd Best (#{second_best_lap_num})",
                f"Session Worst (#{worst_lap_num})", 
                f"2nd Worst (#{second_worst_lap_num})",
                "Specific Lap"
            ]
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
            fig_speed = px.line(lap_data, x="Distance", y="Speed", title="Velocity Profile", 
                                color_discrete_sequence=["#00A19B"], template="plotly_dark")
            st.plotly_chart(fig_speed, use_container_width=True)
        with c2:
            fig_rpm = px.line(lap_data, x="Distance", y="RPM", title="Power Unit Output (RPM)", 
                              color_discrete_sequence=["#FFD700"], template="plotly_dark")
            st.plotly_chart(fig_rpm, use_container_width=True)

        c3, c4 = st.columns([1, 1.2])
        with c3:
            fig_inputs = go.Figure()
            fig_inputs.add_trace(go.Scatter(x=lap_data["Distance"], y=lap_data["Throttle"], name="Throttle", line=dict(color="#00FF00")))
            fig_inputs.update_layout(title="Driver Inputs: Throttle", xaxis_title="Distance (m)", yaxis_title="Throttle (%)", template="plotly_dark")
            st.plotly_chart(fig_inputs, use_container_width=True)
        with c4:
            fig_map = px.scatter(lap_data, x="X", y="Y", color="Speed", title="Track Speed Heatmap",
                                 color_continuous_scale="Viridis", template="plotly_dark")
            st.plotly_chart(fig_map, use_container_width=True)

        # --- SECTION 2: 3D ENGINE ANALYSIS ---
        st.markdown("<hr>", unsafe_allow_html=True)
        st.header("⚡ Advanced 3D Engine Diagnostics")
        c5, c6 = st.columns(2)
        with c5:
            st.write("### Velocity Valley")
            fig_3d = go.Figure(data=[go.Scatter3d(x=lap_data['X'], y=lap_data['Y'], z=lap_data['Speed'],
                mode='lines', line=dict(color=lap_data['Speed'], colorscale='Viridis', width=4))])
            fig_3d.update_layout(template="plotly_dark", height=500)
            st.plotly_chart(fig_3d, use_container_width=True)
        with c6:
            st.write("### PU Thermal / RPM Load")
            fig_3d_rpm = go.Figure(data=[go.Scatter3d(x=lap_data['X'], y=lap_data['Y'], z=lap_data['RPM'],
                mode='markers', marker=dict(size=2, color=lap_data['RPM'], colorscale='Hot'))])
            fig_3d_rpm.update_layout(template="plotly_dark", height=500)
            st.plotly_chart(fig_3d_rpm, use_container_width=True)

        # --- SECTION 3: COMPARISON ANALYSIS ---
        if compare_target != "None":
            st.markdown("<hr>", unsafe_allow_html=True)
            if "Best" in compare_target and "2nd" not in compare_target: ref_num = best_lap_num
            elif "2nd Best" in compare_target: ref_num = second_best_lap_num
            elif "Worst" in compare_target and "2nd" not in compare_target: ref_num = worst_lap_num
            elif "2nd Worst" in compare_target: ref_num = second_worst_lap_num
            else: ref_num = custom_comp_lap
            
            st.header(f"🔍 Comparative Delta Analysis: Lap {selected_lap} vs Lap {ref_num}")
            ref_df = df[df["LapNumber"] == ref_num].sort_values("Distance")
            cur_df = df[df["LapNumber"] == selected_lap].sort_values("Distance")
            
            max_dist = min(ref_df["Distance"].max(), cur_df["Distance"].max())
            ref_distance = np.linspace(0, max_dist, 2000)
            v_ref_interp = np.interp(ref_distance, ref_df["Distance"], ref_df["Speed"])
            v_cur_interp = np.interp(ref_distance, cur_df["Distance"], cur_df["Speed"])
            
            delta_time = np.cumsum((1/(np.clip(v_cur_interp/3.6, 0.1, 100)) - 1/(np.clip(v_ref_interp/3.6, 0.1, 100))) * np.diff(ref_distance, prepend=0))

            fig_delta = make_subplots(
                rows=3, cols=1, 
                shared_xaxes=True, 
                vertical_spacing=0.05,
                subplot_titles=(f"Time Delta (seconds)", f"Speed: Lap {selected_lap}", f"Speed: Lap {ref_num}"),
                row_heights=[0.25, 0.35, 0.35]
            )
            
            fig_delta.add_trace(go.Scatter(x=ref_distance, y=delta_time, name=f"Delta (L{selected_lap}-L{ref_num})", fill='tozeroy', line=dict(color="#FFD700")), row=1, col=1)
            fig_delta.add_trace(go.Scatter(x=ref_distance, y=v_cur_interp, name=f"Lap {selected_lap}", line=dict(color="#00A19B")), row=2, col=1)
            fig_delta.add_trace(go.Scatter(x=ref_distance, y=v_ref_interp, name=f"Lap {ref_num}", line=dict(color="rgba(255,255,255,0.6)", dash='dot')), row=3, col=1)
            
            fig_delta.update_layout(height=800, template="plotly_dark", showlegend=True, hovermode="x unified")
            fig_delta.update_yaxes(title_text="Delta (s)", row=1, col=1)
            fig_delta.update_yaxes(title_text="Speed (km/h)", row=2, col=1)
            fig_delta.update_yaxes(title_text="Speed (km/h)", row=3, col=1)
            fig_delta.update_xaxes(title_text="Distance (m)", row=3, col=1)
            
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
                                     color_discrete_map={f"Lap {selected_lap}": "#00A19B", f"Lap {ref_num}": "#808080"},
                                     template="plotly_dark")
                st.plotly_chart(fig_box_speed, use_container_width=True)

            with col_stats2:
                fig_box_rpm = px.box(combined_comp, x="Lap", y="RPM", color="Lap",
                                    title="RPM Consistency Analysis",
                                    color_discrete_map={f"Lap {selected_lap}": "#FFD700", f"Lap {ref_num}": "#808080"},
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
            st.header(f"🏁 Global Session Comparison")
            
            best_df = df[df["LapNumber"] == best_lap_num].sort_values("Distance")
            sbest_df = df[df["LapNumber"] == second_best_lap_num].sort_values("Distance")
            worst_df = df[df["LapNumber"] == worst_lap_num].sort_values("Distance")
            sworst_df = df[df["LapNumber"] == second_worst_lap_num].sort_values("Distance")
            
            # UPDATED: Generate Global Profiles with separate plots for each lap category
            st.subheader("📈 Velocity & RPM Profiles (Separated by Lap)")
            
            fig_global = make_subplots(
                rows=4, cols=2, 
                shared_xaxes=True,
                column_titles=("Speed Profile (km/h)", "RPM Profile"),
                row_titles=(f"Best: L{best_lap_num}", f"2nd Best: L{second_best_lap_num}", f"Worst: L{worst_lap_num}", f"2nd Worst: L{second_worst_lap_num}"),
                vertical_spacing=0.03,
                horizontal_spacing=0.08
            )

            # Define Plotting Logic to avoid repetitive code
            laps_to_plot = [
                (best_df, best_lap_num, "#00FF7F", 1),
                (sbest_df, second_best_lap_num, "#00CED1", 2),
                (worst_df, worst_lap_num, "#FF6F61", 3),
                (sworst_df, second_worst_lap_num, "#FFA500", 4)
            ]

            for l_df, l_num, l_color, row_idx in laps_to_plot:
                # Speed Plot (Col 1)
                fig_global.add_trace(go.Scatter(x=l_df["Distance"], y=l_df["Speed"], name=f"Lap {l_num} Speed", line=dict(color=l_color)), row=row_idx, col=1)
                # RPM Plot (Col 2)
                fig_global.add_trace(go.Scatter(x=l_df["Distance"], y=l_df["RPM"], name=f"Lap {l_num} RPM", line=dict(color=l_color, dash='dot')), row=row_idx, col=2)

            fig_global.update_layout(height=1000, template="plotly_dark", showlegend=True, hovermode="x unified")
            st.plotly_chart(fig_global, use_container_width=True)

            st.subheader("📊 Global Statistical Distribution")
            combined_global = pd.concat([
                best_df.assign(Lap=f"Best (L{best_lap_num})"),
                sbest_df.assign(Lap=f"2nd Best (L{second_best_lap_num})"),
                worst_df.assign(Lap=f"Worst (L{worst_lap_num})"),
                sworst_df.assign(Lap=f"2nd Worst (L{second_worst_lap_num})")
            ])
            
            ga, gb = st.columns(2)
            with ga:
                fig_box_g_speed = px.box(combined_global, x="Lap", y="Speed", color="Lap",
                                        title="Speed Variance Analysis",
                                        color_discrete_map={f"Best (L{best_lap_num})": "#00FF7F", f"2nd Best (L{second_best_lap_num})": "#00CED1", f"Worst (L{worst_lap_num})": "#FF6F61", f"2nd Worst (L{second_worst_lap_num})": "#FFA500"},
                                        template="plotly_dark")
                st.plotly_chart(fig_box_g_speed, use_container_width=True)
            with gb:
                fig_box_g_rpm = px.box(combined_global, x="Lap", y="RPM", color="Lap",
                                      title="RPM Variance Analysis",
                                      color_discrete_map={f"Best (L{best_lap_num})": "#00FF7F", f"2nd Best (L{second_best_lap_num})": "#00CED1", f"Worst (L{worst_lap_num})": "#FF6F61", f"2nd Worst (L{second_worst_lap_num})": "#FFA500"},
                                      template="plotly_dark")
                st.plotly_chart(fig_box_g_rpm, use_container_width=True)
                
            global_stats_data = [
                get_stats_row(best_df["Speed"], f"Best (L{best_lap_num}) Speed"),
                get_stats_row(sbest_df["Speed"], f"2nd Best (L{second_best_lap_num}) Speed"),
                get_stats_row(worst_df["Speed"], f"Worst (L{worst_lap_num}) Speed"),
                get_stats_row(sworst_df["Speed"], f"2nd Worst (L{second_worst_lap_num}) Speed")
            ]
            st.table(pd.DataFrame(global_stats_data).set_index("Metric"))

    main()