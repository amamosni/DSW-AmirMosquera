# Author: Yogesh K for finxter.com
# python script: trading with Bollinger bands for Binance
from binance.client import Client
from _config import config
from _logger import logger
import pandas as pd     # needs pip install
import random
import datetime
import calendar
import requests
from time import sleep

client = Client(config["BINANCE_API_KEY"], config["BINANCE_API_SECRET_KEY"], testnet=False)
pares = eval(config["BINANCE_TRACE_SYMBOL"])
perdida = float(config["PORCENTAJE_PERDIDA"]) / 100
num_recompra = int(config["NUMERO_RECOMPRAS"])
recompra = float(config["DISTANCIA_RECOMPRAS"]) / 100
recompramonedas = float(config["PORCENTAJE_RECOMPRAS_MONEDAS"])
leverage = int(config["APALANCAMIENTO"])
inversio_inicial = float(config["INVERSION_INICIAL"])
slxcall = float(config["PORCENTAJE_SLX_CALL"]) / 100
slxorder = float(config["PORCENTAJE_SLX_ORDER"]) / 100
pasotrailing = float(config["PASO_SLX_MINIMO"]) / 100
decimales = int(config["DECIMALES_MONEDA"])
order_book_limit = int(config["CANTIDAD_ORDER_BOOK"])

#Conexion a la API de Binance
def conexionApi():
    try:
        client.ping()
        logger.info(f"=== Conexion establecida con la API de binance ===")
    except Exception:
        logger.info(f"=== Fallo la conexión con la API de Binance, revisa tu servidor de internet ===")

#Datos del order book
def order_book():
    global symbol, current_price
    symbol = random.choice(pares)
    url = "https://fapi.binance.com/fapi/v1/depth?symbol=" + symbol + "&limit=" + order_book_limit
    results = requests.get(url).json()
    #print(results)
    #results = client.futures_order_book(symbol = symbol, limit = "50")
    #print(results)

    df = {side: pd.DataFrame(data=results[side], columns=["price", "quantity"],dtype=float) for side in ["bids", "asks"]}
    #df = pd.DataFrame(results)
    #print(frames)
    #print(df)
    arriba = df["asks"]
    arriba = arriba.sort_values(by="quantity", ascending=False)
    arriba = arriba.head(1)
    
    abajo = df["bids"]
    abajo = abajo.sort_values(by="quantity", ascending=False)
    abajo = abajo.head(1)

    #print(arriba)
    #print(abajo)

    block_arriba = arriba.price.max()
    block_abajo = abajo.price.max()

    #print(block_arriba)
    #print(block_abajo)

    current_price = float(client.futures_symbol_ticker(symbol=symbol)['price'])



    """
    print(f"Precio       : {current_price}")
    print(f"Bloque arriba: {block_arriba}")
    print(f"Bloque abajo : {block_abajo}")
    print(f"P arriba     : {distance_block_arriba:.2f}")
    print(f"P abajo      : {distance_block_abajo:.2f}")
    print("-----------------------------")
    """

    logger.info(f"{symbol}, $: {current_price}, OBAr: {block_arriba}, OBAb: {block_abajo}")
    return(current_price, symbol, block_arriba, block_abajo)


# Precio actualizado
def actualizar_precio():
        current_price = float(client.futures_symbol_ticker(symbol=symbol)['price'])
        return(current_price)

        
#Conocer el dinero en USDT en la billetera de futuros
def saldo_futuros():
    #To Get The Balances For The Futures Wallet
    acc_balance = client.futures_account_balance()
    for check_balance in acc_balance:
        if check_balance["asset"] == "USDT":
            usdt_balance_futuros = check_balance["balance"]
            #print(usdt_balance_futuros) # Prints 0.0000
    usdt_balance_futuros = float(usdt_balance_futuros)
    return (usdt_balance_futuros)

#Crear una orden long en futuros
def crear_orden_long():
    #client.futures_change_margin_type(symbol=symbol, marginType='CROSSED')
    global monedas_orden, orden_long_ID, orden_long_Price
    client.futures_change_leverage(symbol=symbol, leverage=leverage)
    (usdt_balance_futuros) = saldo_futuros()
    usdt_crear_orden = usdt_balance_futuros * inversio_inicial
    monedas_orden = round((usdt_crear_orden) / current_price)
    buyorder=client.futures_create_order(
        symbol=symbol,
        side="BUY",
        #type="LIMIT",
        type="MARKET",
        quantity=monedas_orden,
        #price=current_price,
        #timeInForce="GTC"
        )
    #orden_long_ID = round(buyorder['orderId'])
    orden_long_ID = buyorder.get("orderId")
    sleep(1)

