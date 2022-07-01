import telepot
import time
from telepot.loop import MessageLoop
from _config import config
from _logger import logger
from _trade import *

message_chat_id_list = eval(config["TELEGRAM_DEFAULT_CHAT_ID"])
bot = telepot.Bot(config["TELEGRAM_TOKEN"])

def initialize_listening():
    MessageLoop(bot)
    (usdt_balance_futuros) = saldo_futuros()
    try:
        if message_chat_id_list is not None and \
                isinstance(message_chat_id_list, list) and \
                message_chat_id_list != []:
            for chat_id in message_chat_id_list:
                textinitial = (f"🤖 Iniciando el Bot BOOKER 📖 para el par: {pares}.\n💵 Saldo en cuenta de futuros:  {usdt_balance_futuros:.2f} dólares.\nRegistrate en Binance: https://bit.ly/ObtenCriptos")
                bot.sendMessage(chat_id, textinitial)
    except Exception as _e:
            logger.warn(
            "Error al enviar el mensaje : {}".format(str(_e)))
            pass
def send_message(_message):
    try:
        for chat_id in message_chat_id_list:
            #logger.info(f"Enviando mensaje: {_message} solo al chat_id:{chat_id}")
            logger.info(f"Enviando mensaje al chat_id:{chat_id}")
            bot.sendMessage(chat_id, _message, parse_mode="Markdown")
    except Exception as _e:
            logger.warn(
            "Error al enviar el mensaje : {}".format(str(_e)))
            pass

def send_message_orders_actually():
    try:
        (usdt_balance_futuros) = saldo_futuros()
        (total_long, total_short, _message_ordenes_long, _message_ordenes_short) = total_ordenes_activas()
        (contar_filled, contar_cancelled, contar_expired) = total_ordenes_resumen()
        _message_total_ordenes_actualmente = f"🚀 Resumén de ordenes activas:\n🟩 Ordenes LONG: {total_long}\n🟥 Ordenes SHORT: {total_short}\n---------------\n{_message_ordenes_long}\n{_message_ordenes_short}\n🚦 Resumen del día: \nLlevas {contar_filled} ordenes ejecutadas, {contar_cancelled} ordenes canceladas y {contar_expired} ordenes expiradas.\n💵 Saldo en cuenta de futuros: {usdt_balance_futuros:.2f}"
        send_message(_message_total_ordenes_actualmente)
    except Exception as _e:
            logger.warn(
            "Error al enviar el mensaje : {}".format(str(_e)))
            pass

if __name__ == "__main__":
    # Keep the program running.
    MessageLoop(bot)
    logger.info('Telegram esta online...')
    logger.warn("Para que funcione correctamente, ejecute python main.py")
    while 1:
        time.sleep(1)


