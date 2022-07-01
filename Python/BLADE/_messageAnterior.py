import time
import telegram
from _config import config
from _logger import logger
from _trade import *

message_chat_id_list = eval(config["TELEGRAM_DEFAULT_CHAT_ID"])
bot = telegram.Bot(config["TELEGRAM_TOKEN"])

def initialize_listening():
    (usdt_balance_futuros) = saldo_futuros()

    if message_chat_id_list is not None and \
            isinstance(message_chat_id_list, list) and \
            message_chat_id_list != []:
        for chat_id in message_chat_id_list:
            textinitial = (f"🤖 Iniciando el Bot BUHO 🦉 para el par: {pares}, en temporalidad de {config['BINANCE_TRACE_INTERVAL']}.\n💵 Saldo en cuenta de futuros:  {usdt_balance_futuros:.2f} dólares.\nRegistrate en Binance: https://bit.ly/ObtenCriptos")
            #textinitial = (textinitial.encode("utf-8"))
            bot.sendMessage(chat_id, textinitial)

def send_message(_message):
    for chat_id in message_chat_id_list:
        logger.info(f"Enviando mensaje al chat_id:{chat_id}")
        bot.sendMessage(chat_id, _message, parse_mode="Markdown")

if __name__ == "__main__":
    # Keep the program running.
    telegram(bot)
    logger.info('Telegram esta online...')
    logger.warn("Para que funcione correctamente, ejecute python main.py")
    while 1:
        time.sleep(1)
