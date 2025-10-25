import ccxt
import pandas as pd

def get_symbols_from_bybit(quote="USDT"):
    """Lấy danh sách các cặp coin/USDT từ sàn Bybit"""
    exchange = ccxt.bybit()
    markets = exchange.load_markets()
    symbols = [
        symbol for symbol in markets
        if quote in symbol and markets[symbol]["active"] and "USDT" in symbol
    ]
    return symbols

def fetch_ohlcv(symbol, timeframe="1h", limit=500):
    exchange = ccxt.binance()
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(
            ohlcv,
            columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df
    except Exception as e:
        print(f"Lỗi fetch {symbol}: {e}")
        return pd.DataFrame()
