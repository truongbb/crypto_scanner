# setting thông số cho chiến lược RSI đa khung hợp lưu
RSI_CONFLUENCE_CONFIG = {
    "rsi_length": 14,
    "timeframes": {
        '1h': '1h',  # H1
        '4h': '4h',  # H4
        '1d': '1d',  # D1
        '3d': '3d'  # D3 (note: ccxt may not support '3d' for all exchanges; implement using since/limit)
    },
    "rsi_long_threshold": 20,
    "rsi_short_threshold": 80,
    "min_match": 3,  # at least 3 out of 4
    "rate_limit_sleep": 0.25
}
