# -*- coding: utf-8 -*-
import config
from binance.client import Client
from binance.enums import *
import time
import numpy as np
from colorama import init
from colorama import Fore, Back, Style
import math
import mysql.connector
import os
import time

init()
def obtenerFechaActual():
    from datetime import datetime
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    return dt_string

cliente = Client(config.API_KEY, config.API_SECRET)
# User ID to check
user_id = 1

# Lock file name
lock_file = 'main.lock'

# Initialize the Binance client
cliente = Client(config.API_KEY, config.API_SECRET)

# Trading parameters
simbolo = 'BTCUSDT'
simboloBalance = 'BTC'
cantidadOrden = 0.00299
decimales = '{:.3f}'
# ACA CAMBIO EL PRECIO DE LOS DECIMALES EN LA COMPRA, SI PONGO MUCHOS DECIMALES Y LA MONEDA NO ACEPTA ME TIRA ERROR DE PRICE_FILTER
# Initialize colorama
init()
def insert_log_message(user_id, symbol, quantity, price, details):
    try:
        db_params = settings.MYSQL_DATABASES["default"]
        conn = mysql.connector.connect(**db_params)
        cursor = conn.cursor()

        # Insert the log message into the bot_logs table
        insert_query = f'INSERT INTO artifind_APP_purchaselog (user_id, purchase_time, symbol, quantity, price, details) VALUES ({user_id},{obtenerFechaActual()},{symbol},{quantity},{price},{details})'
        cursor.execute(insert_query, (user_id, message))
        conn.commit()

    except Error as e:
        print(f"Error while inserting log message into the database: {e}")
    finally:
        cursor.close()
        conn.close()
def insert_sold_log(user, symbol, quantity, price, details):
    try:
        db_params = settings.MYSQL_DATABASES["default"]
        conn = mysql.connector.connect(**db_params)
        cursor = conn.cursor()

        # Insert the sold log into the 'sold_logs' table
        insert_query = f'INSERT INTO artifind_APP_soldlog (user_id, purchase_time, symbol, quantity, price, details) VALUES ({user_id},{obtenerFechaActual()},{symbol},{quantity},{price},{details})'
        cursor.execute(insert_query, (user.id, symbol, quantity, price, details))
        conn.commit()
    except Exception as e:
        print(f"Error while inserting sold log into the database: {e}")
    finally:
        cursor.close()
        conn.close()


# Database connection parameters
db_params = {
    'host': 'mysql-151901-0.cloudclusters.net',
    'user': 'admin',
    'password': 'eAZJ0Oeq',
    'database': 'artifind',
    'port': 19240,
}



def _ma5_():

    ma5_local = 0
    sum = 0

    try:
        klines = cliente.get_historical_klines(simbolo, Client.KLINE_INTERVAL_5MINUTE, "25 minute ago UTC")

        if(len(klines) == 5):
            for i in range(0, 5):
                sum = sum + float(klines[i][4])  # 4 precio de cierre de la vela

            ma5_local = sum / 5
    except Exception as e:
        print("Error in _ma5_: ", e)
    return ma5_local

def _ma10_():

    ma10_local = 0
    sum = 0

    try:
        klines = cliente.get_historical_klines(simbolo, Client.KLINE_INTERVAL_5MINUTE, "50 minute ago UTC")

        if(len(klines) == 10):
            for i in range(0, 10):
                sum = sum + float(klines[i][4])  # 4 precio de cierre de la vela

            ma10_local = sum / 10
    except Exception as e:
        print("Error in _ma10_: ", e)
    return ma10_local

def _ma20_():

    ma20_local = 0
    sum = 0

    try:
        klines = cliente.get_historical_klines(simbolo, Client.KLINE_INTERVAL_5MINUTE, "100 minute ago UTC")

        if(len(klines) == 20):
            for i in range(0, 20):
                sum = sum + float(klines[i][4])  # 4 precio de cierre de la vela

            ma20_local = sum / 20
    except Exception as e:
        print("Error in _ma20_: ", e)
    return ma20_local

