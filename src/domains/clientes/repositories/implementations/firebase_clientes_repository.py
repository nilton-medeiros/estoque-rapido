import logging

from google.cloud.firestore_v1.base_query import FieldFilter
from google.api_core import exceptions as google_api_exceptions
from firebase_admin import exceptions, firestore
from src.domains.shared import RegistrationStatus

from src.domains.clientes.models.clientes_model import Cliente
from src.domains.clientes.repositories.contracts.clientes_repository import ClientesRepository
from src.shared.utils.deep_translator import deepl_translator
from storage.data import get_firebase_app

logger = logging.getLogger(__name__)


class FirebaseClientesRepository(ClientesRepository):
    """
    Repositório para gerenciar clientes utilizando o Firebase Firestore.

    Esta classe fornece métodos para realizar operações de CRUD em dados de clientes
    armazenados em banco de dados Firestore.
    """

    def __init__(self, empresa_id: str) -> None:
        """
        Inicializa o cliente Firebase Firestore e conecta-se à coleção de clientes.

        Args:
            empresa_id (str): O ID da emp'''''resa logada, utilizado em quase todos os métodos.

        Returns: None
        """
        get_firebase_app()
        self.db = firestore.client()
        self.collection = self.db.collection('clientes')
        self.empresa_id = empresa_id

    def save(self, cliente: Cliente) -> str | None:
        """
        Cria ou atualiza um cliente no banco de dados.
        Caso for criar o registro, o ID já foi gerado em controllers

        Args:
            cliente (Cliente): A instância do cliente a ser salvo.

        Return:
            str: O ID do cliente criado ou atualizado ou None se ocorrer um erro.
        """
        if cliente.id is None:
            raise Exception(
                "Erro ao salvar cliente: O ID do cliente não pode ser nulo")

        try:
            cliente_data = cliente.to_dict_db()

            if not cliente_data.get("created_at"):
                cliente_data["created_at"] = firestore.SERVER_TIMESTAMP # type: ignore [attr-defined]

            cliente_data["updated_at"] = firestore.SERVER_TIMESTAMP # type: ignore [attr-defined]

            if cliente_data.get("status") == RegistrationStatus.ACTIVE.name and not cliente_data.get("activated_at"):
                cliente_data["activated_at"] = firestore.SERVER_TIMESTAMP # type: ignore [attr-defined]

            if cliente_data.get("status") == RegistrationStatus.DELETED.name and not cliente_data.get("deleted_at"):
                cliente_data["deleted_at"] = firestore.SERVER_TIMESTAMP # type: ignore [attr-defined]

            if cliente_data.get("status") == RegistrationStatus.INACTIVE.name and not cliente_data.get("inactivated_at"):
                cliente_data["inactivated_at"] = firestore.SERVER_TIMESTAMP # type: ignore [attr-defined]

            doc_ref = self.collection.document(cliente.id)
            doc_ref.set(cliente_data, merge=True)

            try:
                doc_snapshot = doc_ref.get()

                if not doc_snapshot.exists:
                    logger.warning(
                        f"Documento {cliente.id} não encontrado imediatamente após o set para releitura dos timestamps.")
                    return None

                cliente_data_from_db = doc_snapshot.to_dict()

                cliente_data_from_db["id"] = doc_snapshot.id  # type: ignore

                updated_cliente_obj = Cliente.from_dict(cliente_data_from_db)

                cliente.created_at = updated_cliente_obj.created_at
                cliente.updated_at = updated_cliente_obj.updated_at
                cliente.activated_at = updated_cliente_obj.activated_at
                cliente.inactivated_at = updated_cliente_obj.inactivated_at
                cliente.deleted_at = updated_cliente_obj.deleted_at

            except Exception as e_read:
                logger.error(
                    f"Erro ao reler o documento {cliente.id} para atualizar timestamps: {str(e_read)}")

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
            raise Exception(f"Erro ao salvar cliente: {translated_error}")
        except Exception as e:
            # Captura erros inesperados
            translated_error = deepl_translator(str(e))
            logger.error(
                f"Erro inesperado ao salvar cliente: {translated_error} [{str(e)}]")
            raise

        return cliente.id

    def get_by_id(self, cliente_id: str) -> Cliente | None:
        """
        Encontra um cliente pelo seu ID no banco de dados.

        Args:
            cliente_id (str): O ID do cliente a ser encontrado.

        Returns:
            Cliente | None: Cliente encontrado ou None se não existir.

        Raises:
            Exception: Em caso de erro na operação de banco de dados.
        """
        try:
            doc_ref = self.collection.document(cliente_id).get()
            if not doc_ref.exists:
                logger.info(f"Cliente com ID {cliente_id} não encontrado.")
                return None

            cliente_data = doc_ref.to_dict()
            cliente_data["id"] = doc_ref.id  # type: ignore
            if not cliente_data:
                logger.warning(f"Documento {cliente_id} está vazio.")
                return None

            cliente_data["id"] = doc_ref.id

            return Cliente.from_dict(cliente_data)
        except exceptions.FirebaseError as e:
            logger.error(
                f"Erro do Firebase ao buscar cliente por ID {cliente_id}: Código: {getattr(e, 'code', 'N/A')}, Detalhes: {e}")
            raise  # Re-lança para tratamento em camadas superiores
        except Exception as e:
            logger.error(
                f"Erro inesperado ao buscar cliente por ID {cliente_id}: {e}")
            raise

    def get_all(self, status_deleted: bool = False) -> tuple[list[Cliente], int]:
        """
        Obtém todos os clientes da empresa logada pelo ID self.empresa_id.

        Args:
            status_deleted (bool): Se True, apenas os clientes com status "DELETED" serão incluídos;
                                    caso contrário, todos os clientes, exceto os excluídos, serão retornados.

        Returns:
            list[Cliente]: Lista de clientes.
            int: Número total de clientes marcados como "DELETED".

        Raise:
            Exception: Em caso de erro na operação de banco de dados.
        """
        try:
            query = (self.collection
                     .where(filter=FieldFilter("empresa_id", "==", self.empresa_id))
                     .order_by("name.first_name_lower")
                     .order_by("name.last_name_lower"))

            # ToDo: Após versão beta test, verificar se há necessidade de implementar leitura de 300 registros por vez
            docs = query.stream()

            clientes_result: list[Cliente] = []
            quantidade_deletados = 0
            for doc in docs:
                clientes_data = doc.to_dict()
                if clientes_data:
                    clientes_data["id"] = doc.id
                    cliente_obj = Cliente.from_dict(clientes_data)

                    if cliente_obj.status == RegistrationStatus.DELETED:
                        quantidade_deletados += 1

                    # Adiciona o cliente à lista de resultados com base no filtro 'status_deleted'
                    if status_deleted:  # Se o filtro é para mostrar deletados
                        if cliente_obj.status == RegistrationStatus.DELETED:
                            clientes_result.append(cliente_obj)
                    else:  # not status_deleted (mostrar não deletados)
                        if cliente_obj.status != RegistrationStatus.DELETED:
                            clientes_result.append(cliente_obj)
                else:
                    logger.warning(f"Documento {doc.id} está vazio. Talvez os campos não existam na base de dados.")

            return clientes_result, quantidade_deletados

        except google_api_exceptions.FailedPrecondition as e:
            # Esta é a exceção específica para erros de "índice ausente".
            # A mensagem de erro 'e' já contém o link para criar o índice.
            logger.error(
                f"Erro de pré-condição ao consultar cliente (provavelmente índice ausente): {e}. "
                "O Firestore requer um índice para esta consulta. "
                f"A mensagem de erro original geralmente inclui um link para criá-lo: {str(e)}"
            )
            raise Exception(
                "Erro ao buscar cliente: Um índice necessário não foi encontrado no banco de dados. "
                "Verifique os logs do servidor para uma mensagem de erro do Firestore que inclui um link para criar o índice automaticamente. "
                f"Detalhe original: {str(e)}"
            )
        except exceptions.FirebaseError as e:
            if hasattr(e, 'code') and e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar lista de cliente da empresa logada: {e}"
                )
                # Decide se quer re-lançar ou tratar aqui. Se re-lançar, a camada superior lida.
                # Por ora, vamos re-lançar para manter o comportamento anterior.
                raise
            elif hasattr(e, 'code') and e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar lista de cliente da empresa logada: {e}"
                )
                raise Exception(
                    "Serviço do Firestore temporariamente indisponível."
                )
            else:
                # Outros erros FirebaseError
                logger.error(
                    f"Erro do Firebase ao consultar lista de cliente da empresa logada: Código: {e.code}, Detalhes: {e}"
                )
            raise  # Re-lança o FirebaseError original ou a Exception customizada

        except Exception as e:  # Captura exceções que não são FirebaseError
            # Logar o tipo da exceção pode ajudar a diagnosticar por que não foi pega antes.
            logger.error(
                f"Erro inesperado (Tipo: {type(e)}) ao consultar lista de cliente da empresa logada: {e}"
            )
            raise


    def get_by_name_cpf_or_phone(self, research_data: str) -> list[Cliente]:
        """
        Obtém uma lista de clientes ativos pelo nome (busca parcial), CPF (busca exata) ou telefone (busca parcial).

        Args:
            research_data (str): Dados de pesquisa (nome, CPF ou telefone).

        Returns:
            Lista de clientes encontrados.
        """
        try:
            research_data_normalized = research_data.lower().strip()
            clientes_result: list[Cliente] = []

            # Abordagem 1: Range Query para busca de prefixo (recomendada para performance)
            # Esta abordagem funciona bem quando o usuário digita o início do nome
            if research_data_normalized:
                # Para first_name - busca por prefixo
                query_first_name = (self.collection
                                    .where(filter=FieldFilter("empresa_id", "==", self.empresa_id))
                                    .where(filter=FieldFilter("status", "==", RegistrationStatus.ACTIVE.name))
                                    .where(filter=FieldFilter("name.first_name_lower", ">=", research_data_normalized))
                                    .where(filter=FieldFilter("name.first_name_lower", "<=", research_data_normalized + '\uf8ff')))

                # Para last_name - busca por prefixo
                query_last_name = (self.collection
                                .where(filter=FieldFilter("empresa_id", "==", self.empresa_id))
                                .where(filter=FieldFilter("status", "==", RegistrationStatus.ACTIVE.name))
                                .where(filter=FieldFilter("name.last_name_lower", ">=", research_data_normalized))
                                .where(filter=FieldFilter("name.last_name_lower", "<=", research_data_normalized + '\uf8ff')))

                # Para CPF - busca exata
                query_cpf = (self.collection
                            .where(filter=FieldFilter("empresa_id", "==", self.empresa_id))
                            .where(filter=FieldFilter("status", "==", RegistrationStatus.ACTIVE.name))
                            .where(filter=FieldFilter("cpf", "==", research_data)))

                # Para telefone - vamos buscar todos e filtrar no código
                # pois telefone pode ter formatações diferentes
                query_all_for_phone = (self.collection
                                    .where(filter=FieldFilter("empresa_id", "==", self.empresa_id))
                                    .where(filter=FieldFilter("status", "==", RegistrationStatus.ACTIVE.name)))

                # Executar queries separadamente para evitar problemas de índice
                queries = [query_first_name, query_last_name, query_cpf]
                found_ids = set()  # Para evitar duplicatas

                for query in queries:
                    try:
                        docs = query.stream()
                        for doc in docs:
                            if doc.id not in found_ids:
                                clientes_data = doc.to_dict()
                                if clientes_data:
                                    clientes_data["id"] = doc.id
                                    cliente_obj = Cliente.from_dict(clientes_data)
                                    clientes_result.append(cliente_obj)
                                    found_ids.add(doc.id)
                    except Exception as query_error:
                        logger.warning(
                            f"Erro em uma das queries específicas: {query_error}")
                        continue

                # Busca no telefone com filtragem no código
                try:
                    phone_docs = query_all_for_phone.stream()
                    for doc in phone_docs:
                        if doc.id not in found_ids:
                            clientes_data = doc.to_dict()
                            if clientes_data:
                                cliente_phone = clientes_data.get("phone", "")
                                # Remove formatação do telefone para comparação
                                research_clean = ''.join(
                                    filter(str.isdigit, research_data))

                                # cliente_phone vem do firestore no formato e164 (+5511999999999)
                                if (research_clean in cliente_phone and
                                        len(research_clean) >= 3):  # Mínimo 3 dígitos para busca
                                    clientes_data["id"] = doc.id
                                    cliente_obj = Cliente.from_dict(clientes_data)
                                    clientes_result.append(cliente_obj)
                                    found_ids.add(doc.id)
                except Exception as phone_error:
                    logger.warning(f"Erro na busca por telefone: {phone_error}")

            # Ordenar resultados
            clientes_result.sort(key=lambda x: (
                x.name.first_name if x.name and x.name.first_name else '',
                x.name.last_name if x.name and x.name.last_name else ''
            ))

            return clientes_result

        except google_api_exceptions.FailedPrecondition as e:
            # Esta é a exceção específica para erros de "índice ausente".
            # A mensagem de erro 'e' já contém o link para criar o índice.
            logger.error(
                f"Erro de pré-condição ao consultar cliente (provavelmente índice ausente): {e}. "
                "O Firestore requer um índice para esta consulta. "
                f"A mensagem de erro original geralmente inclui um link para criá-lo: {str(e)}"
            )
            raise Exception(
                "Erro ao buscar cliente: Um índice necessário não foi encontrado no banco de dados. "
                "Verifique os logs do servidor para uma mensagem de erro do Firestore que inclui um link para criar o índice automaticamente. "
                f"Detalhe original: {str(e)}"
            )

        except exceptions.FirebaseError as e:
            if hasattr(e, 'code') and e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar lista de cliente da empresa logada: {e}")
                raise Exception(
                    "Serviço do Firestore temporariamente indisponível.")
            elif hasattr(e, 'code') and e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar lista de cliente da empresa logada: {e}")
                raise
            else:
                logger.error(
                    f"Erro do Firebase ao consultar lista de cliente da empresa logada: Código: {e.code}, Detalhes: {e}")
            raise

        except Exception as e:
            logger.error(
                f"Erro inesperado (Tipo: {type(e)}) ao consultar lista de cliente da empresa logada: {e}")
            raise
