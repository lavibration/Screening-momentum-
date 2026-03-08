import yfinance as yf
import pandas as pd
from typing import List
from timing_engine import calculate_volume_profile, get_timing_status

def get_cac40_tickers() -> List[str]:
    """Returns a list of Yahoo Finance tickers for the CAC 40 components."""
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
        "ALTA.PA", "ATE.PA", "AMUN.PA", "ANTIN.PA", "APAM.PA", "ATO.PA", "BEN.PA", "BB.PA",
        "BOL.PA", "CARM.PA", "CO.PA", "COFA.PA", "COV.PA", "AM.PA", "DBG.PA", "ELIOR.PA",
        "ELIS.PA", "ERA.PA", "RF.PA", "EAPI.PA", "ETL.PA", "FNAC.PA", "GTT.PA", "ICAD.PA",
        "IDL.PA", "NK.PA", "ITP.PA", "IPN.PA", "IPS.PA", "DEC.PA", "MERY.PA", "MRN.PA",
        "MMT.PA", "NEX.PA", "NXI.PA", "RUI.PA", "SK.PA", "SCR.PA", "SESG.PA", "SOI.PA",
        "S30.PA", "SOP.PA", "SPIE.PA", "TE.PA", "TFI.PA", "TRI.PA", "VK.PA", "VLA.PA",
        "VRLA.PA", "VIRP.PA", "VLTSA.PA", "MF.PA"
    ]

def get_cac_small_tickers() -> List[str]:
    """Returns representative tickers for the CAC Small components."""
    return [
        "ABVX.PA", "AYV.PA", "FDJU.PA", "FRVIA.PA", "VU.PA", "SOLB.PA", "VIV.PA", "AF.PA",
        "FII.PA", "VCT.PA", "EMEIS.PA", "EXENS.PA", "PLX.PA", "ABCA.PA", "AKW.PA", "ALM.PA",
        "BENE.PA", "BIG.PA", "BON.PA", "CATG.PA", "CRI.PA", "DBV.PA", "EOS.PA", "GFC.PA",
        "LISI.PA", "NRO.PA", "PGU.PA", "ROTH.PA", "SMCP.PA", "VALN.PA"
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
            cf = stock.cashflow
            
            if bs is None or bs.empty or inc is None or inc.empty:
                print(f"Warning: No fundamental data for {ticker}")
                continue
                
            # History (2 years for 1 year growth + momentum)
            hist = stock.history(period="2y")
            
            data[ticker] = {
                "balance_sheet": bs,
                "financials": inc,
                "cashflow": cf,
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
            cf = d["cashflow"]
            hist = d["history"]
            info = d["info"]
            
            # Get latest available columns (most recent)
            latest_bs_col = bs.columns[0]
            latest_inc_col = inc.columns[0]
            latest_cf_col = cf.columns[0] if not cf.empty else None
            prev_bs_col = bs.columns[1] if len(bs.columns) > 1 else None
            
            # 1. VALUE Components
            pb = info.get('priceToBook')
            pe = info.get('trailingPE')
            if pe is None:
                pe = info.get('forwardPE')

            fcf = info.get('freeCashflow')
            mkt_cap = info.get('marketCap', 0)
            fcf_yield = (fcf / mkt_cap) if (fcf is not None and mkt_cap > 0) else None

            net_income = inc.loc['Net Income', latest_inc_col] if 'Net Income' in inc.index else None

            # 2. INVESTMENT Components
            total_assets = bs.loc['Total Assets', latest_bs_col] if 'Total Assets' in bs.index else None
            prev_total_assets = bs.loc['Total Assets', prev_bs_col] if (prev_bs_col is not None and 'Total Assets' in bs.index) else None

            # 3. PROFITABILITY Components
            revenue = inc.loc['Total Revenue', latest_inc_col] if 'Total Revenue' in inc.index else None
            cogs = inc.loc['Cost Of Revenue', latest_inc_col] if 'Cost Of Revenue' in inc.index else None
            sga = inc.loc['Selling General And Administration', latest_inc_col] if 'Selling General And Administration' in inc.index else None
            interest_expense = inc.loc['Interest Expense', latest_inc_col] if 'Interest Expense' in inc.index else None

            # Book Equity + Minority Interests
            book_equity = None
            for label in ['Stockholders Equity', 'Total Stockholders Equity']:
                if label in bs.index:
                    book_equity = bs.loc[label, latest_bs_col]
                    break
            minority_interest = bs.loc['Minority Interest', latest_bs_col] if 'Minority Interest' in bs.index else None
            
            # Momentum: r(12, 1)
            p_now = hist['Close'].iloc[-1]
            p_1m = hist['Close'].iloc[-22] if len(hist) > 22 else None
            p_12m = hist['Close'].iloc[-253] if len(hist) > 253 else None
            
            momentum = None
            if p_1m is not None and p_12m is not None and p_12m != 0:
                momentum = (p_1m - p_12m) / p_12m
                
            perf_12m = None
            if p_12m is not None and p_12m != 0:
                perf_12m = (p_now - p_12m) / p_12m

            # Volume Profile
            poc, vah, val = calculate_volume_profile(hist)
            zone_prix, dist_poc = get_timing_status(p_now, poc, vah, val)

            rows.append({
                "Ticker": ticker,
                "Name": info.get("longName", ticker),
                "Sector": info.get("sector", "Unknown"),
                "Price": p_now,
                "Price_12m": p_12m,
                "Perf_12m": perf_12m,
                "MarketCap": mkt_cap,
                "PB": pb,
                "PE": pe,
                "FCF_Yield": fcf_yield,
                "NetIncome": net_income,
                "TotalAssets": total_assets,
                "PrevTotalAssets": prev_total_assets,
                "Revenue": revenue,
                "COGS": cogs,
                "SGA": sga,
                "InterestExpense": interest_expense,
                "BookEquity": book_equity,
                "MinorityInterest": minority_interest,
                "Momentum": momentum,
                "POC": poc,
                "VAH": vah,
                "VAL": val,
                "Zone_Prix": zone_prix,
                "Dist_POC": dist_poc
            })
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            
    df = pd.DataFrame(rows)
    if not df.empty:
        df['Price'] = df['Price'].round(2)
    return df
