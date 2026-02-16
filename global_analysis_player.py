import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_DIR = os.path.join(BASE_DIR, "cleaned_Csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "analyse_player")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ✅ READ YOUR ACTUAL HAMILTON FILE
HAMILTON_FILE_PATH = os.path.join(BASE_DIR, "ham_analysis.py")

with open(HAMILTON_FILE_PATH, "r", encoding="utf-8") as f:
    original_code = f.read()

for file in os.listdir(CSV_DIR):
    if file.endswith("_cleaned_sorted.csv"):
        
        driver_code = file.split("_")[1]  # HAM, VER, NOR...
        driver_lower = driver_code.lower()

        modified_code = original_code

        # Change function name
        modified_code = modified_code.replace(
            "def show_hamilton_analysis():",
            f"def show_{driver_lower}_analysis():"
        )

        # Change CSV filename
        modified_code = modified_code.replace(
            "Australia2025_HAM_cleaned_sorted.csv",
            file
        )

        # Change dashboard title
        modified_code = modified_code.replace(
            "Hamilton Telemetry Analysis",
            f"{driver_code} Telemetry Analysis"
        )

        output_path = os.path.join(OUTPUT_DIR, f"{driver_lower}_analysis.py")

        with open(output_path, "w", encoding="utf-8") as out:
            out.write(modified_code)

        print(f"✅ Created: {driver_lower}_analysis.py")

print("\n🚀 All driver dashboards generated successfully!")
