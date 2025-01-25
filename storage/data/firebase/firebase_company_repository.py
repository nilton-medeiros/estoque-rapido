from typing import Optional
from firebase_admin import firestore
from firebase_admin import exceptions

from src.services.payment_gateways.asaas_payment_gateway import AsaasPaymentGateway
from src.utils.deep_translator import deepl_translator
from firebase.firebase_initialize import get_firebase_app
from interfaces.company_repository import CompanyRepository

from models.cnpj import CNPJ
from models.company import Address, Company, CompanySize, ContactInfo, FiscalData


class FirebaseCompanyRepository(CompanyRepository):
    """
    Um repositório para gerenciar empresas utilizando o Firebase Firestore.

    Esta classe fornece métodos para realizar operações de CRUD em dados de empresas
    armazenados em um banco de dados Firestore.
    """

    def __init__(self):
        """
        Inicializa o cliente do Firebase Firestore e conecta-se à coleção 'companies'.

        Garante que o aplicativo Firebase seja inicializado antes de criar o cliente Firestore.
        """
        fb_app = get_firebase_app()
        print(f"Debug: {fb_app}")

        self.db = firestore.client()
        self.collection = self.db.collection('companies')

    async def count(self) -> int:
        """
        Contar o número total de empresas no banco de dados Firestore.

        Retorna:
            int: Número total de empresas.
        """
        return len(self.collection.get())

    async def delete(self, company_id: str) -> bool:
        """
        Excluir uma empresa pelo seu identificador único.

        Args:
            company_id (str): O identificador único da empresa.

        Retorna:
            bool: True se a exclusão for bem-sucedida, False caso contrário.

        Levanta:
            Exception: Se ocorrer um erro no Firebase ou outro erro inesperado durante a exclusão.
        """
        try:
            self.collection.document(company_id).delete()
            return True
        except exceptions.FirebaseError as e:
            translated_error = deepl_translator(str(e))
            raise Exception(
                f"Erro ao excluir empresa com id '{company_id}': {translated_error}")
        except Exception as e:
            raise Exception(
                f"Erro inesperado ao excluir empresa com id '{company_id}': {str(e)}")

    async def exists_by_cnpj(self, cnpj: CNPJ) -> bool:
        """
        Verificar se uma empresa existe com o CNPJ fornecido.

        Args:
            cnpj (CNPJ): O CNPJ da empresa a ser verificado.

        Retorna:
            bool: True se a empresa existir, False caso contrário.
        """
        try:
            query = self.collection.where('cnpj', '==', str(cnpj)).limit(1)
            return len(query.get()) > 0
        except Exception as e:
            print(f"Erro ao verificar a existência da empresa pelo CNPJ: {e}")
            return False

    async def find_by_cnpj(self, cnpj: CNPJ) -> Optional[Company]:
        """
        Encontrar uma empresa pelo seu CNPJ.

        Args:
            cnpj (CNPJ): O CNPJ da empresa a ser encontrada.

        Retorna:
            Optional[Company]: Uma instância da empresa se encontrada, None caso contrário.

        Levanta:
            Exception: Se ocorrer um erro no Firebase ou outro erro inesperado durante a busca.
        """
        try:
            query = self.collection.where('cnpj', '==', str(cnpj)).limit(1)
            docs = query.get()

            if docs:
                doc = docs[0]
                company_data = doc.to_dict()
                company_data['id'] = doc.id
                return self._doc_to_company(company_data)

            return None
        except exceptions.FirebaseError as e:
            translated_error = deepl_translator(str(e))
            raise Exception(
                f"Erro ao buscar empresa pelo CNPJ '{cnpj}': {translated_error}")
        except Exception as e:
            raise Exception(
                f"Erro inesperado ao buscar empresa pelo CNPJ '{cnpj}': {str(e)}")

    async def find_by_id(self, company_id: str) -> Optional[Company]:
        """
        Encontrar uma empresa pelo seu identificador único.

        Args:
            company_id (str): O identificador único da empresa.

        Retorna:
            Optional[Company]: Uma instância da empresa se encontrada, None caso contrário.
        """
        try:
            doc = self.collection.document(company_id).get()
            if doc.exists:
                company_data = doc.to_dict()
                company_data['id'] = doc.id
                return self._doc_to_company(company_data)
        except Exception:
            pass

        return None

    async def save(self, company: Company) -> str:
        """
        Salvar uma empresa no banco de dados Firestore.

        Se a empresa já existir pelo seu CNPJ, atualiza o documento existente em vez
        de criar um novo.

        Args:
            company (Company): A instância da empresa a ser salva.

        Retorna:
            str: O ID do documento da empresa salva.
        """
        company_dict = self._company_to_dict(company)

        existing = self.find_by_cnpj(company.cnpj)
        if existing:
            doc_ref = self.collection.document(existing.id)
            doc_ref.update(company_dict)
            return existing.id

        doc_ref = self.collection.add(company_dict)[1]
        return doc_ref.id

    async def _company_to_dict(self, company: Company) -> dict:
        """
        Converter uma instância de empresa em um dicionário para armazenamento no Firestore.

        Args:
            company (Company): A instância da empresa a ser convertida.

        Retorna:
            dict: A representação da empresa em formato de dicionário.
        """
        # Não adicione id no company_dict, pois o Firebase providenciar um uid se não existir
        company_dict = {
            'name': company.name,
            'corporate_name': company.corporate_name,
            'cnpj': str(company.cnpj),
            'state_registration': company.state_registration,
            'legal_nature': company.legal_nature,
        }

        if company.municipal_registration:
            company_dict['municipal_registration'] = company.municipal_registration
        if company.founding_date:
            company_dict['founding_date'] = company.founding_date
        if company.contact:
            company_dict['contact'] = {
                'email': company.contact.email,
                'phone': company.contact.phone.get_e164(),
                'website': company.contact.website
            }
        if company.address:
            company_dict['address'] = {
                'street': company.address.street,
                'number': company.address.number,
                'complement': company.address.complement,
                'neighborhood': company.address.neighborhood,
                'city': company.address.city,
                'state': company.address.state,
                'postal_code': company.address.postal_code
            }
        if company.size:
            company_dict['size'] = company.size.value
        if company.fiscal:
            company_dict['fiscal'] = {
                'tax_regime': company.fiscal.tax_regime,
                'nfce_series': company.fiscal.nfce_series,
                'nfce_environment': company.fiscal.nfce_environment,
                'nfce_certificate': company.fiscal.nfce_certificate,
                'nfce_certificate_password': company.fiscal.nfce_certificate_password,
                'nfce_certificate_date': company.fiscal.nfce_certificate_date,
                'nfce_sefaz_id_csc': company.fiscal.nfce_sefaz_id_csc,
                'nfce_sefaz_csc': company.fiscal.nfce_sefaz_csc,
            }
        if company.description:
            company_dict['description'] = company.description
        if company.logo_path:
            company_dict['logo_path'] = company.logo_path
        if company.payment_gateway:
            company_dict['payment_gateway'] = {
                'customer_id': company.payment_gateway.customer_id,
                'nextDueDate': company.payment_gateway.nextDueDate,
                'billingType': company.payment_gateway.billingType,
                'status': company.payment_gateway.status,
                'dateCreated': company.payment_gateway.dateCreated,
            }

        return company_dict

    async def _doc_to_company(self, doc_data: dict) -> Company:
        """
        Converter os dados de um documento do Firestore em uma instância de empresa.

        Args:
            doc_data (dict): Os dados do documento Firestore representando uma empresa.

        Retorna:
            Company: A instância correspondente da empresa.
        """
        from models.cnpj import CNPJ
        from models.phone_number import PhoneNumber

        contact_info = None
        if doc_data.get('contact'):
            contact_info = ContactInfo(
                email=doc_data['contact']['email'],
                phone=PhoneNumber(doc_data['contact']['phone']),
                website=doc_data['contact'].get('website')
            )

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

        size_info = CompanySize(doc_data.get('size')) if doc_data.get('size') else None

        fiscal_info = None
        if doc_data.get("fiscal"):
            fiscal_info = FiscalData(
                tax_regime=doc_data['fiscal']['tax_regime'],
                nfce_series=doc_data['fiscal']['nfce_series'],
                nfce_environment=doc_data['fiscal']['nfce_environment'],
                nfce_certificate=doc_data['fiscal']['nfce_certificate'],
                nfce_certificate_password=doc_data['fiscal']['nfce_certificate_password'],
                nfce_certificate_date=doc_data['fiscal']['nfce_certificate_date'],
                nfce_sefaz_id_csc=doc_data['fiscal']['nfce_sefaz_id_csc'],
                nfce_sefaz_csc=doc_data['fiscal']['nfce_sefaz_csc'],
            )

        payment_gwy = None
        if doc_data.get("payment_gateway"):
            payment_gwy = AsaasPaymentGateway(
                customer_id=doc_data['payment_gateway']['customer_id'],
                nextDueDate=doc_data['payment_gateway']['nextDueDate'],
                billingType=doc_data['payment_gateway']['billingType'],
                status=doc_data['payment_gateway']['status'],
                dateCreated=doc_data['payment_gateway']['dateCreated'],
            )

        return Company(
            id=doc_data["id"],
            name=doc_data['name'],
            corporate_name=doc_data['corporate_name'],
            cnpj=CNPJ(doc_data['cnpj']),
            state_registration=doc_data['state_registration'],
            legal_nature=doc_data['legal_nature'],
            municipal_registration=doc_data.get('municipal_registration'),
            founding_date=doc_data.get('founding_date'),
            contact=contact_info,
            address=address,
            size=size_info,
            fiscal=fiscal_info,
            description=doc_data['description'],
            logo_path=doc_data['logo_path'],
            payment_gateway=payment_gwy,
        )
