import pandas as pd
import re
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.colors as colors 
from matplotlib.colors import BoundaryNorm
from scipy.ndimage import gaussian_filter1d

# Code to analyse the temperature data from the SB card inside the buoy
# Create temperature profiles for spwcific time sequences
# Pcolor graph

# Path to your .txt file
file_path = 'data/TEMPDATA.TXT'

# List to store each row of parsed data
data = []

with open(file_path, 'r') as f:
    for line in f:
        
        # Skip lines that are empty
        if not line.strip():
            continue

        match = re.match(r"\s*\d+\s+(\d{4}/\d{2}/\d{2})\s+(\d{2}:\d{2}:\d{2})\s+\d+\s+.*?((?:-?\d+\.\d+\s+)+)", line)
        if match:
            date_str = match.group(1) + ' ' + match.group(2)
            timestamp = datetime.strptime(date_str, '%Y/%m/%d %H:%M:%S')
            
            # Only keep from december 2024 (deployment)
            if timestamp >= datetime(2024, 12, 1) and timestamp < datetime(2025, 4, 15):
            #if timestamp >= datetime(2024, 12, 1):
                float_values_str = match.group(3)
                float_values = [float(val) for val in float_values_str.split()]
                data.append((timestamp, float_values))

df = pd.DataFrame(data, columns=["timestamp", "temperatures"])

# Create depth data
length = len(df["temperatures"][0])
depth = np.linspace(0, (length-1)*2, length)

depth_100cm = np.where(depth == 200)
df_top = df.copy()
df_top["temperatures"] = df_top["temperatures"].apply(lambda x: x[:depth_100cm[0][0]])
depth_top = depth[:depth_100cm[0][0]]

def find_ice(target_time):
        df["time_diff"] = df["timestamp"].apply(lambda x: abs(x - target_time))
        closest_row = df.loc[df["time_diff"].idxmin()]
        date = closest_row["timestamp"]
        temps = closest_row["temperatures"]

        df_top["time_diff"] = df_top["timestamp"].apply(lambda x: abs(x - target_time))
        closest_row_top = df_top.loc[df_top["time_diff"].idxmin()]
        date_top = closest_row_top["timestamp"]
        temps_top = closest_row_top["temperatures"]

        # find lowest 0C 
        resolution = 0.0625
        max_iter = 100
        found = False
        for i in range(max_iter):
                tol = resolution * i
                mask = np.abs(np.array(temps_top) - 0) <= tol
                if np.any(mask):
                        # Among those, find the one with **maximum depth**
                        deepest_idx = np.argmax(np.array(depth_top)[mask])
                        candidate_depths = np.array(depth_top)[mask]
                        candidate_temps = np.array(temps_top)[mask]
                        found = True
                        break
        original_indices = np.where(mask)[0]
        deepest_idx = original_indices[deepest_idx]

        depth_zero = depth_top[:deepest_idx]
        temps_zero = temps_top[:deepest_idx]

        temps_smooth = gaussian_filter1d(temps_zero, sigma=2) 
        # dT/dz
        grad = np.abs(np.diff(temps_smooth) / np.diff(depth_zero))

        dTdz = np.gradient(temps_smooth, depth_zero)
        d2Tdz2 = np.gradient(dTdz, depth_zero)
        max_idx = np.argmax(np.abs(d2Tdz2))
        
        
        ice_thickness = depth_zero[max_idx] - depth_zero[-1]
        
        #if depth_zero[-1] < 40:
        #        ice_thickness = 0
        
        return ice_thickness


# To plot one date:
#target_time = datetime(2025, 1, 31, 10, 0, 0)
target_time = datetime(2025, 4, 14, 10, 0, 0)
print(target_time)

df["time_diff"] = df["timestamp"].apply(lambda x: abs(x - target_time))
closest_row = df.loc[df["time_diff"].idxmin()]
date = closest_row["timestamp"]
temps = closest_row["temperatures"]

df_top["time_diff"] = df_top["timestamp"].apply(lambda x: abs(x - target_time))
closest_row_top = df_top.loc[df_top["time_diff"].idxmin()]
date_top = closest_row_top["timestamp"]
temps_top = closest_row_top["temperatures"]

'''
#day = 100
#date = df["timestamp"][day]

fig, ax = plt.subplots(figsize=(6,6))
#plt.plot(df["temperatures"][day], depth/100)
plt.plot(temps, depth/100)
ax.invert_yaxis()
ax.set_title(date, fontweight ="extra bold", color='k',  family='sans-serif')
ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Depth (m)")
plt.grid()
plt.savefig(
        f"plots/bouee_temp_{date}.png", dpi=300
        )
'''

fig, ax = plt.subplots(figsize=(5,7))
plt.plot(temps_top, depth_top-40, linewidth=2,c='b', zorder=100)
ax.invert_yaxis()
ax.set_title(f"Top 100 cm of {date_top}", fontweight ="extra bold", color='k',  family='sans-serif')
ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Depth (cm)")
ax.axhline(y=0, c='k')
ax.axvline(x=0, c='gray')
plt.grid()
plt.savefig(
        f"plots/bouee_top_temp_{date_top}.png", dpi=300
        )


# ID the ice thickness

# find lowest 0C 
resolution = 0.0625
max_iter = 100
found = False
for i in range(max_iter):
    tol = resolution * i
    mask = np.abs(np.array(temps_top) - 0) <= tol
    if np.any(mask):
        # Among those, find the one with **maximum depth**
        deepest_idx = np.argmax(np.array(depth_top)[mask])
        candidate_depths = np.array(depth_top)[mask]
        candidate_temps = np.array(temps_top)[mask]
        found = True
        break
original_indices = np.where(mask)[0]
deepest_idx = original_indices[deepest_idx]


