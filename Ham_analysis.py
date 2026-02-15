import pandas as pd
import os

# --- CONFIGURATION --- #

# Driver code and full name mapping (extend as needed)
driver_code = "HAM"
driver_full_name = "Lewis_Hamilton"  # use underscore or space‑free format

# Folder for this driver’s telemetry CSVs
driver_folder = f"F1_Data/Australia2025/{driver_code}"

# Create the report folder if it doesn't exist
report_folder = "report"
os.makedirs(report_folder, exist_ok=True)

# Report file path (named after the driver)
report_file = os.path.join(report_folder, f"{driver_full_name}.txt")

# Folder where cleaned CSV will be saved
cleaned_folder = "cleaned_Csv"
os.makedirs(cleaned_folder, exist_ok=True)

# Final cleaned sorted CSV path
sorted_cleaned_csv = os.path.join(cleaned_folder, f"Australia2025_{driver_code}_cleaned_sorted.csv")

driverahead_summary = []

# --- Generate inspection report --- #
with open(report_file, "w") as report:

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

        # Save number of missing DriverAhead
        if "DriverAhead" in df.columns:
            missing_da = df["DriverAhead"].isna().sum()
            driverahead_summary.append((os.path.basename(file_path), missing_da))

        # Context around missing DriverAhead
        if "DriverAhead" in df.columns:
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

    # Check driver folder exists
    if not os.path.isdir(driver_folder):
        report.write(f"ERROR: Directory {driver_folder} not found!\n")
    else:
        report.write(f"{driver_full_name} telemetry inspection report\n")
        report.write("=" * 100 + "\n")

        # Inspect each CSV for the driver
        for filename in sorted(os.listdir(driver_folder)):
            if filename.endswith(".csv"):
                inspect_csv(os.path.join(driver_folder, filename))

        report.write("\nSUMMARY — DriverAhead Missing Values\n")
        report.write("=" * 60 + "\n")
        total_missing = 0
        for fname, miss in driverahead_summary:
            report.write(f"{fname}: {miss} missing DriverAhead values\n")
            total_missing += miss

        report.write("\n" + "=" * 60 + "\n")
        report.write(f"Total DriverAhead missing across all files: {total_missing}\n")
        report.write("\n✅ Done inspecting.\n")

print(f"Inspection report saved to: {report_file}")

# --- Merge, clean, and sort the data --- #

combined = pd.DataFrame()

for filename in sorted(os.listdir(driver_folder)):
    if not filename.endswith(".csv"):
        continue

    path = os.path.join(driver_folder, filename)
    df = pd.read_csv(path)

    # Extract lap number from filename
    lap_number = int(filename.replace("lap_", "").replace(".csv", ""))

    df["Driver"] = driver_code
    df["LapNumber"] = lap_number

    combined = pd.concat([combined, df], ignore_index=True)

# Replace missing DriverAhead with "None"
if "DriverAhead" in combined.columns:
    combined["DriverAhead"] = combined["DriverAhead"].fillna("None")

# Clear DistanceToDriverAhead for clean air
if "DistanceToDriverAhead" in combined.columns:
    combined.loc[combined["DriverAhead"] == "None", "DistanceToDriverAhead"] = None

# Sort by lap and session time
if "SessionTime" in combined.columns:
    combined["SessionTime"] = pd.to_timedelta(combined["SessionTime"]).dt.total_seconds()

combined = combined.sort_values(by=["LapNumber", "SessionTime"])
combined.reset_index(drop=True, inplace=True)

# Save cleaned sorted CSV
combined.to_csv(sorted_cleaned_csv, index=False)

print(f"Cleaned sorted CSV saved to: {sorted_cleaned_csv}")
