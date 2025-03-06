import os
import urllib.parse
import logging
from typing import Dict, Optional
import aiohttp
from datetime import datetime, timedelta, timezone

from src.controllers.app_config_controller import handle_get_config, handle_save_config
from src.domain.models.certificate_a1 import CertificateA1
from src.domain.models.company import Company
from src.domain.models.company_subclass import Environment
from src.services.contracts.dfe_provider import DFeProvider

logger = logging.getLogger(__name__)


class NuvemFiscalDFeProvider(DFeProvider):
    """Um Provider para gerenciar a integração com a API da Nuvem Fiscal"""

    def __init__(self, ambiente: Environment):
        self.token = None
        self.token_expires_in = None
        self.settings = None
        self._token_get()

        # Verifica se o ambiente é do tipo correto
        if not isinstance(ambiente, Environment):
            raise ValueError(
                'O parâmetro "ambiente" deve ser um valor do enum Environment: Environment.PRODUCAO ou Environment.HOMOLOGACAO.'
            )

        # Define a URL base conforme o ambiente
        self.base_url = (
            "https://api.nuvemfiscal.com.br"
            if ambiente == Environment.PRODUCAO
            else "https://api.sandbox.nuvemfiscal.com.br"
        )

    async def certificate_save(self, cpf_cnpj: str, certificate_binary: bytes, password: str) -> CertificateA1:
        """
        Cadastra ou atualiza um certificado digital e vincula a empresa emitente,
        para que possa iniciar a emissão de notas.

        Args:
            cpf_cnpj: CPF ou CNPJ da empresa sem máscara
            certificate_binary: Binário do certificado digital (.pfx ou .p12)
            password: Senha do certificado

        Returns:
            CertificateA1: Objeto com as informações do certificado ou None em caso de erro
        """
        if not self.token:
            logger.error("Token não disponível para upload do certificado")
            result = {
                "is_error": True,
                "message": "Token não disponível para upload do certificado",
            }

            return result

        # Garante a remoção de caracteres especiais do documento CNPJ/CPF
        cpf_cnpj = ''.join(filter(str.isdigit, cpf_cnpj))

        try:
            # Endpoint correto para upload do certificado
            endpoint = f"/empresas/{cpf_cnpj}/certificado"
            url = f"{self.base_url}{endpoint}"

            # Codifica o binário do certificado em base64
            import base64
            certificate_base64 = base64.b64encode(certificate_binary)

            # Prepara o payload
            payload = {
                "certificado": certificate_base64,
                "password": password
            }

            # Configura os headers com o token de autenticação
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}"
            }

            # Realiza a requisição PUT (método corrigido)
            async with aiohttp.ClientSession() as session:
                async with session.put(url,
                                       headers=headers,
                                       json=payload) as response:

                    # Processa a resposta
                    if response.status == 200:
                        certificate_data = await response.json()
                        logger.info(
                            f"Certificado salvo com sucesso para o documento: {cpf_cnpj}")

                        # Cria e retorna o objeto CertificateA1 com os dados da resposta
                        certificate = CertificateA1(
                            serial_number=certificate_data.get(
                                "serial_number"),
                            issuer_name=certificate_data.get("issuer_name"),
                            not_valid_before=datetime.fromisoformat(
                                certificate_data.get("not_valid_before").replace("Z", "+00:00")),
                            not_valid_after=datetime.fromisoformat(
                                certificate_data.get("not_valid_after").replace("Z", "+00:00")),
                            thumbprint=certificate_data.get("thumbprint"),
                            subject_name=certificate_data.get("subject_name"),
                            cpf_cnpj=certificate_data.get("cpf_cnpj"),
                            nome_razao_social=certificate_data.get(
                                "nome_razao_social"),
                            password=password
                        )

                        result = {
                            "is_error": False,
                            "message": f"Certificado salvo com sucesso para o documento: {cpf_cnpj}",
                            "certificate": certificate
                        }

                        return result
                    else:
                        # Verifica o content-type da resposta para processar adequadamente
                        content_type = response.headers.get('Content-Type', '')

                        result = {
                            "is_error": True,
                            "message": "",
                        }
                        message = ""

                        if 'application/json' in content_type:
                            # Resposta é um JSON
                            error_data = await response.json()
                            error_code = error_data.get(
                                'error', {}).get('code', 'Unknown')
                            error_message = error_data.get('error', {}).get(
                                'message', 'No error message provided')
                            message = f"Erro ao salvar certificado: Status {response.status} - Código: {error_code} - Mensagem: {error_message}"
                            logger.error(message)
                        elif content_type.startswith('text/'):
                            # Resposta é texto
                            error_text = await response.text()
                            message = f"Erro ao salvar certificado: Status {response.status} - Resposta em texto: {error_text}"
                            logger.error(message)
                        else:
                            # Outro tipo de resposta
                            message = f"Erro ao salvar certificado: Status {response.status} - Content-Type: {content_type}"
                            logger.error(message)

                        result["message"] = message
                        return result

        except Exception as e:
            result = {
                "is_error": True,
                "message": f"Erro ao salvar certificado: {str(e)}",
            }

            logger.error(f"Erro ao salvar certificado: {str(e)}")
            return result

    async def certificate_get(self, cpf_cnpj: str) -> CertificateA1:
        """Consulta um certificado digital pelo documento vinculado a empresa emitente."""
        raise NotImplementedError("Módulo aguardando implementação")

    async def certificate_delete(self, cpf_cnpj: str) -> bool:
        """Exclui um certificado digital pelo documento vinculado a empresa emitente."""
        raise NotImplementedError("Módulo aguardando implementação")

    async def company_save(self, issuer: Company) -> str:
        """Cadastra uma nova empresa (emitente/prestador) no Provedor DFe."""
        raise NotImplementedError("Módulo aguardando implementação")

    async def company_update(self, issuer: Company) -> str:
        """Altera o cadastro de uma empresa (emitente/prestador) no Provedor DFe."""
        raise NotImplementedError("Módulo aguardando implementação")

    async def company_get(self, cpf_cnpj: str) -> Company:
        """Consulta uma empresa (emitente/prestador) pelo seu documento."""
        raise NotImplementedError("Módulo aguardando implementação")

    async def company_delete(self, cpf_cnpj: str) -> bool:
        """Exclui uma empresa (emitente/prestador) no Provedor de DFe."""
        raise NotImplementedError("Módulo aguardando implementação")

    async def _token_get(self):
        # Acessa o database para consultar informações do token, o id do documento é 'settings'
        response = handle_get_config("settings")

        if response['is_found']:
            # Verifica se o token expirou
            self.settings = response['settings']
            self.token = self.settings.dfe_api_token
            self.token_expires_in = self.settings.dfe_api_token_expires_in
            self.settings.dfe_api_token = self.token
            self.settings.dfe_api_token_expires_in = self.token_expires_in

        # Obtem a data e hora do servidor em UTC
        agora_utc = datetime.now(timezone.utc)

        # Se não encontrou, obtem um novo token, se encontrou (is_found), verifica a validade do token
        if not self.token_expires_in or (self.token_expires_in <= agora_utc):
            # Validade do Token expirou ou token não encontrado, obtem novo token da API da Nuvemfiscal
            token_data = self._new_token_get()

            if token_data:
                # Campo 'expires_in' é retornado em segundos
                expires_in: int = token_data['expires_in']
                date_now = datetime.fromisoformat(token_data['create_at'])
                date_expiration = date_now + timedelta(seconds=expires_in)

                self.token = token_data['access_token']
                self.token_expires_in = date_expiration
                self.settings.dfe_api_token = self.token
                self.settings.dfe_api_token_expires_in = date_expiration

                # Atualiza a nova configuração no database coleção app_config id: settings
                response = handle_save_config(
                    settings=self.settings, create_new=False)
                if response['is_error']:
                    logger.error(
                        f"Erro ao salvar settings no db: Mensagem {response['message']}")
                    return None

    async def _new_token_get(self) -> Optional[Dict]:
        """
        Obtém um novo token de acesso usando o fluxo OAuth 2.0 client_credentials.

        Returns:
            Dict: Dicionário contendo o token e informações relacionadas ou None em caso de erro
        """
        try:
            # Configuração do endpoint e headers
            token_url = "https://auth.nuvemfiscal.com.br/oauth/token"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }

            # Obtém as credenciais das variáveis de ambiente
            client_id = os.getenv("NUVEMFISCAL_CLIENT_ID")
            client_secret = os.getenv("NUVEMFISCAL_CLIENT_SECRET")

            if not client_id or not client_secret:
                logger.error(
                    "Credenciais da Nuvem Fiscal não encontradas nas variáveis de ambiente")
                return None

            # Prepara os parâmetros da requisição com percent-encoding
            params = {
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
                "scope": "conta empresa cep cnpj nfce"
            }

            # Codifica os parâmetros no formato correto
            encoded_params = urllib.parse.urlencode(params)

            # Realiza a requisição POST
            async with aiohttp.ClientSession() as session:
                async with session.post(token_url,
                                        headers=headers,
                                        data=encoded_params) as response:

                    if response.status != 200:
                        logger.error(
                            f"Erro ao obter token: Status {response.status}")
                        return None

                    token_data = await response.json()

                    # Adiciona timestamp da criação do token
                    token_data['created_at'] = datetime.now(
                        timezone.utc).isoformat()

                    logger.info("Token obtido com sucesso")
                    return token_data

        except Exception as e:
            logger.error(f"Erro ao obter token: {str(e)}")
            return None
