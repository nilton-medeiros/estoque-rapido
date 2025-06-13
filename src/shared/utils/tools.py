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


def capitalize_first_word_of_sentence(text: str) -> str:
    """
    Capitaliza a primeira palavra de uma frase. As demais palavras permanecem inalteradas.
    Preserva os espaços iniciais e finais da string original.

    Args:
        text (str): A frase ou palavra a ser processada.

    Returns:
        str: O texto com a primeira palavra capitalizada.
             Retorna a string original se ela for vazia ou contiver apenas espaços.

    Exemplo:
        >>> capitalize_first_word_of_sentence("lava roupa em pó Karina Multi ação")
        'Lava roupa em pó Karina Multi ação'
        >>> capitalize_first_word_of_sentence("palavra")
        'Palavra'
        >>> capitalize_first_word_of_sentence("")
        ''
        >>> capitalize_first_word_of_sentence("  teste com espaços  ")
        '  Teste com espaços  '
        >>> capitalize_first_word_of_sentence("   ") # Apenas espaços
        '   '
        >>> capitalize_first_word_of_sentence("primeira")
        'Primeira'
    """
    if not text.strip(): # Retorna original se for vazia ou só espaços
        return text
    parts = text.split(' ', 1)
    parts[0] = parts[0].capitalize()
    return ' '.join(parts)


def capitalize_words(text: str) -> str:
    return ' '.join(word.capitalize() for word in text.split())
