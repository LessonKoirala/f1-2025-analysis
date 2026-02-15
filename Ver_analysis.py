import pandas as pd
import os
import re

# --- CONFIGURATION --- #

# Driver code and full name mapping
driver_code = "VER"
driver_full_name = "Max_Verstappen"

# Folder for this driver’s telemetry CSVs
driver_folder = f"F1_Data/Australia2025/{driver_code}"

# Create the report folder if it doesn't exist
report_folder = "report"
os.makedirs(report_folder, exist_ok=True)

# Report file path
report_file = os.path.join(report_folder, f"{driver_full_name}.txt")

# Folder where cleaned CSV will be saved
cleaned_folder = "cleaned_Csv"
os.makedirs(cleaned_folder, exist_ok=True)

# Final cleaned sorted CSV path
sorted_cleaned_csv = os.path.join(cleaned_folder, f"Australia2025_{driver_code}_cleaned_sorted.csv")

driverahead_summary = []

# Helper: case-insensitive column finder
def find_col(df, target):
    target = target.lower()
    for c in df.columns:
        if c.lower() == target:
            return c
    return None

# --- PART 1: Generate inspection report --- #
print(f"Starting inspection for {driver_full_name}...")

with open(report_file, "w", encoding="utf-8") as report:

    def inspect_csv(file_path):
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
        report.write(
            df.iloc[max(0, pos_25 - 2):min(n, pos_25 + 3)].to_string(index=False)
            + "\n"
        )

        report.write(f"\nRows around 75% (index {pos_75 - 2} to {pos_75 + 2}):\n")
        report.write(
            df.iloc[max(0, pos_75 - 2):min(n, pos_75 + 3)].to_string(index=False)
            + "\n"
        )

        # Missing values summary
        report.write("\nMissing values per column:\n")
        report.write(df.isna().sum().to_string() + "\n")

        # Try to find DriverAhead column safely
        da_col = find_col(df, "DriverAhead")

        if da_col:
            missing_da = df[da_col].isna().sum()
            driverahead_summary.append((os.path.basename(file_path), missing_da))

            report.write(f"\nContext around missing {da_col} values:\n")

            nan_indices = df[df[da_col].isna()].index.tolist()
            if not nan_indices:
                report.write("None\n")
            else:
                for idx in nan_indices:
                    start = max(0, idx - 5)
                    end = min(len(df), idx + 6)

                    report.write(f"\nMissing at index {idx} | context {start}-{end - 1}:\n")
                    report.write(df.iloc[start:end].to_string(index=True))
                    report.write("\n" + "-" * 80 + "\n")
        else:
            report.write("\nDriverAhead column not found in this file.\n")
            driverahead_summary.append((os.path.basename(file_path), None))

        report.write("\n" + "-" * 80 + "\n")

    # Check driver folder exists
    if not os.path.isdir(driver_folder):
        report.write(f"ERROR: Directory {driver_folder} not found!\n")
    else:
        report.write(f"{driver_full_name} telemetry inspection report\n")
        report.write("=" * 100 + "\n")

        # Inspect each CSV for the driver
        csv_files = sorted([f for f in os.listdir(driver_folder) if f.endswith(".csv")])
        for filename in csv_files:
            inspect_csv(os.path.join(driver_folder, filename))

        report.write("\nSUMMARY — DriverAhead Missing Values\n")
        report.write("=" * 60 + "\n")
        total_missing = 0
        for fname, miss in driverahead_summary:
            if miss is None:
                report.write(f"{fname}: DriverAhead column NOT FOUND\n")
            else:
                report.write(f"{fname}: {miss} missing DriverAhead values\n")
                total_missing += miss

        report.write("\n" + "=" * 60 + "\n")
        report.write(f"Total DriverAhead missing across valid files: {total_missing}\n")
        report.write("\n✅ Done inspecting.\n")

print(f"Inspection report saved to: {report_file}")

# --- PART 2: Merge, clean, and sort the data --- #
print(f"Merging and cleaning telemetry for {driver_code}...")

combined = pd.DataFrame()

# Reload list to ensure order
csv_files = sorted([f for f in os.listdir(driver_folder) if f.endswith(".csv")])

for filename in csv_files:
    path = os.path.join(driver_folder, filename)
    df = pd.read_csv(path)

    # Extract lap number from filename (handles formats like lap_1.csv or 1.csv)
    lap_match = re.search(r'(\d+)', filename)
    lap_number = int(lap_match.group(1)) if lap_match else 0

    df["Driver"] = driver_code
    df["LapNumber"] = lap_number

    combined = pd.concat([combined, df], ignore_index=True)

if not combined.empty:
    # Standardize column names (lowercase check)
    da_col = find_col(combined, "DriverAhead")
    dist_col = find_col(combined, "DistanceToDriverAhead")
    time_col = find_col(combined, "SessionTime")

    # Replace missing DriverAhead with "None"
    if da_col:
        combined[da_col] = combined[da_col].fillna("None")
        
        # Clear DistanceToDriverAhead for clean air
        if dist_col:
            combined.loc[combined[da_col] == "None", dist_col] = None

    # Sort by lap and session time
    if time_col:
        # Convert to timedelta then total seconds for numeric sorting
        combined[time_col] = pd.to_timedelta(combined[time_col]).dt.total_seconds()

    combined = combined.sort_values(by=["LapNumber", time_col if time_col else "LapNumber"])
    combined.reset_index(drop=True, inplace=True)

    # Save cleaned sorted CSV
    combined.to_csv(sorted_cleaned_csv, index=False)
    print(f"Cleaned sorted CSV saved to: {sorted_cleaned_csv}")
else:
    print("No data found to merge.")

print("✅ Process complete.")