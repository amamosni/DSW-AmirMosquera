from _logger import logger
from _message import initialize_listening, send_message, send_message_orders_actually
from _trade import actualizar_precio, order_book, long, short, conexionApi
from _config import config
import datetime
from time import sleep

def mainloop():
    order_book_cnt = 0
    resumen = 0
    last_message_type = "Undefined"
    this_message_type = "Undefined"
    _message = "Undefined"
    distance_block_arriba = 0
    distance_block_abajo = 0

    while True:

        now = datetime.datetime.now()
        now_time = now.strftime('%d/%m/%Y %H:%M:%S')
        print("--- Buscando bloque de ordenes ---")
        sleep(3)
        (current_price, symbol, block_arriba, block_abajo) = order_book()
        
        while order_book_cnt == 0:

            (current_price) = actualizar_precio()
            distance_block_arriba = float(round((block_arriba - current_price) / block_arriba,4) * 100)
            distance_block_abajo = float(round((current_price - block_abajo) / block_abajo,4) * 100)
            _message_caption = f"**{symbol}** precio: ${current_price:.5f}\n"

            print("            Moneda: " + symbol)
            print(f"    Precio actual: {current_price:.5f}")
            print(f"    Bloque arriba: {block_arriba:.5f}")
            print(f"Distancia a SHORT: {distance_block_arriba:.2f}")
            print(f"     Bloque abajo: {block_abajo:.5f}") 
            print(f" Distancia a LONG: {distance_block_abajo:.2f}")
            print("------------------------------")

        
            if distance_block_arriba <= float(config['NEAR_ORDER_BOOK']): #Porcentaje cerca de la order book para short
                _message = "🟥 SHORT en " + _message_caption + "\n🤖 Bot BOOKER\n" + now_time
                this_message_type = "Sell"
            elif distance_block_abajo <= float(config['NEAR_ORDER_BOOK']): #Porcentaje cerca de la order book para long
                _message = "🟩 LONG en " + _message_caption + "\n🤖 Bot BOOKER\n" + now_time
                this_message_type = "Buy"
            else:
                this_message_type = "Skip"

            # Revisar si entra en operación
            if (this_message_type == "Sell" or this_message_type == "Buy") and ((last_message_type != this_message_type) or order_book_cnt == 0):
                last_message_type = this_message_type
                
                #Enviar mensaje informando inicio de operación
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
                    
                order_book_cnt = 1 # Reset Count until 30 (300s = 5Min)
            if resumen > 5400:
                send_message_orders_actually()
                resumen = 0
                
            if resumen < 9999999: # Don't have to count more than 9999999
                resumen += 1
            sleep(1)
        order_book_cnt = 0

if __name__ == "__main__":
    logger.info(f"=== Inicio del programa ===")
    conexionApi()
    initialize_listening()
    mainloop()
    pass
