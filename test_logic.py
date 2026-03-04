import unittest
import pandas as pd
import numpy as np
from src.scoring_engine import calculate_scores
from src.strategy import generate_signals

class TestPortfolioLogic(unittest.TestCase):
    def setUp(self):
        self.sample_data = pd.DataFrame({
            'Ticker': ['A', 'B', 'C', 'D'],
            'MarketCap': [1000, 1000, 1000, 1000],
            'BookValue': [100, 200, 300, 400], # Value Ranks: 25, 50, 75, 100
            'AssetGrowth': [0.1, 0.05, 0.15, 0.2], # Inv Ranks: 50, 100, 25, 0 (ascending=False)
            'GrossProfit': [200, 200, 200, 200],
            'TotalAssets': [1000, 800, 1200, 1000], # Prof: 0.2, 0.25, 0.166, 0.2 -> Ranks: 50, 100, 25, 50
            'Momentum': [0.1, 0.2, 0.05, -0.1] # Mom Ranks: 50, 100, 25, 0
        })

    def test_scoring_ranks(self):
        scored = calculate_scores(self.sample_data)
        self.assertIn('VIP_Rank', scored.columns)
        self.assertTrue(all(scored['Value_Rank'] > 0))
        
    def test_strategy_signals(self):
        scored = calculate_scores(self.sample_data)
        print("\nScored data in test:")
        print(scored[['Ticker', 'Momentum_Rank', 'VIP_Rank']])
        # B should be a Buy (Mom_Rank=100, High VIP)
        # D should be a Sell (Mom_Rank low)
        signals = generate_signals(scored, buy_vip_threshold=50, exit_momentum_threshold=30)
        
        b_signal = signals.loc[signals['Ticker'] == 'B', 'Signal'].values[0]
        d_signal = signals.loc[signals['Ticker'] == 'D', 'Signal'].values[0]
        
        self.assertEqual(b_signal, "Buy")
        self.assertEqual(d_signal, "Sell")

if __name__ == '__main__':
    unittest.main()
