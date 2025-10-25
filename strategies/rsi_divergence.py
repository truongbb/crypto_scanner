import pandas as pd
from indicators.rsi import compute_rsi
from utils.data_fetcher import fetch_ohlcv


def detect_divergence(df: pd.DataFrame):
    df["rsi"] = compute_rsi(df["close"], period=14)

    signals = []
    for i in range(2, len(df)):
        price_now, price_prev = df["close"].iloc[i], df["close"].iloc[i - 2]
        rsi_now, rsi_prev = df["rsi"].iloc[i], df["rsi"].iloc[i - 2]

        # ---- Bullish divergence ----
        if price_now < price_prev and rsi_now > rsi_prev and rsi_now < 20:
            signals.append({
                "type": "bullish",
                "index": i,
                "price": price_now,
                "rsi": rsi_now
            })

        # ---- Bearish divergence ----
        elif price_now > price_prev and rsi_now < rsi_prev and rsi_now > 80:
            signals.append({
                "type": "bearish",
                "index": i,
                "price": price_now,
                "rsi": rsi_now
            })
    return signals


class RsiDivergenceDetector:
    def __init__(self, exchange, timeframe="1h", expiry_behavior="ignore_expired", expiry_limit=10):
        self.exchange = exchange
        self.timeframe = timeframe
        self.expiry_behavior = expiry_behavior
        self.expiry_limit = expiry_limit

    def compute_score(self, signal, current_index, df):
        score = 0

        # Base score: 5 cho phát hiện hợp lệ
        score += 5

        # Càng gần vùng cực trị 20/80 thì điểm càng cao
        if signal["type"] == "bullish":
            if signal["rsi"] < 20:
                score += 3
        elif signal["type"] == "bearish":
            if signal["rsi"] > 80:
                score += 3

        # === Kiểm tra hiệu lực tín hiệu (đã nâng cấp) ===
        idx = signal["index"]
        levels = self.calculate_trade_levels(df, signal)
        entry, sl, tp = levels["entry"], levels["stop_loss"], levels["take_profit"]

        # Tính mức 2R
        r_value = abs(entry - sl)
        tp_2r = entry + 2 * r_value if signal["type"] == "bullish" else entry - 2 * r_value

        # 1️⃣ Hết hiệu lực nếu quá số nến quy định
        if (current_index - idx) > self.expiry_limit:
            if self.expiry_behavior == "ignore_expired":
                return None
            elif self.expiry_behavior == "penalize_expired":
                score -= 2
        else:
            # 2️⃣ Hết hiệu lực nếu đạt ≥ 2R
            recent_window = df.iloc[idx + 1: min(len(df), idx + self.expiry_limit + 1)]
            if not recent_window.empty:
                if signal["type"] == "bullish":
                    if (recent_window["high"] >= tp_2r).any():
                        return None
                else:
                    if (recent_window["low"] <= tp_2r).any():
                        return None

        return round(score, 1)

    def calculate_trade_levels(self, df, signal):
        """
        Tính entry, stop loss, take profit từ cụm 3 nến gần nhất quanh tín hiệu
        """
        idx = signal["index"]
        cluster = df.iloc[max(0, idx - 2): idx + 1]

        entry = (cluster["high"].max() + cluster["low"].min()) / 2

        if signal["type"] == "bullish":
            stop_loss = cluster["low"].min()
            take_profit = entry + (entry - stop_loss) * 2
        else:  # bearish
            stop_loss = cluster["high"].max()
            take_profit = entry - (stop_loss - entry) * 2

        return {
            "entry": entry,
            "stop_loss": stop_loss,
            "take_profit": take_profit
        }

    def analyze_symbol(self, symbol):
        try:
            df = fetch_ohlcv(self.exchange, symbol, self.timeframe)
            signals = detect_divergence(df)
            if not signals:
                return None

            latest_index = len(df) - 1
            best_signal = None
            best_score = -999

            for s in signals:
                score = self.compute_score(s, latest_index, df)
                if score is None:
                    continue
                if score > best_score:
                    best_signal = s
                    best_score = score

            if best_signal:
                levels = self.calculate_trade_levels(df, best_signal)
                return {
                    "symbol": symbol,
                    "type": best_signal["type"],
                    "price": best_signal["price"],
                    "rsi": best_signal["rsi"],
                    "score": best_score,
                    **levels
                }
        except Exception as e:
            if "does not have market symbol" not in str(e):
                print(f"Lỗi fetch {symbol}: {e}")
            return None
