import aiohttp

async def consult_cnpj_api(cnpj):

    # Remove caracteres especiais do CNPJ
    cnpj_clean = ''.join(filter(str.isdigit, cnpj))

    """
    url = www.receitaws.com.br/v1/cnpj: 3 consultas por minuto
    # 3 consultas por minuto
    url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj_clean}"
    # 50.000 consultas por mês
    url = f"https://api.nuvemfiscal.com.br/cnpj/{cnpj_clean}"
        token = "SEU_TOKEN"
        headers = {
            "Accept": "*/*",
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(url, headers=headers)
    """
    try:
        # Faz a consulta à API
        url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_clean}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return {
                    'is_error': False,
                    'response': response,
                    'data': await response.json()
                }

    except Exception as error:
        # Mostra erro genérico
        return {
            'is_error': True,
            'message': f"Erro ao consultar CNPJ: {str(error)}"
        }


async def main():
    result = await consult_cnpj_api("06953263000100")

    print(f"Error: {result['is_error']}")
    print(f"Response: {result['response']}")
    print(f"Status: {result['response'].status}")
    # print(f"Data: {result['data']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())