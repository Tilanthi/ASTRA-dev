# H015 Analysis Script
# Objective: Test if RAR scatter correlates with star formation rate surface density
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

data_path = "/shared/ASTRA/data/discovery_run/radial_acceleration_relation.csv"
rar_data = pd.read_csv(data_path)

# Placeholder for SFR data
# sfr_data = pd.read_csv("/path/to/sfr_data.csv")  # To be updated after data acquisition

# Calculate RAR residuals (simplified, to be refined with actual formula)
rar_data["residual"] = np.log10(rar_data["g_obs"]) - np.log10(rar_data["g_tot"])

# Placeholder for merging with SFR data
# merged_data = rar_data.merge(sfr_data, on="galaxy_id")

# Placeholder correlation test
# correlation = merged_data["residual"].corr(merged_data["sfr_surface_density"])
# print(f"Correlation between RAR residuals and SFR surface density: {correlation}")

# Save placeholder plot
plt.figure(figsize=(10, 6))
plt.scatter(np.log10(rar_data["g_bar"]), rar_data["residual"], alpha=0.5)
plt.xlabel("Log(g_bar) [m/s^2]")
plt.ylabel("RAR Residual [dex]")
plt.title("RAR Residuals vs Baryonic Acceleration (Placeholder for H015)")
plt.savefig("/shared/ASTRA/data/h015_star_formation/h015_rar_residuals_placeholder.png")
plt.close()

print("H015 analysis placeholder complete. Awaiting SFR data.")
