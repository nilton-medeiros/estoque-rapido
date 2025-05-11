import logging
from src.domains.empresas import Environment
from src.services.providers.nuvemfiscal_provider import NuvemFiscalDFeProvider
from src.services.apis.dfe_services import DFeServices

logger = logging.getLogger(__name__)

"""
Essa estrutura garante um controle claro de responsabilidades, onde dfe_controller atua organizando
e redirecionando os dados ao repositório de dados do provedor DFe (Documento Fiscal Eletrônico).
Isso promove uma arquitetura mais limpa e modular, facilitando manutenção e escalabilidade do sistema.
"""

async def handle_upload_certificate_a1(
        cpf_cnpj: str, certificate_content: bytes,
        a1_password: str, ambiente: Environment) -> dict:
    """
    Manipula a operação de upload do certificado A1 (pfx/p12).

    Esta função manipula a operação de enviar (upload) um binário do certificado A1 codificado na base64 para
    o provedor de API de DFe's (Documentos Fiscais Eletronicos).
    Este controller utiliza um repositório específico para realizar as operações necessárias com o provider.
    Aqui o provider de API pode ser trocado facilmente: Nuvem Fiscal, Focus NFe, WebManiaBR, etc.

    Args:
        cpf_cnpj (str): Documento do emitente da NFC-e (CPF ou CNPJ).
        a1_encoded_base64 (str): O binário do certificado digital A1 codificado em base64.
        a1_password (str): Senha do certificado digital A1
        ambiente (Environment): Tipo de API a ser consumida, Produção: API de produção ou Homologação (Sandbox): API de teste.

    Returns:
        dict: Um dicionário contendo o status da operação, uma mensagem de sucesso ou erro, e os dados do A1.

    Raises:
        ValueError: Se houver um erro de validação ao enviar o A1 para o provider.
        Exception: Se ocorrer um erro inesperado durante a operação.

    Exemplo:
        # Codifica o conteúdo em Base64
        base64_encoded = base64.b64encode(file_content).decode("utf-8")

        >>> # Envia o certificado para a API do provedor
        >>> cpf_cnpj = cnpj.value if tipo_doc.value == "CNPJ" else cpf.value
        >>> response = handle_upload_certificate_a1(cpf_cnpj, base64_encoded, 'senha_123')
        >>> print(response)
    """
    response = {
        "is_error": False,
        "message": "",
        "certificate": None
    }

    try:
        # Usa o provider Nuvem Fiscal, troque o provider abaixo se quiser usar outro provedor.
        provider = NuvemFiscalDFeProvider(ambiente)
        dfe_service = DFeServices(provider, cpf_cnpj)

        result = await dfe_service.certificate_save(certificado=certificate_content, password=a1_password)

        response["is_error"] = result.get("is_error")
        response["message"] = result.get("message")
        response["certificate"] = result.get("certificate", None)

    except ValueError as e:
        response["is_error"] = True
        response["message"] = f"Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["is_error"] = True
        response["message"] = str(e)
        logger.error(response["message"])

    return response
