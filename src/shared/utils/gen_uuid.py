import uuid

def get_uuid(raw: bool = True) -> str:
    """
    Gera um UUID versão 4 (aleatório).

    Args:
        raw (bool): Se True, retorna o UUID sem hífens. Se False, retorna o formato padrão.

    Returns:
        str: UUID em string no formato solicitado
    """
    uuid_value = uuid.uuid4()
    return str(uuid_value).replace('-', '') if raw else str(uuid_value)
