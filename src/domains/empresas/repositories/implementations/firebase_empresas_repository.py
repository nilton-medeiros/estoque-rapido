import logging

from typing import Optional
from firebase_admin import firestore
from firebase_admin import exceptions

from src.domains.empresas import CNPJ, Empresa, EmpresasRepository
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

    async def count(self) -> int:
        """
        Contar o número total de empresas no banco de dados Firestore.

        Retorna:
            int: Número total de empresas.
        """
        return len(self.collection.get())

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
            translated_error = deepl_translator(str(e))
            logger.error(f"Erro ao excluir empresa com id '{empresa_id}': {translated_error}")
            raise Exception(
                f"Erro ao excluir empresa com id '{empresa_id}': {translated_error}")
        except Exception as e:
            logger.error(f"Erro inesperado ao excluir empresa com id '{empresa_id}': {str(e)}")
            raise Exception(
                f"Erro inesperado ao excluir empresa com id '{empresa_id}': {str(e)}")

    async def exists_by_cnpj(self, cnpj: CNPJ) -> bool:
        """
        Verificar se uma empresa existe com o CNPJ fornecido.

        Args:
            cnpj (CNPJ): O CNPJ da empresa a ser verificado.

        Retorna:
            bool: True se a empresa existir, False caso contrário.
        """
        try:
            query = self.collection.where(
                field_path='cnpj', op_string='==', value=str(cnpj)).limit(1)
            return len(query.get()) > 0
        except Exception as e:
            logger.error(f"Erro ao verificar a existência da empresa pelo CNPJ: {e}")
            return False

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
            query = self.collection.where(
                field_path='cnpj', op_string='==', value=str(cnpj)).limit(1)
            docs = query.get()

            if docs:
                doc = docs[0]
                empresa_data = doc.to_dict()
                empresa_data['id'] = doc.id
                return self._doc_to_empresa(empresa_data)

            return None
        except exceptions.FirebaseError as e:
            translated_error = deepl_translator(str(e))
            logger.error(f"Erro ao buscar empresa pelo CNPJ '{cnpj}': {translated_error}")
            raise Exception(
                f"Erro ao buscar empresa pelo CNPJ '{cnpj}': {translated_error}")
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar empresa pelo CNPJ '{cnpj}': {str(e)}")
            raise Exception(
                f"Erro inesperado ao buscar empresa pelo CNPJ '{cnpj}': {str(e)}")

    async def find_by_id(self, empresa_id: str) -> Optional[Empresa]:
        """
        Encontrar uma empresa pelo seu identificador único.

        Args:
            empresa_id (str): O identificador único da empresa.

        Retorna:
            Optional[Empresa]: Uma instância da empresa se encontrada, None caso contrário.
        """
        try:
            doc = self.collection.document(empresa_id).get()
            if doc.exists:
                empresa_data = doc.to_dict()
                empresa_data['id'] = doc.id
                return self._doc_to_empresa(empresa_data)
        except Exception:
            pass

        return None

    async def save(self, empresa: Empresa) -> str:
        """
        Salvar uma empresa no banco de dados Firestore.

        Se a empresa já existir pelo seu CNPJ, atualiza o documento existente em vez
        de criar um novo.

        Args:
            empresa (Empresa): A instância da empresa a ser salva.

        Retorna:
            str: O ID do documento da empresa salva.
        """
        try:
            empresa_dict = self._empresa_to_dict(empresa)

            existing = self.find_by_cnpj(empresa.cnpj)
            if existing:
                doc_ref = self.collection.document(existing.id)
                doc_ref.set(empresa_dict, merge=True)
                return existing.id

            doc_ref = self.collection.add(empresa_dict)[1]
            return doc_ref.id  # Garante que o ID retornado seja o ID real do documento

        except Exception as e:
            # Tratar erros de forma adequada, como logar a exceção e retornar uma mensagem de erro informativa
            logger.error(f"Erro ao salvar empresa: {e}")
            raise  # Re-lançar a exceção para que seja tratada em camadas superiores

    async def _empresa_to_dict(self, empresa: Empresa) -> dict:
        """
        Converter uma instância de empresa em um dicionário para armazenamento no Firestore.

        Args:
            empresa (Empresa): A instância da empresa a ser convertida.

        Retorna:
            dict: A representação da empresa em formato de dicionário.
        """
        # Não adicione id no empresa_dict, pois o Firebase providenciar um uid se não existir

        empresa_dict = {
            'name': empresa.name,
            'corporate_name': empresa.corporate_name,
            'store_name': empresa.store_name,
            'phone': empresa.phone.get_e164(),
        }

        empresa_dict['cnpj'] = str(empresa.cnpj)
        empresa_dict['ie'] = empresa.ie
        empresa_dict['im'] = empresa.im

        if empresa.address:
            empresa_dict['address'] = {
                'street': empresa.address.street,
                'number': empresa.address.number,
                'complement': empresa.address.complement,
                'neighborhood': empresa.address.neighborhood,
                'city': empresa.address.city,
                'state': empresa.address.state,
                'postal_code': empresa.address.postal_code,
                'logo_url': empresa.logo_url,
            }

        if empresa.size:
            empresa_dict['size'] = empresa.size.name  # Armazena o name do enum size

        if fiscal := empresa.get_nfce_data():
            empresa_dict['fiscal'] = {
                'crt_name': fiscal.get('crt_name'),  # Armazena o name do enum CodigoRegimeTributario
                'environment_name': fiscal.get('environment_name'),  # Armazena o name do enum Environment
                'nfce_series': fiscal.get('nfce_series'),
                'nfce_number': fiscal.get('nfce_number'),
                'nfce_sefaz_id_csc': fiscal.get('nfce_sefaz_id_csc'),
                'nfce_sefaz_csc': fiscal.get('nfce_sefaz_csc'),
            }

        if certificate := empresa.get_certificate_data():
            empresa_dict['certificate_a1'] = {
                'serial_number': certificate.serial_number,
                'not_valid_before': certificate.not_valid_before,
                'not_valid_after': certificate.not_valid_after,
                'subject_name': certificate.subject_name,
                'file_name': certificate.file_name,
                'cpf_cnpj': certificate.cpf_cnpj,
                'nome_razao_social': certificate.nome_razao_social,
                'password_encrypted': certificate.password_encrypted,
                'storage_path': certificate.storage_path,
            }

        # ToDo: Verificar estes campos quando for implementado o gateway de pagamento
        if empresa.payment_gateway:
            empresa_dict['payment_gateway'] = {
                'customer_id': empresa.payment_gateway.customer_id,
                'nextDueDate': empresa.payment_gateway.nextDueDate,
                'billingType': empresa.payment_gateway.billingType,
                'status': empresa.payment_gateway.status,
                'dateCreated': empresa.payment_gateway.dateCreated,
            }

        return empresa_dict

    async def _doc_to_empresa(self, doc_data: dict) -> Empresa:
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
            address = Address(
                street=doc_data['address']['street'],
                number=doc_data['address']['number'],
                complement=doc_data['address'].get('complement'),
                neighborhood=doc_data['address'].get('neighborhood'),
                city=doc_data['address']['city'],
                state=doc_data['address']['state'],
                postal_code=doc_data['address']['postal_code']
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
                crt_enum = CodigoRegimeTributario[fiscal.get('crt_name')]

            # Obtem o 'name' do ambiente fiscal vindo do banco
            if fiscal.get('environment_name'):
                amb_enum = Environment[fiscal.get('environment_name')]

            fiscal_info = FiscalData(
                crt=crt_enum,
                environment=amb_enum,
                nfce_series=fiscal.get('nfce_series', None),
                nfce_number=fiscal.get('nfce_number', None),
                nfce_sefaz_id_csc=fiscal.get('nfce_sefaz_id_csc', None),
                nfce_sefaz_csc=fiscal.get('nfce_sefaz_csc', None),
            )

        certificate_a1 = None

        if certificate := doc_data.get("certificate_a1"):
            certificate_a1 = CertificateA1(
                serial_number = certificate.serial_number,
                not_valid_before = certificate.not_valid_before,
                not_valid_after = certificate.not_valid_after,
                subject_name = certificate.subject_name,
                file_name = certificate.file_name,
                cpf_cnpj = certificate.cpf_cnpj,
                nome_razao_social = certificate.nome_razao_social,
                storage_path = certificate.storage_path,
            )
            certificate_a1.password_encrypted = certificate.password_encrypted

        payment_gateway = None
        if pg := doc_data.get("payment_gateway"):
            payment_gateway = AsaasPaymentGateway(
                customer_id=pg.get('customer_id'),
                nextDueDate=pg.get('nextDueDate'),
                billingType=pg.get('billingType'),
                status=pg.get('status'),
                dateCreated=pg.get('dateCreated'),
            )


        cnpj = CNPJ(doc_data.get('cnpj'))

        return Empresa(
            id=doc_data.get('id'),
            corporate_name=doc_data.get('corporate_name'),
            name=doc_data.get('name'),
            email=doc_data.get('email'),
            cnpj=cnpj,
            store_name=doc_data.get('store_name', "Matriz"),
            ie=doc_data['ie'],
            im=doc_data.get('im'),
            phone=PhoneNumber(doc_data['phone']),
            address=address,
            size=size_info,
            fiscal=fiscal_info,
            certificate_a1=certificate_a1,
            logo_url=doc_data.get('logo_url'),
            payment_gateway=payment_gateway,
        )
