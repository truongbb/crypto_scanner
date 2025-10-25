
# setting thoong số cho chiến lược quét RSI phân kỳ
RSI_DIVERGENCE_MULTI_TF_STRATEGY_CONFIG = {
    # === Multi-timeframe settings ===
    "timeframe_pairs": [
        ("15m", "1h"),
        ("1h", "4h"),
        ("4h", "1d"),
    ],

    # === RSI settings ===
    "rsi_period": 14,

    # === Signal validity ===
    "expiry_limit": 10,  # số nến tối đa tín hiệu còn hiệu lực
    "expiry_behavior": "penalize_expired",  # ignore_expired | penalize_expired

    # === Scoring weights ===
    "score_weights": {
        "base": 5,
        "extreme_rsi": 3,
        "trend_alignment": 2,
        "trend_conflict_penalty": -99,  # coi như loại bỏ
        "expiry_penalty": -2,
    },
}
