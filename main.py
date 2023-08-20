from binance.client import Client
from binance.enums import *
import time
import math
import datetime
import numpy as np

client = Client(apik, apis, tld='com')
symbolTicker = 'DOGEEUR' 
symbolPrice = 0
ma24 = 0
auxPrice = 0.0
apik=""""""
apis=""""""

def orderStatus(orderToCkeck):
    try:
        status = client.get_order(
            symbol = symbolTicker,
            orderId = orderToCkeck.get('orderId')
        )
        return status.get('status')
    except Exception as e:
        print(e)
        return 7
    
def _ma24_(): 
    ma24_local = 0
    sum = 0

    klines = client.get_historical_klines(symbolTicker, Client.KLINE_INTERVAL_15MINUTE, "6 hour ago UTC") 

    if (len(klines) == 24):

        for i in range(0,24):
            sum = sum + float(klines[i][4])
        ma24_local = sum / 24

    return ma24_local

def _tendencia_ma24_4hs_15minCandles_():
    x = []
    y = []
    sum = 0
    ma24_i = 0

    time.sleep(1)

    resp = False

    klines = client.get_historical_klines(symbolTicker, Client.KLINE_INTERVAL_15MINUTE, "6 hour ago UTC") 

    if (len(klines) != 24):
        return False
    for i in range(0,24):
        for j in range(i-24,i):
            sum = sum + float(klines[j][4]) 
        ma24_i = round(sum / 24,7)
        sum = 0
        x.append(i)
        y.append(float(ma24_i))

    modelo = np.polyfit(x, y, 1)

    if (modelo[0]>0): 
        resp = True

    return resp

while 1:

    time.sleep(3)
    sum = 0
    try:
        list_of_tickers = client.get_all_tickers()
    except Exception as e:
        with open("doge.txt", "a") as myfile:
            myfile.write(str(datetime.datetime.now()) +" - an exception occured - {}".format(e)+ " Oops 1 ! \n")
        client = Client(apik, apis, tld='com')
        continue

    for tick_2 in list_of_tickers:
        if tick_2['symbol'] == symbolTicker:
            symbolPrice = float(tick_2['price'])
            break
    

    ma24 = _ma24_()
    if (ma24 == 0): continue
    
    try:
        orders = client.get_open_orders(symbol=symbolTicker)
    except Exception as e:
        client = Client(apik, apis, tld='com')
        continue

    if (len(orders) != 0):
        time.sleep(20)
        continue
        
        
    if (not _tendencia_ma50_4hs_15minCandles_()):
        time.sleep(15)
        continue
    else:

    if ( symbolPrice < ma50*0.99 ):

        try:

            buyOrder = client.create_order(
                        symbol=symbolTicker,
                        side='BUY',
                        type='STOP_LOSS_LIMIT',
                        quantity=100,
                        price='{:.4f}'.format(round(symbolPrice*1.0005,4)),
                        stopPrice='{:.4f}'.format(round(symbolPrice*1.0001,4)),
                        timeInForce='GTC')

            auxPrice = symbolPrice
            time.sleep(3)
            while orderStatus(buyOrder)=='NEW':

                
                try:
                    list_of_tickers = client.get_all_tickers()
                except Exception as e:
                    with open("doge.txt", "a") as myfile:
                        myfile.write(str(datetime.datetime.now()) +" - an exception occured - {}".format(e)+ " Oops 2 ! \n")
                    client = Client(apik, apis, tld='com')
                    continue

                for tick_2 in list_of_tickers:
                    if tick_2['symbol'] == symbolTicker:
                        symbolPrice = float(tick_2['price'])
                        break 
                

                if (symbolPrice < auxPrice):

                    try:
                        result = client.cancel_order(
                            symbol=symbolTicker,
                            orderId=buyOrder.get('orderId'))

                        time.sleep(3)
                    except Exception as e:
                        with open("doge.txt", "a") as myfile:
                            myfile.write(str(datetime.datetime.now()) +" - an exception occured - {}".format(e)+ "Error Canceling Oops 4 ! \n")
                        break


                    buyOrder = client.create_order(
                                symbol=symbolTicker,
                                side='BUY',
                                type='STOP_LOSS_LIMIT',
                                quantity=1000,
                                price='{:.4f}'.format(round(symbolPrice*1.0005,4)),
                                stopPrice='{:.4f}'.format(round(symbolPrice*1.0001,4)),
                                timeInForce='GTC')
                    auxPrice = symbolPrice
                    time.sleep(1)

            time.sleep(10)

            orderOCO = client.order_oco_sell(
                        symbol = symbolTicker,
                        quantity = 100,
                        price = '{:.4f}'.format(round(float(symbolPrice)*1.02,4)),
                        stopPrice = '{:.4f}'.format(round(float(symbolPrice)*1.002,4)),
                        stopLimitPrice ='{:.4f}'.format(round(float(symbolPrice)*0.995,4)),
                        stopLimitTimeInForce = 'GTC'
                    )

            time.sleep(20)

        except Exception as e:
            with open("doge.txt", "a") as myfile:
                myfile.write(str(datetime.datetime.now()) +" - an exception occured - {}".format(e)+ " Oops 3 ! \n")
            client = Client(apik, apis, tld='com')
            print(e)
            orders = client.get_open_orders(symbol=symbolTicker)
            if (len(orders)>0):
                result = client.cancel_order(
                    symbol=symbolTicker,
                    orderId=orders[0].get('orderId'))


            continue
