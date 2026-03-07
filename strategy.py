import pandas as pd
import numpy as np

def generate_signals(df: pd.DataFrame, buy_vip_threshold: float = 80, exit_vip_threshold: float = 50, exit_momentum_threshold: float = 20) -> pd.DataFrame:
    """
    Applies the strategy logic:
    - Buy: Momentum > 50th percentile AND VIP Rank > buy_vip_threshold AND Global Reliability >= 0.5
    - Sell/Exit: VIP Rank < exit_vip_threshold OR Momentum < 50
    - If Global Reliability < 0.5: Mark as 'Données Insuffisantes'
    """
    if df.empty:
        return df
        
    df = df.copy()
    
    signals = []
    for _, row in df.iterrows():
        # Data Integrity Check
        if row['Global_Rel'] < 0.5:
            signal = "Données Insuffisantes"
        # Buy Condition
        elif row['Momentum_Rank'] >= 50 and row['VIP_Rank'] >= buy_vip_threshold:
            signal = "Buy"
        # Sell Condition: VIP below exit OR Momentum below 50
        elif row['VIP_Rank'] < exit_vip_threshold or row['Momentum_Rank'] < 50:
            signal = "Sell"
        else:
            signal = "Hold"
            
        signals.append(signal)
        
    df['Signal'] = signals
    return df
