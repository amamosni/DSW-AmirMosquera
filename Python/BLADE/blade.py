from _logger import logger
from _message import initialize_listening, send_message, send_message_orders_actually
from _trade import order_book, long, short, conexionApi
from _config import config
import datetime
from time import sleep

def mainloop():
    order_book_cnt = 0
    resumen = 0
    last_message_type = "Undefined"
    this_message_type = "Undefined"
    _message = "Undefined"
    promedioA1 = 0
    promedioA2 = 0
    promedioA3 = 0
    promedioA4 = 0
    promedioA5 = 0
    promedioB1 = 0
    promedioB2 = 0
    promedioB3 = 0
    promedioB4 = 0
    promedioB5 = 0
    distance_block_arriba_promedio = 0
    distance_block_abajo_promedio = 0

    while True:

        now = datetime.datetime.now()
        now_time = now.strftime('%d/%m/%Y %H:%M:%S')
        (current_price, symbol, distance_block_arriba, distance_block_abajo, rsi) = order_book()
        _message_caption = f"**{symbol}** precio: ${current_price:.5f}\n"

        promedioA5 = promedioA4
        promedioA4 = promedioA3
        promedioA3 = promedioA2
        promedioA2 = promedioA1
        promedioA1 = distance_block_arriba      

        promedioB5 = promedioB4
        promedioB4 = promedioB3
        promedioB3 = promedioB2
        promedioB2 = promedioB1
        promedioB1 = distance_block_abajo
        print(f" 3 últimos a Long: {promedioA1:.2f}, {promedioA2:.2f}, {promedioA3:.2f}")
        print(f"3 últimos a Short: {promedioB1:.2f}, {promedioB2:.2f}, {promedioB3:.2f}, {promedioB4:.2f}, {promedioB5:.2f}")
        #distance_block_arriba_promedio = (promedioA1 + promedioA2 + promedioA3 + promedioA4 + promedioA5) / 5
        #distance_block_abajo_promedio = (promedioB1 + promedioB2 + promedioB3 + promedioB4 + promedioB5) / 5
        distance_block_arriba_promedio = (promedioA1 + promedioA2 + promedioA3) / 3
        distance_block_abajo_promedio = (promedioB1 + promedioB2 + promedioB3) / 3
        print(f"  A Long: {distance_block_arriba_promedio:.2f}")
        print(f" A Short: {distance_block_abajo_promedio:.2f}")

        if order_book_cnt >= 6: #Cantidad de ciclos antes de repetir mensaje 6
            # Determine Sell(Short) or Buy(Long) or Skip(Dejar)
            #if count_promedio <= 5
      
            if distance_block_abajo_promedio <= float(config['A_SHORT_MIN']) and distance_block_arriba_promedio >= float(config['A_SHORT_MAX']) and rsi >= float(config['RSI_SHORT']): #Porcentaje cerca de la order book para short
                _message = "🟥 SHORT en " + _message_caption + "\nPresión abajo del: " + f"{distance_block_abajo_promedio:.2f}%, RSI: {rsi}" + "\n🤖 Bot BLADE\n" + now_time
                this_message_type = "Sell"
            elif distance_block_arriba_promedio <= float(config['A_LONG_MIN']) and distance_block_abajo_promedio >= float(config['A_LONG_MAX']) and rsi <= float(config['RSI_LONG']): #Porcentaje cerca de la order book para long
                _message = "🟩 LONG en " + _message_caption + "\nPresión arriba del: " + f"{distance_block_arriba_promedio:.2f}%, RSI: {rsi}" + "\n🤖 Bot BLADE\n" + now_time
                this_message_type = "Buy"
            else:
                this_message_type = "Skip"

        # Revisar si entra en operación
        if (this_message_type == "Sell" or this_message_type == "Buy"): 
            #and ((last_message_type != this_message_type))
            #last_message_type = this_message_type
            
            #Enviar mensaje informando inicio de operación
            send_message(_message)

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
            
            order_book_cnt = 0 # Reset Count

        if resumen > 5400:
            send_message_orders_actually()
            resumen = 0

        if order_book_cnt < 9999999: # Don't have to count more than 9999999
            order_book_cnt += 1
        if resumen < 9999999: # Don't have to count more than 9999999
            resumen += 1
        sleep(2)

if __name__ == "__main__":
    logger.info(f"=== Inicio del programa ===")
    conexionApi()
    initialize_listening()
    mainloop()
    pass
