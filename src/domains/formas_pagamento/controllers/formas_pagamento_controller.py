import logging
from typing import Any

from firebase_admin import exceptions
from src.domains.formas_pagamento.models.formas_pagamento_model import FormaPagamento
from src.domains.formas_pagamento.services.formas_pagamento_service import FormasPagamentoService
from src.domains.shared.models.registration_status import RegistrationStatus
from src.domains.usuarios.models.usuarios_model import Usuario

logger = logging.getLogger(__name__)


class FormasPagamentoController:
    def __init__(self, service: FormasPagamentoService):
        """
        Controllers da Formas de Pagamento

        Args:
            service (FormasPagamentoService): Serviço de Formas de Pagamento.
        """
        self.service = service

    def get_formas_pagamento(self, empresa_id: str, status_deleted: bool = False) -> tuple[list[FormaPagamento], int]:
        """
        Obtém todas as formas de pagamento para uma empresa, com tratamento de status.

        Args:
            empresa_id (str): ID da empresa.
            status_deleted (bool): Status para filtrar Ativos&Inativos ou apenas deletados.

        Returns:
            tuple (list[FormaPagamento], int): Lista de formas de pagamento e a quantidade de deletados.
        """
        try:
            return self.service.get_all_formas_pagamento(empresa_id, status_deleted)
        except Exception as e:
            logger.error(
                f"Erro no controller ao obter formas de pagamento: {e}")
            raise  # Re-lança para ser tratado em uma camada superior (ex: API)

    def get_formas_pagamento_summary(self, empresa_id: str) -> dict[str, Any]:
        """
        Obtém um resumo das formas de pagamento para uma empresa.

        Args:
            empresa_id (str): ID da empresa logada.

        Returns:
            dict: Resumo das formas de pagamento.
                 sucesso: {"status": "success", "data": [summary_list]}
                 erro: {"status": "error", "message": "mensagem de erro"}
        """
        response = {}
        try:
            if not empresa_id:
                logger.error("ID da empresa não pode ser nulo ou vazio.")
                return {"status": "error", "message": "ID da empresa não pode ser nulo ou vazio."}

            summary_list = self.service.get_summary(empresa_id)

            if summary_list:
                response = {"status": "success", "data": summary_list}
            else:
                response = {"status": "error", "message": "Nenhuma forma de pagamento encontrada."}
        except ValueError as e:
            response = {"status": "error", "message": f"ValueError: Erro de validação: {str(e)}"}
        except Exception as e:
            response = {"status": "error", "message": "Erro ao obter resumo das formas de pagamento."}
        return response


    def get_forma_pagamento(self, empresa_id: str, forma_pagamento_id: str) -> FormaPagamento | None:
        """
        Obtém uma forma de pagamento específica pelo ID.

        Args:
            empresa_id (str): ID da empresa.
            forma_pagamento_id (str): ID da forma de pagamento.

        Returns:
            FormaPagamento: A forma de pagamento encontrada ou uma excessão
        """
        try:
            return self.service.get_forma_pagamento_by_id(empresa_id, forma_pagamento_id)
        except Exception as e:
            logger.error(
                f"Erro no controller ao obter forma de pagamento por ID: {e}")
            raise

    def save_forma_pagamento(self, forma_pagamento: FormaPagamento, current_user: Usuario) -> dict[str,str]:
        """
        Cria uma nova forma de pagamento.

        Args:
            forma_pagamento (FormaPagamento): Objeto da forma de pagamento a ser criada.
            current_user (Usuario): Usuário logado.

        Returns:
            dict: Resultado com status e mensagem (ex.: {"status": "success", "id": id} ou {"status": "error", "message": mensagem}).
        """
        try:
            if forma_pagamento.id:
                id = self.service.update_forma_pagamento(forma_pagamento, current_user)
            else:
                id = self.service.create_forma_pagamento(forma_pagamento, current_user)
            return {"status": "success", "id": id, "message": "Forma de pagamento salvo com sucesso."}
        except ValueError as ve:
            logger.error(
                f"Erro de validação ao salvar forma de pagamento: {ve}")
            return {"status": "error", "message": f"Erro de validação: {str(ve)}"}
        except exceptions.FirebaseError as fe:
            logger.error(f"Erro do Firebase ao salvar forma de pagamento: {fe}")
            return {"status": "error", "message": "Falha ao salvar no banco de dados. Tente novamente mais tarde."}
        except Exception as e:
            logger.error(f"Erro inesperado ao salvar forma de pagamento: {e}")
            return {"status": "error", "message": "Erro inesperado. Consulte o suporte técnico."}

    def delete_forma_pagamento(self, forma_pagamento: FormaPagamento, current_user: Usuario) -> dict[str,str]:
        if not forma_pagamento.id:
            logger.error("ID da forma de pagamento não encontrado.")
            return {"status": "error", "message": "ID da forma de pagamento não encontrado."}
        try:
            id = self.service.delete_forma_pagamento(forma_pagamento, current_user)
            return {"status": "success", "id": id, "message": "Forma de pagamento enviada para lixeira com sucesso."}
        except ValueError as ve:
            logger.error(
                f"Erro de validação no 'SOFT DELETE' forma de pagamento: {ve}")
            return {"status": "error", "message": f"Erro de validação: {str(ve)}"}
        except exceptions.FirebaseError as fe:
            logger.error(f"Erro do Firebase no 'SOFT DELETE' forma de pagamento: {fe}")
            return {"status": "error", "message": "Falha ao enviar para lixeira. Tente novamente mais tarde."}
        except Exception as e:
            logger.error(f"Erro inesperado no 'SOFT DELETE' forma de pagamento: {e}")
            return {"status": "error", "message": "Erro inesperado. Consulte o suporte técnico."}

    def restore_from_trash_forma_pagamento(self, forma_pagamento: FormaPagamento, current_user: Usuario) -> dict[str,str]:
        if not forma_pagamento.id:
            logger.error("ID da forma de pagamento não encontrado.")
            return {"status": "error", "message": "ID da forma de pagamento não encontrado."}
        try:
            id = self.service.restore_forma_pagamento(forma_pagamento, current_user)
            return {"status": "success", "id": id, "message": "Forma de pagamento enviada para lixeira com sucesso."}
        except ValueError as ve:
            logger.error(
                f"Erro de validação no 'SOFT DELETE' forma de pagamento: {ve}")
            return {"status": "error", "message": f"Erro de validação: {str(ve)}"}
        except exceptions.FirebaseError as fe:
            logger.error(f"Erro do Firebase no 'SOFT DELETE' forma de pagamento: {fe}")
            return {"status": "error", "message": "Falha ao enviar para lixeira. Tente novamente mais tarde."}
        except Exception as e:
            logger.error(f"Erro inesperado no 'SOFT DELETE' forma de pagamento: {e}")
            return {"status": "error", "message": "Erro inesperado. Consulte o suporte técnico."}