# Busca la orden recien ejecutada y trae el precio de cierre long
def buscar_orden_recien_ejecutada_long():
    global orden_long_Price
    #print(client.futures_get_all_orders())
    orden_long_ID_use = orden_long_ID
    status_orders = client.futures_get_all_orders(symbol=symbol)
    for check_status in status_orders:
        if check_status["orderId"] == orden_long_ID_use:
            orden_long_Precio = check_status["avgPrice"]
            orden_long_Price = float(orden_long_Precio)

def stop_lost_long():
    #Perdidas o Stop loss order LONG
    global id_long_stop
    precio_cierre = orden_long_Price - (orden_long_Price * perdida)
    precio_cierre = float(round(precio_cierre,decimales))
    stoploss_order=client.futures_create_order(
        symbol=symbol,
        side="SELL",
        type="STOP_MARKET",
        stopPrice = precio_cierre,
        closePosition = "true"
    )
    id_long_stop = stoploss_order.get("orderId")

#Recompras para long
def recompras_long():
    global precio_recompra, monedas_recompra
    precio_recompra = orden_long_Price
    monedas_recompra = monedas_orden
    #Perdidas o Stop loss order LONG
    try:
        for i in range(0, num_recompra, 1):
            #global precio_recompra, monedas_recompra
            precio_cierre = precio_recompra - (precio_recompra * recompra)
            precio_cierre = float(round(precio_cierre,decimales))
            monedas_orden_recompras = monedas_recompra + (monedas_recompra * recompramonedas)
            monedas_orden_recompras = round(monedas_orden_recompras)
            
            def recompras_long_ordenes():
                recompras_order=client.futures_create_order(
                    symbol=symbol,
                    side="BUY",
                    type="LIMIT",
                    quantity=monedas_orden_recompras,
                    price=precio_cierre,
                    timeInForce="GTC"
                )
            precio_recompra = precio_cierre
            monedas_recompra = monedas_orden_recompras
            recompras_long_ordenes()
    except:
        print("--------------------------------------------")
        print("No se crearon las todas ordenes de recompra.\nNo tienes dinero en tu cuenta")
        print("--------------------------------------------")
        pass

