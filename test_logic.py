import unittest
import pandas as pd
import numpy as np
from scoring_engine import calculate_scores
from strategy import generate_signals

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
        self.assertIn('Value_Rank', scored.columns)
        self.assertIn('Inv_Rank', scored.columns)
        self.assertIn('Prof_Rank', scored.columns)
        self.assertTrue(all(scored['Value_Rank'] > 0))

    def test_dynamic_weighting(self):
        # Case 1: Small cap (MarketCap <= 6e9)
        small_cap_data = pd.DataFrame({
            'Ticker': ['S1'],
            'MarketCap': [1e9],
            'BookValue': [5e8],
            'AssetGrowth': [0.1],
            'GrossProfit': [1e8],
            'TotalAssets': [5e8],
            'Momentum': [0.1]
        })
        # Ranks will be 100 for a single row
        scored_small = calculate_scores(small_cap_data)
        # 1/3 * 100 + 1/3 * 100 + 1/3 * 100 = 100
        self.assertAlmostEqual(scored_small.iloc[0]['VIP_Score'], 100.0)

        # Case 2: Large cap (MarketCap > 6e9)
        large_cap_data = pd.DataFrame({
            'Ticker': ['L1'],
            'MarketCap': [10e9],
            'BookValue': [5e9],
            'AssetGrowth': [0.1],
            'GrossProfit': [1e9],
            'TotalAssets': [5e9],
            'Momentum': [0.1]
        })
        scored_large = calculate_scores(large_cap_data)
        # 0.2 * 100 + 0.5 * 100 + 0.3 * 100 = 100
        # To really test weighting, we need different ranks. Let's use two rows.
        multi_data = pd.DataFrame({
            'Ticker': ['L1', 'L2'],
            'MarketCap': [10e9, 10e9],
            'BookValue': [1e9, 2e9], # L2 better Value
            'AssetGrowth': [0.05, 0.1], # L1 better Investment (lower growth)
            'GrossProfit': [1e8, 5e8], # L2 better Profitability
            'TotalAssets': [1e9, 1e9],
            'Momentum': [0.1, 0.1]
        })
        # L1: Value_Rank=50, Inv_Rank=100, Prof_Rank=50
        # L2: Value_Rank=100, Inv_Rank=50, Prof_Rank=100

        # Expected VIP_Score for L1 (Large Cap): 0.2*50 + 0.5*100 + 0.3*50 = 10 + 50 + 15 = 75
        # Expected VIP_Score for L2 (Large Cap): 0.2*100 + 0.5*50 + 0.3*100 = 20 + 25 + 30 = 75
        # (Wait, let's pick different values to distinguish)

        multi_data_v2 = pd.DataFrame({
            'Ticker': ['L1', 'L2'],
            'MarketCap': [10e9, 10e9],
            'BookValue': [1e9, 2e9], # L1: 50, L2: 100
            'AssetGrowth': [0.1, 0.05], # L1: 50, L2: 100
            'GrossProfit': [1e8, 5e8], # L1: 50, L2: 100
            'TotalAssets': [1e9, 1e9],
            'Momentum': [0.1, 0.1]
        })
        # If weights were equal, both would have scores relative to their ranks.
        # Let's use a more complex one.
        multi_data_v3 = pd.DataFrame({
            'Ticker': ['L1', 'L2'],
            'MarketCap': [10e9, 10e9],
            'BookValue': [2e9, 1e9], # L1: 100, L2: 50 (Value)
            'AssetGrowth': [0.1, 0.05], # L1: 50, L2: 100 (Investment)
            'GrossProfit': [1e8, 5e8], # L1: 50, L2: 100 (Profitability)
            'TotalAssets': [1e9, 1e9],
            'Momentum': [0.1, 0.1]
        })
        scored_v3 = calculate_scores(multi_data_v3)
        # L1 (Large): 0.2*100 + 0.5*50 + 0.3*50 = 20 + 25 + 15 = 60
        # L2 (Large): 0.2*50 + 0.5*100 + 0.3*100 = 10 + 50 + 30 = 90
        l1_score = scored_v3.loc[scored_v3['Ticker']=='L1', 'VIP_Score'].values[0]
        l2_score = scored_v3.loc[scored_v3['Ticker']=='L2', 'VIP_Score'].values[0]
        self.assertEqual(l1_score, 60.0)
        self.assertEqual(l2_score, 90.0)

        # Same data but small cap
        multi_data_v3['MarketCap'] = 1e9
        scored_v3_small = calculate_scores(multi_data_v3)
        # L1 (Small): (100 + 50 + 50) / 3 = 200/3 = 66.66...
        # L2 (Small): (50 + 100 + 100) / 3 = 250/3 = 83.33...
        l1_score_s = scored_v3_small.loc[scored_v3_small['Ticker']=='L1', 'VIP_Score'].values[0]
        # Rounded to 1 decimal: 66.7
        self.assertEqual(l1_score_s, 66.7)

    def test_weighting_type(self):
        data = pd.DataFrame({
            'Ticker': ['S1', 'L1'],
            'MarketCap': [1e9, 10e9],
            'BookValue': [5e8, 5e9],
            'AssetGrowth': [0.1, 0.1],
            'GrossProfit': [1e8, 1e9],
            'TotalAssets': [5e8, 5e9],
            'Momentum': [0.1, 0.1]
        })
        scored = calculate_scores(data)
        self.assertEqual(scored.loc[scored['Ticker']=='S1', 'Weighting_Type'].values[0], "Pondération 1/N")
        self.assertEqual(scored.loc[scored['Ticker']=='L1', 'Weighting_Type'].values[0], "Pondération Custom")
        
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
