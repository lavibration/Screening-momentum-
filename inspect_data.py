import yfinance as yf
ticker = "MC.PA"
stock = yf.Ticker(ticker)
print("--- BALANCE SHEET ---")
print(stock.balance_sheet.index.tolist())
print("\n--- FINANCIALS ---")
print(stock.financials.index.tolist())
