import pandas as pd
from scoring_engine import calculate_scores
sample_data = pd.DataFrame({
    'Ticker': ['A', 'B', 'C', 'D'],
    'MarketCap': [1000, 1000, 1000, 1000],
    'BookValue': [100, 200, 300, 400],
    'AssetGrowth': [0.1, 0.05, 0.15, 0.2],
    'Revenue': [1000, 1000, 1000, 1000],
    'COGS': [200, 200, 200, 200],
    'SGA': [100, 100, 100, 100],
    'InterestExpense': [50, 50, 50, 50],
    'MinorityInterest': [0, 0, 0, 0],
    'Momentum': [0.1, 0.2, 0.05, -0.1]
})
scored = calculate_scores(sample_data)
print(scored[['Ticker', 'Momentum_Rank', 'VIP_Rank', 'Value_Rank', 'Inv_Rank', 'Prof_Rank', 'VIP_Score']])
