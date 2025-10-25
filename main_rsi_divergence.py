# main.py
import concurrent.futures

from config.rsi_divergence import RSI_DIVERGENCE_MULTI_TF_STRATEGY_CONFIG
from strategies.rsi_divergence_multi_tf import RsiDivergenceMultiTF
from utils.market_selector import get_top_binance_symbols
from utils.print_signals import print_top_signals


def process_symbol_wrapper(exchange, symbol, strategy):
    """
    wrapper để gọi analyze_symbol của strategy và trả về kết quả kèm symbol.
    strategy có thể là instance cho 1 cặp lower/higher TF.
    """
    try:
        res = strategy.analyze_symbol(symbol)
        # res là dict hoặc None. Nếu có kết quả, bổ sung symbol đảm bảo nhất quán
        if res:
            # đảm bảo các key chuẩn tên giống main cũ
            out = {
                "symbol": res.get("symbol", symbol),
                "type": res.get("type"),
                "rsi": res.get("rsi"),
                "score": res.get("score"),
                "entry": res.get("entry"),
                "stop_loss": res.get("stop_loss"),
                "take_profit": res.get("take_profit"),
                "rating": res.get("rating", res.get("rating", "")),
                "lower_tf": res.get("lower_tf", strategy.lower_tf),
                "higher_tf": res.get("higher_tf", strategy.higher_tf),
            }
            # In nhanh theo format (vẫn in chi tiết mỗi khi có tín hiệu)
            print(
                f"{out['symbol']} | [{out['type']}] ({out['lower_tf']}→{out['higher_tf']}) "
                f"{out['rating']:^8} score={out['score']:.1f} | RSI={out['rsi']:.1f} | "
                f"Entry={out['entry']:.4f} | SL={out['stop_loss']:.4f} | TP={out['take_profit']:.4f}"
            )
            return out
    except Exception as e:
        if "does not have market symbol" not in str(e):
            # in lỗi chi tiết cho debug
            print(f"Lỗi fetch {symbol}: {e}")
    return None


def main_rsi_divergence():
    print("🚀 Đang khởi động hệ thống quét PHÂN KỲ RSI ĐA KHUNG trên Binance...")

    # ==== 1️⃣ Lấy danh sách coin trên Binance (không đổi) ====
    symbols = get_top_binance_symbols(limit=150, source="coingecko")
    print(f"✅ Tìm thấy {len(symbols)} cặp coin hợp lệ (đã loại stablecoin).")

    # ==== 2️⃣ Khởi tạo exchange (ccxt instance) ====
    from ccxt import binance
    exchange = binance()

    # ==== 3️⃣ Lặp qua từng cặp timeframe được cấu hình trong config ====
    # Lưu tất cả tín hiệu từ mọi cặp vào list_all
    list_all = []

    tf_pairs = RSI_DIVERGENCE_MULTI_TF_STRATEGY_CONFIG["timeframe_pairs"]
    for lower_tf, higher_tf in tf_pairs:
        print(f"\n🔎 Quét cặp khung: {lower_tf} → {higher_tf} (multithread)...")
        strategy = RsiDivergenceMultiTF(exchange, lower_tf=lower_tf, higher_tf=higher_tf,
                                        expiry_behavior=RSI_DIVERGENCE_MULTI_TF_STRATEGY_CONFIG.get("expiry_behavior",
                                                                                                    "penalize_expired"),
                                        expiry_limit=RSI_DIVERGENCE_MULTI_TF_STRATEGY_CONFIG.get("expiry_limit", 10))

        # đa luồng quét symbols cho cặp timeframe hiện tại
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(process_symbol_wrapper, exchange, symbol, strategy): symbol
                for symbol in symbols
            }
            for fut in concurrent.futures.as_completed(futures):
                r = fut.result()
                if r:
                    results.append(r)

        print(f"→ Hoàn tất quét {lower_tf}→{higher_tf}: tìm được {len(results)} tín hiệu.")
        list_all.extend(results)

    # ==== 4️⃣ Nếu không có tín hiệu nào ====
    if not list_all:
        print("\n⚠️ Không phát hiện tín hiệu nào ở bất kỳ khung nào.")
        return

    # ==== 5️⃣ Lọc: chỉ giữ tín hiệu mạnh nhất cho mỗi coin (symbol) ====
    best_per_symbol = {}
    for s in list_all:
        sym = s["symbol"]
        # nếu chưa có hoặc score hiện tại lớn hơn score lưu trước đó -> cập nhật
        if sym not in best_per_symbol or (s["score"] is not None and s["score"] > best_per_symbol[sym]["score"]):
            best_per_symbol[sym] = s

    top_signals = sorted(best_per_symbol.values(), key=lambda x: x["score"], reverse=True)[:20]

    # ==== 6️⃣ In bảng đẹp ====
    print_top_signals(top_signals)
