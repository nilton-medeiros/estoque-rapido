# log_config.py
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent

def get_log_dir():
    return ROOT_DIR / 'logs'

class LogConfig:
    def __init__(self, log_level=logging.DEBUG):
        log_dir = get_log_dir()
        print("Entrou em LogConfig")

        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception as e:
            print(f"Error creating log directory: {e}")
            return # Caso não consiga criar o diretório

        log_file = os.path.join(log_dir, "app.log")

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Configura o logger raiz
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        try:
            file_handler = RotatingFileHandler(log_file, maxBytes=5242880, backupCount=5)
            print("Criou o file_handler")
        except Exception as e:
            print(f"Error creating RotatingFileHandler: {e}")
            return # Caso não consiga criar o logger, não tenta mais nada

        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        root_logger.addHandler(console_handler)

# Instancia a configuração do log uma única vez
LogConfig()