#Trailing stop long
def trailling_stop_long():
    #print(account)
    check = 0
    cicloroe = 0
    while check == 0:
        while cicloroe <= slxcall:
            check = 0
            current_price = float(client.futures_symbol_ticker(symbol=symbol)['price'])
            account = client.futures_account()
            for datos in account["positions"]:
                if datos["symbol"] == symbol:
                    try:
                        initialmargin = float(datos["initialMargin"])
                        unrealizedprofit = float(datos["unrealizedProfit"])
                        precio_entrada_slx = float(datos["entryPrice"])
                        #roe = (unrealizedprofit / initialmargin)
                        #roe = float(round((precio_entrada_slx - current_price) / precio_entrada_slx,4)) #trailling_stop_short
                        roe = float(round((current_price -precio_entrada_slx) / current_price,4)) #trailling_stop_long
                        unrealizedprofitShow = float(round(unrealizedprofit,4))
                        roeShow = float(round(roe * 100,2)) 
                        slxcallShow = float(round(slxcall * 100,2))
                        print("---Orden LONG activo en: " + symbol + "---")
                        print("PNL: " + str(unrealizedprofitShow) + " USDT")
                        print("ROE: " + str(roeShow) + "%")
                        print("SLX: " + str(slxcallShow) + "%")
                    except Exception:
                        pass
                    cicloroe = roe
                    #Toma de ganancias o Take Profit SHORT con SLX
                    precio_entrada_slx = precio_entrada_slx + (precio_entrada_slx * slxorder)
                    precio_entrada_slx = float(round(precio_entrada_slx,decimales))
                    #os.system('cls')
        try:
            #print(precio_cierre)
            stoploss_slx_order=client.futures_create_order(
                symbol=symbol,
                side="SELL",
                type="STOP_MARKET",
                stopPrice = precio_entrada_slx,
                closePosition = "true"
            )
            check = 1
        except Exception:
            pass
    
    old_price = precio_entrada_slx
    current_price = float(client.futures_symbol_ticker(symbol=symbol)['price'])
    price_expected = old_price + (old_price * slxcall)
    price_expected = float(round(price_expected,decimales))
    orden_abierta = 1

    while current_price > old_price and orden_abierta > 0:
        price_expected = float(round(price_expected,decimales))
        print("---SLX LONG activado en: " + symbol + " ---")
        print("Prev Price order: " + str(old_price))
        print("   Current Price: " + str(current_price))
        print("  Expected price: " + str(price_expected))

        if current_price >= price_expected:
            slxcancel = client.futures_cancel_order(
                symbol = symbol,
                orderId = stoploss_slx_order.get("orderId")
            )
            try:
                old_price = old_price + (old_price * slxorder)
                old_price = float(round(old_price,decimales))
                stoploss_slx_order=client.futures_create_order(
                symbol=symbol,
                side="SELL",
                type="STOP_MARKET",
                stopPrice = old_price,
                closePosition = "true"
                )
            except Exception:
                old_price = old_price - (old_price * slxorder)
                old_price = float(round(old_price,decimales))
                stoploss_slx_order=client.futures_create_order(
                symbol=symbol,
                side="SELL",
                type="STOP_MARKET",
                stopPrice = old_price,
                closePosition = "true"
                )
                pass
            price_expected = old_price + (old_price * pasotrailing)
            price_expected = float(round(price_expected,decimales))
        account = client.futures_account()
        for datos in account["positions"]:
            if datos["symbol"] == symbol:
                orden_abierta = float(datos["initialMargin"])
        current_price = float(client.futures_symbol_ticker(symbol=symbol)['price'])
        #os.system('cls')
    print("---SLX desactivado---")
    active_orders = client.futures_get_open_orders()
    for orders_futures in active_orders:
        if orders_futures["orderId"] == id_long_stop:
            cancel_order = client.futures_cancel_order(
                symbol = symbol,
                orderId = id_long_stop
                )

#Crear una orden short en futuros
def crear_orden_short():
    #client.futures_change_margin_type(symbol=symbol, marginType='CROSSED')
    global monedas_orden, orden_short_ID
    client.futures_change_leverage(symbol=symbol, leverage=leverage)
    (usdt_balance_futuros) = saldo_futuros()
    usdt_crear_orden = usdt_balance_futuros * inversio_inicial
    monedas_orden = round((usdt_crear_orden) / current_price)
    buyorder=client.futures_create_order(
        symbol=symbol,
        side="SELL",
        #type="LIMIT",
        type="MARKET",
        quantity=monedas_orden,
        #price=current_price,
        #timeInForce="GTC"
        )
    orden_short_ID = buyorder.get("orderId")
    sleep(1)

# Busca la orden recien ejecutada y trae el precio de cierre long
def buscar_orden_recien_ejecutada_short():
    global orden_short_Price
    #print(client.futures_get_all_orders())
    orden_short_ID_use = orden_short_ID
    status_orders = client.futures_get_all_orders(symbol=symbol)
    for check_status in status_orders:
        if check_status["orderId"] == orden_short_ID_use:
            orden_short_Precio = check_status["avgPrice"]
            orden_short_Price = float(orden_short_Precio)
    #print(orden_short_Price)

def stop_lost_short():
    #Perdidas o Stop loss order SHORT
    global id_short_stop
    precio_cierre = orden_short_Price + (orden_short_Price * perdida)
    precio_cierre = float(round(precio_cierre,decimales))
    stoploss_order=client.futures_create_order(
        symbol=symbol,
        side="BUY",
        type="STOP_MARKET",
        stopPrice = precio_cierre,
        closePosition = "true"
    )
    id_short_stop = stoploss_order.get("orderId")

