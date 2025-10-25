# utils/print_signals.py
from tabulate import tabulate


def print_top_signals(signals, top_n=20):
    """
    signals: list[dict] như [
        {'symbol': 'BTC/USDT', 'type': 'bullish', 'score': 6.0,
         'entry': 109040.9, 'stop_loss': 108668.0, 'take_profit': 109786.7,
         'rsi': 42.1, 'timeframes': '1h-4h'},
        ...
    ]
    """
    if not signals:
        print("Không có tín hiệu để hiển thị.")
        return

    sorted_signals = sorted(signals, key=lambda x: x.get('score', 0), reverse=True)[:top_n]

    table_data = []
    for idx, s in enumerate(sorted_signals, start=1):
        icon = "🟢" if s.get('type', '').lower() == "bullish" else "🔴"

        # Podium icons cho top 3
        # podium = {1: " 🏆", 2: " 🥈", 3: " 🥉"}.get(idx, "")

        # Chuẩn hóa dữ liệu an toàn
        sym = str(s.get('symbol', ''))
        # typ = f"{icon}{s.get('type', '').capitalize()}{podium}"
        typ = f"{icon}{s.get('type', '').capitalize()}"
        score_str = f"{float(s.get('score', 0)):.1f}"
        rsi_str = f"{float(s.get('rsi', 0)):.1f}"
        entry_str = f"{float(s.get('entry', 0)):.4f}"
        sl_str = f"{float(s.get('stop_loss', 0)):.4f}"
        tp_str = f"{float(s.get('take_profit', 0)):.4f}"
        tf_pair = str(s.get('lower_tf', '') + "-" + s.get('higher_tf', ''))  # ví dụ "1h–4h"

        table_data.append([
            sym, tf_pair, typ, score_str, rsi_str, entry_str, sl_str, tp_str
        ])

    headers = ["Cặp", "Khung", "Tín hiệu", "Score", "RSI", "Entry", "SL", "TP"]

    print("\n===== 🏆 TOP {} TÍN HIỆU MẠNH NHẤT (mỗi coin 1 tín hiệu mạnh nhất) =====".format(top_n))
    print(tabulate(
        table_data,
        headers=headers,
        tablefmt="fancy_grid",
        stralign="center",
        numalign="right"
    ))
