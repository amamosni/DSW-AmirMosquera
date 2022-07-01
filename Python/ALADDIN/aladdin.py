from symtable import Symbol
from _logger import logger
from _message import initialize_listening, send_message, send_message_orders_actually, conexionApi
from _trade import bollinger_trade_logic, long, short
from _config import config
import datetime

def mainloop():
    reporte_diario = 0
    msg_cnt = -0
    last_message_type = "Undefined"
    this_message_type = "Undefined"
    _message = "Undefined"

    while True:

        now = datetime.datetime.now()
        now_time = now.strftime('%d/%m/%Y %H:%M:%S')
        (current_price, current_upper, current_lower, percentage_current_upper, percentage_current_lower, symbol, rsi, distanceBB) = bollinger_trade_logic()
        _message_caption = f"**{symbol}** precio: ${current_price:.4f}\n"
        #_caption = f"{now_time} - {symbol} Precio actual: {current_price:.4f}, Temporalidad: {config['BINANCE_TRACE_INTERVAL']}, BB Superior: {current_upper:.4f}, BB Inferior: {current_lower:.4f}, Ratio: {current_price_percentage:.2f}%"
                
        if distanceBB >= float(config['DISTANCIA_ENTRE_BB']):
            
            # Determine Sell(Short) or Buy(Long) or Skip(Dejar)
            if percentage_current_upper >= float(config['BOLLINGER_VALOR']) and rsi >= float(config['RSI_ARRIBA']): #Porcentaje por fuera de la banda de bolinger para short
                _message = "🟥 SHORT en " + _message_caption + "\nBollinger arriba: " + f"{percentage_current_upper:.2f}%" + "\nRSI arriba: " f"{rsi:.2f}\n🤖 Bot ALADDIN\n" + now_time
                this_message_type = "Sell"
            elif percentage_current_lower >= float(config['BOLLINGER_VALOR'])  and rsi <= float(config['RSI_ABAJO']): #Porcentaje por fuera de la banda de bolinger para long
                _message = "🟩 LONG en " + _message_caption + "\nBollinger abajo: " + f"{percentage_current_lower:.2f}%" + "\nRSI abajo: " f"{rsi:.2f}\n🤖 Bot ALADDIN\n" + now_time
                this_message_type = "Buy"
            else:
                this_message_type = "Skip"

            # Revisar si entra en operación
            if (this_message_type == "Sell" or this_message_type == "Buy") and ((last_message_type != this_message_type) or msg_cnt > 5): #Cantidad de ciclos antes de repetir mensaje 90
                last_message_type = this_message_type
                try:
                    send_message(_message)
                except:
                    send_message(_message)
                    pass
                if this_message_type == "Sell" and config["ACTIVAR_SHORT"] == "SI":
                    short()
                    try:
                        send_message(f"Orden SHORT cerrada en " + symbol)
                    except:
                        send_message(f"Orden SHORT cerrada en " + symbol)
                    pass
                elif this_message_type == "Buy" and config["ACTIVAR_LONG"] == "SI":
                    long()
                    try:
                        send_message(f"Orden LONG cerrada en " + symbol)
                    except:
                        send_message(f"Orden LONG cerrada en " + symbol)
                    pass
                else:
                    send_message(f"Orden no creada.")
                
                msg_cnt = 0  # Reset Count until 30 (300s = 5Min)

        if msg_cnt < 9999999: # Don't have to count more than 9999999
            msg_cnt += 1
        
        #Reporte de monedas en LONG y SHORT
        reporte_diario += 1
        if reporte_diario == 5400: #Cada 2800 ciclos envia el resumen del día
            send_message_orders_actually()
            reporte_diario = 0

if __name__ == "__main__":
    logger.info(f"=== Inicio del programa ===")
    initialize_listening()
    conexionApi()
    mainloop()
    pass
