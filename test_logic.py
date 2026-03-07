import unittest
import pandas as pd
import numpy as np
from scoring_engine import calculate_scores
from strategy import generate_signals

class TestPortfolioLogic(unittest.TestCase):
    def setUp(self):
        # Sample data with some missing values
        self.sample_data = pd.DataFrame({
            'Ticker': ['A', 'B', 'C', 'D'],
            'MarketCap': [10e9, 10e9, 1e9, 1e9],
            'NetIncome': [100, -50, 100, 100],
            'PB': [1.0, 2.0, 1.5, np.nan],
            'PE': [10, 15, np.nan, np.nan],
            'FCF_Yield': [0.05, 0.06, 0.04, 0.03],
            'TotalAssets': [1000, 1100, 1000, np.nan],
            'PrevTotalAssets': [900, 1000, 950, 900],
            'Revenue': [1000, 1000, 1000, 1000],
            'COGS': [200, 200, 200, 200],
            'SGA': [100, 100, 100, 100],
            'InterestExpense': [50, 50, 50, 50],
            'BookEquity': [500, 500, 500, 500],
            'MinorityInterest': [0, 0, 0, 0],
            'Momentum': [0.1, 0.2, 0.05, -0.1]
        })

    def test_value_composite(self):
        scored = calculate_scores(self.sample_data)
        # B has negative Net Income, PE Rank should be 0
        b_pe_rank = scored.loc[scored['Ticker'] == 'B', 'PE_Rank_Raw'].values[0]
        self.assertEqual(b_pe_rank, 0)

        # D has missing PB and PE, Value_Rank should be based only on FCF_Yield_Rank
        d_val_rank = scored.loc[scored['Ticker'] == 'D', 'Value_Rank'].values[0]
        self.assertFalse(pd.isna(d_val_rank))

        # Check Value Reliability
        self.assertEqual(scored.loc[scored['Ticker'] == 'A', 'Rel_V'].values[0], 1.0)
        self.assertEqual(scored.loc[scored['Ticker'] == 'C', 'Rel_V'].values[0], 0.5)

    def test_investment_robustness(self):
        scored = calculate_scores(self.sample_data)
        # D has missing TotalAssets, Inv_Rank should be 50
        d_inv_rank = scored.loc[scored['Ticker'] == 'D', 'Inv_Rank'].values[0]
        self.assertEqual(d_inv_rank, 50)
        self.assertEqual(scored.loc[scored['Ticker'] == 'D', 'Rel_I'].values[0], 0.0)

    def test_profitability_robustness(self):
        data = self.sample_data.copy()
        data.loc[0, 'Revenue'] = np.nan # A has missing Revenue
        scored = calculate_scores(data)
        # A should have Prof_Rank = 50 and Rel_P = 0
        self.assertEqual(scored.loc[scored['Ticker'] == 'A', 'Prof_Rank'].values[0], 50)
        self.assertEqual(scored.loc[scored['Ticker'] == 'A', 'Rel_P'].values[0], 0.0)

    def test_strategy_signals_integrity(self):
        # Create a row with very low reliability
        data = pd.DataFrame({
            'Ticker': ['LOW_REL'],
            'MarketCap': [1e9],
            'NetIncome': [np.nan],
            'PB': [np.nan],
            'PE': [np.nan],
            'FCF_Yield': [np.nan],
            'TotalAssets': [np.nan],
            'PrevTotalAssets': [np.nan],
            'Revenue': [np.nan],
            'COGS': [np.nan],
            'SGA': [np.nan],
            'InterestExpense': [np.nan],
            'BookEquity': [np.nan],
            'MinorityInterest': [np.nan],
            'Momentum': [0.5]
        })
        scored = calculate_scores(data)
        signals = generate_signals(scored)
        self.assertEqual(signals.iloc[0]['Signal'], "Données Insuffisantes")

if __name__ == '__main__':
    unittest.main()
