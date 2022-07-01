from _logger import logger
from dotenv import dotenv_values
import os
import shutil
import json

path_to_read = ".env"
if os.path.exists(path_to_read):
    config = dotenv_values(path_to_read)
else:
    shutil.copyfile("config.env",".env")
    logger.error("El archivo .env no existe y fue creado a partir de una plantilla. Edita el .env y vuelve a intentarlo")

if __name__ == "__main__":
    logger.info("[Configuración cargada]\n{}".format(json.dumps(config, indent=4, sort_keys=True, separators=(",",": "))))
    logger.error("Ejecutar python main.py, en su lugar")
