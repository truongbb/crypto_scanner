import concurrent.futures
from typing import Dict, Any

from ccxt import binance

from config.rsi_confluence import RSI_CONFLUENCE_CONFIG
from strategies.rsi_confluence import analyze_symbol
from utils.market_selector import get_top_binance_symbols
from utils.print_signals import print_top_signals

def _normalize_confluence_result(item: Dict[str, Any], exchange) -> Dict[str, Any]:
    sym = item.get('symbol')
    signal = item.get('signal', '').upper()
    matched = item.get('matched', 0)
    typ = 'bullish' if signal == 'LONG' else ('bearish' if signal == 'SHORT' else '')

    entry = 0.0
    try:
        ticker = exchange.fetch_ticker(sym)
        entry = float(ticker.get('last') or ticker.get('close') or 0.0)
    except Exception:
        entry = 0.0

    score = float(matched)
    rsi_vals = [v for v in item.get('rsi', {}).values() if v is not None]
    rsi_avg = float(sum(rsi_vals) / len(rsi_vals)) if rsi_vals else 0.0

    return {
        "symbol": sym,
        "type": typ,
        "score": score,
        "entry": entry,
        "stop_loss": 0.0,
        "take_profit": 0.0,
        "rsi": rsi_avg,
        "lower_tf": "multi",
        "higher_tf": "multi",
    }



def main_rsi_confluence_signals():
    print("🚀 Đang khởi động hệ thống quét RSI ĐA KHUNG HỢP LƯU trên Binance...")

    # ==== 1️⃣ Lấy danh sách coin trên Binance (không đổi) ====
    symbols = get_top_binance_symbols(limit=150, source="coingecko")
    print(f"✅ Tìm thấy {len(symbols)} cặp coin hợp lệ (đã loại stablecoin).")

    # ==== 2️⃣ Khởi tạo exchange (ccxt instance) ====
    exchange = binance()

    list_all = []

    print("\n🔎 Chạy scanner: RSI ĐA KHUNG HỢP LƯU (H1,H4,D1,D3)...")

    # 3) Multithread: gọi analyze_symbol cho từng symbol
    results = []
    rate_limit_sleep = RSI_CONFLUENCE_CONFIG.get("rate_limit_sleep", 0.25)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_symbol = {
            executor.submit(analyze_symbol, exchange, symbol, rate_limit_sleep): symbol for symbol in symbols
        }
        for fut in concurrent.futures.as_completed(future_to_symbol):
            sym = future_to_symbol[fut]
            try:
                res = fut.result()
                if res:
                    results.append(res)
            except Exception as e:
                # in lỗi tối thiểu, tiếp tục
                print(f"Lỗi worker cho {sym}: {e}")
                continue

    print(f"→ Scanner trả về {len(results)} cặp phù hợp.")

    if not results:
        print("⚠️ Không có tín hiệu nào được phát hiện.")
        return

    # 4) Chuẩn hoá, giữ tín hiệu mạnh nhất mỗi symbol và in
    normalized = []
    for it in results:
        normalized.append(_normalize_confluence_result(it, exchange))

    best_per_symbol = {}
    for s in normalized:
        sym = s["symbol"]
        if sym not in best_per_symbol or (s["score"] is not None and s["score"] > best_per_symbol[sym]["score"]):
            best_per_symbol[sym] = s

    top_signals = sorted(best_per_symbol.values(), key=lambda x: x["score"], reverse=True)[:20]
    print_top_signals(top_signals)



    # try:
    #     # scan_rsi_confluence_signals có thể nhận api keys nếu cần nhưng public OHLCV thường đủ
    #     scan_results = scan_rsi_confluence_signals(api_key=None, secret=None, max_symbols=len(symbols))
    #     print(f"→ Scanner trả về {len(scan_results)} cặp phù hợp.")
    #     # Chuẩn hoá kết quả thành format main/print_signals
    #     for it in scan_results:
    #         norm = _normalize_confluence_result(it, exchange)
    #         list_all.append(norm)
    # except Exception as e:
    #     print(f"Lỗi khi chạy scanner confluence: {e}")
    #
    # # ==== 4️⃣ Nếu không có tín hiệu nào ====
    # if not list_all:
    #     print("\n⚠️ Không phát hiện tín hiệu nào ở bất kỳ khung nào.")
    #     return
    #
    # # ==== 5️⃣ Lọc: chỉ giữ tín hiệu mạnh nhất cho mỗi coin (symbol) ====
    # best_per_symbol = {}
    # for s in list_all:
    #     sym = s["symbol"]
    #     # nếu chưa có hoặc score hiện tại lớn hơn score lưu trước đó -> cập nhật
    #     if sym not in best_per_symbol or (s["score"] is not None and s["score"] > best_per_symbol[sym]["score"]):
    #         best_per_symbol[sym] = s
    #
    # top_signals = sorted(best_per_symbol.values(), key=lambda x: x["score"], reverse=True)[:20]
    #
    # # ==== 6️⃣ In bảng đẹp ====
    # print_top_signals(top_signals)
