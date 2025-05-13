import pandas as pd
import re
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import BoundaryNorm
from scipy.ndimage import gaussian_filter1d

# Code to analyse the temperature data from the SB card inside the buoy
# Create temperature profiles for spwcific time sequences
# Pcolor graph
# Need to clean up


# ----------------- Open temperature data from the SD card of the buoy ----------------------------------------------

# Path to .txt file (data from SD card in the buoy)
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

# Days we went on the field
field_days = np.array([datetime(2024, 12, 17, 22, 0, 0), datetime(2025, 1, 31, 10, 0, 0),datetime(2025, 2, 8, 10, 0, 0), datetime(2025, 2, 14, 10, 0, 0), datetime(2025, 3, 11, 10, 0, 0), datetime(2025, 3, 21, 10, 0, 0), datetime(2025, 3, 26, 10, 0, 0)])



def find_ice(df, target_time):
    # Create depth data
    length = len(df["temperatures"][0])
    depth = np.linspace(0, (length-1)*2, length)

    depth_100cm = np.where(depth == 200)
    df_top = df.copy()
    df_top["temperatures"] = df_top["temperatures"].apply(lambda x: x[:depth_100cm[0][0]])
    depth_top = depth[:depth_100cm[0][0]]
    df["time_diff"] = df["timestamp"].apply(lambda x: abs(x - target_time))
    closest_row = df.loc[df["time_diff"].idxmin()]
    date = closest_row["timestamp"]
    temps = closest_row["temperatures"]

    df_top["time_diff"] = df_top["timestamp"].apply(lambda x: abs(x - target_time))
    closest_row_top = df_top.loc[df_top["time_diff"].idxmin()]
    date_top = closest_row_top["timestamp"]
    temps_top = closest_row_top["temperatures"]
    
    # change sigma for smoothness 
    temps_smooth = gaussian_filter1d(temps_top, sigma=2) 

    # find lowest 0C 
    resolution = 0.0625
    max_iter = 100
    found = False
    for i in range(max_iter):
        tol = resolution * i
        #mask = np.abs(np.array(temps_top) - 0) <= tol
        mask = np.abs(np.array(temps_smooth) - 0) <= tol
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
    #temps_zero = temps_top[:deepest_idx]
    temps_zero = temps_smooth[:deepest_idx]
    
    print(depth_zero.shape)
    print(temps_zero.shape)

    # change sigma for smoothness 
    #temps_smooth = gaussian_filter1d(temps_zero, sigma=1) 
    # dT/dz
    #grad = np.abs(np.diff(temps_smooth) / np.diff(depth_zero))

    #dTdz = np.gradient(temps_smooth, depth_zero)
    dTdz = np.gradient(temps_zero, depth_zero)
    d2Tdz2 = np.gradient(dTdz, depth_zero)
    max_idx = np.argmax(np.abs(d2Tdz2))
        
        
    ice_thickness = depth_zero[max_idx] - depth_zero[-1]
        
    #if depth_zero[-1] < 40:
    #        ice_thickness = 0

    return ice_thickness, depth_zero[max_idx], depth_zero[-1], temps_zero[max_idx], temps_zero[-1], temps_zero, depth_zero

    
    

def plot_temperature_profile_top(df, target_time):
    # Create depth data
    length = len(df["temperatures"][0])
    depth = np.linspace(0, (length-1)*2, length)

    depth_100cm = np.where(depth == 200)
    df_top = df.copy()
    df_top["temperatures"] = df_top["temperatures"].apply(lambda x: x[:depth_100cm[0][0]])
    depth_top = depth[:depth_100cm[0][0]]
    
    df["time_diff"] = df["timestamp"].apply(lambda x: abs(x - target_time))
    closest_row = df.loc[df["time_diff"].idxmin()]
    date = closest_row["timestamp"]
    temps = closest_row["temperatures"]

    df_top["time_diff"] = df_top["timestamp"].apply(lambda x: abs(x - target_time))
    closest_row_top = df_top.loc[df_top["time_diff"].idxmin()]
    date_top = closest_row_top["timestamp"]
    temps_top = closest_row_top["temperatures"]
    
    # Plot the top 200 cm of the ice (by itself)
    fig, ax = plt.subplots(figsize=(5,7))
    plt.plot(temps_top, depth_top, linewidth=2,c='b', zorder=100)
    ax.invert_yaxis()
    ax.set_title(f"Top 200 cm of {date_top}", fontweight ="extra bold", color='k',  family='sans-serif')
    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel("Depth (cm)")
    ax.axhline(y=38, c='k')
    ax.axvline(x=0, c='gray')
    ax.set_ylim(top=0)
    yticks = np.arange(np.min(depth_top), np.max(depth_top)+0.1, 10)
    ax.set_yticks(yticks)
    plt.grid()
    plt.savefig(
            f"plots/bouee_top_temp_{date_top}.png", dpi=300
            )
    
    return

