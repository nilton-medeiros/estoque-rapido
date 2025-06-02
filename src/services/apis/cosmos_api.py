import requests
import json
import os
import logging

# Configurar o logger
logger = logging.getLogger(__name__)

# É uma boa prática carregar configurações sensíveis de variáveis de ambiente
# Você precisaria ter COSMOS_API_TOKEN definido no seu .env e carregado adequadamente
# (ex: usando python-dotenv na inicialização da sua aplicação)
COSMOS_API_TOKEN = os.getenv("COSMOS_API_TOKEN")
COSMOS_BASE_URL = "https://api.cosmos.bluesoft.com.br/gtins"

HEADERS = {
    'X-Cosmos-Token': COSMOS_API_TOKEN,
    'Content-Type': 'application/json',
    'User-Agent': 'EstoqueRapidoApp/1.0 Cosmos-API-Client'
}

def fetch_product_info_by_ean(ean: str) -> dict | None:
    """
    Consulta informações de um produto pelo código EAN na API Cosmos.

    Args:
        ean: O código EAN (GTIN) do produto a ser consultado.

    Returns:
        Um dicionário com os dados do produto se encontrado, None caso contrário ou em caso de erro.
    """
    if not COSMOS_API_TOKEN:
        logger.error("Token da API Cosmos não configurado. Verifique a variável de ambiente COSMOS_API_TOKEN.")
        return None

    url = f"{COSMOS_BASE_URL}/{ean}.json"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10) # Adicionado timeout
        response.raise_for_status()  # Levanta uma exceção para respostas de erro HTTP (4xx ou 5xx)
        result = {"status_code": response.status_code, "data": response.json()}
        logger.info(f"Dados do produto EAN {ean} obtidos com sucesso.")
        return result

    except requests.exceptions.HTTPError as http_err:
        status_code = http_err.response.status_code
        response_text = http_err.response.text
        if status_code == 401:
            logger.error(f"Erro de autenticação (401) ao consultar API Cosmos para EAN {ean}. Verifique o COSMOS_API_TOKEN. Detalhes: {response_text}")
        elif status_code == 403:
            logger.error(f"Acesso negado (403) ao consultar API Cosmos para EAN {ean}. Verifique as permissões do token. Detalhes: {response_text}")
        elif status_code == 404:
            logger.warning(f"Recurso não encontrado (404) na API Cosmos para EAN {ean}. O produto pode não existir. Detalhes: {response_text}")
        elif status_code == 422:
            logger.error(f"Erro de negócio/validação (422) ao consultar API Cosmos para EAN {ean}. Verifique os dados enviados. Detalhes: {response_text}")
        elif status_code == 429:
            logger.warning(f"Limite de requisições excedido (429) para a API Cosmos ao consultar EAN {ean}. Tente novamente mais tarde. Detalhes: {response_text}")
            return {"status_code": status_code, "message": response_text}
        elif 400 <= status_code < 500:
            logger.error(f"Erro do cliente HTTP ({status_code}) ao consultar API Cosmos para EAN {ean}: {http_err} - Response: {response_text}")
        elif 500 <= status_code < 600:
            logger.error(f"Erro de servidor HTTP ({status_code}) da API Cosmos ao consultar EAN {ean}: {http_err} - Response: {response_text}")
        else:
            logger.error(f"Erro HTTP inesperado ({status_code}) ao consultar API Cosmos para EAN {ean}: {http_err} - Response: {response_text}")
    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"Erro de conexão ao tentar acessar API Cosmos para EAN {ean}: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        logger.error(f"Timeout ao tentar acessar API Cosmos para EAN {ean}: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Erro geral na requisição para API Cosmos para EAN {ean}: {req_err}")
    except json.JSONDecodeError as json_err:
        logger.error(f"Erro ao decodificar JSON da resposta da API Cosmos para EAN {ean}: {json_err} - Response: {response.text if 'response' in locals() else 'N/A'}")

    return None

# if __name__ == '__main__':
#     # Exemplo de uso (apenas para teste direto do script)
#     # Para usar em sua aplicação, você importaria a função fetch_product_info_by_ean

#     # Para carregar variáveis do .env ao executar este script diretamente
#     from dotenv import load_dotenv
#     load_dotenv()

#     COSMOS_API_TOKEN = os.getenv("COSMOS_API_TOKEN")
#     HEADERS['X-Cosmos-Token'] = COSMOS_API_TOKEN

#     # Configuração básica de logging para o exemplo
#     logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

#     # Simular que o token está no ambiente para o teste
#     # Em uma aplicação real, isso seria carregado de um .env
#     if not COSMOS_API_TOKEN:
#         # Esta mensagem agora só aparecerá se o .env não tiver a variável ou não for carregado corretamente
#        >>> print("AVISO: COSMOS_API_TOKEN não foi encontrado após tentar carregar o .env. Verifique seu arquivo .env ou defina a variável manualmente para teste.")
#         # Exemplo: COSMOS_API_TOKEN = "SEU_TOKEN_AQUI" # Apenas para teste local, não commitar!
#         # Se não definir e a função for chamada, retornará None e logará um erro.

#     # test_ean = "7891910000197" # EAN de exemplo
#     test_ean = "7896089500233" # EAN de exemplo
#     product_data = fetch_product_info_by_ean(test_ean)

#    >>> if product_data:
#    >>>     print("\nDados do Produto:")
#    >>>     print(json.dumps(product_data, indent=4, ensure_ascii=False))
#    >>> else:
#    >>>     print(f"\nNão foi possível obter dados para o EAN {test_ean}.")
