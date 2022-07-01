import time
import telegram
from _config import config
from _logger import logger
from _trade import *

#graph_chat_id_list = eval(config["TELEGRAM_DEFAULT_CHAT_ID"])
message_chat_id_list = eval(config["TELEGRAM_DEFAULT_CHAT_ID"])
bot = telegram.Bot(config["TELEGRAM_TOKEN"])

def initialize_listening():
    (usdt_balance_futuros) = saldo_futuros()

    if message_chat_id_list is not None and \
            isinstance(message_chat_id_list, list) and \
            message_chat_id_list != []:
        for chat_id in message_chat_id_list:
            bot.sendMessage(chat_id, f"🤖 Iniciando el Bot para los pares: {pares}, en temporalidad de {config['BINANCE_TRACE_INTERVAL']}.\n💵 Saldo en cuenta de futuros:  {usdt_balance_futuros:.2f} dólares.\nRegistrate en Binance: https://bit.ly/ObtenCriptos")

"""
def send_message_with_image(_caption, _file):
    for chat_id in message_chat_id_list:
        if chat_id in graph_chat_id_list:
            logger.info(f"Enviando mensaje: {_caption} con la imágen al chat_id:{chat_id}")
            bot.sendPhoto(chat_id, photo=open(_file, 'rb'), caption=_caption)
        else:
            logger.info(f"{chat_id} se omite porque no está el graph_chat_id_list")
"""
def send_message(_message):
    for chat_id in message_chat_id_list:
        #logger.info(f"Enviando mensaje: {_message} solo al chat_id:{chat_id}")
        logger.info(f"Enviando mensaje al chat_id:{chat_id}")
        bot.sendMessage(chat_id, _message, parse_mode="Markdown")

def send_message_orders_actually():
    (usdt_balance_futuros) = saldo_futuros()
    (total_long, total_short, _message_ordenes_long, _message_ordenes_short) = total_ordenes_activas()
    (contar_filled, contar_cancelled, contar_expired) = total_ordenes_resumen()
    _message_total_ordenes_actualmente = f"🚀 Resumén de ordenes activas:\n🟩 Ordenes LONG: {total_long} - 🟥 Ordenes SHORT: {total_short}\n\n{_message_ordenes_long}\n{_message_ordenes_short}\n🚦 Resumen del día: \nLlevas {contar_filled} ordenes ejecutadas, {contar_cancelled} ordenes canceladas y {contar_expired} ordenes expiradas.\n💵 Saldo en cuenta de futuros: {usdt_balance_futuros:.2f}"
    send_message(_message_total_ordenes_actualmente)

if __name__ == "__main__":
    # Keep the program running.
    #telegram(bot)
    logger.info('Telegram esta online...')
    logger.warn("Para que funcione correctamente, ejecute python main.py")
    while 1:
        time.sleep(1)
