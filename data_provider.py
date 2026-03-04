import yfinance as yf
import pandas as pd
from typing import List

def get_cac40_tickers() -> List[str]:
    """Returns a list of Yahoo Finance tickers for the CAC 40 components."""
    # Simplified list for initial testing/dev
    return [
        "AC.PA", "AI.PA", "AIR.PA", "ALO.PA", "MT.AS", "CS.PA", "BNP.PA", "EN.PA",
        "CAP.PA", "CA.PA", "ACA.PA", "BN.PA", "DSY.PA", "EDEN.PA", "ENGI.PA", "EL.PA",
        "RMS.PA", "KER.PA", "LR.PA", "OR.PA", "MC.PA", "ML.PA", "ORA.PA", "RI.PA",
        "PUB.PA", "SAF.PA", "SGO.PA", "SAN.PA", "SU.PA", "GLE.PA", "STLAP.PA",
        "STMPA.PA", "TTE.PA", "HO.PA", "VIE.PA", "DG.PA", "WLN.PA"
    ]

def get_cac_mid_tickers() -> List[str]:
    """Returns representative tickers for the CAC Mid 60 components."""
    return [
        "ADP.PA", "AF.PA", "ALTE.PA", "APAM.PA", "ATO.PA", "ELIS.PA", "IPN.PA", "NK.PA",
        "DEC.PA", "NEOEN.PA", "RUI.PA", "SEB.PA", "SK.PA", "SPIE.PA", "VRLA.PA", "VK.PA"
    ]

def get_cac_small_tickers() -> List[str]:
    """Returns representative tickers for the CAC Small components."""
    return [
        "ABCA.PA", "AKW.PA", "BENE.PA", "BIG.PA", "BON.PA", "CRI.PA", "LISI.PA", "MMT.PA",
        "VALN.PA", "GFC.PA", "DBV.PA", "ARG.PA"
    ]

def fetch_data(tickers: List[str]):
    """
    Fetches historical prices and fundamental data for a list of tickers.
    Returns a dictionary of DataFrames.
    """
    data = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            
            # Fundamentals
            bs = stock.balance_sheet
            inc = stock.financials
            
            if bs is None or bs.empty or inc is None or inc.empty:
                print(f"Warning: No fundamental data for {ticker}")
                continue
                
            # History (2 years for 1 year growth + momentum)
            hist = stock.history(period="2y")
            
            data[ticker] = {
                "balance_sheet": bs,
                "financials": inc,
                "history": hist,
                "info": stock.info
            }
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            
    return data

def get_financial_metrics(data_dict):
    """
    Extracts relevant metrics into a single DataFrame for the latest available year.
    """
    rows = []
    for ticker, d in data_dict.items():
        try:
            bs = d["balance_sheet"]
            inc = d["financials"]
            hist = d["history"]
            info = d["info"]
            
            # Get latest available columns (most recent)
            latest_bs_col = bs.columns[0]
            latest_inc_col = inc.columns[0]
            prev_bs_col = bs.columns[1] if len(bs.columns) > 1 else None
            
            # Note: yfinance indices can vary slightly. We use .get or check existence.
            total_assets = bs.loc['Total Assets', latest_bs_col] if 'Total Assets' in bs.index else None
            gross_profit = inc.loc['Gross Profit', latest_inc_col] if 'Gross Profit' in inc.index else None
            
            # Book Value can be 'Stockholders Equity' or 'Total Stockholders Equity'
            book_value = None
            for label in ['Stockholders Equity', 'Total Stockholders Equity']:
                if label in bs.index:
                    book_value = bs.loc[label, latest_bs_col]
                    break
            
            # Asset growth (Investment factor)
            asset_growth = None
            if prev_bs_col is not None and 'Total Assets' in bs.index:
                prev_total_assets = bs.loc['Total Assets', prev_bs_col]
                if prev_total_assets != 0:
                    asset_growth = (total_assets - prev_total_assets) / prev_total_assets
                
            # Momentum: 12m - 1m
            # Price 1 month ago (approx 21 trading days)
            p_now = hist['Close'].iloc[-1]
            p_1m = hist['Close'].iloc[-22] if len(hist) > 22 else None
            # Price 12 months ago (approx 252 trading days)
            p_12m = hist['Close'].iloc[-253] if len(hist) > 253 else None
            
            momentum = None
            if p_1m is not None and p_12m is not None and p_12m != 0:
                momentum = (p_1m - p_12m) / p_12m
                
            rows.append({
                "Ticker": ticker,
                "Name": info.get("longName", ticker),
                "Sector": info.get("sector", "Unknown"),
                "Price": p_now,
                "TotalAssets": total_assets,
                "GrossProfit": gross_profit,
                "BookValue": book_value,
                "AssetGrowth": asset_growth,
                "Momentum": momentum,
                "MarketCap": info.get("marketCap", 0)
            })
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            
    return pd.DataFrame(rows)

if __name__ == "__main__":
    # Test with a few tickers
    test_tickers = ["MC.PA", "ORA.PA", "TTE.PA"]
    raw_data = fetch_data(test_tickers)
    df = get_financial_metrics(raw_data)
    print(df)
