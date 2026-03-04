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
    
    # Inverted rank for Investment: lower growth is better
    df['Inv_Rank'] = df['AssetGrowth'].rank(pct=True, ascending=False) * 100
    
    # Momentum Rank (Condition Filter)
    df['Momentum_Rank'] = df['Momentum'].rank(pct=True) * 100
    
    # Combined Score (VIP): Mean of Value, Investment, Profitability ranks
    df['VIP_Score'] = df[['Value_Rank', 'Inv_Rank', 'Prof_Rank']].mean(axis=1)
    
    # Final Rank of VIP Score
    df['VIP_Rank'] = df['VIP_Score'].rank(pct=True) * 100
    
    return df

if __name__ == "__main__":
    # Test data
    data = {
        'Ticker': ['A', 'B', 'C', 'D'],
        'MarketCap': [1000, 2000, 1500, 3000],
        'BookValue': [500, 400, 900, 600],
        'AssetGrowth': [0.1, 0.05, 0.2, 0.01],
        'GrossProfit': [200, 300, 150, 400],
        'TotalAssets': [1000, 1500, 1200, 2000],
        'Momentum': [0.2, -0.1, 0.05, 0.15]
    }
    df = pd.DataFrame(data)
    scored_df = calculate_scores(df)
    print(scored_df[['Ticker', 'Value_Rank', 'Inv_Rank', 'Prof_Rank', 'VIP_Score', 'VIP_Rank', 'Momentum_Rank']])
