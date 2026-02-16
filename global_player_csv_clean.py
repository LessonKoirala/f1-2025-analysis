import pandas as pd
import os

# --- CONFIGURATION --- #
base_data_path = "F1_Data/Australia2025"
report_folder = "report"
cleaned_folder = "cleaned_Csv"

# Driver mapping for report naming
driver_map = {
    "VER": "Max_Verstappen", "HAM": "Lewis_Hamilton", "LEC": "Charles_Leclerc",
    "TSU": "Yuki_Tsunoda", "NOR": "Lando_Norris", "PIA": "Oscar_Piastri",
    "RUS": "George_Russell", "SAI": "Carlos_Sainz", "ALO": "Fernando_Alonso",
    "STR": "Lance_Stroll", "GAS": "Pierre_Gasly", "OCO": "Esteban_Ocon",
    "ALB": "Alex_Albon", "HUL": "Nico_Hulkenberg", "LAW": "Liam_Lawson",
    "BEA": "Oliver_Bearman", "ANT": "Kimi_Antonelli", "DOO": "Jack_Doohan",
    "BOR": "Gabriel_Bortoleto", "HAD": "Isack_Hadjar"
}

os.makedirs(report_folder, exist_ok=True)
os.makedirs(cleaned_folder, exist_ok=True)

# --- HELPER FUNCTIONS --- #

def inspect_csv(file_path, report, driverahead_summary):
    report.write("\n" + "=" * 80 + "\n")
    report.write(f"Inspecting: {file_path}\n")
    report.write("=" * 80 + "\n")

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        report.write(f"⚠️ Failed to read CSV: {e}\n")
        report.write("\n" + "-" * 80 + "\n")
        return

    # Print columns
    report.write("\nColumns:\n")
    report.write(str(df.columns.tolist()) + "\n")

    # First rows snippet
    report.write("\nFirst 5 rows:\n")
    report.write(df.head(5).to_string(index=False) + "\n")

    n = len(df)
    if n == 0:
        report.write("\n⚠️ Empty CSV file!\n")
        report.write("\n" + "-" * 80 + "\n")
        return

    # Snippet around 25% & 75%
    pos_25 = int(n * 0.25)
    pos_75 = int(n * 0.75)

    report.write(f"\nRows around 25% (index {pos_25 - 2} to {pos_25 + 2}):\n")
    report.write(df.iloc[max(0, pos_25 - 2):min(n, pos_25 + 3)].to_string(index=False) + "\n")

    report.write(f"\nRows around 75% (index {pos_75 - 2} to {pos_75 + 2}):\n")
    report.write(df.iloc[max(0, pos_75 - 2):min(n, pos_75 + 3)].to_string(index=False) + "\n")

    # Missing values summary
    report.write("\nMissing values per column:\n")
    report.write(df.isna().sum().to_string() + "\n")

    # Save number of missing DriverAhead
    if "DriverAhead" in df.columns:
        missing_da = df["DriverAhead"].isna().sum()
        driverahead_summary.append((os.path.basename(file_path), missing_da))

        # Context around missing DriverAhead
        report.write("\nContext around missing DriverAhead values:\n")
        nan_indices = df[df["DriverAhead"].isna()].index.tolist()
        if not nan_indices:
            report.write("None\n")
        else:
            for idx in nan_indices:
                start = max(0, idx - 5)
                end = min(len(df), idx + 6)
                report.write(f"\nMissing at index {idx} | context {start}-{end - 1}:\n")
                report.write(df.iloc[start:end].to_string(index=True))
                report.write("\n" + "-" * 80 + "\n")

    report.write("\n" + "-" * 80 + "\n")

# --- MAIN LOOP --- #

for driver_code in sorted(os.listdir(base_data_path)):
    driver_path = os.path.join(base_data_path, driver_code)
    
    if not os.path.isdir(driver_path):
        continue

    full_name = driver_map.get(driver_code, f"Driver_{driver_code}")
    print(f"🚀 Processing: {full_name}")

    report_file = os.path.join(report_folder, f"{full_name}.txt")
    sorted_cleaned_csv = os.path.join(cleaned_folder, f"Australia2025_{driver_code}_cleaned_sorted.csv")
    
    driverahead_summary = []
    combined = pd.DataFrame()

    # 1. Generate inspection report
    with open(report_file, "w") as report:
        report.write(f"{full_name} telemetry inspection report\n")
        report.write("=" * 100 + "\n")

        csv_files = sorted([f for f in os.listdir(driver_path) if f.endswith(".csv")])
        
        for filename in csv_files:
            inspect_csv(os.path.join(driver_path, filename), report, driverahead_summary)

        # Report Summary Section
        report.write("\nSUMMARY — DriverAhead Missing Values\n")
        report.write("=" * 60 + "\n")
        total_missing = 0
        for fname, miss in driverahead_summary:
            report.write(f"{fname}: {miss} missing DriverAhead values\n")
            total_missing += miss

        report.write("\n" + "=" * 60 + "\n")
        report.write(f"Total DriverAhead missing across all files: {total_missing}\n")
        report.write("\n✅ Done inspecting.\n")

    # 2. Merge, clean, and sort
    for filename in csv_files:
        path = os.path.join(driver_path, filename)
        df = pd.read_csv(path)

        # Extract lap number
        lap_number = int(filename.replace("lap_", "").replace(".csv", ""))
        df["Driver"] = driver_code
        df["LapNumber"] = lap_number
        combined = pd.concat([combined, df], ignore_index=True)

    if not combined.empty:
        if "DriverAhead" in combined.columns:
            combined["DriverAhead"] = combined["DriverAhead"].fillna("None")

        if "DistanceToDriverAhead" in combined.columns:
            combined.loc[combined["DriverAhead"] == "None", "DistanceToDriverAhead"] = None

        if "SessionTime" in combined.columns:
            combined["SessionTime"] = pd.to_timedelta(combined["SessionTime"]).dt.total_seconds()

        combined = combined.sort_values(by=["LapNumber", "SessionTime"])
        combined.reset_index(drop=True, inplace=True)
        combined.to_csv(sorted_cleaned_csv, index=False)

print("\n✅ All driver CSVs cleaned and reports generated.")