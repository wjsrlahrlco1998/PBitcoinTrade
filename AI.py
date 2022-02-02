import time
import pyupbit
import datetime
import schedule
import numpy as np
from fbprophet import Prophet

access = "your-access"
secret = "your-secret"

coin_Fname = "KRW-STEEM"
coin_Sname = "STEEM"


def get_best_k():
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
    if ror > best_ror:
      best_ror = ror
      best_k = k
  return k

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

predicted_close_price = 0
def predict_price(ticker):
    """Prophet으로 당일 종가 가격 예측"""
    global predicted_close_price
    df = pyupbit.get_ohlcv(ticker, interval="minute60")
    df = df.reset_index()
    df['ds'] = df['index']
    df['y'] = df['close']
    data = df[['ds','y']]
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=24, freq='H')
    forecast = model.predict(future)
    closeDf = forecast[forecast['ds'] == forecast.iloc[-1]['ds'].replace(hour=9)]
    if len(closeDf) == 0:
        closeDf = forecast[forecast['ds'] == data.iloc[-1]['ds'].replace(hour=9)]
    closeValue = closeDf['yhat'].values[0]
    predicted_close_price = closeValue
predict_price(coin_Fname)
schedule.every().hour.do(lambda: predict_price(coin_Fname))

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("Login Success")

print("Target Coin : " + coin_Fname + "(" + coin_Sname + ")")
print("Are you sure you want to edit? (yes : 1, no : 0)")
answer_edit = input()
if answer_edit == 1:
  print("Target Coin Full Name : ")
  coin_Fname = input()
  print("Target Coin Small Name : ")
  coin_Sname = input()

# Best K 값 구하기
k = get_best_k()

print("Autotrade start")

# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time(coin_Fname)
        end_time = start_time + datetime.timedelta(days=1)
        schedule.run_pending()

        if start_time < now < end_time - datetime.timedelta(seconds=10):
            target_price = get_target_price(coin_Fname, k)
            current_price = get_current_price(coin_Fname)
            if target_price < current_price and current_price < predicted_close_price:
                krw = get_balance("KRW")
                if krw > 5000:
                    upbit.buy_market_order(coin_Fname, krw*0.9995)
        else:
            btc = get_balance(coin_Sname)
            min_number = 5000 / get_current_price(coin_Fname)
            if btc > min_number:
                upbit.sell_market_order(coin_Fname, btc*0.9995)
                k = get_best_k() # 종가 처리할 때마다 k 값 업데이트
        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)
