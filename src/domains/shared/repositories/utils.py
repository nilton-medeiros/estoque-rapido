from firebase_admin import firestore

from src.domains.shared import RegistrationStatus


def set_audit_timestamps(data: dict) -> dict:
    """
    Define os timestamps de auditoria para um dicionário de dados a ser salvo no Firestore.

    Esta função modifica o dicionário `data` in-place e o retorna.

    Args:
        data (dict): O dicionário de dados da entidade, geralmente vindo de `to_dict_db()`.

    Returns:
        dict: O mesmo dicionário de dados, agora com os timestamps de auditoria definidos.
    """
    # Define `created_at` apenas na criação inicial do documento.
    if not data.get("created_at"):
        data['created_at'] = firestore.SERVER_TIMESTAMP # type: ignore

    # `updated_at` é sempre definido/atualizado a cada salvamento.
    data['updated_at'] = firestore.SERVER_TIMESTAMP # type: ignore

    status = data.get("status")

    # Gerencia os timestamps de status com base na mudança de estado.
    if status == RegistrationStatus.ACTIVE.name and not data.get("activated_at"):
        data['activated_at'] = firestore.SERVER_TIMESTAMP # type: ignore
    elif status == RegistrationStatus.DELETED.name and not data.get("deleted_at"):
        data['deleted_at'] = firestore.SERVER_TIMESTAMP # type: ignore
    elif status == RegistrationStatus.INACTIVE.name and not data.get("inactivated_at"):
        data['inactivated_at'] = firestore.SERVER_TIMESTAMP # type: ignore

    return data
