def fetch_ohlcv(exchange, symbol, timeframe="1h", limit=100):
    data = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    import pandas as pd
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
    return df