# Main loop
while True:
    try:
        # Check if the lock file exists
        if not os.path.exists(lock_file):
            # Create the lock file to prevent concurrent execution
            open(lock_file, 'w').close()

            # Connect to the database
            conn = mysql.connector.connect(**db_params)
            cursor = conn.cursor(dictionary=True)

            # Query the database to check the bot status
            cursor.execute(f"SELECT bot_activado FROM artifind_APP_botactivationstatus WHERE user_id = {user_id}")
            bot_status = cursor.fetchone()

            if bot_status and bot_status['bot_activado'] == 1:
                # Bot is activated, run the trading logic
                sum_simbolo = 0.0
                try:
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
                        print(" Balance en billetera => ", simboloBalance, " %.8f  == " % sum_simbolo)
                        print("USDT %.8f " % own_usd)

                        time.sleep(10)

                        requestMinQtOrder = cliente.get_symbol_info(simbolo)
                        ordenes = cliente.get_open_orders(symbol=simbolo)
                        print(Fore.YELLOW, "Ordenes actuales abiertas")  # si devuelve [] está vacío
                        print(ordenes)
                        if(len(ordenes) != 0):
                            print(len(ordenes))
                            print("Cantidad a vender   ", str(math.floor(sum_simbolo)))
                            print("Precio de venta si BAJA   ", ordenes[0]['price'])
                            print("Precio de venta si SUBE   ", ordenes[1]['price'])
                            time.sleep(20)  # mando el robot a dormir porque EN TEORÍA abrió un orden, dejamos que el mercado opere.
                            continue

                        if(len(ordenes) != 0):
                            print(Fore.RED, " Hay ordenes abiertas, no se compra")
                            time.sleep(10)
                            continue

                        # obtengo el precio del token que estoy tradeando
                        list_of_tickers = cliente.get_all_tickers()
                        for tick_2 in list_of_tickers:
                            if tick_2['symbol'] == simbolo:
                                symbolPrice = float(tick_2['price'])
                        # fin obtener precio.

                        ma5 = _ma5_()
                        ma10 = _ma10_()
                        ma20 = _ma20_()

                        if(ma20 == 0):
                            continue

                        requestMinQtOrder = cliente.get_symbol_info(simbolo)
                        minQtOrder = float(requestMinQtOrder['filters'][1]['minQty'])
                        print("minQty", minQtOrder)
                        if (minQtOrder != 1):
                            print("ordenes acepta decimales")
                            order_local = '{:.8f}'.format(cantidadOrden*0.999)
                        else:
                            print("ordenes acepta SOLO numeros enteros")
                            order_local = '{:.0f}'.format(cantidadOrden*0.999)

                        # importante acomodar los decimales de la moneda porque arroja Error Price Filter.

                        print(Fore.YELLOW, "--------", simbolo, "---------")
                        print(" Precio actual de ", simbolo, "es: ", str(decimales.format(symbolPrice)))  # el .8 es la cantidad de decimales que no trae el símbolo
                        print("*******************************")
                        print(Fore.GREEN, " Precio MA5 ", str(decimales.format(ma5)))
                        print(Fore.YELLOW, " Precio MA10 ", str(decimales.format(ma10)))
                        print(Fore.RED, " Precio MA20 ", str(decimales.format(ma20)))
                        print(" Precio en que se va a comprar", str(decimales.format(ma20*0.995)))

                        if (symbolPrice > ma5 and ma5 > ma10 and ma10 > ma20):
                            print(Fore.GREEN, "Comprando si no hay otras ordenes abiertas")
                            purchase_message = f"Comprado exitosamente {cantidadOrden} {simbolo} al precio de {symbolPrice}"
                            
                            insert_sold_log(1, simboloBalance, order_local, str(decimales.format(symbolPrice*1.01)), purchase_message)
                            # ORDENES DE PRUEBA
                            # order = cliente.create_test_order(
                            # symbol = simbolo,
                            # side = SIDE_BUY,
                            # type = ORDER_TYPE_LIMIT,
                            # timeInForce = TIME_IN_FORCE_GTC,
                            # quantity = cantidadOrden*0.999,
                            # price = str(decimales.format(symbolPrice*1.02)),
                            # )
                            #
                            # orders = cliente(symbol=simbolo)
                            # print(orders)

                            order = cliente.order_market_buy(
                                symbol=simbolo,
                                quantity=cantidadOrden
                            )
                            time.sleep(5)

                            # Pongo orden OCO
                            print("COLOCANDO ORDEN OCO")
                            print("StopLimitPrice >   ", str(decimales.format(symbolPrice*0.985)))
                            print("Cantidad >   ", str(math.floor(sum_simbolo)))
                            print("StopPrice >   ", str(decimales.format(symbolPrice*0.99)))
                            print("Precio >   ", str(decimales.format(symbolPrice*1.01)))
                            ordenOCO = cliente.create_oco_order(
                                symbol=simbolo,
                                side=SIDE_SELL,
                                quantity=order_local,
                                price=str(decimales.format(symbolPrice*1.01)),
                                stopPrice=str(decimales.format(symbolPrice*0.99)),
                                stopLimitPrice=str(decimales.format(symbolPrice*0.985)),
                                stopLimitTimeInForce=TIME_IN_FORCE_GTC
                            )
                            time.sleep(20)
                              # mando el robot a dormir porque EN TEORÍA abrió un orden, dejamos que el mercado opere.
                            messageSold = f"Comprado exitosamente {cantidadOrden} {simbolo} al precio de {symbolPrice}"
                            insert_sold_log(1, simboloBalance, order_local, str(decimales.format(symbolPrice*1.01)), messageSold)
                        else:
                            print(Fore.RED, "No se cumplen las condiciones de compra")
                            time.sleep(20)  # mando el robot a dormir porque EN TEORÍA abrió un orden, dejamos que el mercado opere.
                            pass
                except Exception as e:
                    print("Error in main loop: ", e)
                    time.sleep(60)
                    if e == 'APIError(code=-2010): Account has insufficient balance for requested action.':
                        print('No hay saldo suficiente en la cuenta para realizar la operación')
                    print("Bot is not activated. Skipping execution.")
                    conn.close()

                    # Remove the lock file to allow the script to run again
                    os.remove(lock_file)

                    # Sleep for a minute before the next iteration
            # Close the database connection
            else:
                # Bot is not activated, remove the lock file
                print("Bot is not activated. Skipping execution.")
                conn.close()
                # Remove the lock file to allow the script to run again
                os.remove(lock_file)
        else:
            print("main.py is already running. Skipping execution.")
            # Remove the lock file to allow the script to run again
            os.remove(lock_file)
    except Exception as e:
        print(f"Error: {e}")

    # Wait for 10 seconds before the next check
    time.sleep(10)