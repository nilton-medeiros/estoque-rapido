import logging
from enum import Enum  # Certifique-se de importar o módulo 'Enum'

from typing import Optional

from google.cloud.firestore import Query
from google.cloud.firestore_v1.base_query import FieldFilter
from firebase_admin import firestore
from firebase_admin import exceptions

from src.domains.empresas.models.cnpj import CNPJ  # Importação direta
from src.domains.empresas.models.empresa_model import Empresa  # Importação direta
from src.domains.empresas.repositories.contracts.empresas_repository import EmpresasRepository
from src.services.gateways.asaas_payment_gateway import AsaasPaymentGateway
from src.shared import deepl_translator
from storage.data.firebase.firebase_initialize import get_firebase_app

logger = logging.getLogger(__name__)


class FirebaseEmpresasRepository(EmpresasRepository):
    """
    Um repositório para gerenciar empresas utilizando o Firebase Firestore.

    Esta classe fornece métodos para realizar operações de CRUD em dados de empresas
    armazenados em um banco de dados Firestore.
    """

    def __init__(self):
        """
        Inicializa o cliente do Firebase Firestore e conecta-se à coleção 'empresas'.

        Garante que o aplicativo Firebase seja inicializado antes de criar o cliente Firestore.
        """
        # fb_app = get_firebase_app()
        get_firebase_app()

        self.db = firestore.client()
        self.collection = self.db.collection('empresas')

    async def save(self, empresa: Empresa) -> str:
        """
        Salvar uma empresa no banco de dados Firestore.

        O ID (empresa_id) é o próprio CNPJ, o Firestore Insere se não existir ou atualiza se existir.
        Garante a unicidade do CNPJ no banco de dados.

        Args:
            empresa (Empresa): A instância da empresa a ser salva.

        Retorna:
            str: O ID do documento da empresa salva.
        """
        try:
            empresa_dict = self._empresa_to_dict(empresa)
            # Insere ou atualiza o documento na coleção 'empresas'
            self.collection.document(empresa.id).set(empresa_dict, merge=True)
            return empresa.id  # Garante que o ID retornado seja o ID real do documento
        except exceptions.FirebaseError as e:
            if e.code == 'invalid-argument':
                logger.error("Argumento inválido fornecido.")
            elif e.code == 'not-found':
                logger.error("Documento ou recurso não encontrado.")
            elif e.code == 'permission-denied':
                logger.error("Permissão negada para realizar a operação.")
            elif e.code == 'resource-exhausted':
                logger.error("Cota do Firebase excedida.")
            else:
                logger.error(f"Erro desconhecido do Firebase: {e.code}")
            translated_error = deepl_translator(str(e))
            raise Exception(f"Erro ao salvar empresa: {translated_error}")
        except Exception as e:
            # Captura erros inesperados
            logger.error(f"Erro inesperado ao salvar empresa: {str(e)}")
            translated_error = deepl_translator(str(e))
            raise Exception(f"Erro inesperado ao salvar empresa: {translated_error}")

    async def find_by_id(self, id: str) -> Optional[Empresa]:
        """
        Encontrar uma empresa pelo seu identificador único.

        Args:
            id (str): O identificador único da empresa.

        Retorna:
            Optional[Empresa]: Uma instância da empresa se encontrada, None caso contrário.
        """
        try:
            doc = self.collection.document(id).get()
            if doc.exists:
                empresa_data = doc.to_dict()
                empresa_data['id'] = doc.id
                return self._doc_to_empresa(empresa_data)
            return None  # Retorna None se o documento não existir
        except exceptions.FirebaseError as e:
            if e.code == 'permission-denied':
                logger.warning(f"Permissão negada ao consultar empresa com id '{id}': {e}")
            elif e.code == 'unavailable':
                logger.error(f"Serviço do Firestore indisponível ao consultar empresa com id '{id}': {e}")
                # Pode considerar re-lançar uma exceção específica para tratamento de disponibilidade
                raise Exception(f"Serviço do Firestore temporariamente indisponível.")
            else:
                logger.error(f"Erro do Firebase ao consultar empresa com id '{id}': Código: {e.code}, Detalhes: {e}")
            raise  # Re-lançar a exceção para tratamento em camadas superiores
        except Exception as e:
            # Captura outros erros inesperados (problemas de rede, etc.)
            logger.error(f"Erro inesperado ao consultar empresa com id '{id}': {e}")
            raise

    async def find_by_cnpj(self, cnpj: CNPJ) -> Optional[Empresa]:
        """
        Encontrar uma empresa pelo seu CNPJ.

        Args:
            cnpj (CNPJ): O CNPJ da empresa a ser encontrada.

        Retorna:
            Optional[Empresa]: Uma instância da empresa se encontrada, None caso contrário.

        Levanta:
            Exception: Se ocorrer um erro no Firebase ou outro erro inesperado durante a busca.
        """
        try:
            query = self.collection.where(filter=FieldFilter("cnpj", "==", cnpj.raw_cnpj)).limit(1)
            # query = self.collection.where(field_path='cnpj', op_string='==', value=cnpj.raw_cnpj).limit(1)  # Método antigo
            docs = query.get()

            if docs:
                doc = docs[0]
                empresa_data = doc.to_dict()
                empresa_data['id'] = doc.id
                return self._doc_to_empresa(empresa_data)

            return None
        except exceptions.FirebaseError as e:
            if e.code == 'permission-denied':
                logger.warning(f"Permissão negada ao consultar empresa com CNPJ '{str(cnpj)}': {e}")
            elif e.code == 'unavailable':
                logger.error(f"Serviço do Firestore indisponível ao consultar empresa com CNPJ '{str(cnpj)}': {e}")
                # Pode considerar re-lançar uma exceção específica para tratamento de disponibilidade
                raise Exception(f"Serviço do Firestore temporariamente indisponível.")
            else:
                logger.error(f"Erro do Firebase ao consultar empresa com CNPJ '{str(cnpj)}': Código: {e.code}, Detalhes: {e}")
            raise  # Re-lançar a exceção para tratamento em camadas superiores
        except Exception as e:
            # Captura outros erros inesperados (problemas de rede, etc.)
            logger.error(f"Erro inesperado ao consultar empresa com CNPJ '{str(cnpj)}': {e}")
            raise

    async def exists_by_cnpj(self, cnpj: CNPJ) -> bool:
        """
        Verificar se uma empresa existe com o CNPJ fornecido.

        Args:
            cnpj (CNPJ): O CNPJ da empresa a ser verificado.

        Retorna:
            bool: True se a empresa existir, False caso contrário.
        """
        try:
            query = self.collection.where(filter=FieldFilter("cnpj", "==", cnpj.raw_cnpj)).limit(1)
            # query = self.collection.where(field_path='cnpj', op_string='==', value=cnpj.raw_cnpj).limit(1)  # Método antigo
            return len(query.get()) > 0
        except exceptions.FirebaseError as e:
            if e.code == 'permission-denied':
                logger.warning(f"Permissão negada ao consultar empresa com CNPJ '{str(cnpj)}': {e}")
            elif e.code == 'unavailable':
                logger.error(f"Serviço do Firestore indisponível ao consultar empresa com CNPJ '{str(cnpj)}': {e}")
                # Pode considerar re-lançar uma exceção específica para tratamento de disponibilidade
                raise Exception(f"Serviço do Firestore temporariamente indisponível.")
            else:
                logger.error(f"Erro do Firebase ao consultar empresa com CNPJ '{str(cnpj)}': Código: {e.code}, Detalhes: {e}")
            raise  # Re-lançar a exceção para tratamento em camadas superiores
        except Exception as e:
            # Captura outros erros inesperados (problemas de rede, etc.)
            logger.error(f"Erro inesperado ao consultar empresa com CNPJ '{str(cnpj)}': {e}")
            raise

    async def find_all(self, ids_empresas: set[str]) -> list[Empresa]:
        """
        Faz uma busca de todas as empresas que estão na lista de ids_empresas.

        Args:
            ids_empresas (set[str]): Lista dos IDs de documentos das empresas do usuário logado

        Return:
            list[Empresa]: Lista de empresas encontradas ou vazio se não encontrar
        Raise:
            Exception: Se ocorrer erro no Firebase ou outro erro inesperado durante a busca.
        """
        try:
            ids_empresas_list = list(ids_empresas)

            # Buscar documentos diretamente pelos IDs
            empresas = []
            for empresa_id in ids_empresas_list:
                doc_ref = self.collection.document(empresa_id)
                doc = doc_ref.get()
                if doc.exists:
                    doc_dict = doc.to_dict()
                    # Adicionar o ID do documento ao dicionário antes de converter para objeto Empresa
                    doc_dict['id'] = doc.id  # Isso ajuda se o seu método _doc_to_empresa precisa do ID
                    empresas.append(self._doc_to_empresa(doc_dict))
                else:
                    logger.warning(f"Documento com ID {empresa_id} não encontrado")

            return empresas
        except exceptions.FirebaseError as e:
            if e.code == 'permission-denied':
                print(f"ERROR: Permissão negada ao consultar lista de empresas do usuário logado: {e}")
                logger.warning(f"Permissão negada ao consultar lista de empresas do usuário logado: {e}")
            elif e.code == 'unavailable':
                print(f"ERROR: Serviço do Firestore indisponível ao consultar lista de empresas do usuário logado: {e}")
                logger.error(f"Serviço do Firestore indisponível ao consultar lista de empresas do usuário logado: {e}")
                raise Exception(f"Serviço do Firestore temporariamente indisponível.")
            else:
                print(f"ERROR: Erro do Firebase ao consultar lista de empresas do usuário logado: Código: {e.code}, Detalhes: {e}")
                logger.error(f"Erro do Firebase ao consultar lista de empresas do usuário logado: Código: {e.code}, Detalhes: {e}")
            raise  # Re-lançar a exceção para tratamento em camadas superiores
        except Exception as e:
            # Captura outros erros inesperados (problemas de rede, etc.)
            print(f"ERROR: Erro inesperado ao consultar lista de empresas do usuário logado: {e}")
            logger.error(f"Erro inesperado ao consultar lista de empresas do usuário logado: {e}")
            raise

    async def delete(self, empresa_id: str) -> bool:
        """
        Excluir uma empresa pelo seu identificador único.

        Args:
            empresa_id (str): O identificador único da empresa.

        Retorna:
            bool: True se a exclusão for bem-sucedida, False caso contrário.

        Levanta:
            Exception: Se ocorrer um erro no Firebase ou outro erro inesperado durante a exclusão.
        """
        try:
            self.collection.document(empresa_id).delete()
            return True
        except exceptions.FirebaseError as e:
            if e.code == 'not-found':
                logger.info(f"Empresa com id '{empresa_id}' não encontrada para exclusão.")
                return True  # Retorna True pois o estado desejado (não existir) já foi atingido
            elif e.code == 'permission-denied':
                logger.error(f"Permissão negada ao excluir empresa com id '{empresa_id}': {e}")
                translated_error = deepl_translator(str(e))
                raise Exception(f"Erro de permissão ao excluir empresa: {translated_error}")
            elif e.code == 'unavailable':
                logger.error(f"Serviço do Firestore indisponível ao excluir empresa com id '{empresa_id}': {e}")
                translated_error = deepl_translator(str(e))
                raise Exception(f"Serviço do Firestore temporariamente indisponível.")
            else:
                logger.error(f"Erro do Firebase ao excluir empresa com id '{empresa_id}': Código: {e.code}, Detalhes: {e}")
                translated_error = deepl_translator(str(e))
                raise Exception(f"Erro ao excluir empresa: {translated_error}")
        except Exception as e:
            logger.error(f"Erro inesperado ao excluir empresa com id '{empresa_id}': {str(e)}")
            translated_error = deepl_translator(str(e))
            raise Exception(f"Erro inesperado ao excluir empresa: {translated_error}")


    def _doc_to_empresa(self, doc_data: dict) -> Empresa:
        """
        Converter os dados de um documento do Firestore em uma instância de empresa.

        Args:
            doc_data (dict): Os dados do documento Firestore representando uma empresa.

        Retorna:
            Empresa: A instância correspondente da empresa.
        """
        from src.domains.empresas import Address, CertificateA1, CodigoRegimeTributario, EmpresaSize, Environment, FiscalData
        from src.domains.shared import PhoneNumber

        address = None
        if doc_data.get('address'):
            address_data = doc_data['address']
            address = Address(
                street=address_data.get('street'),
                number=address_data.get('number'),
                complement=address_data.get('complement'),
                neighborhood=address_data.get('neighborhood'),
                city=address_data.get('city'),
                state=address_data.get('state'),
                postal_code=address_data.get('postal_code'),
            )

        size_info = None
        if size_name := doc_data.get('size'):
            size_info = EmpresaSize[size_name]

        fiscal_info = None
        if fiscal := doc_data.get('fiscal'):

            # Obtem o enum CodigoRegimeTributario correspondente ao código crt_code
            crt_enum = None
            amb_enum = None

            # Obtem o 'name' do enum CRT vindo do banco
            if fiscal.get('crt_name'):
                crt_enum = CodigoRegimeTributario[fiscal['crt_name']]

            # Obtem o 'name' do ambiente fiscal vindo do banco
            if fiscal.get('environment_name'):
                amb_enum = Environment[fiscal['environment_name']]

            fiscal_info = FiscalData(
                crt=crt_enum,
                environment=amb_enum,
                nfce_series=fiscal.get('nfce_series'),
                nfce_number=fiscal.get('nfce_number'),
                nfce_sefaz_id_csc=fiscal.get('nfce_sefaz_id_csc'),
                nfce_sefaz_csc=fiscal.get('nfce_sefaz_csc'),
                nfce_api_enabled=fiscal.get('nfce_api_enabled'),
            )

        certificate_a1 = None

        from src.domains.shared.password import Password

        if certificate := doc_data.get("certificate_a1"):
            encrypted_password = certificate.get("password")
            # Criar instância a partir do valor criptografado
            password = Password.from_encrypted(encrypted_password)
            certificate_a1 = CertificateA1(
                password=password,
                serial_number=certificate.get('serial_number'),
                not_valid_before=certificate.get('not_valid_before'),
                not_valid_after=certificate.get('not_valid_after'),
                subject_name=certificate.get('subject_name'),
                file_name=certificate.get('file_name'),
                cpf_cnpj=certificate.get('cpf_cnpj'),
                nome_razao_social=certificate.get('nome_razao_social'),
                storage_path=certificate.get('storage_path'),
            )

        """
        ToDo: Substituir o AsaasPaymentGateway por um repositório específico para o gateway de pagamento
        O repositório é o responsável por qual é gateway atual que deve ser usado.
        """
        payment_gateway = None
        if pg := doc_data.get("payment_gateway"):
            payment_gateway = AsaasPaymentGateway(
                customer_id=pg.get('customer_id'),
                nextDueDate=pg.get('nextDueDate'),
                billingType=pg.get('billingType'),
                status=pg.get('status'),
                dateCreated=pg.get('dateCreated'),
            )

        cnpj = None
        if doc_data.get('cnpj'):
            cnpj = CNPJ(doc_data['cnpj'])

        phone = None
        if doc_data.get('phone'):
            phone = PhoneNumber(doc_data['phone'])

        return Empresa(
            id=doc_data.get('id'),
            corporate_name=doc_data.get('corporate_name'),
            trade_name=doc_data.get('trade_name'),
            store_name=doc_data.get('store_name', "Matriz"),
            cnpj=cnpj,
            email=doc_data.get('email'),
            ie=doc_data.get('ie'),
            im=doc_data.get('im'),
            phone=phone,
            address=address,
            size=size_info,
            fiscal=fiscal_info,
            certificate_a1=certificate_a1,
            logo_url=doc_data.get('logo_url'),
            payment_gateway=payment_gateway,
        )

    def _empresa_to_dict(self, empresa: Empresa) -> dict:
        """
        Converter uma instância de empresa em um dicionário para armazenamento no Firestore.

        Args:
            empresa (Empresa): A instância da empresa a ser convertida.

        Retorna:
            dict: A representação da empresa em formato de dicionário.
        """

        empresa_dict = empresa.to_dict()

        if empresa.cnpj:
            # Armazena o CNPJ como string
            empresa_dict.update({
                'cnpj': empresa.cnpj.raw_cnpj,
            })
        if empresa.phone:
            # Armazena o telefone como string
            empresa_dict.update({
                'phone': empresa.phone.get_e164(),
            })
        if empresa.size:
            # Armazena o name do enum size
            empresa_dict.update({
                'size': empresa.size,
            })

        # Remove os campos desnecessários para o Firestore; O id é passado diretamente no documento de referencia
        empresa_dict.pop('id', None)
        empresa_dict_filtered = {k: v for k, v in empresa_dict.items() if v is not None}
        return empresa_dict_filtered
