# strategies/rsi_confluence.py
import time
from typing import Optional, Dict

from config.rsi_confluence import RSI_CONFLUENCE_CONFIG
from indicators.rsi import compute_rsi
from utils.data_fetcher import _ohlcv_to_df, _safe_fetch_ohlcv, _aggregate_n_days_to_n_days


def analyze_symbol(exchange, symbol: str, rate_limit_sleep: float = None) -> Optional[Dict]:
    """
    Kiểm tra 1 symbol xem có thỏa điều kiện RSI đa khung hợp lưu không.
    Trả về dict:
      {'symbol': str, 'signal': 'LONG'|'SHORT', 'rsi': {'1h', '4h', '1d', '3d'}, 'matched': int}
    Hoặc None nếu không thỏa.
    """
    if rate_limit_sleep is None:
        rate_limit_sleep = RSI_CONFLUENCE_CONFIG.get("rate_limit_sleep", 0.25)

    try:
        rsi_values = {}
        match_count_long = 0
        match_count_short = 0

        # H1, H4, D1
        for tf in ['1h', '4h', '1d']:
            limit = RSI_CONFLUENCE_CONFIG["rsi_length"] + 5
            ohlcv = _safe_fetch_ohlcv(exchange, symbol, timeframe=tf, limit=limit)
            if not ohlcv or len(ohlcv) < RSI_CONFLUENCE_CONFIG["rsi_length"]:
                rsi_values[tf] = None
                continue
            df = _ohlcv_to_df(ohlcv)
            rsi = compute_rsi(df['close'], RSI_CONFLUENCE_CONFIG["rsi_length"]).iloc[-1]
            rsi_values[tf] = float(round(rsi, 2))
            if rsi <= RSI_CONFLUENCE_CONFIG["rsi_long_threshold"]:
                match_count_long += 1
            if rsi >= RSI_CONFLUENCE_CONFIG["rsi_short_threshold"]:
                match_count_short += 1
            time.sleep(rate_limit_sleep)

        # D3: thử '3d' trực tiếp, nếu không có thì aggregate từ 1d
        tf_3d_value = None
        try:
            ohlcv_3d = _safe_fetch_ohlcv(exchange, symbol, timeframe='3d',
                                         limit=RSI_CONFLUENCE_CONFIG["rsi_length"] + 5)
        except Exception:
            ohlcv_3d = None

        if ohlcv_3d and len(ohlcv_3d) >= RSI_CONFLUENCE_CONFIG["rsi_length"]:
            df3 = _ohlcv_to_df(ohlcv_3d)
            tf_3d_value = float(round(compute_rsi(df3['close'], RSI_CONFLUENCE_CONFIG["rsi_length"]).iloc[-1], 2))
        else:
            ohlcv_1d = _safe_fetch_ohlcv(exchange, symbol, timeframe='1d',
                                         limit=(RSI_CONFLUENCE_CONFIG["rsi_length"] + 5) * 3)
            if ohlcv_1d and len(ohlcv_1d) >= RSI_CONFLUENCE_CONFIG["rsi_length"] * 3:
                df1d = _ohlcv_to_df(ohlcv_1d)
                df3d = _aggregate_n_days_to_n_days(df1d, n_days=3)
                if len(df3d) >= RSI_CONFLUENCE_CONFIG["rsi_length"]:
                    tf_3d_value = float(round(compute_rsi(df3d['close'], RSI_CONFLUENCE_CONFIG["rsi_length"]).iloc[-1], 2))

        rsi_values['3d'] = tf_3d_value
        if tf_3d_value is not None:
            if tf_3d_value <= RSI_CONFLUENCE_CONFIG["rsi_long_threshold"]:
                match_count_long += 1
            if tf_3d_value >= RSI_CONFLUENCE_CONFIG["rsi_short_threshold"]:
                match_count_short += 1

        # Decide signal
        signal = None
        matched = 0
        if match_count_long >= RSI_CONFLUENCE_CONFIG["min_match"]:
            signal = 'LONG'
            matched = match_count_long
        elif match_count_short >= RSI_CONFLUENCE_CONFIG["min_match"]:
            signal = 'SHORT'
            matched = match_count_short

        if signal:
            return {
                'symbol': symbol,
                'signal': signal,
                'rsi': {
                    '1h': rsi_values.get('1h'),
                    '4h': rsi_values.get('4h'),
                    '1d': rsi_values.get('1d'),
                    '3d': rsi_values.get('3d'),
                },
                'matched': matched
            }
    except Exception:
        # im lặng và trả None để worker có thể tiếp tục
        return None

    return None
