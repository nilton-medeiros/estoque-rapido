import logging

from src.domains.formas_pagamento.models.formas_pagamento_model import FormaPagamento
from src.domains.formas_pagamento.repositories.implementations import FirebaseFormasPagamentoRepository
from src.domains.shared.models.registration_status import RegistrationStatus
from src.domains.usuarios.models.usuarios_model import Usuario
from src.shared.utils import get_uuid

logger = logging.getLogger(__name__)


class FormasPagamentoService:
    def __init__(self, repository: FirebaseFormasPagamentoRepository):
        """
        Serviço de Formas de Pagamento

        Args:
            repository (FirebaseFormasPagamentoRepository): Repositório de Formas de Pagamento.
        """
        self.repository = repository

    def get_all_formas_pagamento(self, empresa_id: str, status_deleted: bool = False) -> tuple[list[FormaPagamento], int]:
        """
        Obtém todas as formas de pagamento para uma determinada empresa.

        Args:
            empresa_id (str): ID da empresa.
            status (RegistrationStatus): Status para filtrar as formas de pagamento (opcional).

        Returns:
            tuple (list[FormaPagamento], int): Lista de formas de pagamento e a quantidade de deletados.
        """
        try:
            return self.repository.get_all_by_empresa(empresa_id, status_deleted)
        except Exception as e:
            logger.error(
                f"Erro ao obter formas de pagamento para empresa {empresa_id}: {e}")
            raise

    def get_forma_pagamento_by_id(self, empresa_id: str, forma_pagamento_id: str) -> FormaPagamento | None:
        """
        Obtém uma forma de pagamento específica pelo ID.

        Args:
            empresa_id (str): ID da empresa.
            forma_pagamento_id (str): ID da forma de pagamento.

        Returns:
            FormaPagamento | None: A forma de pagamento encontrada ou None.
        """
        try:
            forma_pagamento = self.repository.get_by_id(
                empresa_id, forma_pagamento_id)
            return forma_pagamento
        except Exception as e:
            logger.error(
                f"Erro ao obter forma de pagamento {forma_pagamento_id} para empresa {empresa_id}: {e}")
            raise

    def create_forma_pagamento(self, forma_pagamento: FormaPagamento, current_user: Usuario) -> str:
        """
        Cria uma nova forma de pagamento.

        Args:
            forma_pagamento (FormaPagamento): Objeto da forma de pagamento a ser criada.
            current_user (Usuario): Usuário logado.

        Returns:
            str: ID da forma de pagamento criada.
        """
        forma_pagamento.id = "fpg_" + get_uuid()
        forma_pagamento.created_at = None
        forma_pagamento.created_by_id = current_user.id
        forma_pagamento.created_by_name = current_user.name.nome_completo

        return self.repository.save(forma_pagamento)

    def update_forma_pagamento(self, forma_pagamento: FormaPagamento, current_user: Usuario) -> str:
        """
        Atualiza uma forma de pagamento.

        Args:
            forma_pagamento (FormaPagamento): Objeto da forma de pagamento a ser criada.
            current_user (Usuario): Usuário logado.

        Returns:
            str: ID da forma de pagamento atualizada.
        """
        forma_pagamento.updated_by_id = current_user.id
        forma_pagamento.updated_by_name = current_user.name.nome_completo

        return self.repository.save(forma_pagamento)

    def delete_forma_pagamento(self, forma_pagamento: FormaPagamento, current_user: Usuario) -> str:
        """
        Envia para a lixeira (soft delete) uma forma de pagamento.

        Args:
            forma_pagamento (FormaPagamento): Objeto da forma de pagamento a ser deletada.
            current_user (Usuario): Usuário logado.

        Returns:
            str: ID da forma de pagamento atualizada.
        """
        previous_status = forma_pagamento.status
        forma_pagamento.status = RegistrationStatus.DELETED
        forma_pagamento.deleted_at = None
        forma_pagamento.deleted_by_id = current_user.id
        forma_pagamento.deleted_by_name = current_user.name.nome_completo

        try:
            return self.repository.save(forma_pagamento)
        except Exception as e:
            forma_pagamento.status = previous_status
            forma_pagamento.deleted_at = None
            forma_pagamento.deleted_by_id = None
            forma_pagamento.deleted_by_name = None
            raise

    def restore_forma_pagamento(self, forma_pagamento: FormaPagamento, current_user: Usuario) -> str:
        """
        Restaura da lixeira (soft delete) uma forma de pagamento.

        Args:
            forma_pagamento (FormaPagamento): Objeto da forma de pagamento a ser restaurada.
            current_user (Usuario): Usuário logado.

        Returns:
            str: ID da forma de pagamento atualizada.
        """
        if not forma_pagamento.id:
            raise Exception("ID da forma de pagamento não encontrado.")
        if forma_pagamento.status != RegistrationStatus.DELETED:
            return forma_pagamento.id

        forma_pagamento.status = RegistrationStatus.ACTIVE
        forma_pagamento.updated_at = None
        forma_pagamento.updated_by_id = current_user.id
        forma_pagamento.updated_by_name = current_user.name.nome_completo

        try:
            return self.repository.save(forma_pagamento)
        except Exception as e:
            forma_pagamento.status = RegistrationStatus.DELETED
            forma_pagamento.updated_at = None
            forma_pagamento.updated_by_id = None
            forma_pagamento.updated_by_name = None
            raise
