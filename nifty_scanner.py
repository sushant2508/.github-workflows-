# ===============================================================
# NIFTY50 ELITE LONG + SHORT SWING SCANNER
# ATR BASED STOP LOSS + ATR BASED TARGET
# ---------------------------------------------------------------
# HIGH PROBABILITY ONLY
# ===============================================================

import yfinance as yf
import pandas as pd
import numpy as np
from ta.trend import EMAIndicator, ADXIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator
from datetime import datetime

# ===============================================================
# CONFIG
# ===============================================================

CAPITAL = 1000000            # 10 lakh
RISK_PER_TRADE = 0.01       # 1%
MAX_TRADES = 5
MIN_SCORE = 88

# ATR MULTIPLIERS
SL_ATR = 1.5                # stop = 1.5 ATR
TP_ATR = 4.5                # target = 4.5 ATR (1:3 RR)

# ===============================================================
# NIFTY50
# ===============================================================

stocks = [
    "RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS",
    "ITC.NS","LT.NS","SBIN.NS","BHARTIARTL.NS","KOTAKBANK.NS",
    "HINDUNILVR.NS","AXISBANK.NS","ASIANPAINT.NS","MARUTI.NS",
    "BAJFINANCE.NS","SUNPHARMA.NS","WIPRO.NS","ULTRACEMCO.NS",
    "TITAN.NS","NESTLEIND.NS","NTPC.NS","POWERGRID.NS",
    "TATAMOTORS.NS","M&M.NS","HCLTECH.NS","TECHM.NS",
    "ADANIENT.NS","ADANIPORTS.NS","JSWSTEEL.NS","COALINDIA.NS",
    "INDUSINDBK.NS","BAJAJFINSV.NS","ONGC.NS","GRASIM.NS",
    "DRREDDY.NS","BPCL.NS","HEROMOTOCO.NS","DIVISLAB.NS",
    "BRITANNIA.NS","CIPLA.NS","EICHERMOT.NS","TATASTEEL.NS",
    "HDFCLIFE.NS","SBILIFE.NS","UPL.NS","APOLLOHOSP.NS",
    "BAJAJ-AUTO.NS","SHRIRAMFIN.NS","HINDALCO.NS","PIDILITIND.NS"
]

# ===============================================================
# NIFTY INDEX
# ===============================================================

try:
    nifty = yf.download("^NSEI", period="6mo", interval="1d", auto_adjust=True)
    nifty_ret = (nifty["Close"].iloc[-1] / nifty["Close"].iloc[-21]) - 1
except:
    nifty_ret = 0

# ===============================================================
# ANALYSIS
# ===============================================================

