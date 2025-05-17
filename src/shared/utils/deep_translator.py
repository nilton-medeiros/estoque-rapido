import logging
import os
import deepl

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def deepl_translator(texto_ingles: str) -> str:
    """
    Tradução do Inglês para Português Brasil via Deepl.

    Args:
        texto_ingles (str): Texto em inglês que será traduzido.

    Returns:
        str: Texto traduzido para o português.

    Exceções:
        ValueError: Se o texto fornecido for inválido.
        Exception: Se a API key não for encontrada.
    """
    # Carrega as variáveis de ambiente do arquivo .env
    load_dotenv()
    auth_key = os.getenv('DEEPL_API_KEY')

    if auth_key is None:
        logger.warning("API key is required. Configure a variável DEEPL_API_KEY no arquivo .env.")
        raise Exception("API key is required. Configure a variável DEEPL_API_KEY no arquivo .env.")

    if not texto_ingles or not isinstance(texto_ingles, str):
        logger.warning("Texto inválido. Forneça um texto em inglês válido para tradução.")
        raise ValueError("Texto inválido. Forneça um texto em inglês válido para tradução.")

    try:
        # Configura a API Deepl
        translator = deepl.Translator(auth_key)
        traducao = translator.translate_text(texto_ingles, source_lang="EN", target_lang="PT-BR")
        return traducao.text # type: ignore  # Retorna apenas o texto traduzido
    except deepl.DeepLException as e:
        logger.error(f"Erro ao usar a API Deepl: {e}")
        raise Exception(f"Erro ao usar a API Deepl: {e}")
