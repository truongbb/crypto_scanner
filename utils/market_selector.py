import requests
import ccxt

STABLECOINS = {"USDC", "BUSD", "TUSD", "FDUSD", "DAI", "USDP", "USDS"}

def get_top_binance_symbols(limit=150, source="coingecko"):
    """
    Trả về danh sách cặp coin/USDT trên Binance được sắp xếp theo:
    - Market cap toàn cầu (CoinGecko)
    - Hoặc volume 24h trên Binance nếu không gọi API được
    """

    exchange = ccxt.binance()
    markets = exchange.load_markets()

    # ✅ Lọc chỉ các cặp SPOT
    spot_markets = {s: m for s, m in markets.items() if m.get("type") == "spot"}

    if source == "coingecko":
        try:
            print("🌐 Đang lấy dữ liệu market cap từ CoinGecko...")
            resp = requests.get(
                "https://api.coingecko.com/api/v3/coins/markets",
                params={"vs_currency": "usd", "order": "market_cap_desc", "per_page": 250, "page": 1},
                timeout=10
            )
            data = resp.json()
            top_coins = [item["symbol"].upper() for item in data]

            # Ghép với danh sách Binance
            valid = []
            for s, m in spot_markets.items():
                if m["quote"] == "USDT" and m["base"] not in STABLECOINS:
                    if m["base"].upper() in top_coins:
                        valid.append({
                            "symbol": s,
                            "base": m["base"],
                            "market_cap_rank": top_coins.index(m["base"].upper())
                        })

            valid_sorted = sorted(valid, key=lambda x: x["market_cap_rank"])
            print(f"✅ Lấy thành công {len(valid_sorted)} coin theo market cap.")
            return [v["symbol"] for v in valid_sorted[:limit]]

        except Exception as e:
            print(f"⚠️ Lỗi CoinGecko: {e} — chuyển sang sắp xếp theo volume Binance.")
            return get_top_binance_symbols(limit=limit, source="volume")

    # Nếu không dùng coingecko
    elif source == "volume":
        filtered = [
            {"symbol": s, "base": m["base"], "quote": m["quote"], "info": m}
            for s, m in markets.items()
            if m["quote"] == "USDT" and m["base"] not in STABLECOINS
        ]
        sorted_coins = sorted(
            filtered,
            key=lambda x: x["info"].get("info", {}).get("volume", 0) or 0,
            reverse=True
        )
        print(f"✅ Lấy {len(sorted_coins)} coin theo volume Binance.")
        return [c["symbol"] for c in sorted_coins[:limit]]
