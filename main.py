import uvicorn
import requests
import time
import json
import math

from statistics import mean
from datetime import datetime, timedelta
from fastapi import FastAPI

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

############## CONST ##############
TRF_FEE = {
    'xrp': 1,
    'xlm': 0.2,
    'doge': 5,
    'bch': 5e-4,
    'ada': 1,
    'eos': 0.1,
    'ltc': 0.02,
    'btc': 5e-4,
    'eth': 1e-2,
}
coin_names = ['xrp', 'xlm', 'doge', 'bch', 'eos', 'ltc', 'btc', 'eth']

BUY_MAKER_RATE = 0.3
SELL_MAKER_RATE = 0.2
KRW_WITHDRAW_FEE = 1000
IDR = 113.4 * 1e6
BANDAR_RATE = 12.60


############## END CONST ##############


def get_sentbe_rate():
    headers = {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoidHJhbnNmZXIiLCJyb2xlIjoidHJhbnNmZXIiLCJzYWx0IjoiWVQjdDQiLCJleHAiOjQ2NjY0MjEwMTJ9.sivUSmZDNkYPL-PTgoN8HrZKjUVE8pE_L5MqqA6cvxk'}
    res = requests.get('https://fx.service.sentbe.com/v1/global_rates', headers=headers).json()
    return float(res['krw_idr']) * 0.9894


def get_hanpass_rate():
    json = {"inputAmount": "1000000", "inputCurrencyCode": "KRW", "toCurrencyCode": "IDR", "toCountryCode": "ID",
            "mtoServiceCenterCode": "", "mtoProviderCode": ""}
    res = requests.post('https://www.hanpass.com/getCost', json=json).json()
    return float(res['exchangeRate'])


SENTBE_RATE = get_sentbe_rate()
HANPASS_RATE = get_hanpass_rate()


def get_coin_price(coin='xrp'):
    indodax_coin_res = requests.get('https://indodax.com/api/ticker/' + coin.lower() + 'idr')
    gopax_coin_res = requests.get('https://api.gopax.co.kr/trading-pairs/' + coin.upper() + '-KRW/ticker')
    coin_buy = int(indodax_coin_res.json()['ticker']['sell'])
    coin_sell = int(gopax_coin_res.json()['ask'])
    return coin_buy, coin_sell


def get_coin_price_v2(indodax_price, coin='xrp'):
    gopax_coin_res = requests.get('https://api.gopax.co.kr/trading-pairs/' + coin.upper() + '-KRW/ticker').json()
    coin_sell = int(gopax_coin_res['ask'])
    coin_sell_vol = round(float(gopax_coin_res['quoteVolume']) / 1e9, 2)

    buy = indodax_price['tickers'][coin.lower() + '_idr']
    coin_buy = int(buy['sell'])
    coin_buy_vol = round(float(buy['vol_idr']) / 1e9, 2)

    return coin_buy, coin_sell, coin_buy_vol, coin_sell_vol


@app.get("/update_ex_rate")
async def update_ex_rate(request: Request):
    SENTBE_RATE = get_sentbe_rate()
    HANPASS_RATE = get_hanpass_rate()
    return {'SENTBE_RATE': SENTBE_RATE, 'HANPASS_RATE': HANPASS_RATE}


@app.get("/get_ex_rate")
async def get_ex_rate(request: Request):
    return {'SENTBE_RATE': SENTBE_RATE, 'HANPASS_RATE': HANPASS_RATE}


############## KIMCHI CORE CALCULATION ##############
def calc_kimchi(coin_buy, coin_sell, coin_name):
    ex_rate = mean([BANDAR_RATE])

    # Buying Coin from Indodax
    coin_bought = (IDR - BUY_MAKER_RATE / 100 * IDR) / coin_buy

    # Transfer Coin to Gopax
    coin_transferred = coin_bought - TRF_FEE[coin_name]

    # Sell Coin at Gopax
    coin_sell_maker_fee = SELL_MAKER_RATE / 100 * (coin_transferred * coin_sell)
    krw = coin_transferred * coin_sell - coin_sell_maker_fee

    # Withdraw to Korea bank
    krw_bank = int(krw - KRW_WITHDRAW_FEE)

    return ((krw_bank * ex_rate / IDR) - 1) * 100


def update_kimchi(coin_name):
    coin_buy, coin_sell = get_coin_price(coin_name)
    coin_kimchi = calc_kimchi(coin_buy, coin_sell, coin_name)

    coin_ctx = {
        'ts': datetime.now().strftime("%y/%m/%d %H:%M"),
        'coin_name': coin_name,
        'gopax_price': "{:,.0f}원".format(coin_sell),
        'indodax_price': "Rp {:,.0f}".format(coin_buy),
        'kimchi': "{:.2f}".format(coin_kimchi)
    }

    return coin_ctx


def get_kimchi(idr: int = 100):
    # EXTERNAL API CALL
    # HANPASS_RATE = get_hanpass_rate()
    # SENTBE_RATE = get_sentbe_rate()

    indodax_price = requests.get('https://indodax.com/api/ticker_all').json()

    fear_pairs = requests.get('https://datavalue.dunamu.com/api/fearindex').json()['pairs']

    fear_levels = {}
    for pair in fear_pairs:
        fear_levels[pair['currency']] = "{:.2f}".format(float(pair['score']))

    coins = []
    for coin_name in coin_names:
        coin_buy, coin_sell, coin_buy_vol, coin_sell_vol = get_coin_price_v2(indodax_price, coin_name)

        coin_kimchi = calc_kimchi(coin_buy, coin_sell, coin_name)
        coin_fear = fear_levels.get(coin_name.upper())

        coin_ctx = {
            'coin_name': coin_name,
            'gopax_price': coin_sell,
            'indodax_price': coin_buy,
            'coin_fear': coin_fear,
            'coin_buy_vol': coin_buy_vol,
            'coin_sell_vol': coin_sell_vol,
            'kimchi': "{:.2f}".format(coin_kimchi)
        }
        coins.append(coin_ctx)

    context = {
        'ts': datetime.now().strftime("%y/%m/%d %H:%M"),
        'coins': coins,
        'kurs': mean([BANDAR_RATE]),
    }

    return context


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # CALCULATE KIMCHI
    context = get_kimchi()

    return templates.TemplateResponse("index.html", {"request": request, "context": context})


@app.get("/get_all_coins")
async def get_all_coins(request: Request):
    return {'coins': coin_names}


@app.get("/update_coin")
async def update_coin(coin_name: str = 'xrp'):
    context = update_kimchi(coin_name)
    return context


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6969)
