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
            'Revenue': [1000, 1000, 1000, 1000],
            'COGS': [200, 200, 200, 200],
            'SGA': [100, 100, 100, 100],
            'InterestExpense': [50, 50, 50, 50],
            'MinorityInterest': [0, 0, 0, 0],
            # Profitability = (1000 - 200 - 100 - 50) / (BookValue + 0) = 650 / BookValue
            # A: 6.5, B: 3.25, C: 2.166, D: 1.625
            # Prof Ranks: 100, 75, 50, 25
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
            'Revenue': [2e9],
            'COGS': [1e9],
            'SGA': [2e8],
            'InterestExpense': [1e8],
            'MinorityInterest': [0],
            'Momentum': [0.1]
        })
        scored_large = calculate_scores(large_cap_data)
        # 0.2 * 100 + 0.5 * 100 + 0.3 * 100 = 100
        self.assertAlmostEqual(scored_large.iloc[0]['VIP_Score'], 100.0)

        # To really test weighting, we need different ranks. Let's use two rows.
        multi_data_v3 = pd.DataFrame({
            'Ticker': ['L1', 'L2'],
            'MarketCap': [10e9, 10e9],
            'BookValue': [2e9, 1e9], # L1: 100, L2: 50 (Value)
            'AssetGrowth': [0.1, 0.05], # L1: 50, L2: 100 (Investment)
            # We want Prof_Rank L1: 50, L2: 100
            'Revenue': [1e9, 2e9],
            'COGS': [0, 0],
            'SGA': [0, 0],
            'InterestExpense': [0, 0],
            'MinorityInterest': [0, 0],
            # Prof L1 = 1e9 / 2e9 = 0.5
            # Prof L2 = 2e9 / 1e9 = 2.0
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
        # Scored output for sample data:
        # Ticker  Momentum_Rank  VIP_Rank  Signal (expected)
        # A       75.0           75.0      Hold
        # B       100.0          100.0     Buy
        # C       50.0           50.0      Hold
        # D       25.0           25.0      Sell

        # Buy Condition: Mom_Rank >= 50 AND VIP_Rank >= 80
        # Sell Condition: VIP_Rank < 50 OR Mom_Rank < 50

        signals = generate_signals(scored, buy_vip_threshold=80, exit_vip_threshold=50)
        
        b_signal = signals.loc[signals['Ticker'] == 'B', 'Signal'].values[0]
        c_signal = signals.loc[signals['Ticker'] == 'C', 'Signal'].values[0]
        d_signal = signals.loc[signals['Ticker'] == 'D', 'Signal'].values[0]
        a_signal = signals.loc[signals['Ticker'] == 'A', 'Signal'].values[0]
        
        self.assertEqual(b_signal, "Buy")
        # For C: VIP_Rank=50, Mom_Rank=50 -> Hold
        self.assertEqual(c_signal, "Hold")
        # For D: VIP_Rank=25 (< 50), Mom_Rank=25 (< 50) -> Sell
        self.assertEqual(d_signal, "Sell")
        # For A: VIP_Rank=75 (< 80), Mom_Rank=75 (>= 50) -> Hold
        self.assertEqual(a_signal, "Hold")

if __name__ == '__main__':
    unittest.main()
