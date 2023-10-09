import config
from binance.client import Client
from binance.enums import *
import time
import numpy as np
from colorama import init
from colorama import Fore, Back, Style
import math
init()


cliente = Client(config.API_KEY, config.API_SECRET, tld='com')

simbolo = 'BTCUSDT'
simboloBalance = 'BTC'
cantidadOrden = 7 # cantidad a comprar (algunas monedas COMO BTC con compras menores a 20 USD tira errore min notional)

decimales = '{:.4f}' # ACA CAMBIO EL PRECIO DE LOS DECIMALES EN LA COMPRA, SI PONGO MUCHOS DECIMALES Y LA MONEDA NO ACEPTA ME TIRA ERROR DE PRICE_FILTER 

def _ma5_():

    ma5_local = 0
    sum = 0

    klines = cliente.get_historical_klines(simbolo, Client.KLINE_INTERVAL_5MINUTE, "25 minute ago UTC")

    if(len(klines)==5):
        for i in range (0,5):
            sum = sum +float(klines[i][4]) # 4 precio de cierre de la vela
        
        ma5_local = sum / 5

    return ma5_local

def _ma10_():

    ma10_local = 0
    sum = 0

    klines = cliente.get_historical_klines(simbolo, Client.KLINE_INTERVAL_5MINUTE, "50 minute ago UTC")

    if(len(klines)==10):
        for i in range (0,10):
            sum = sum +float(klines[i][4]) # 4 precio de cierre de la vela
        
        ma10_local = sum / 10

    return ma10_local

def _ma20_():

    ma20_local = 0
    sum = 0

    klines = cliente.get_historical_klines(simbolo, Client.KLINE_INTERVAL_5MINUTE, "100 minute ago UTC")

    if(len(klines)==20):
        for i in range (0,20):
            sum = sum +float(klines[i][4]) # 4 precio de cierre de la vela
        
        ma20_local = sum / 20

    return ma20_local

