import pandas as pd

def is_bullish_pinbar(open, high, low, close):
    body = abs(close - open)
    tail = close - low if close > open else open - low
    return tail > 2 * body and (close - low) / (high - low) > 0.6

def is_bearish_pinbar(open, high, low, close):
    body = abs(close - open)
    wick = high - close if close < open else high - open
    return wick > 2 * body and (high - close) / (high - low) > 0.6

def is_bullish_engulfing(prev_open, prev_close, open, close):
    return close > open and prev_close < prev_open and close > prev_open and open < prev_close

def is_bearish_engulfing(prev_open, prev_close, open, close):
    return close < open and prev_close > prev_open and close < prev_open and open > prev_close

def is_doji(open, close, high, low):
    return abs(close - open) <= 0.1 * (high - low)

def is_morning_star(candle1, candle2, candle3):
    return (candle1['close'] < candle1['open'] and
            abs(candle2['close'] - candle2['open']) < (candle1['open'] - candle1['close']) * 0.5 and
            candle3['close'] > candle3['open'] and
            candle3['close'] > (candle1['open'] + candle1['close']) / 2)

def is_evening_star(candle1, candle2, candle3):
    return (candle1['close'] > candle1['open'] and
            abs(candle2['close'] - candle2['open']) < (candle1['close'] - candle1['open']) * 0.5 and
            candle3['close'] < candle3['open'] and
            candle3['close'] < (candle1['open'] + candle1['close']) / 2)

def detect_reversal_patterns(df: pd.DataFrame):
    patterns = []
    for i in range(2, len(df)):
        o, h, l, c = df.loc[i, ['open', 'high', 'low', 'close']]
        po, ph, pl, pc = df.loc[i-1, ['open', 'high', 'low', 'close']]
        ppo, pph, ppl, ppc = df.loc[i-2, ['open', 'high', 'low', 'close']]

        pattern = None
        if is_bullish_pinbar(o, h, l, c): pattern = 'bullish_pinbar'
        elif is_bearish_pinbar(o, h, l, c): pattern = 'bearish_pinbar'
        elif is_bullish_engulfing(po, pc, o, c): pattern = 'bullish_engulfing'
        elif is_bearish_engulfing(po, pc, o, c): pattern = 'bearish_engulfing'
        elif is_doji(o, c, h, l): pattern = 'doji'
        elif is_morning_star({'open': ppo, 'close': ppc}, {'open': po, 'close': pc}, {'open': o, 'close': c}): pattern = 'morning_star'
        elif is_evening_star({'open': ppo, 'close': ppc}, {'open': po, 'close': pc}, {'open': o, 'close': c}): pattern = 'evening_star'

        if pattern:
            patterns.append((i, pattern))

    return patterns
