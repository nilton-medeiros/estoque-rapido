import os

from src.shared.utils.gen_uuid import get_uuid


def generate_unique_bucket_filename(original_filename: str, prefix: str) -> str:
    """
    Gera um nome de arquivo único e padronizado para armazenamento em um bucket.

    O formato gerado é: <prefix>/img_<uuid>.<extensao_em_minusculo>

    Args:
        original_filename (str): O nome original do arquivo, incluindo a extensão.
        prefix (str): O prefixo a ser usado no caminho do bucket,
                      normalmente representando um domínio (ex: 'usuarios', 'empresas/logos').

    Returns:
        str: Uma string única para ser usada como chave do objeto no bucket.
    """
    file_uid = get_uuid()
    _, dot_extension = os.path.splitext(original_filename)
    dot_extension = dot_extension.lower()
    return f"{prefix}/img_{file_uid}{dot_extension}"

