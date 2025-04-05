import re


def validate_password_strength(password: str) -> str:
    """
    Valida a força da senha seguindo critérios de segurança.
    Retorna string com mensagem de erro ou "Senha forte"
    """
    if len(password) < 8:
        return "A senha deve ter:\n• pelo menos 8 caracteres"

    checks = [
        (r'[A-Z]', "pelo menos uma letra maiúscula"),
        (r'[a-z]', "pelo menos uma letra minúscula"),
        (r'[0-9]', "pelo menos um número"),
        (r'[!@#$%^&*(),.?":{}|<>]', "pelo menos um caractere especial")
    ]

    failed_checks = [msg for pattern,
                     msg in checks if not re.search(pattern, password)]

    if failed_checks:
        # Cria a mensagem de erro com uma quebra de linha antes de cada item
        return "A senha deve conter:\n• " + "\n• ".join(failed_checks)

    return "Senha forte"


def validate_email(email: str) -> bool:
    """
    Valida o formato do email usando regex.
    Retorna True ou False
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not email:
        return False, "O email é obrigatório"
    if not re.match(email_pattern, email):
        return False
    return True


def format_phone_number(phone: str) -> str:
    """
    Formata o número de telefone para o padrão E.164.
    """
    # Remove todos os caracteres não numéricos
    phone = re.sub(r'\D', '', phone)
    # phone = ''.join(filter(str.isdigit, phone)) // Outra forma de remover caracteres

    # Adiciona o código do país (+55 para Brasil) se não estiver presente
    if not phone.startswith('55'):
        phone = '55' + phone

    # Retorna o número formatado no padrão E.164
    return f"+{phone}"


def validate_phone(phone: str) -> str:
    """
    Valida o número de telefone.
    Retorna uma tupla (is_valid, message)
    """
    # Remove todos os caracteres não numéricos para a validação
    numbers = re.sub(r'\D', '', phone)
    # numbers = ''.join(filter(str.isdigit, phone)) // Outra forma de remover caracteres

    if not numbers:
        return "O telefone é obrigatório"

    if len(numbers) < 10:
        return "O telefone deve ter pelo menos 10 dígitos"

    if len(numbers) > 11:
        return "O telefone não pode ter mais de 11 dígitos"

    if len(numbers) == 11 and numbers[2] not in '9678':
        return "Celular inválido (deve começar com 9)"

    dispositivo = 'Celular' if len(
        numbers) == 11 and numbers[2] in '9678' else 'Telefone'
    return f"OK: {dispositivo} válido"
