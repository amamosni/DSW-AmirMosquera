from symtable import Symbol
from _logger import logger
from _message import initialize_listening
from _trade import bollinger_trade_logic
from _message import send_message_with_image, send_message
from _config import config
from time import sleep
import datetime


def mainloop():
    img_cnt = -1
    msg_cnt = -1
    last_message_type = "Undefined"
    this_message_type = "Undefined"
    _message = "*Undefined*"

    while True:

        now = datetime.datetime.now()
        now_time = now.strftime('%d/%m/%Y %H:%M:%S')
        (current_price, current_upper, current_lower,
         current_price_percentage, percentage_current_upper, percentage_current_lower, symbol) = bollinger_trade_logic()
        _message_caption = f"{symbol} precio: ${current_price:.4f}\n"
        _caption = f"{now_time} - {symbol} Precio actual: {current_price:.4f}, Temporalidad: {config['BINANCE_TRACE_INTERVAL']}, BB Superior: {current_upper:.4f}, BB Inferior: {current_lower:.4f}, Ratio: {current_price_percentage:.2f}%"

        # Graph First time and after, every 10Min
        if img_cnt > 10:
            try:
                send_message_with_image(_caption, "output.jpg")
            except Exception as _e:
                logger.warn("Error al enviar el mensaje: {}".format(str(_e)))
            img_cnt = 0

        if img_cnt < 9999999:  # Don't have to count more than 9999999
            img_cnt += 1

        # Determine Sell(Short) or Buy(Long) or Skip(Dejar)
        config['BOLLINGER_VALOR'] = float(True)
        if percentage_current_upper >= config['BOLLINGER_VALOR']: #Porcentaje por fuera de la banda de bolinger para short
            _message = "🟥 SHORT en " + _message_caption + "Se movio un " + f"{percentage_current_upper:.2f}%" + " por encima de la banda de bollinger.\n" + now_time
            this_message_type = "Sell"

        elif percentage_current_lower >= config['BOLLINGER_VALOR']: #Porcentaje por fuera de la banda de bolinger para long
            _message = "🟩 LONG en " + _message_caption + "Se movio un " + f"{percentage_current_lower:.2f}%" + " por debajo de la banda de bollinger.\n" + now_time
            this_message_type = "Buy"

        else:
            this_message_type = "Skip"

        logger.debug("DETERMINE: last_message_type:{}, this_message_type:{}, current_price_percentage:{}, msg_cnt:{}".format(
            last_message_type, this_message_type, current_price_percentage, msg_cnt))

        # Send Message
        if (this_message_type == "Sell" or this_message_type == "Buy") and \
           ((last_message_type != this_message_type) or msg_cnt > 1): #Cantidad de ciclos antes de repetir mensaje 10
            last_message_type = this_message_type
            try:
                send_message(_message)
            except Exception as _e:
                logger.warn(
                    "Error al enviar el mensaje : {}".format(str(_e)))
            msg_cnt = 0  # Reset Count until 90 (900s = 15Min)

        if msg_cnt < 9999999: # Don't have to count more than 9999999
            msg_cnt += 1

        logger.info(f"Ciclo de mensajes/Contador de imágen - msg_cnt:{msg_cnt} / img_cnt:{img_cnt}")
        sleep(1)  # 10 Second, cada cuando hace el ciclo


if __name__ == "__main__":
    logger.info(f"=== Program Loop Start ===")
    initialize_listening()
    mainloop()
    pass
