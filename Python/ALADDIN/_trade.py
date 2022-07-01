# Author: Yogesh K for finxter.com
# python script: trading with Bollinger bands for Binance
from binance.client import Client
from binance.enums import HistoricalKlinesType
from _config import config
from _logger import logger
import pandas as pd     # needs pip install
import random
import datetime
import calendar
import requests
from time import sleep

client = Client(config["BINANCE_API_KEY"], config["BINANCE_API_SECRET_KEY"], testnet=False)
interval = config["BINANCE_TRACE_INTERVAL"]
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

#Conexion a la API de Binance
def conexionApi():
    try:
        client.ping()
        logger.info(f"=== Conexion establecida con la API de binance ===")
    except Exception:
        logger.info(f"=== Fallo la conexión con la API de Binance, revisa tu servidor de internet ===")

def get_data_frame():
    global symbol, current_price
    symbol = random.choice(pares)

    # valid intervals - 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
    # request historical candle (or klines) data using timestamp from above, interval either every min, hr, day or month
    # starttime = '30 minutes ago UTC' for last 30 mins time
    # e.g. client.get_historical_klines(symbol='ETHUSDT', '1m', starttime)
    # starttime = '1 Dec, 2017', '1 Jan, 2018'  for last month of 2017
    # e.g. client.get_historical_klines(symbol='BTCUSDT', '1h', "1 Dec, 2017", "1 Jan, 2018")
    #starttime = '1 day ago UTC'  # to start for 1 day ago

    current_price = float(client.futures_symbol_ticker(symbol = symbol)['price'])

    starttime = '1 hours ago UTC'  # to start for 1 day ago
    bars = client.get_historical_klines(symbol, interval, starttime, klines_type=HistoricalKlinesType.FUTURES)
    

    for line in bars:        # Keep only first 5 columns, "date" "open" "high" "low" "close"
        del line[5:]
    df = pd.DataFrame(bars, columns=['date', 'open', 'high', 'low', 'close']) #  2 dimensional tabular data
    #print(df)
    return (df)


def buy_or_sell(df):
    (rsi) = rsi_trade_logic()
    #current_price = float(client.futures_symbol_ticker(symbol=symbol)['price'])
    current_upper = pd.to_numeric(df.iloc[-1:]['upper'], downcast='float')[0]
    current_lower = pd.to_numeric(df.iloc[-1:]['lower'], downcast='float')[0]
    #upper_lower_delta = current_upper - current_lower
    #current_price_delta = current_price - current_lower
    #current_price_percentage = current_price_delta / upper_lower_delta * 100.0
    percentage_current_upper = ((current_price - current_upper) / current_upper) * 100
    percentage_current_lower = ((current_lower - current_price) / current_lower) * 100

    # Determina si la distancia entre las bollinger es mayor a distanceBB, si es asi continua el proceso, esto se hace para mitigar rangos donde el precio
    # rompe con fuerza y queda dentro de la operación mucho tiempo.
    if percentage_current_upper >= 0:
        valor_arriba = 0
    else:
        valor_arriba = percentage_current_upper

    if percentage_current_lower >= 0:
        valor_abajo = 0
    else:
        valor_abajo = percentage_current_lower
    
    distanceBB = (valor_arriba + valor_abajo) * -1
    

    logger.info(f"{symbol}, $: {current_price}, BBSup: {percentage_current_upper:.2f}%, BBInf: {percentage_current_lower:.2f}%, DBB: {distanceBB:.2f}%, RSI: {rsi:.1f}")
    return (current_price, current_upper, current_lower, percentage_current_upper, percentage_current_lower, symbol, rsi, distanceBB)


#Bollinger Data
def bollinger_trade_logic():
    symbol_df = get_data_frame()
    period = 20
    # small time Moving average. calculate 20 moving average using Pandas over close price
    symbol_df['sma'] = symbol_df['close'].rolling(period).mean()
    # Get standard deviation
    symbol_df['std'] = symbol_df['close'].rolling(period).std()
    # Calculate Upper Bollinger band
    symbol_df['upper'] = symbol_df['sma']  + (2 * symbol_df['std'])
    # Calculate Lower Bollinger band
    symbol_df['lower'] = symbol_df['sma']  - (2 * symbol_df['std'])
    # To print in human readable date and time (from timestamp)
    symbol_df.set_index('date', inplace=True)
    symbol_df.index = pd.to_datetime(symbol_df.index, unit='ms') # index set to first column = date_and_time

    (current_price, current_upper, current_lower, percentage_current_upper, percentage_current_lower, symbol, rsi, distanceBB) = buy_or_sell(symbol_df)
    return (current_price, current_upper, current_lower, percentage_current_upper, percentage_current_lower, symbol, rsi, distanceBB)


# RSI Data
def rsi_trade_logic():
    url = "https://fapi.binance.com/fapi/v1/klines?symbol="+symbol+"&interval="+interval+"&limit=100"
    data = requests.get(url).json()

    D = pd.DataFrame(data)
    D.columns = ["open_time", "open", "high", "low", "close", "volume", "close_time", "qav", "num_trades", "taker_base_vol", "taker_quote_vol", "is_best_match"]

    period = 14
    df = D
    df["close"] = df["close"].astype(float)
    df2 = df["close"].to_numpy()

    df2 = pd.DataFrame(df2, columns = ["close"])
    delta = df2.diff()

    up, down = delta.copy(), delta.copy()
    up[up<0] = 0
    down[down>0] = 0

    _gain = up.ewm(com = (period -1), min_periods = period).mean()
    _lost = down.abs().ewm(com = (period - 1), min_periods = period).mean()

    RS = _gain / _lost

    rsi = 100 - (100/(1+RS))
    rsi = rsi["close"].iloc[-1]
    rsi = round(rsi,1)
    text = "Binance futures: " + symbol + " RSI: " + str(rsi)
    #print(text)
    return (rsi)

    
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
                        roe = float(round((current_price - precio_entrada_slx) / current_price,4)) #trailling_stop_long
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
        """ 
        if (total_long <= 0 and total_short <= 0):
        for orders_futures in active_orders:
            if orders_futures["status"] == "NEW" and orders_futures["type"] == "STOP_MARKET":
                order_id = orders_futures["orderId"]
                order_symbol = orders_futures["symbol"]
                cancel_order = client.futures_cancel_order(
                    symbol = order_symbol,
                    orderId = order_id
                )
        """

    #print("Total de ordenes en LONG:", total_long)
    #print("Total de ordenes en SHORT:", total_short)
    #_message_ordenes_long = f"Resumén de ordenes actuales:\nOrdenes LONG: {total_long} - Ordenes SHORT: {total_short}\n"
    return(total_long, total_short, _message_ordenes_long, _message_ordenes_short)


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
    bollinger_trade_logic()
       # Change symbol here e.g. BTCUSDT, BNBBTC, ETHUSDT, NEOBTC