#Recompras para Short
def recompras_short():
    global precio_recompra, monedas_recompra
    precio_recompra = orden_short_Price
    monedas_recompra = monedas_orden
    try:
        for i in range(0, num_recompra, 1):
            #global precio_recompra, monedas_recompra
            precio_cierre = precio_recompra + (precio_recompra * recompra)
            precio_cierre = float(round(precio_cierre,decimales))
            monedas_orden_recompras = monedas_recompra + (monedas_recompra * recompramonedas)
            monedas_orden_recompras = round(monedas_orden_recompras)
            
            def recompras_short_ordenes():
                recompras_order=client.futures_create_order(
                    symbol=symbol,
                    side="SELL",
                    type="LIMIT",
                    quantity=monedas_orden_recompras,
                    price=precio_cierre,
                    timeInForce="GTC"
                )
            precio_recompra = precio_cierre
            monedas_recompra = monedas_orden_recompras
            recompras_short_ordenes()
    except:
        print("--------------------------------------------")
        print("No se crearon las todas ordenes de recompra.\nNo tienes dinero en tu cuenta")
        print("--------------------------------------------")
        pass


#Trailing stop loss
def trailling_stop_short():
    #print(account)
    check = 0
    cicloroe = 0
    while check == 0:
        while cicloroe <= slxcall:
            check = 0
            current_price = float(client.futures_symbol_ticker(symbol=symbol)['price'])
            account = client.futures_account()
            for datos in account["positions"]:
                if datos["symbol"] == symbol:
                    try:
                        initialmargin = float(datos["initialMargin"])
                        unrealizedprofit = float(datos["unrealizedProfit"])
                        precio_entrada_slx = float(datos["entryPrice"])
                        #roe = (unrealizedprofit / initialmargin)
                        roe = float(round((precio_entrada_slx - current_price) / precio_entrada_slx,4)) #trailling_stop_short
                        #roe = float(round((current_price -precio_entrada_slx) / current_price,4)) #trailling_stop_long
                        unrealizedprofitShow = float(round(unrealizedprofit,4))
                        roeShow = float(round(roe * 100,2))
                        slxcallShow = float(round(slxcall * 100,2)) 
                        print("---Orden SHORT activo en: " + symbol + "---")
                        print("PNL: " + str(unrealizedprofitShow) + " USDT")
                        print("ROE: " + str(roeShow) + "%")
                        print("SLX: " + str(slxcallShow) + "%")
                    except Exception:
                        pass
                    cicloroe = roe
                    #Toma de ganancias o Take Profit SHORT con SLX
                    precio_entrada_slx = precio_entrada_slx - (precio_entrada_slx * slxorder)
                    precio_entrada_slx = float(round(precio_entrada_slx,decimales))
                    #os.system('cls')
        try:
            #print(precio_cierre)
            stoploss_slx_order=client.futures_create_order(
                symbol=symbol,
                side="BUY",
                type="STOP_MARKET",
                stopPrice = precio_entrada_slx,
                closePosition = "true"
            )
            check = 1
        except Exception:
            pass
    old_price = precio_entrada_slx
    current_price = float(client.futures_symbol_ticker(symbol=symbol)['price'])
    price_expected = old_price - (old_price * slxcall)
    price_expected = float(round(price_expected,decimales))
    orden_abierta = 1

    while current_price < old_price and orden_abierta > 0:
        print("---SLX SHORT activado en: " + symbol + " ---")
        print("Prev Price order: " + str(old_price))
        print("   Current Price: " + str(current_price))
        print("  Expected price: " + str(price_expected))

        if current_price <= price_expected:
            slxcancel = client.futures_cancel_order(
                symbol = symbol,
                orderId = stoploss_slx_order.get("orderId")
            )
            try:
                old_price = old_price - (old_price * slxorder)
                old_price = float(round(old_price,decimales))
                stoploss_slx_order=client.futures_create_order(
                symbol=symbol,
                side="BUY",
                type="STOP_MARKET",
                stopPrice = old_price,
                closePosition = "true"
                )
            except Exception:
                old_price = old_price + (old_price * slxorder)
                old_price = float(round(old_price,decimales))
                stoploss_slx_order=client.futures_create_order(
                symbol=symbol,
                side="BUY",
                type="STOP_MARKET",
                stopPrice = old_price,
                closePosition = "true"
                )
                pass
            price_expected = old_price - (old_price * pasotrailing)
            price_expected = float(round(price_expected,decimales))
        account = client.futures_account()
        for datos in account["positions"]:
            if datos["symbol"] == symbol:
                orden_abierta = float(datos["initialMargin"])
        current_price = float(client.futures_symbol_ticker(symbol=symbol)['price'])
        #os.system('cls')
    print("---SLX desactivado---")
    active_orders = client.futures_get_open_orders()
    for orders_futures in active_orders:
        if orders_futures["orderId"] == id_short_stop:
            cancel_order = client.futures_cancel_order(
                symbol = symbol,
                orderId = id_short_stop
                )        