depth_zero = depth_top[:deepest_idx]
temps_zero = temps_top[:deepest_idx]
print(depth_zero)
print(temps_zero)
temps_smooth = gaussian_filter1d(temps_zero, sigma=2) 
# dT/dz
grad = np.abs(np.diff(temps_smooth) / np.diff(depth_zero))

dTdz = np.gradient(temps_smooth, depth_zero)
d2Tdz2 = np.gradient(dTdz, depth_zero)
max_idx = np.argmax(np.abs(d2Tdz2))

print(depth_zero[max_idx])


fig, ax = plt.subplots(figsize=(5,7))
plt.plot(temps_top, depth_top, linewidth=2,c='b', zorder=10, label = "temperature profile")
plt.plot(temps_smooth, depth_zero, linewidth=2,c='forestgreen', linestyle='--', zorder=100, label='smoothed profile')
plt.scatter(temps_smooth[max_idx], depth_zero[max_idx], c='fuchsia',marker='*', s=200, zorder=1000)
plt.scatter(temps_smooth[-1], depth_zero[-1], c='fuchsia',marker='*',s=200, zorder=1000, label='top/bottom of ice')
ax.invert_yaxis()
ax.set_title(f"Top 100 cm of {date_top}", fontweight ="extra bold", color='k',  family='sans-serif')
ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Depth (cm)")
ax.axhline(y=0, c='k')
ax.axvline(x=0, c='gray')

yticks = np.arange(np.min(depth_top), np.max(depth_top)+0.1, 10)
ax.set_yticks(yticks)

plt.grid()
plt.savefig(
        f"plots/tests/smooth_bouee_top_temp_{date_top}.png", dpi=300
        )



# pcolor

# data from physical measurements
df_measures = pd.read_csv('data/physical_measurements/ice_data.csv', parse_dates=['date'])
df_measures_slush = pd.read_csv('data/physical_measurements/slush_data.csv', parse_dates=['date'])


df["temperatures"] = df["temperatures"].apply(lambda x: [x[-1]] + x[:-1])
temperature_matrix = np.array(df["temperatures"].to_list()).T  # shape: (depth, time)
depth_m = depth  # convert to meters if in cm
dates = df["timestamp"]

df["ice_thickness"] = np.nan
for i, timestamp in enumerate(df["timestamp"]):
        print(timestamp)
        ice_thickness_val = find_ice(timestamp)
        df.at[i, "ice_thickness"] = ice_thickness_val

fig, ax = plt.subplots(figsize=(8, 5))

# Create the pcolormesh plot
#pcm = ax.pcolormesh(dates, depth_m-19*2, temperature_matrix, shading='auto', cmap='turbo', vmin=-3, vmax=5)
# Define discrete levels
levels = np.linspace(-3, 3, 25)  # 13 levels from -3 to 3

# Create a colormap and norm
#cmap = plt.get_cmap('RdBu_r', len(levels)-1)
cmap = plt.get_cmap('seismic', len(levels)-1)
norm = BoundaryNorm(boundaries=levels, ncolors=cmap.N)

# Plot with discrete colors
pcm = ax.pcolormesh(dates, depth_m - 19*2, temperature_matrix, 
                    shading='auto', cmap=cmap, norm=norm)
#pcm = ax.pcolormesh(dates, depth_m, temperature_matrix, 
#                    shading='auto', cmap=cmap, norm=norm)
#pcm = ax.pcolormesh(dates, depth_m-19*2, temperature_matrix, shading='auto', cmap='seismic', vmin=-3, vmax=3)
#pcm = ax.pcolormesh(dates, depth_m, temperature_matrix, norm=colors.LogNorm(vmin=-20, vmax=0), shading='auto', cmap='turbo')
ax.invert_yaxis()
ax.set_ylabel("Depth (cm)")
ax.set_xlabel("Date")
fig.autofmt_xdate()

ax.axhline(y=0, c='k',zorder=100)

#ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
fig.autofmt_xdate()

ax.set_title("Gault IMB temperature profile")

ax.scatter(df_measures['date'], df_measures['ice'], color='black', marker='1', s=50,label='Measured ice thickness', zorder=1000)
ax.scatter(df_measures['date'], df_measures['ice']+df_measures_slush['ice'], color='blue', marker='1', s=50,label='Measured ice+slush thickness', zorder=1000)

df["ice_thickness_smooth"] = gaussian_filter1d(df["ice_thickness"], sigma=2) 
plt.plot(dates, -df["ice_thickness"], c='goldenrod', label='ice detection', zorder=100)
plt.plot(dates, -df["ice_thickness_smooth"], c='gold', label='ice detection smooth', zorder=100)
# Add colorbar
cbar = fig.colorbar(pcm, ax=ax, label="Temperature (°C)")

plt.legend(loc='lower right')

plt.tight_layout()
plt.savefig(
        f"plots/pcolor_bouee.png", dpi=300
        )


# CROP

temperature_matrix = np.array(df_top["temperatures"].to_list()).T  # shape: (depth, time)
depth_m = depth_top  # convert to meters if in cm
dates = df_top["timestamp"]

fig, ax = plt.subplots(figsize=(10, 6))

# Create the pcolormesh plot
pcm = ax.pcolormesh(dates, depth_m, temperature_matrix, shading='auto', cmap='turbo')
ax.invert_yaxis()
ax.set_ylabel("Depth (cm)")
ax.set_xlabel("Date")
fig.autofmt_xdate()

ax.axhline(y=18*2, c='k',zorder=100)

ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
ax.set_title("Temperature profile over time")

# Add colorbar
cbar = fig.colorbar(pcm, ax=ax, label="Temperature (°C)")

plt.tight_layout()
plt.savefig(
        f"plots/pcolor_top_bouee.png", dpi=300
        )