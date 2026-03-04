import pandas as pd
import numpy as np

def generate_signals(df: pd.DataFrame, buy_vip_threshold: float = 80, exit_vip_threshold: float = 50, exit_momentum_threshold: float = 20) -> pd.DataFrame:
    """
    Applies the strategy logic:
    - Buy: Momentum > 50th percentile AND VIP Rank > buy_vip_threshold
    - Sell/Exit: VIP Rank < exit_vip_threshold OR Momentum < exit_momentum_threshold
    """
    if df.empty:
        return df
        
    df = df.copy()
    
    signals = []
    for _, row in df.iterrows():
        # Buy Condition
        if row['Momentum_Rank'] >= 50 and row['VIP_Rank'] >= buy_vip_threshold:
            signal = "Buy"
        # Sell Condition: VIP below exit OR Momentum below 50 (as per latest request)
        elif row['VIP_Rank'] < exit_vip_threshold or row['Momentum_Rank'] < 50:
            signal = "Sell"
        else:
            signal = "Hold"
            
        signals.append(signal)
        
    df['Signal'] = signals
    return df

def backtest_static(df: pd.DataFrame):
    """
    Simple 1/N backtest visualization for the current selection.
    This doesn't do a full temporal backtest but shows the potential allocation.
    """
    portfolio = df[df['Signal'] == "Buy"].copy()
    if portfolio.empty:
        return 0, portfolio
        
    n = len(portfolio)
    portfolio['Weight'] = 1.0 / n
    
    # Expected return (simple mean of momentum as proxy for current performance)
    expected_return = portfolio['Momentum'].mean()
    
    return expected_return, portfolio

if __name__ == "__main__":
    # Test
    data = {
        'Ticker': ['A', 'B', 'C', 'D', 'E'],
        'VIP_Rank': [85, 90, 40, 60, 20],
        'Momentum_Rank': [60, 30, 70, 55, 10],
        'Momentum': [0.1, 0.2, 0.05, 0.15, -0.2]
    }
    df = pd.DataFrame(data)
    df_signals = generate_signals(df, buy_vip_threshold=80, exit_vip_threshold=50, exit_momentum_threshold=20)
    print(df_signals)