def total_ordenes_resumen():
    contar_filled = 0
    contar_cancelled = 0
    contar_expired = 0

    #Día actual
    today = datetime.date.today()
    #print(today)

    #convertir la fecha a formato numero
    timeup = (calendar.timegm(today.timetuple()) ) * 1000
    #print(timeup)
    
    #print(client.futures_get_all_orders())
    status_orders = client.futures_get_all_orders()
    for check_status in status_orders:
        if check_status["status"] == "FILLED" and check_status["time"] > timeup and check_status["side"] == "BUY":
            contar_filled += 1
        if check_status["status"] == "CANCELED" and check_status["time"] > timeup:
            contar_cancelled += 1
        if check_status["status"] == "EXPIRED" and check_status["time"] > timeup:
            contar_expired += 1

    #print(contar_filled)
    #print(contar_cancelled)
    #print(contar_expired)
    return (contar_filled, contar_cancelled, contar_expired)
    #send_message(_message_ordenes)
    
# Cuantas ordenes hay colocadas de short y de long con su respectivo par
def total_ordenes_activas(): # Cuantas ordenes hay colocadas de short y de long con su respectivo par
    _message_ordenes_long = " \n"
    _message_ordenes_short = " \n"
    total_long = 0
    total_short = 0
    #print(client.futures_get_open_orders())
    active_orders = client.futures_get_open_orders()
    for orders_futures in active_orders:
        if orders_futures["side"] == "SELL" and orders_futures["type"] == "LIMIT":
            order_symbol = orders_futures["symbol"] 
            #price = float(orders_futures["price"])
            stopPrice = float(orders_futures["stopPrice"])
            #coins = float(orders_futures["origQty"])
            #order_dinero_invertido = float((price * coins) / 10)
            #_message_ordenes_long = f"🟢LONG: {order_symbol} - Precio: {price} - Monedas: {coins} - Inversión: {order_dinero_invertido:.2f} dls\n" + _message_ordenes_long
            _message_ordenes_long = f"🟢 LONG: {order_symbol} - Take profit: {stopPrice}\n" + _message_ordenes_long
            #print(orders_futures["positionSide"],  "en:", orders_futures["symbol"], "precio:", orders_futures["price"])
            total_long += 1
        #else:
            #_message_ordenes_long = "No hay más ordenes LONG\n"
    for orders_futures in active_orders:
        if orders_futures["side"] == "BUY" and orders_futures["type"] == "LIMIT":
            order_symbol = orders_futures["symbol"]
            #price = float(orders_futures["price"])
            stopPrice = float(orders_futures["stopPrice"])
            #coins = float(orders_futures["origQty"])
            #order_dinero_invertido = float((price * coins) / 10)
            #_message_ordenes_short = f"🔴SHORT: {order_symbol} - Precio: {price} - Monedas: {coins} - Inversión: {order_dinero_invertido:.2f} dls\n" + _message_ordenes_short
            _message_ordenes_short = f"🔴 SHORT: {order_symbol} - Take profit: {stopPrice}\n" + _message_ordenes_short
            #print(orders_futures["positionSide"],  "en:", orders_futures["symbol"], "precio:", orders_futures["price"])
            total_short += 1
        #else:
            #_message_ordenes_short = "No hay más ordenes SHORT\n"
    #print("Total de ordenes en LONG:", total_long)
    #print("Total de ordenes en SHORT:", total_short)
    #_message_ordenes_long = f"Resumén de ordenes actuales:\nOrdenes LONG: {total_long} - Ordenes SHORT: {total_short}\n"
    return(total_long, total_short, _message_ordenes_long, _message_ordenes_short)


def long():
    crear_orden_long()
    buscar_orden_recien_ejecutada_long()
    stop_lost_long()
    recompras_long()
    trailling_stop_long()

def short():
    crear_orden_short()
    buscar_orden_recien_ejecutada_short()
    stop_lost_short()
    recompras_short()
    trailling_stop_short()

if __name__ == "__main__":
    logger.warn("Ejecutar python main.py, en su lugar, Iniciar la recogida con la configuración por defecto")
    order_book()
       # Change symbol here e.g. BTCUSDT, BNBBTC, ETHUSDT, NEOBTC