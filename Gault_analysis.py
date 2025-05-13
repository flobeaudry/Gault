import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Rectangle
import pandas as pd
import data.physical_measurements.data as dtf
import xarray as xr
import re

# Open file with snow, ice and slush measurements from the field, and plot the data

xls = pd.ExcelFile("Gault_Data_2025_layer.xlsx", engine="openpyxl")
#xls = pd.ExcelFile("Gault_Data_2025_03_12.xlsx", engine="openpyxl")

# Filter only the sheet names that are YYYY-MM-DD
sheet_names = xls.sheet_names
date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
valid_sheets = [name for name in sheet_names if date_pattern.match(name)]
print("Sheets to process:", valid_sheets)

dfs_by_date = {}
for sheet in valid_sheets:
    # Read the sheet, skipping the first 4 rows, and selecting columns 6, 7, 8, 9 (index 5, 6, 7, 8)
    df = pd.read_excel(xls, sheet_name=sheet, skiprows=5, usecols=[5, 6, 7, 8])

    # Generate the "Distance (m)" column
    num_rows = len(df)  # Get the number of rows in the DataFrame for that date
    distance = np.linspace(0, 124, num=num_rows)  # Uniformly spaced values between 0 and 124 (length until middle of the lake)

    # Add "Distance (m)" as a new column
    df["Distance (m)"] = distance

    # Store each sheet's data in a dictionary with the date as the key
    dfs_by_date[sheet] = df


date = "2025-02-14"
date = "2025-03-11"
date = "2025-03-21"

def fill_isolated_nans(series):
    """
    Replaces isolated NaNs (single NaN between two valid values) with the previous valid value.
    """
    series = series.copy()
    nan_mask = series.isna()
    
    for i in range(1, len(series) - 1):
        if nan_mask[i] and not nan_mask[i - 1] and not nan_mask[i + 1]:  
            series.iloc[i] = series.iloc[i - 1]  # Replace NaN with previous value
            
    return series

# For single figures (one day)
def fig_one_day(dfs_by_date, date, ymin = -90, ymax = 30):
    distance_plot = dfs_by_date[date]["Distance (m)"]
    ice = dfs_by_date[date]["Ice (cm)"]
    slush = dfs_by_date[date]["Slush (cm).1"]
    snow = dfs_by_date[date]["Snow (cm)"]
    layer = dfs_by_date[date]["Layer (cm)"]
    
    snow = fill_isolated_nans(snow)
    slush = fill_isolated_nans(slush)
    ice = fill_isolated_nans(ice)
    layer = fill_isolated_nans(layer)
    distance_plot = fill_isolated_nans(distance_plot)

    #distance_bouee = 18
    distance_labels = str(distance_plot)

    # Create stacked bar plots
    fig, ax = plt.subplots(figsize=(7,4.5))
    fig.set_tight_layout(True)

    # plot buoy
    radius = 3
    loc_bouee =  (distance_plot - 48).abs().idxmin()
    height_bouee = snow[loc_bouee] + slush[loc_bouee]
    circle = Ellipse(
        (48, height_bouee),
        radius,
        #radius * aspect_ratio,
        radius,
        color="darkorange",
        #label="buoy",
    )
    plt.scatter(48, height_bouee, s=100,color='darkorange', label="buoy", zorder=1000)


    ax.stackplot(
        distance_plot,
        snow,
        colors=[ "xkcd:baby blue"],
        labels=["snow"],
    )

    ax.stackplot(
        distance_plot,
        -ice-np.nan_to_num(slush),
        colors=[ "xkcd:robin's egg blue"],
        labels=[ "ice"],
    )

    ax.stackplot(
        distance_plot,
        -slush,
        colors=["xkcd:dark blue"],
        labels=["snow-ice"],
    )
    
    layer = np.where(layer == 0, np.nan, layer)
    ax.scatter(distance_plot, -layer, color='red',marker='1', label='melt layer', zorder=1000)
    
    # Adding a rectangular patch with hatching
    #hatch_area = Rectangle(
    #    (70, 0.2),  # (x, y) bottom-left corner of the rectangle
    #    4,  # Width
    #    4.6,  # Height (adjust according to your y-range)
    #    facecolor='none',  # Keep it transparent but with hatching
    #    edgecolor='xkcd:dark blue',
    #    hatch='////',
    #)
    #ax.add_patch(hatch_area)

    # Labels and title and legend
    ax.set_xlabel("Distance from dock [m]")
    ax.set_xticks(distance[::2]*10)
    ax.set_ylabel(
        "Thickness [cm]",
        rotation=0,
        multialignment="left",
        ha="right",
        position=(0, 0.9),
    )

    ax.set_ylim((np.nanmin(- ice) - 5, np.nanmax(snow + slush)+ 7))
    ax.set_xlim((0, np.nanmax(distance_plot)))

    # vertical lines
    ylenght = ax.get_ylim()[0]

    ax.set_ylim(ymin, ymax)

    ax.set_title(date, fontweight ="extra bold", color='k',  family='sans-serif')

    # legend
    ax.legend(
        loc="lower right",
        bbox_to_anchor=(-0.1, 0.4),
        frameon=False,
        ncol=1,
        handlelength=1,
    )

    plt.savefig(
        f"plots/gault_{date}.png", dpi=300
        )
    
    return


