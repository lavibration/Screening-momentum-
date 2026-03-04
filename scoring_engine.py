import pandas as pd
import numpy as np

def calculate_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates Value, Investment, Profitability and Momentum ranks and the VIP score.
    """
    if df.empty:
        return df
        
    # Copy to avoid side effects
    df = df.copy()
    
    # Fill NaN values for essential columns
    df['BookValue'] = df['BookValue'].fillna(0)
    df['MarketCap'] = df['MarketCap'].fillna(1e6) # Small cap if unknown
    df['AssetGrowth'] = df['AssetGrowth'].fillna(0)
    df['GrossProfit'] = df['GrossProfit'].fillna(0)
    df['TotalAssets'] = df['TotalAssets'].fillna(1)
    df['Momentum'] = df['Momentum'].fillna(0)

    # 1. Value: Book-to-Market (BookValue / MarketCap)
    # MarketCap from info, BookValue from BS
    df['Value'] = df['BookValue'] / df['MarketCap']
    
    # 2. Investment: Asset Growth (calculated in data_provider)
    # Already named 'AssetGrowth'
    
    # 3. Profitability: Gross Profit / Total Assets
    df['Profitability'] = df['GrossProfit'] / df['TotalAssets']
    
    # Normalisation: Rank 1 to 100
    # Higher is better for Value and Profitability
    df['Value_Rank'] = df['Value'].rank(pct=True) * 100
    df['Prof_Rank'] = df['Profitability'].rank(pct=True) * 100
    
    # Inverted rank for Investment: lower growth is better (rigorous balance sheet)
    df['Inv_Rank'] = df['AssetGrowth'].rank(pct=True, ascending=False) * 100
    
    # Momentum Rank (Condition Filter)
    df['Momentum_Rank'] = df['Momentum'].rank(pct=True) * 100
    
    # Dynamic weighting based on Market Cap
    # Seuil: 6 Mds €
    threshold = 6e9

    def compute_vip(row):
        if row['MarketCap'] > threshold:
            # For large caps, overweight Investment and Profitability
            return 0.2 * row['Value_Rank'] + 0.5 * row['Inv_Rank'] + 0.3 * row['Prof_Rank']
        else:
            # 1/N for smaller caps
            return (row['Value_Rank'] + row['Inv_Rank'] + row['Prof_Rank']) / 3.0

    df['VIP_Score'] = df.apply(compute_vip, axis=1)
    
    # Final Rank of VIP Score
    df['VIP_Rank'] = df['VIP_Score'].rank(pct=True) * 100
    
    # Weighting classification
    df['Weighting_Type'] = np.where(df['MarketCap'] > threshold, "Pondération Custom", "Pondération 1/N")

    # Rounding to 1 decimal place for all ranks and score
    cols_to_round = ['Value_Rank', 'Inv_Rank', 'Prof_Rank', 'Momentum_Rank', 'VIP_Score', 'VIP_Rank']
    df[cols_to_round] = df[cols_to_round].round(1)

    return df
