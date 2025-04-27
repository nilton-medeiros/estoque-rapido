import uuid

def get_uuid(raw: bool = True) -> str:
    """
    Gera um UUID versão 4 (aleatório).

    Args:
        raw (bool): Se True, retorna o UUID sem hífens. Se False, retorna o formato padrão.

    Returns:
        str: UUID em string no formato solicitado

    Nota: Para gerar um token, usar secrets
          import secrets
          tamanho = 30  # Tamanho do token a ser gerado
          chave = secrets.token_hex(30)
          print(chave)
    """
    uuid_value = str(uuid.uuid4())
    return uuid_value.replace('-', '') if raw else uuid_value
