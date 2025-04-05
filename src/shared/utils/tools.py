from typing import Tuple


def get_first_and_last_name(full_name: str) -> Tuple[str, str | None]:
    """
    Extrai o primeiro e o último nome de uma string de nome completo.

    Parametrôs:
        full_name (str): Nome e/ou sobrenome do usuário.
    Retorna uma tupla (first_name, last_name).
    """
    list_names = full_name.split()
    first_name = list_names[0].strip().capitalize()
    last_name = list_names[-1].strip().capitalize() if len(list_names) > 1 else None

    return first_name, last_name


def initials(name: str) -> str:
    """Retorna as iniciais do nome completo"""
    palavras_ignoradas = {'da', 'das', 'de', 'do', 'dos'}
    palavras = name.split()
    iniciais = [palavra[0]
                for palavra in palavras if palavra not in palavras_ignoradas]
    return ''.join(iniciais)
