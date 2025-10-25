# Crypto Scanner Bot

## Mục tiêu
Tự động scan các cặp coin (Binance Futures/Spot) để phát hiện tín hiệu kỹ thuật theo từng phương pháp (RSI Divergence, OB, FVG, ...).

## Cài đặt

```bash
pip install -r requirements.txt
python main.py
```

## Cấu trúc project
```
crypto_scanner/
├── data/
├── strategies/
├── indicators/
├── notifier/
├── config/
└── main.py
```