while 1:

    ## Calculamos el balance en cuenta para poner una orden OCO exacta y evitar LotSize o insuficent balance
    sum_simbolo = 0.0
    balances = cliente.get_account()
    for _balance in balances["balances"]:
        asset = _balance["asset"]
        if float(_balance["free"]) != 0.0 or float(_balance["locked"]) != 0.0:
            try:
                simbolo_quantity = float(_balance["free"]) + float(_balance["locked"])
                if asset == simboloBalance:
                    sum_simbolo += simbolo_quantity
                else:
                    _price = cliente.get_symbol_ticker(symbol=asset + simboloBalance)
                    sum_simbolo += simbolo_quantity * float(_price["price"])
            except:
                pass
    current_simbolo_price_USD = cliente.get_symbol_ticker(symbol="BTCUSDT")["price"]
    own_usd = sum_simbolo * float(current_simbolo_price_USD)
    print(" Balance en billetera => "  + simboloBalance + " %.8f  == " % sum_simbolo, end="")
    print("USDT %.8f " % own_usd)
    
    time.sleep(10)



    requestMinQtOrder = cliente.get_symbol_info(simbolo)
    ordenes = cliente.get_open_orders(symbol=simbolo)
    print(Fore.YELLOW + "Ordenes actuales abiertas") # si devuelve [] esta vacio
    

   
    if(len(ordenes) != 0 ):
        print(len(ordenes))
        print("Cantidad a vender   " + str(math.floor(sum_simbolo)))
        print("Precio de venta si BAJA   " + ordenes[0]['price'])
        print("Precio de venta si SUBE   " + ordenes[1]['price'])
        time.sleep(20) #mando el robot a dormir porque EN TEORIA abrio un orden, dejamos que el mercado opere.
        continue

    

    if(len(ordenes) !=0 ):
        print(Fore.RED + " Hay ordenes abiertas, no se compra")
        time.sleep(10)
        continue

    # obtengo el precio del token que estoy tradeando
    list_of_tickers = cliente.get_all_tickers()
    for tick_2 in list_of_tickers:
        if tick_2['symbol'] == simbolo:
            symbolPrice = float(tick_2['price'])
    # fin obtener precio. 

    ma5  = _ma5_()
    ma10 = _ma10_()
    ma20 = _ma20_()

    if(ma20 == 0 ): continue

    requestMinQtOrder = cliente.get_symbol_info(simbolo)

    

    print("Cantidad minima de ordenes de compra es: ", requestMinQtOrder['filters'][1]['minQty'])
    try:
        minQtOrder = float(requestMinQtOrder['filters'][1]['minQty'])
    except KeyError:
        minQtOrder = 0.0
    if (minQtOrder !=1 ):
        print("ordenes acepta decimales")
        order_local = '{:.8f}'.format(cantidadOrden*0.999)
    else:
        print("ordenes acepta SOLO numeros enteros")
        order_local = '{:.0f}'.format(cantidadOrden*0.999)
    
    # importante acomodar los decimales de la moneda porque arroja Error Price Filter.

    print(Fore.YELLOW + "--------" + simbolo + "---------")
    print(" Precio actual de " + simbolo + "es: " + str(decimales.format(symbolPrice))) #el .8 es la cantidad de decimales que no trae el simbolo 
    print("*******************************")
    print(Fore.GREEN + " Precio MA5 " + str(decimales.format(ma5)))
    print(Fore.YELLOW + " Precio MA10 " + str(decimales.format(ma10)))
    print(Fore.RED + " Precio MA20 " + str(decimales.format(ma20)))
    print(" Precio en que se va a comprar" + str(decimales.format(ma20*0.995)))


    if ( symbolPrice > ma5 and ma5 > ma10 and ma10 > ma20):
        print(Fore.GREEN + "Comprando si no hay otras ordenes abiertas")
    
    # ORDENES DE PRUEBA 
        #order = cliente.create_test_order(
        #symbol = simbolo,
        #side = SIDE_BUY,
        #type = ORDER_TYPE_LIMIT,
        #timeInForce = TIME_IN_FORCE_GTC,
        #quantity = cantidadOrden*0.999,
        #price = str(decimales.format(symbolPrice*1.02)),
        #)
#
        #orders = cliente(symbol=simbolo)
        #print(orders)

        order = cliente.order_market_buy(
            symbol = simbolo,
            quantity = cantidadOrden
        )
        time.sleep(5)

        #Pongo orden OCO
        print("COLOCANDO ORDEN OCO")
        print("StopLimitPrice >   " +str(decimales.format(symbolPrice*0.985)),)
        print("Cantidad >   " + str(math.floor(sum_simbolo)))
        print("StopPrice >   " + str(decimales.format(symbolPrice*0.99)))
        print("Precio >   " + str(decimales.format(symbolPrice*1.01)))

        ordenOCO = cliente.create_oco_order(
            symbol = simbolo,
            side = SIDE_SELL,
            stopLimitPrice = str(decimales.format(symbolPrice*0.985)),
            stopLimitTimeInForce = TIME_IN_FORCE_GTC,
            ## Error  LOT SIZE es porque no soporta decimales en quantity
            quantity = str(math.floor(sum_simbolo)), # BINANCE cobra un fee, tarifa. Sino va a tirar un error de insuficent FOUNDS. O Error LOT SIZE. 
            stopPrice = str(decimales.format(symbolPrice*0.99)),
            price = str(decimales.format(symbolPrice*1.01)), 
            )
    
        time.sleep(20) #mando el robot a dormir porque EN TEORIA abrio un orden, dejamos que el mercado opere.

    else: 
        print(Fore.RED + "No se cumplen las condiciones de compra")
        time.sleep(20) #mando el robot a dormir porque EN TEORIA abrio un orden, dejamos que el mercado opere.
    
    # FIN ordenes de prueba

# corregir ma20
# eliminar import BTC primera linea
# corregir filter por FILTERS
# corregir identado en ordenes de prueba
