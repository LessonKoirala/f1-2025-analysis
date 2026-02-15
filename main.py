import fastf1
import pandas as pd
import os

# enable local cache (speeds up repeated runs)
fastf1.Cache.enable_cache('fastf1cache')

# load the Australia 2025 race session
session = fastf1.get_session(2025, 'Australia', 'R')
session.load(telemetry=True, laps=True)

# base folder to store CSVs
base_folder = "F1_Data/Australia2025"
os.makedirs(base_folder, exist_ok=True)

# loop through drivers
for driver in session.laps.Driver.unique():
    driver_folder = os.path.join(base_folder, driver)
    os.makedirs(driver_folder, exist_ok=True)

    # select all laps for this driver
    driver_laps = session.laps.pick_driver(driver)

    for lap_number in driver_laps.LapNumber.unique():
        lap = driver_laps[driver_laps.LapNumber == lap_number]

        # get lap telemetry
        telemetry = lap.get_telemetry()

        if telemetry.empty:
            continue

        # add computed columns
        telemetry = telemetry.add_distance().add_relative_distance().add_driver_ahead()

        # select the 15 key columns plus identifiers
        cols = [
            "Date", "SessionTime", "Time",
            "Speed", "RPM", "nGear", "Throttle", "Brake", "DRS",
            "X", "Y", "Z",
            "Distance", "RelativeDistance",
            "DriverAhead", "DistanceToDriverAhead"
        ]

        # filter existing columns safely (some may be missing depending on session)
        available_cols = [c for c in cols if c in telemetry.columns]

        # subset the dataframe
        df = telemetry.loc[:, available_cols]

        # save CSV
        csv_path = os.path.join(driver_folder, f"lap_{int(lap_number)}.csv")
        df.to_csv(csv_path, index=False)

        print(f"Saved telemetry for {driver} lap {int(lap_number)} → {csv_path}")