def time_progress_fig (dfs_by_date, variable, color):
    dates = []
    mean_snow = []
    max_snow = []
    min_snow = []
    snow_bouee = []

    # Loop through all available dates in dfs_by_date
    for date in dfs_by_date.keys():
        snow = dfs_by_date[date][variable]
        distance_plot = dfs_by_date[date]["Distance (m)"]
        print('HI', distance_plot)
    
        loc_bouee =  (distance_plot - 48).abs().idxmin()
        if np.isnan(snow.loc[loc_bouee]):
            # Find the nearest valid non-NaN value
            nearest_value = snow.loc[loc_bouee:].ffill().bfill().iloc[0]  
        else:
            nearest_value = snow.loc[loc_bouee]
        
        # Compute statistics
        mean_snow.append(snow.mean())
        max_snow.append(snow.max())
        min_snow.append(snow.min())
        #snow_bouee.append(snow[loc_bouee])
        snow_bouee.append(nearest_value)
        
        dates.append(date)  # Store the date

    # Convert dates to sorted order (if needed)
    dates = sorted(dates)  # Ensure dates are in ascending order

    # Convert to numpy arrays for better handling in plots
    mean_snow = np.array(mean_snow)
    max_snow = np.array(max_snow)
    min_snow = np.array(min_snow)

    # Plot the results
    plt.figure(figsize=(7, 3))
    plt.fill_between(dates, min_snow, max_snow, color=color, alpha=0.9, label="Min-Max Range")
    plt.plot(dates, mean_snow, marker='.', c="grey")
    plt.plot(dates, max_snow, marker=".", c='grey')
    plt.plot(dates, min_snow, marker=".", c='grey')
    plt.plot(dates, snow_bouee, c='darkorange', label='Buoy',linewidth=2 )
    
    # Formatting
    #plt.xlabel("Date")
    plt.ylabel(variable)
    #plt.title("Snow Depth Statistics Over Time")
    plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
    plt.legend()
    #plt.grid(True)

    # Save the figure
    plt.savefig(f"plots/{variable}_statistics.png", dpi=300, bbox_inches="tight")
    
    if variable == "Ice (cm)":
        df_ice = pd.DataFrame({
        'date': dates,
        'ice': snow_bouee
            })

        df_ice.to_csv('ice_data.csv', index=False)
        
    if variable == "Slush (cm).1":
        df_slush = pd.DataFrame({
        'date': dates,
        'ice': snow_bouee
            })

        df_slush.to_csv('slush_data.csv', index=False)
    
    return 

date = "2025-02-14"
#date = "2025-02-08"
date = "2025-03-11"
date = "2025-03-21"
date = "2025-03-26"
#date = "2025-01-31" #this day is messed up, better take the gault_plot.py code
fig_one_day(dfs_by_date, date)

time_progress_fig (dfs_by_date, "Ice (cm)", color="xkcd:robin's egg blue")
time_progress_fig (dfs_by_date, "Snow (cm)", color="xkcd:baby blue")
time_progress_fig (dfs_by_date, "Slush (cm).1", color="xkcd:dark blue")

