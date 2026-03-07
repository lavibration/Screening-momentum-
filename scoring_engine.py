import pandas as pd
import numpy as np

def calculate_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates Value, Investment, Profitability scores with robustness rules and reliability indices.
    """
    if df.empty:
        return df
        
    df = df.copy()
    
    # 1. VALUE PILLAR (Composite)
    # Rules: PB (asc), PE (asc), FCF Yield (desc). If Net Income < 0, Rank_PE = 0.
    
    # Calculate Ranks
    # PB Rank (Low is better -> Ascending=False)
    df['PB_Rank'] = df['PB'].rank(pct=True, ascending=False, na_option='keep') * 100
    
    # PE Rank (Low is better -> Ascending=False)
    df['PE_Rank_Raw'] = df['PE'].rank(pct=True, ascending=False, na_option='keep') * 100
    df.loc[df['NetIncome'] < 0, 'PE_Rank_Raw'] = 0
    
    # FCF Yield Rank (High is better -> Ascending=True)
    df['FCF_Yield_Rank'] = df['FCF_Yield'].rank(pct=True, ascending=True, na_option='keep') * 100
    
    # Value Robustness: Average of available percentiles
    value_cols = ['PB_Rank', 'PE_Rank_Raw', 'FCF_Yield_Rank']
    df['Value_Rank'] = df[value_cols].mean(axis=1)
    
    # Value Reliability
    def get_value_rel(row):
        available = row[value_cols].count()
        if available == 3: return 1.0
        if available > 0: return 0.5
        return 0.0
    df['Rel_V'] = df.apply(get_value_rel, axis=1)

    # 2. INVESTMENT PILLAR
    # Asset Growth (Variation in Total Assets)
    df['AssetGrowth'] = (df['TotalAssets'] - df['PrevTotalAssets']) / df['PrevTotalAssets']

    # Robustness: assign 50 if data is missing
    df['Inv_Rank'] = df['AssetGrowth'].rank(pct=True, ascending=False, na_option='keep') * 100
    # Reliability
    df['Rel_I'] = 1.0
    df.loc[df['TotalAssets'].isna() | df['PrevTotalAssets'].isna(), 'Rel_I'] = 0.0
    # Fill missing with 50 (neutral) after ranking
    df['Inv_Rank'] = df['Inv_Rank'].fillna(50)

    # 3. PROFITABILITY PILLAR
    # (Revenue - COGS - SGA - Int) / (Equity + Minority)
    # Rules: Handle missing components, assign 50 if missing or aberrant
    num = (df['Revenue'].fillna(0) - df['COGS'].fillna(0) - df['SGA'].fillna(0) - df['InterestExpense'].fillna(0))
    den = (df['BookEquity'].fillna(0) + df['MinorityInterest'].fillna(0))

    df['Profitability_Raw'] = np.where(den != 0, num / den, np.nan)

    # Check for aberrant values
    df['Profitability_Final'] = df['Profitability_Raw']
    df.loc[df['Profitability_Final'].abs() > 2, 'Profitability_Final'] = np.nan
    # Also if essential data is missing (Revenue or BookEquity), it's aberrant/missing
    df.loc[df['Revenue'].isna() | df['BookEquity'].isna(), 'Profitability_Final'] = np.nan

    df['Prof_Rank'] = df['Profitability_Final'].rank(pct=True, na_option='keep') * 100
    # Reliability
    def get_prof_rel(row):
        if pd.isna(row['Revenue']) or pd.isna(row['BookEquity']): return 0.0
        if pd.isna(row['COGS']) or pd.isna(row['SGA']) or pd.isna(row['InterestExpense']): return 0.5
        return 1.0
    df['Rel_P'] = df.apply(get_prof_rel, axis=1)
    # Fill missing with 50 (neutral) after ranking
    df['Prof_Rank'] = df['Prof_Rank'].fillna(50)

    # GLOBAL RELIABILITY
    df['Global_Rel'] = (df['Rel_V'] + df['Rel_I'] + df['Rel_P']) / 3.0

    # MOMENTUM RANK
    df['Momentum_Rank'] = df['Momentum'].rank(pct=True) * 100
    
    # DYNAMIC WEIGHTING
    threshold_mktcap = 6e9

    def compute_vip(row):
        if row['MarketCap'] > threshold_mktcap:
            return 0.2 * row['Value_Rank'] + 0.5 * row['Inv_Rank'] + 0.3 * row['Prof_Rank']
        else:
            return (row['Value_Rank'] + row['Inv_Rank'] + row['Prof_Rank']) / 3.0

    df['Weighting_Type'] = np.where(df['MarketCap'] > threshold_mktcap, "Pondération Custom", "Pondération 1/N")
    df['VIP_Score'] = df.apply(compute_vip, axis=1)
    df['VIP_Rank'] = df['VIP_Score'].rank(pct=True) * 100
    
    # Rounding
    cols_to_round = ['Value_Rank', 'Inv_Rank', 'Prof_Rank', 'Momentum_Rank', 'VIP_Score', 'VIP_Rank', 'Global_Rel']
    df[cols_to_round] = df[cols_to_round].round(1)

    return df
