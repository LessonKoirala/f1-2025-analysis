import streamlit as st
import sys
import os

# Add the current directory to path so it can find the subfolders
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import individual driver functions
from analyse_player.analyse_HAM import show_hamilton_analysis
from analyse_player.analyse_lec import show_leclerc_analysis
from analyse_player.analyse_Ver import show_verstappen_analysis

# Import the comparison logic
from compare_player import show_comparison_analysis

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="F1 Driver Insights 2025",
    page_icon="🏎️",
    layout="wide"
)

def get_available_drivers():
    """Scans the cleaned_Csv folder to find available driver codes."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cleaned_Csv")
    if not os.path.exists(path):
        return []
    files = [f for f in os.listdir(path) if f.endswith('.csv')]
    # Extracts 'HAM' from 'Australia2025_HAM_cleaned_sorted.csv'
    drivers = sorted(list(set([f.split('_')[1] for f in files])))
    return drivers

def main():
    # --- SIDEBAR NAVIGATION ---
    st.sidebar.title("🏎️ F1 Telemetry Hub")
    
    # Navigation selection
    page = st.sidebar.radio(
        "Select Mode:",
        ["Home", "Max Verstappen", "Lewis Hamilton", "Charles Leclerc", "Compare Drivers"]
    )

    st.sidebar.markdown("---")
    st.sidebar.info("Data Source: Australia 2025 GP")

    # --- ROUTING LOGIC ---
    if page == "Home":
        st.title("F1 Performance Dashboard")
        st.write("### Welcome to the 2025 Analytics Suite")
        st.markdown("""
            Use the sidebar to navigate between specific driver telemetry or the comparison engine.
            * **Verstappen Analysis:** Red Bull RB21 Telemetry.
            * **Hamilton Analysis:** Mercedes W16 Telemetry.
            * **Leclerc Analysis:** Ferrari SF-25 Telemetry.
            * **Compare Drivers:** Head-to-head overlay of any two drivers.
        """)
    
    elif page == "Max Verstappen":
        show_verstappen_analysis()
        
    elif page == "Lewis Hamilton":
        show_hamilton_analysis()
        
    elif page == "Charles Leclerc":
        show_leclerc_analysis()

    elif page == "Compare Drivers":
        st.title("⚔️ Driver Comparison Engine")
        
        drivers = get_available_drivers()
        
        if len(drivers) < 2:
            st.warning("Not enough driver data found in cleaned_Csv to perform a comparison.")
        else:
            # Layout for driver selection
            col1, col2 = st.columns(2)
            with col1:
                d1 = st.selectbox("Select Driver 1", drivers, index=0)
            with col2:
                # Set default index to 1 if available
                d2 = st.selectbox("Select Driver 2", drivers, index=1 if len(drivers) > 1 else 0)
            
            if d1 == d2:
                st.info("Select two different drivers to see the delta.")
            else:
                # Call the global comparison function
                show_comparison_analysis(d1, d2)

if __name__ == "__main__":
    main()