# H015 Analysis Script (Updated)
# Objective: Test if RAR scatter correlates with star formation rate surface density
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

data_path = "/shared/ASTRA/data/discovery_run/radial_acceleration_relation.csv"
rar_data = pd.read_csv(data_path)

# Check column names for correct references
print("Column names in dataset:", rar_data.columns.tolist())

# Update column names based on actual data (placeholder, adjust after inspection)
# Assuming correct columns after inspection, e.g., "gObs" and "gBar"
# Calculate RAR residuals (simplified, to be refined with actual formula)
# Adjust these based on actual column names after inspection
try:
    rar_data["residual"] = np.log10(rar_data["gObs"]) - np.log10(rar_data["gBar"])
except KeyError as e:
    print("KeyError occurred:", e)
    print("Using placeholder calculation or skipping to plot.")
    rar_data["residual"] = 0  # Placeholder if columns don’t match

# Placeholder for merging with SFR data
# sfr_data = pd.read_csv("/path/to/sfr_data.csv")  # To be updated after data acquisition

# Placeholder correlation test
# correlation = merged_data["residual"].corr(merged_data["sfr_surface_density"])
# print(f"Correlation between RAR residuals and SFR surface density: {correlation}")

# Save placeholder plot
plt.figure(figsize=(10, 6))
try:
    plt.scatter(np.log10(rar_data["gBar"]), rar_data["residual"], alpha=0.5)
except KeyError:
    plt.scatter(np.arange(len(rar_data)), rar_data["residual"], alpha=0.5)  # Fallback if column missing
plt.xlabel("Log(g_bar) [m/s^2]")
plt.ylabel("RAR Residual [dex]")
plt.title("RAR Residuals vs Baryonic Acceleration (Placeholder for H015)")
plt.savefig("/shared/ASTRA/data/h015_star_formation/h015_rar_residuals_placeholder.png")
plt.close()

print("H015 analysis placeholder complete. Awaiting SFR data.")
