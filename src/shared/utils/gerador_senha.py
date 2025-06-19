import random
import string

def gerar_senha(tamanho: int = 8):
    """
    Gera uma senha aleatória com tamanho especificado.

    A senha conterá pelo menos:
    - 1 caractere especial
    - 1 letra maiúscula
    - 1 letra minúscula
    - 1 número

    Args:
        tamanho (int): Tamanho desejado da senha (mínimo 4)

    Returns:
        str: Senha gerada

    Raises:
        ValueError: Se o tamanho for menor que 4
    """
    if tamanho < 4:
        raise ValueError("Tamanho da senha deve ser pelo menos 4 para incluir todos os tipos de caracteres")

    # Conjuntos de caracteres
    minusculas = string.ascii_lowercase
    maiusculas = string.ascii_uppercase
    numeros = string.digits
    # especiais = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    especiais = "!@#%&"

    # Garantir pelo menos um de cada tipo
    senha = [
        random.choice(minusculas),
        random.choice(maiusculas),
        random.choice(numeros),
        random.choice(especiais)
    ]

    # Preencher o restante com caracteres aleatórios de todos os tipos
    # todos_caracteres = minusculas + maiusculas + numeros + especiais
    todos_caracteres = minusculas + maiusculas + numeros

    for _ in range(tamanho - 4):
        senha.append(random.choice(todos_caracteres))

    # Embaralhar a senha para não ter padrão previsível
    random.shuffle(senha)

    return ''.join(senha)

# Exemplo de uso
# if __name__ == "__main__":
#     # Testando diferentes tamanhos
#     for tamanho in [8, 12, 16, 20]:
#         senha = gerar_senha(tamanho)
#         print(f"Senha de {tamanho} caracteres: {senha}")

#     # Função adicional para verificar se a senha atende aos critérios
#     def verificar_senha(senha):
#         """Verifica se a senha atende a todos os critérios"""
#         tem_minuscula = any(c.islower() for c in senha)
#         tem_maiuscula = any(c.isupper() for c in senha)
#         tem_numero = any(c.isdigit() for c in senha)
#         tem_especial = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in senha)

#         return tem_minuscula and tem_maiuscula and tem_numero and tem_especial

#     # Testando a verificação
#     print("\nVerificação das senhas geradas:")
#     for tamanho in [8, 12, 16]:
#         senha = gerar_senha(tamanho)
#         valida = verificar_senha(senha)
#         print(f"Senha: {senha} - Válida: {valida}")