def plot_detect_temperature_profile_top(df, target_time):
    # Create depth data
    length = len(df["temperatures"][0])
    depth = np.linspace(0, (length-1)*2, length)

    depth_100cm = np.where(depth == 200)
    df_top = df.copy()
    df_top["temperatures"] = df_top["temperatures"].apply(lambda x: x[:depth_100cm[0][0]])
    depth_top = depth[:depth_100cm[0][0]]
    
    
    df["time_diff"] = df["timestamp"].apply(lambda x: abs(x - target_time))
    closest_row = df.loc[df["time_diff"].idxmin()]
    df_top["time_diff"] = df_top["timestamp"].apply(lambda x: abs(x - target_time))
    closest_row_top = df_top.loc[df_top["time_diff"].idxmin()]
    date_top = closest_row_top["timestamp"]
    temps_top = closest_row_top["temperatures"]
    
    ice_thickness, top_ice, bottom_ice, top_temp, bottom_temp, temps_smooth,  depth_smooth = find_ice(df, target_time)
    
    fig, ax = plt.subplots(figsize=(5,7))
    plt.plot(temps_top, depth_top, linewidth=2,c='b', zorder=10, label = "Temperature profile")
    plt.plot(temps_smooth, depth_smooth, linewidth=2,c='forestgreen', linestyle='--', zorder=100, label='Smoothed profile')
    plt.scatter(top_temp, top_ice, c='fuchsia',marker='*', s=200, zorder=1000)
    plt.scatter(bottom_temp, bottom_ice, c='fuchsia',marker='*',s=200, zorder=1000, label='Top/bottom of ice')
    ax.invert_yaxis()
    ax.set_title(f"Top 100 cm of {date_top}", fontweight ="extra bold", color='k',  family='sans-serif')
    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel("Depth (cm)")
    ax.legend(loc='lower left')
    ax.axhline(y=0, c='k')
    ax.axvline(x=0, c='gray')

    yticks = np.arange(np.min(depth_top), np.max(depth_top)+0.1, 10)
    ax.set_yticks(yticks)

    plt.grid()
    plt.savefig(
            f"plots/temperature_profiles_detection/top_temp_{date_top}.png", dpi=300
            )
    return





# To plot one date:
#target_time = datetime(2025, 1, 31, 10, 0, 0)
#target_time = datetime(2025, 4, 14, 10, 0, 0)


for target_time in field_days:
    plot_detect_temperature_profile_top(df, target_time)
    print("Fig created for: ", target_time)





# pcolor
# data from physical measurements
df_measures = pd.read_csv('data/physical_measurements/ice_data.csv', parse_dates=['date'])
df_measures_slush = pd.read_csv('data/physical_measurements/slush_data.csv', parse_dates=['date'])

length = len(df["temperatures"][0])
depth = np.linspace(0, (length-1)*2, length)

df["temperatures"] = df["temperatures"].apply(lambda x: [x[-1]] + x[:-1])
temperature_matrix = np.array(df["temperatures"].to_list()).T  
depth_m = depth  # convert to meters if in cm
dates = df["timestamp"]

df["ice_thickness"] = np.nan
for i, timestamp in enumerate(df["timestamp"]):
        print(timestamp)
        ice_thickness_val, depth_zero, depth_zero, temps_zero, temps_zero, temps_zero, depth_zero = find_ice(df, timestamp)
        df.at[i, "ice_thickness"] = ice_thickness_val

fig, ax = plt.subplots(figsize=(8, 5))

# Create the pcolormesh plot
levels = np.linspace(-3, 3, 25)

cmap = plt.get_cmap('RdBu_r', len(levels)-1)
#cmap = plt.get_cmap('twilight', len(levels)-1)
norm = BoundaryNorm(boundaries=levels, ncolors=cmap.N)

# Plot with discrete colors
pcm = ax.pcolormesh(dates, depth_m - 19*2, temperature_matrix, 
                    shading='auto', cmap=cmap, norm=norm)
ax.invert_yaxis()
ax.set_ylabel("Depth (cm)")
ax.set_xlabel("Date")
fig.autofmt_xdate()

#ax.axhline(y=0, c='k',zorder=100)

ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
fig.autofmt_xdate()

ax.set_title("Gault IMB temperature profile")

ax.scatter(df_measures['date'], df_measures['ice'], color= "xkcd:robin's egg blue", edgecolors='k', marker='X', s=50,label='Measured ice thickness', zorder=1000)
ax.scatter(df_measures['date'], df_measures['ice']+df_measures_slush['ice'], color="xkcd:dark blue", edgecolors='k', marker='X', s=50,label='Measured ice+slush thickness', zorder=900)

df["ice_thickness_smooth"] = gaussian_filter1d(df["ice_thickness"], sigma=2) 
plt.plot(dates, -df["ice_thickness"], c='xkcd:dirt', linewidth=1.5, label='Ice detection',alpha=0.6,  zorder=100)
plt.plot(dates, -df["ice_thickness_smooth"], c='k',linewidth=2, label='Ice detection smooth', zorder=100)
# Add colorbar
cbar = fig.colorbar(pcm, ax=ax, label="Temperature (°C)")

plt.legend(loc='lower right')

plt.tight_layout()
plt.savefig(
        f"plots/pcolor_bouee.png", dpi=300
        )


