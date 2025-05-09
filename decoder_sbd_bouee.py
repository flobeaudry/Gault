import isbd # need to have the isbd.py file; download from https://xed.ch/project/isbd/ and change a few things that are not up to date
import pandas as pd
import re
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt


# Time of the file you are decoding.. need better way to get this
#target_time = datetime(2025, 4, 27, 10, 0, 0)
target_time = datetime(2025, 2, 26, 16, 0,0)


#filename = "300534063682480_001657.sbd" # 2025-04-27 10:00
filename = "300534063682480_001052.sbd" # 2025-02-26 16:01
#filename= "300534063682480_000752.sbd" # ? idk when

# Open the .sbd file and extract the payload (hex too)
msg = isbd.Isbdmsg()
extracted_msg = msg.read_sbd_file(filename)
hex_data = str(extracted_msg.payload_hex)[2:-1]


# Function to decode the hex from the payload into temperatures
def decode_temperature_hex(hex_string):

    hex_string = hex_string.replace(" ", "").lower()
    
    # Break into 2-byte (4 hex digit) chunks
    words = [hex_string[i:i+4] for i in range(0, len(hex_string), 4)]

    temperatures = []
    for word in words:
        
        # Some chunks = weird (ignore for now; maybe creating problems?)
        if len(word) != 4:
            print(f"Skipping incomplete word: {word}")
            continue 

        # Decode little-endian
        low = int(word[0:2], 16)
        high = int(word[2:4], 16)
        value = (high << 8) | low

        # Convert to float temperature
        temp = value / 16.0
        temperatures.append(temp)

    return temperatures


# Get the temperatures
temps_iridium = decode_temperature_hex(hex_data)
# Get the length (missing top 9 temperature values for some reason?)
length = len(temps_iridium)
depth_iridium = np.linspace(0, (length-1)*2, length)+18



# Compare to the data on the SD card
file_path = 'TEMPDATA.TXT'

data = []
with open(file_path, 'r') as f:
    for line in f:
    
        if not line.strip():
            continue

        match = re.match(r"\s*\d+\s+(\d{4}/\d{2}/\d{2})\s+(\d{2}:\d{2}:\d{2})\s+\d+\s+.*?((?:-?\d+\.\d+\s+)+)", line)
        if match:
            date_str = match.group(1) + ' ' + match.group(2)
            timestamp = datetime.strptime(date_str, '%Y/%m/%d %H:%M:%S')
            
            # Only keep from december 2024 (deployment)
            if timestamp >= datetime(2024, 12, 1):
                float_values_str = match.group(3)
                float_values = [float(val) for val in float_values_str.split()]
                data.append((timestamp, float_values))

df = pd.DataFrame(data, columns=["timestamp", "temperatures"])

# Create depth data
length = len(df["temperatures"][0])
depth = np.linspace(0, (length-1)*2, length)

df["time_diff"] = df["timestamp"].apply(lambda x: abs(x - target_time))
closest_row = df.loc[df["time_diff"].idxmin()]
date = closest_row["timestamp"]
temps = closest_row["temperatures"]

# FIG

fig, ax = plt.subplots(figsize=(5,7))
plt.plot(temps[:-1], depth[:-1]-40, color='blue', linewidth=3, label='SD card')
plt.plot(temps_iridium, depth_iridium-40, color='r', linestyle='--', label='Iridium')
ax.invert_yaxis()
ax.set_title(f"{date}", fontweight ="extra bold", color='k',  family='sans-serif')
ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Depth (cm)")
ax.set_xlim(-10,10)
plt.legend()
plt.grid()
plt.savefig(
        f"plots/decoded_{date}.png", dpi=300
        )