def scan(symbol):
    try:
        df = yf.download(symbol, period="1y", interval="1d", auto_adjust=True)

        if len(df) < 220:
            return None

        close = df["Close"]

        # -------------------------------------------------------
        # INDICATORS
        # -------------------------------------------------------

        df["EMA20"] = EMAIndicator(close,20).ema_indicator()
        df["EMA50"] = EMAIndicator(close,50).ema_indicator()
        df["EMA200"] = EMAIndicator(close,200).ema_indicator()

        df["RSI"] = RSIIndicator(close,14).rsi()

        macd = MACD(close)
        df["MACD"] = macd.macd()
        df["MACD_SIGNAL"] = macd.macd_signal()

        df["ADX"] = ADXIndicator(
            df["High"], df["Low"], close, 14
        ).adx()

        df["ATR"] = AverageTrueRange(
            df["High"], df["Low"], close, 14
        ).average_true_range()

        df["OBV"] = OnBalanceVolumeIndicator(
            close, df["Volume"]
        ).on_balance_volume()

        df["VOL20"] = df["Volume"].rolling(20).mean()

        # -------------------------------------------------------
        # WEEKLY FILTER
        # -------------------------------------------------------

        weekly = df.resample("W").last()

        weekly["EMA20W"] = EMAIndicator(
            weekly["Close"],20
        ).ema_indicator()

        weekly["EMA50W"] = EMAIndicator(
            weekly["Close"],50
        ).ema_indicator()

        x = df.iloc[-1]
        p = df.iloc[-2]
        w = weekly.iloc[-1]

        price = x["Close"]
        atr = x["ATR"]

        rs = ((price / df["Close"].iloc[-21]) - 1) - nifty_ret

        # =======================================================
        # LONG SCORE
        # =======================================================

        long_score = 0

        if x["EMA20"] > x["EMA50"] > x["EMA200"]:
            long_score += 20

        if w["EMA20W"] > w["EMA50W"]:
            long_score += 15

        if 58 < x["RSI"] < 68:
            long_score += 10

        if x["MACD"] > x["MACD_SIGNAL"]:
            long_score += 10

        if x["ADX"] > 28:
            long_score += 10

        if price > p["High"]:
            long_score += 15

        if x["Volume"] > x["VOL20"] * 1.8:
            long_score += 10

        if x["OBV"] > p["OBV"]:
            long_score += 10

        if rs > 0.03:
            long_score += 15

        # =======================================================
        # SHORT SCORE
        # =======================================================

        short_score = 0

        if x["EMA20"] < x["EMA50"] < x["EMA200"]:
            short_score += 20

        if w["EMA20W"] < w["EMA50W"]:
            short_score += 15

        if 32 < x["RSI"] < 42:
            short_score += 10

        if x["MACD"] < x["MACD_SIGNAL"]:
            short_score += 10

        if x["ADX"] > 28:
            short_score += 10

        if price < p["Low"]:
            short_score += 15

        if x["Volume"] > x["VOL20"] * 1.8:
            short_score += 10

        if x["OBV"] < p["OBV"]:
            short_score += 10

        if rs < -0.03:
            short_score += 15

        # =======================================================
        # LONG TRADE
        # =======================================================

        if long_score >= MIN_SCORE and long_score > short_score:

            sl = price - (atr * SL_ATR)
            tp = price + (atr * TP_ATR)

            risk = price - sl
            qty = int((CAPITAL * RISK_PER_TRADE) / risk)

            return {
                "Stock": symbol,
                "Side": "LONG",
                "Entry": round(price,2),
                "SL": round(sl,2),
                "TP": round(tp,2),
                "ATR": round(atr,2),
                "Qty": qty,
                "Score": long_score
            }

        # =======================================================
        # SHORT TRADE
        # =======================================================

        elif short_score >= MIN_SCORE and short_score > long_score:

            sl = price + (atr * SL_ATR)
            tp = price - (atr * TP_ATR)

            risk = sl - price
            qty = int((CAPITAL * RISK_PER_TRADE) / risk)

            return {
                "Stock": symbol,
                "Side": "SHORT",
                "Entry": round(price,2),
                "SL": round(sl,2),
                "TP": round(tp,2),
                "ATR": round(atr,2),
                "Qty": qty,
                "Score": short_score
            }

        return None

    except Exception as e:
        print(f"Error scanning {symbol}: {str(e)}")
        return None

# ===============================================================
# RUN SCANNER
# ===============================================================

results = []

for s in stocks:
    out = scan(s)
    if out:
        results.append(out)

df = pd.DataFrame(results)

# ===============================================================
# OUTPUT
# ===============================================================

output = []
output.append("="*60)
output.append("      NIFTY50 ELITE ATR SWING TRADE SETUPS")
output.append("="*60)
output.append("")

if len(df) == 0:
    output.append("No high probability setups today.")
else:
    df = df.sort_values(by="Score", ascending=False).head(MAX_TRADES)
    output.append(df.to_string(index=False))

output.append("")
output.append(f"Generated: {datetime.now()}")
output.append("="*60)

# Print to console
output_text = "\n".join(output)
print(output_text)

# Save to file
with open("scan_results.txt", "w") as f:
    f.write(output_text)

print("\n✅ Results saved to scan_results.txt")
