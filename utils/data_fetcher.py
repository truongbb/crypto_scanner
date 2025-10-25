from typing import List

import ccxt
import pandas as pd


def fetch_ohlcv(exchange, symbol, timeframe="1h", limit=100):
    data = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    import pandas as pd
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
    return df


def _safe_fetch_ohlcv(exchange: ccxt.Exchange, symbol: str, timeframe: str, limit: int = 100):
    """
    Wrapper for ccxt.fetch_ohlcv with basic error handling.
    Returns list of ohlcv rows: [timestamp, open, high, low, close, volume]
    """
    try:
        return exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    except Exception:
        # Some exchanges or symbols may not support certain timeframes; return None
        return None


def _ohlcv_to_df(ohlcv: List[List]) -> pd.DataFrame:
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    df = df.dropna(subset=['close']).reset_index(drop=True)
    return df

def _aggregate_n_days_to_n_days(df_daily: pd.DataFrame, n_days: int = 3) -> pd.DataFrame:
    """
    Aggregate daily candles into n_days candles by grouping consecutive rows.
    Output columns: timestamp (end), open (first), high (max), low (min), close (last), volume (sum)
    """
    if n_days <= 1:
        return df_daily.copy()
    # Ensure integer index
    df = df_daily.reset_index(drop=True).copy()
    groups = (df.index // n_days)
    agg = df.groupby(groups).agg({
        'timestamp': 'last',
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).reset_index(drop=True)
    return agg