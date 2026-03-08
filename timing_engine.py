import pandas as pd
import numpy as np

def calculate_volume_profile(history_df: pd.DataFrame, bins: int = 100):
    """
    Calculates POC, VAH, and VAL from the last 252 days of history.
    """
    if history_df is None or len(history_df) < 20:
        return None, None, None

    df = history_df.tail(252).copy()

    # Use the average of High and Low as the representative price for the day
    df['avg_price'] = (df['High'] + df['Low']) / 2

    price_min = df['avg_price'].min()
    price_max = df['avg_price'].max()

    if price_max == price_min:
        return price_min, price_min, price_min

    # Histogram of volume-weighted prices
    counts, bin_edges = np.histogram(df['avg_price'], bins=bins, weights=df['Volume'], range=(price_min, price_max))

    # POC: Bin with the maximum volume
    poc_idx = np.argmax(counts)
    poc = (bin_edges[poc_idx] + bin_edges[poc_idx+1]) / 2

    # Total Volume
    total_vol = counts.sum()
    target_vol = total_vol * 0.70

    # Value Area: Expand from POC
    low_idx = poc_idx
    high_idx = poc_idx
    current_vol = counts[poc_idx]

    while current_vol < target_vol:
        if low_idx > 0 and high_idx < bins - 1:
            # Check which side adds more volume
            if counts[low_idx-1] >= counts[high_idx+1]:
                low_idx -= 1
                current_vol += counts[low_idx]
            else:
                high_idx += 1
                current_vol += counts[high_idx]
        elif low_idx > 0:
            low_idx -= 1
            current_vol += counts[low_idx]
        elif high_idx < bins - 1:
            high_idx += 1
            current_vol += counts[high_idx]
        else:
            break

    val = bin_edges[low_idx]
    vah = bin_edges[high_idx+1]

    return float(poc), float(vah), float(val)

def get_timing_status(price, poc, vah, val):
    """
    Determines the price zone and distance to POC.
    """
    if price is None or poc is None or vah is None:
        return "N/A", None

    dist_poc = (price - poc) / poc * 100

    if price < poc:
        zone = "Prix de Gros"
    elif poc <= price <= vah:
        zone = "Prix de Détail"
    else:
        zone = "Extension Haute"

    return zone, round(dist_poc, 1)
