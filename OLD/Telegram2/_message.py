import telepot
import time
from telepot.loop import MessageLoop
from _config import config
from _logger import logger
from _trade import *

message_chat_id_list = eval(config["TELEGRAM_DEFAULT_CHAT_ID"])
graph_chat_id_list = eval(config["TELEGRAM_DEFAULT_CHAT_ID"])
bot = telepot.Bot(config["TELEGRAM_TOKEN"])

def initialize_listening():
    MessageLoop(bot, handle).run_as_thread()

    if message_chat_id_list is not None and \
            isinstance(message_chat_id_list, list) and \
            message_chat_id_list != []:
        for chat_id in message_chat_id_list:
            bot.sendMessage(chat_id, f"Inicialización del Bot para el par {pares}, en temporalidad de {config['BINANCE_TRACE_INTERVAL']}")

def handle(msg):
    global message_chat_id_list, graph_chat_id_list

    content_type, chat_type, chat_id = telepot.glance(msg)
    if chat_id in message_chat_id_list and msg is not None:
        if 'text' in msg.keys() and msg['text'] == 'quit':
            bot.sendMessage(chat_id, "No recibo informacion de compra. quit o graph Suscríbete si ingresas la cadena excluida.")
            message_chat_id_list.remove(chat_id)
        if 'text' in msg.keys() and msg['text'] == 'graph':
            if chat_id in graph_chat_id_list:
                bot.sendMessage(chat_id, "No recibir graficas. graph Entrar para agregar.")
                graph_chat_id_list = list(filter(lambda x: chat_id != x, graph_chat_id_list))
            else:
                bot.sendMessage(chat_id, "Cada 10 minutos recibir el gráfico. graph excluir.")
                graph_chat_id_list.append(chat_id)
    else:
        message_chat_id_list.append(chat_id)
        bot.sendMessage(
            chat_id, "Recibir información de compra cada 15 minutos. 'quit' apagar.")

    message_chat_id_list = list(set(message_chat_id_list))
    graph_chat_id_list = list(set(graph_chat_id_list))

    logger.info(str(msg))


def send_message_with_image(_caption, _file):
    for chat_id in message_chat_id_list:
        if chat_id in graph_chat_id_list:
            logger.info(f"Enviando mensaje: {_caption} con la imágen al chat_id:{chat_id}")
            bot.sendPhoto(chat_id, photo=open(_file, 'rb'), caption=_caption)
        else:
            logger.info(f"{chat_id} se omite porque no está el graph_chat_id_list")

def send_message(_message):
    for chat_id in message_chat_id_list:
        logger.info(f"Enviando mensaje: {_message} solo al chat_id:{chat_id}")
        bot.sendMessage(chat_id, _message, parse_mode="Markdown")


if __name__ == "__main__":
    # Keep the program running.
    MessageLoop(bot, handle).run_as_thread()
    logger.info('Telegram esta funcionando, online...')
    logger.warn("Para que funcione correctamente, ejecute python main.py")
    while 1:
        time.sleep(10)
