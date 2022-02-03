import time
import pyupbit
import datetime
import numpy as np

access = ""
secret = ""

coin_Fname = "KRW-STEEM"
coin_Sname = "STEEM"


def get_best_K():
    best_ror = 0
    best_k = 0.5
    for k in np.arange(0.1, 1.0, 0.1):
        df = pyupbit.get_ohlcv("KRW-STEEM", count=7)
        df['range'] = (df['high'] - df['low']) * k
        df['target'] = df['open'] + df['range'].shift(1)

        df['ror'] = np.where(df['high'] > df['target'],
                             df['close'] / df['target'],
                             1)

        ror = df['ror'].cumprod()[-2]

        if best_ror < ror:
            best_ror = ror
            best_k = k

    return best_k

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_ma15(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)
    ma15 = df['close'].rolling(15).mean().iloc[-1]
    return ma15

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("Autotrade start")
best_k = get_best_K()

# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time(coin_Fname)
        end_time = start_time + datetime.timedelta(days=1)

        if start_time < now < end_time - datetime.timedelta(seconds=10):
            target_price = get_target_price(coin_Fname, best_k)
            ma15 = get_ma15(coin_Fname)
            current_price = get_current_price(coin_Fname)
            if target_price < current_price and ma15 < current_price:
                krw = get_balance("KRW")
                if krw > 5000:
                    upbit.buy_market_order(coin_Fname, krw*0.9995)
        else:
            btc = get_balance(coin_Sname)
            if btc > (5000 / get_current_price(coin_Fname)):
                upbit.sell_market_order(coin_Fname, btc*0.9995)
                best_k = get_best_K() # k값 하루에 한번씩 업데이트
        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)
