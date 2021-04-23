import uvicorn
import requests
import time
import json
import math

from statistics import mean
from datetime import datetime
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
}
coin_names = ['xrp', 'xlm', 'doge', 'bch', 'eos', 'ltc']

BUY_MAKER_RATE = 0.3
SELL_MAKER_RATE = 0.2
KRW_WITHDRAW_FEE = 1000

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
    coin_buy = int(indodax_coin_res.json()['ticker']['last'])
    coin_sell = int(gopax_coin_res.json()['price'])
    return coin_buy, coin_sell

def get_coin_price_v2(indodax_price, coin='xrp'):
    gopax_coin_res = requests.get('https://api.gopax.co.kr/trading-pairs/' + coin.upper() + '-KRW/ticker').json()
    coin_sell = int(gopax_coin_res['bid'])
    coin_sell_vol = round(float(gopax_coin_res['quoteVolume'])/1e9, 2)

    
    buy = indodax_price['tickers'][coin.lower()+'_idr']
    coin_buy = int(buy['buy'])
    coin_buy_vol = round(float(buy['vol_idr'])/1e9, 2)

    return coin_buy, coin_sell, coin_buy_vol, coin_sell_vol

@app.get("/test")
async def test(request: Request):
    indodax_price = requests.get('https://indodax.com/api/ticker_all').json()
    
    get_coin_price_v2(indodax_price, 'xrp')
    return {'ok': 'ok'}


@app.get("/update_ex_rate")
async def update_ex_rate(request: Request):
    SENTBE_RATE = get_sentbe_rate()
    HANPASS_RATE = get_hanpass_rate()
    return {'SENTBE_RATE': SENTBE_RATE, 'HANPASS_RATE': HANPASS_RATE}

@app.get("/get_ex_rate")
async def get_ex_rate(request: Request):
    return {'SENTBE_RATE': SENTBE_RATE, 'HANPASS_RATE': HANPASS_RATE}




############## KIMCHI CORE CALCULATION ##############
def calc_kimchi(idr, coin_buy, coin_sell, coin_name):
    # Buying Coin from Indodax
    coin_bought = (idr - BUY_MAKER_RATE / 100 * idr) / coin_buy

    # Transfer Coin to Gopax
    coin_transferred = coin_bought - TRF_FEE[coin_name]

    # Sell Coin at Gopax
    coin_sell_maker_fee = SELL_MAKER_RATE / 100 * (coin_transferred * coin_sell)
    krw = coin_transferred * coin_sell - coin_sell_maker_fee

    # Withdraw to Korea bank
    krw_bank = int(krw - KRW_WITHDRAW_FEE)
    
    return krw_bank

def calculate_kimchi(idr: int = 100):
    # EXTERNAL API CALL
    # HANPASS_RATE = get_hanpass_rate()
    # SENTBE_RATE = get_sentbe_rate()
    BANDAR_RATE = 12.75
    indodax_price = requests.get('https://indodax.com/api/ticker_all').json()
    ex_rate = mean([SENTBE_RATE, HANPASS_RATE, BANDAR_RATE])
    
    fear_pairs = requests.get('https://datavalue.dunamu.com/api/fearindex').json()['pairs']
    fear_levels = {}
    for pair in fear_pairs:
        fear_levels[pair['currency']] = "{:.2f}".format(float(pair['score']))

    IDR = idr * 1e6
    coins = []
    for coin_name in coin_names:
        coin_buy, coin_sell, coin_buy_vol, coin_sell_vol = get_coin_price_v2(indodax_price, coin_name)
        coin_kimchi = calc_kimchi(IDR, coin_buy, coin_sell, coin_name)
        coin_fear = fear_levels.get(coin_name.upper())
        
        # rows = [
        #     {
        #         'remittance': 'Sentbe',
        #         'rate': "{:.2f}".format(SENTBE_RATE),
        #         'kimchi': "{:.2f}".format(((coin_kimchi * SENTBE_RATE / IDR) - 1) * 100)
        #     },
        #     {
        #         'remittance': 'Hanpass',
        #         'rate': "{:.2f}".format(HANPASS_RATE),
        #         'kimchi': "{:.2f}".format(((coin_kimchi * HANPASS_RATE / IDR) - 1) * 100)
        #     },
        #     {
        #         'remittance': 'Bandar',
        #         'rate': "{:.2f}".format(BANDAR_RATE),
        #         'kimchi': "{:.2f}".format(((coin_kimchi * BANDAR_RATE / IDR) - 1) * 100)
        #     },
        # ]
        coin_ctx = {
            'coin_name': coin_name,
            'gopax_price': coin_sell,
            'indodax_price': coin_buy,
            'coin_fear': coin_fear,
            'coin_buy_vol': coin_buy_vol,
            'coin_sell_vol': coin_sell_vol,
            'kimchi': "{:.2f}".format(((coin_kimchi * ex_rate / IDR) - 1) * 100)
            # 'rows': rows,
        }
        coins.append(coin_ctx)    

    context = {
        'ts': datetime.now().strftime("%y/%m/%d %H:%M"),
        'coins': coins,
        'kurs': ex_rate,
    }

    return context


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # CALCULATE KIMCHI
    context = calculate_kimchi(100)

    return templates.TemplateResponse("index.html", {"request": request, "context": context})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6969)
