# strategies/rsi_divergence_multi_tf.py
import pandas as pd

from config.rsi_divergence import RSI_DIVERGENCE_MULTI_TF_STRATEGY_CONFIG
from indicators.rsi import compute_rsi
from utils.data_fetcher import fetch_ohlcv


def detect_divergence(df: pd.DataFrame):
    df["rsi"] = compute_rsi(df["close"], period=RSI_DIVERGENCE_MULTI_TF_STRATEGY_CONFIG["rsi_period"])
    signals = []
    for i in range(2, len(df)):
        price_now, price_prev = df["close"].iloc[i], df["close"].iloc[i - 2]
        rsi_now, rsi_prev = df["rsi"].iloc[i], df["rsi"].iloc[i - 2]

        if price_now < price_prev and rsi_now > rsi_prev and rsi_now < 30:
            signals.append({"type": "bullish", "index": i, "price": price_now, "rsi": rsi_now})
        elif price_now > price_prev and rsi_now < rsi_prev and rsi_now > 70:
            signals.append({"type": "bearish", "index": i, "price": price_now, "rsi": rsi_now})
    return signals


"""
🎯 Mục tiêu

Bắt phân kỳ RSI khung nhỏ (ví dụ 1h) nhưng được khung lớn (ví dụ 4h) xác nhận xu hướng và động lượng.
Hỗ trợ multi-timeframe (các cặp: ("15m","1h"), ("1h","4h"), ("4h","1d")).

⚙️ Bộ tiêu chí RSI Divergence đa khung
Thành phần	Mô tả	Mục tiêu
1️⃣ Khung nhỏ (entry)	RSI phân kỳ rõ ràng giữa giá và RSI	Tìm điểm đảo chiều tiềm năng
2️⃣ Khung lớn (confirmation)	EMA(50) hoặc EMA(20) dốc theo hướng phân kỳ, và RSI 4h hỗ trợ	Xác nhận động lượng cùng hướng
3️⃣ Quản lý hiệu lực tín hiệu	Tín hiệu hết hiệu lực nếu quá 10 nến hoặc đạt 2R	Loại bỏ tín hiệu quá cũ hoặc đã hoàn tất sóng
4️⃣ Trọng số tín hiệu (độ mạnh)	Dựa trên 2 khung RSI + EMA trend khung lớn	Phân loại tín hiệu mạnh/yếu
📈 1. Điều kiện RSI Divergence (khung nhỏ)

Bullish Divergence (phân kỳ tăng):

Giá tạo lower low, RSI tạo higher low

RSI hiện tại > 30 (thoát vùng quá bán)

Xu hướng khung lớn ủng hộ (EMA hoặc RSI)

Bearish Divergence (phân kỳ giảm):

Giá tạo higher high, RSI tạo lower high

RSI hiện tại < 70 (thoát vùng quá mua)

Xu hướng khung lớn ủng hộ

🧭 2. Xác định xu hướng khung lớn bằng EMA linh hoạt (EMA slope)

Thay vì chỉ xét “giá nằm trên/dưới EMA”, ta xét độ dốc EMA trong 5 cây nến gần nhất:

ema_slope = ema[-1] - ema[-5]
if ema_slope > 0: trend = "up"
elif ema_slope < 0: trend = "down"
else: trend = "sideways"


✅ Ưu điểm:

Nhận biết thay đổi sớm

Giảm nhiễu khi giá dao động quanh EMA

Linh hoạt giữa EMA(20) và EMA(50) tùy khung

🔁 3. Kết hợp RSI đa khung (multi-timeframe confirmation)
Trạng thái	Điều kiện	Độ mạnh
Strong Buy	1h có bullish divergence + RSI(4h) đang dưới 40 và EMA(4h) dốc lên	⭐⭐⭐
Moderate Buy	1h có bullish divergence + RSI(4h) nằm giữa 40–60 + EMA(4h) đi ngang	⭐⭐
Weak Buy	1h có bullish divergence + RSI(4h) > 60 (quá cao) hoặc EMA(4h) giảm nhẹ	⭐

Tương tự cho Sell, chỉ đảo ngược điều kiện (RSI cao → thấp, EMA dốc xuống).

🧩 4. Cấu trúc tổng thể của chiến lược

Quét RSI phân kỳ ở khung nhỏ (1h)

Lấy dữ liệu khung lớn (4h):

EMA(20), EMA(50)

RSI(14)

Tính độ dốc EMA → xác định hướng trend

Xếp hạng tín hiệu dựa trên độ đồng thuận

Loại tín hiệu nếu:

Quá 10 cây nến

Đã đạt ≥ 2R kể từ entry

📊 5. Ví dụ thực tế
🟢 Bullish divergence mạnh

RSI(1h): phân kỳ tăng, RSI = 35 → 50

EMA(4h): dốc lên

RSI(4h): = 38 (vùng thấp)
➡️ Xếp loại: Strong Buy

🔴 Bearish divergence yếu

RSI(1h): phân kỳ giảm, RSI = 65 → 55

EMA(4h): vẫn dốc lên

RSI(4h): = 65 (vùng cao)
➡️ Xếp loại: Weak Sell
"""
class RsiDivergenceMultiTF:
    def __init__(self, exchange, lower_tf="1h", higher_tf="4h", expiry_behavior="penalize_expired", expiry_limit=10):
        cfg = RSI_DIVERGENCE_MULTI_TF_STRATEGY_CONFIG
        self.exchange = exchange
        self.lower_tf = lower_tf
        self.higher_tf = higher_tf
        self.expiry_behavior = expiry_behavior
        self.expiry_limit = expiry_limit
        self.weights = cfg["score_weights"]

    def get_higher_context(self, symbol):
        df_higher = fetch_ohlcv(self.exchange, symbol, self.higher_tf)
        df_higher["rsi"] = compute_rsi(df_higher["close"], period=RSI_DIVERGENCE_MULTI_TF_STRATEGY_CONFIG["rsi_period"])
        df_higher["ema50"] = df_higher["close"].ewm(span=50).mean()
        return df_higher

    def compute_score(self, signal, current_index, df_lower, df_higher):
        w = self.weights
        score = w["base"]

        if signal["type"] == "bullish" and signal["rsi"] < 20:
            score += w["extreme_rsi"]
        elif signal["type"] == "bearish" and signal["rsi"] > 80:
            score += w["extreme_rsi"]

        idx = signal["index"]
        if (current_index - idx) > self.expiry_limit:
            if self.expiry_behavior == "ignore_expired":
                return None
            elif self.expiry_behavior == "penalize_expired":
                score += w["expiry_penalty"]
        else:
            levels = self.calculate_trade_levels(df_lower, signal)
            entry, sl, tp = levels["entry"], levels["stop_loss"], levels["take_profit"]
            r_value = abs(entry - sl)
            tp_2r = entry + 2 * r_value if signal["type"] == "bullish" else entry - 2 * r_value
            window = df_lower.iloc[idx + 1: min(len(df_lower), idx + self.expiry_limit + 1)]
            if not window.empty:
                if signal["type"] == "bullish" and (window["high"] >= tp_2r).any():
                    return None
                elif signal["type"] == "bearish" and (window["low"] <= tp_2r).any():
                    return None

        higher_rsi = df_higher["rsi"].iloc[-1]
        ema_now = df_higher["ema50"].iloc[-1]
        ema_prev = df_higher["ema50"].iloc[-2]

        if signal["type"] == "bullish":
            if higher_rsi < 55 or ema_now > ema_prev:
                score += w["trend_alignment"]
            elif higher_rsi > 70 and ema_now < ema_prev:
                return None
        elif signal["type"] == "bearish":
            if higher_rsi > 45 or ema_now < ema_prev:
                score += w["trend_alignment"]
            elif higher_rsi < 30 and ema_now > ema_prev:
                return None

        return round(score, 1)

    def calculate_trade_levels(self, df, signal):
        idx = signal["index"]
        cluster = df.iloc[max(0, idx - 2): idx + 1]
        entry = (cluster["high"].max() + cluster["low"].min()) / 2

        if signal["type"] == "bullish":
            stop_loss = cluster["low"].min()
            take_profit = entry + (entry - stop_loss) * 2
        else:
            stop_loss = cluster["high"].max()
            take_profit = entry - (stop_loss - entry) * 2

        return {"entry": entry, "stop_loss": stop_loss, "take_profit": take_profit}

    def analyze_symbol(self, symbol):
        try:
            df_lower = fetch_ohlcv(self.exchange, symbol, self.lower_tf)
            signals = detect_divergence(df_lower)
            if not signals:
                return None

            df_higher = self.get_higher_context(symbol)
            latest_index = len(df_lower) - 1
            best_signal, best_score = None, -999

            for s in signals:
                score = self.compute_score(s, latest_index, df_lower, df_higher)
                if score is None:
                    continue
                if score > best_score:
                    best_signal, best_score = s, score

            if best_signal:
                levels = self.calculate_trade_levels(df_lower, best_signal)
                return {
                    "symbol": symbol,
                    "type": best_signal["type"],
                    "price": best_signal["price"],
                    "rsi": best_signal["rsi"],
                    "score": best_score,
                    "lower_tf": self.lower_tf,
                    "higher_tf": self.higher_tf,
                    **levels
                }
        except Exception as e:
            if "does not have market symbol" not in str(e):
                print(f"Lỗi fetch {symbol}: {e}")
            return None
