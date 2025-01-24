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
    """Implementação de CompanyRepository usando Firebase Firestore."""

    def __init__(self):
        # Inicializar app Firebase se ainda não estiver inicializado
        fb_app = get_firebase_app()
        print(f"Debug: {fb_app}")

        self.db = firestore.client()
        self.collection = self.db.collection('companies')

    async def count(self) -> int:
        """Contar o número total de empresas no Firestore."""
        return len(self.collection.get())

    async def delete(self, company_id: str) -> bool:
        """
        Excluir uma empresa por seu ID.

        :param company_id: Identificador único da empresa
        :return: True se a exclusão foi bem-sucedida, False caso contrário
        """
        try:
            self.collection.document(company_id).delete()
            return True
        except exceptions.FirebaseError as e:
            translated_error = deepl_translator(str(e))
            raise Exception(
                f"Erro ao deletar empresa com id '{company_id}': {translated_error}")
        except Exception as e:
            raise Exception(
                f"Erro inesperado ao deletar empresa com id '{company_id}': {str(e)}")

    async def exists_by_cnpj(self, cnpj: CNPJ) -> bool:
        """
        Verificar se uma empresa existe com o CNPJ fornecido.

        :param cnpj: CNPJ da empresa a verificar
        :return: True se a empresa existe, False caso contrário
        """
        try:
            query = self.collection.where('cnpj', '==', str(cnpj)).limit(1)
            return len(query.get()) > 0
        except Exception as e:
            # Lida com possíveis exceções, se necessário
            print(f"Erro ao verificar se a empresa existe pelo CNPJ: {e}")
            return False

    async def find_by_cnpj(self, cnpj: CNPJ) -> Optional[Company]:
        """Encontrar uma empresa por seu CNPJ.

        :param cnpj: CNPJ da empresa a procurar
        :return: Instância da Empresa se encontrada, None caso contrário
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
        Encontrar uma empresa por seu ID.

        :param company_id: Identificador único da empresa
        :return: Instância da Empresa se encontrada, None caso contrário
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
        Salvar uma empresa no Firestore.

        :param company: Instância da Empresa a salvar
        :return: ID do documento da empresa salva
        """
        company_dict = self._company_to_dict(company)

        # Se a empresa já existe por CNPJ, atualizar em vez de criar novo
        existing = self.find_by_cnpj(company.cnpj)
        if existing:
            doc_ref = self.collection.document(existing.id)
            doc_ref.update(company_dict)
            return existing.id

        # Criar novo documento
        doc_ref = self.collection.add(company_dict)[1]
        return doc_ref.id

    async def _company_to_dict(self, company: Company) -> dict:
        """
        Converter instância de Empresa para dicionário para armazenamento no Firestore.

        :param company: Instância da Empresa
        :return: Representação em dicionário da empresa
        """
        # ATENÇÃO: O ID não faz parte desta lista de campos a serem salvos no banco
        company_dict = {
            'name': company.name,
            'corporate_name': company.corporate_name,
            'cnpj': str(company.cnpj),
            'state_registration': company.state_registration,
            'legal_nature': company.legal_nature,
        }

        # Campos opcionais
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
        Converter dados de documento do Firestore para instância de Empresa.

        :param doc_data: Dicionário de dados da empresa do Firestore
        :return: Instância da Empresa
        """
        from models.cnpj import CNPJ
        from models.phone_number import PhoneNumber

        # Reconstruir campos opcionais
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
