import uvicorn
import requests
import time
import json

from datetime import datetime
from fastapi import FastAPI

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


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


def get_coin_price(coin='xrp'):
    indodax_coin_res = requests.get('https://indodax.com/api/ticker/' + coin.lower() + 'idr')
    gopax_coin_res = requests.get('https://api.gopax.co.kr/trading-pairs/' + coin.upper() + '-KRW/ticker')
    coin_buy = int(indodax_coin_res.json()['ticker']['last'])
    coin_sell = int(gopax_coin_res.json()['price'])
    return coin_buy, coin_sell


def calculate_kimchi(idr: int = 100):
    # EXTERNAL API CALL
    xrp_buy, xrp_sell = get_coin_price('xrp')

    HANPASS_RATE = get_hanpass_rate()
    SENTBE_RATE = get_sentbe_rate()

    xrp_buy = int(indodax_xrp_res.json()['ticker']['buy'])
    xrp_sell = int(gopax_xrp_res.json()['bid'])

    coin_rate = xrp_buy / xrp_sell

    IDR = idr * 1e6
    DAX_TRANSFER_FEE = int(6500 * (IDR / 25 * 1e6))

    # Buying XRP from Indodax
    XRP_BUY_MAKER_RATE = 0.3
    xrp_buy_maker_fee = XRP_BUY_MAKER_RATE / 100 * IDR
    xrp_bought = (IDR - DAX_TRANSFER_FEE - xrp_buy_maker_fee) / xrp_buy

    # Transfer XRP to Gopax
    XRP_TRANSFER_FEE = 3
    xrp_transferred = xrp_bought - XRP_TRANSFER_FEE

    # Sell XRP at Gopax
    XRP_SELL_MAKER_RATE = 0.2
    xrp_sell_maker_fee = XRP_SELL_MAKER_RATE / 100 * (xrp_transferred * xrp_sell)
    krw = xrp_transferred * xrp_sell - xrp_sell_maker_fee

    # Withdraw to bank
    DEPOSIT_FEE = 1000
    krw_bank = int(krw - DEPOSIT_FEE)

    now = datetime.now().strftime("%y/%m/%d %H:%M")

    context = {
        'Date': now,
        'rows': [
            {
                'remittance': 'Sentbe',
                'rate': "{:.2f}".format(SENTBE_RATE),
                'kimchi': "{:.2f}".format(((krw_bank * SENTBE_RATE / IDR) - 1) * 100)
            },
            {
                'remittance': 'Hanpass',
                'rate': "{:.2f}".format(HANPASS_RATE),
                'kimchi': "{:.2f}".format(((krw_bank * HANPASS_RATE / IDR) - 1) * 100)
            },

        ],
        'GOPAX Price [KRW]': "{:,}".format(xrp_sell),
        'Indodax Price [IDR]': "{:,}".format(xrp_buy),
    }

    return context


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # CALCULATE KIMCHI
    # TODO: add more coin
    context = calculate_kimchi(100)

    return templates.TemplateResponse("index.html", {"request": request, "context": context})


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=6969)
