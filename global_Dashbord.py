import streamlit as st
import sys
import os
import importlib

# Add the current directory to path so it can find subfolders
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
    # Extracts 'HAM', 'VER', 'TSU', etc. from filenames
    drivers = sorted(list(set([f.split('_')[1] for f in files])))
    return drivers

def load_driver_analysis(driver_code):
    """
    Dynamically imports the analysis module for a driver and returns the show function.
    Assumes the function is named: show_<drivername>_analysis
    """
    module_name = f"analyse_player.{driver_code.lower()}_analysis"
    try:
        mod = importlib.import_module(module_name)
        func_name = f"show_{driver_code.lower()}_analysis"
        return getattr(mod, func_name)
    except (ModuleNotFoundError, AttributeError) as e:
        st.error(f"Analysis module/function not found for {driver_code}: {e}")
        return None

def main():
    # --- SIDEBAR NAVIGATION ---
    st.sidebar.title("🏎️ F1 Telemetry Hub")
    
    # Fetch all available drivers
    drivers = get_available_drivers()
    page_options = ["Home", "Compare Drivers"] + drivers
    
    page = st.sidebar.radio("Select Mode:", page_options)
    st.sidebar.markdown("---")
    st.sidebar.info("Data Source: Australia 2025 GP")
    
    if page == "Home":
        st.title("F1 Performance Dashboard")
        st.write("### Welcome to the 2025 Analytics Suite")
        st.markdown("""
            Use the sidebar to navigate between specific driver telemetry or the comparison engine.
            * Select any driver to view their telemetry analysis.
            * Use 'Compare Drivers' to overlay performance of two drivers head-to-head.
        """)
    
    elif page == "Compare Drivers":
        st.title("⚔️ Driver Comparison Engine")
        if len(drivers) < 2:
            st.warning("Not enough driver data found in cleaned_Csv to perform a comparison.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                d1 = st.selectbox("Select Driver 1", drivers, index=0)
            with col2:
                d2 = st.selectbox("Select Driver 2", drivers, index=1 if len(drivers) > 1 else 0)
            
            if d1 == d2:
                st.info("Select two different drivers to see the delta.")
            else:
                show_comparison_analysis(d1, d2)
    
    else:
        # It's a driver page
        func = load_driver_analysis(page)
        if func:
            func()  # Call the driver analysis function

if __name__ == "__main__":
    main()
