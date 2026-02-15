import pandas as pd
import os
import re

# --- CONFIGURATION --- #
# Driver specific details
driver_code = "LEC"
driver_full_name = "Charles_Leclerc"

# Relative paths based on your project structure
driver_folder = f"F1_Data/Australia2025/{driver_code}"
report_folder = "report"
cleaned_folder = "cleaned_Csv"

# Ensure target directories exist
os.makedirs(report_folder, exist_ok=True)
os.makedirs(cleaned_folder, exist_ok=True)

# File paths
report_file = os.path.join(report_folder, f"{driver_full_name}.txt")
sorted_cleaned_csv = os.path.join(cleaned_folder, f"Australia2025_{driver_code}_cleaned_sorted.csv")

driverahead_summary = []

def find_col(df, target):
    """Case-insensitive column finder."""
    target = target.lower()
    for c in df.columns:
        if c.lower() == target:
            return c
    return None

# --- Part 1: Inspection & Reporting --- #
print(f"--- Running Inspection for {driver_full_name} ---")

with open(report_file, "w", encoding="utf-8") as report:
    def inspect_csv(file_path):
        report.write("\n" + "=" * 80 + "\n")
        report.write(f"Inspecting: {file_path}\n")
        report.write("=" * 80 + "\n")

        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            report.write(f"⚠️ Failed to read CSV: {e}\n")
            return

        report.write(f"\nColumns: {df.columns.tolist()}\n")
        
        n = len(df)
        if n == 0:
            report.write("\n⚠️ Empty CSV file!\n")
            return

        # Missing DriverAhead logic
        da_col = find_col(df, "DriverAhead")
        if da_col:
            missing_da = df[da_col].isna().sum()
            driverahead_summary.append((os.path.basename(file_path), missing_da))
        else:
            driverahead_summary.append((os.path.basename(file_path), None))

    if not os.path.isdir(driver_folder):
        print(f"Error: Directory {driver_folder} not found!")
    else:
        csv_files = sorted([f for f in os.listdir(driver_folder) if f.endswith(".csv")])
        for filename in csv_files:
            inspect_csv(os.path.join(driver_folder, filename))
        print(f"Inspection complete. Report: {report_file}")

# --- Part 2: Merge & Clean --- #
print(f"--- Merging Data for {driver_code} ---")
combined_data = []

if os.path.isdir(driver_folder):
    for filename in sorted(os.listdir(driver_folder)):
        if filename.endswith(".csv"):
            path = os.path.join(driver_folder, filename)
            df = pd.read_csv(path)
            
            # Extract lap number from filename (e.g., lap_1.csv -> 1)
            lap_match = re.search(r'lap_(\d+)', filename)
            df["LapNumber"] = int(lap_match.group(1)) if lap_match else 0
            df["Driver"] = driver_code
            combined_data.append(df)

if combined_data:
    combined = pd.concat(combined_data, ignore_index=True)
    
    # Clean DriverAhead
    da_col = find_col(combined, "DriverAhead")
    if da_col:
        combined[da_col] = combined[da_col].fillna("None")
        
    # Standardize SessionTime to seconds
    st_col = find_col(combined, "SessionTime")
    if st_col:
        if combined[st_col].dtype == object:
            combined[st_col] = pd.to_timedelta(combined[st_col]).dt.total_seconds()
        combined = combined.sort_values(by=["LapNumber", st_col])

    combined.to_csv(sorted_cleaned_csv, index=False)
    print(f"Merged CSV saved: {sorted_cleaned_csv}")