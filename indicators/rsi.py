import pandas as pd


def compute_rsi(series, period=14):
    """
    Hàm này sử dụng Trung bình Động Đơn giản (Simple Moving Average - SMA),
    được tính bằng phương thức .rolling(period).mean() của pandas.
    """
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def compute_rsi_v2(series: pd.Series, length: int = 14) -> pd.Series:
    """
    Compute RSI using Wilder's smoothing.
    Returns pd.Series aligned with input series.

    Hàm này sử dụng Trung bình Động Hàm mũ (Exponential Moving Average - EMA)
        theo công thức làm mịn của J. Welles Wilder Jr. (người tạo ra chỉ báo RSI).
    Công thức này tương đương với một EMA với hệ số làm mịn $\alpha = \frac{1}{\text{length}}$.
    """
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)

    # Use Wilder's EMA (alpha = 1/length)
    roll_up = up.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    roll_down = down.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()

    rs = roll_up / roll_down
    rsi = 100 - (100 / (1 + rs))
    return rsi
