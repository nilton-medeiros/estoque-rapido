class PhoneNumber:
    """
    Classe para padronizar o número de telefone no padrão E.164 para o banco de dados e formatar para visualização.

    Esta classe lida com a padronização e formatação de números de telefone, garantindo que
    os números sejam armazenados corretamente no banco de dados e fornecendo funcionalidades adicionais
    para manipulação dos números.

    Attributes:
        raw_number (str): Número de telefone bruto sem formatação.
        e164 (str): Número de telefone no formato E.164.

    Example:
        Exemplo de como instanciar e usar a classe:
        >>> phone = PhoneNumber("+5511999999999")
        >>> print(phone.get_national())  # Imprime: (11) 99999-9999
    """

    def __init__(self, number: str):
        """
        Inicializa a instância de PhoneNumber com validação e formatação.

        Args:
            number (str): Número de telefone em formato E.164 (ex: +5511999999999).

        Raises:
            ValueError: Se o número de telefone estiver vazio.
        """
        self.raw_number = ''.join(filter(str.isdigit, number))

        if not self.raw_number:
            raise ValueError("O número de telefone não pode estar vazio")

        self.e164 = self.format_to_e164()

    def __str__(self) -> str:
        """
        Returns:
            str: Retorna o número sem o código do país no formato (XX) XXXXX-XXXX.
        """
        return self.get_national()

    @classmethod
    def from_dict(cls, data: str | dict) -> 'PhoneNumber':
        """
        Cria uma instância de PhoneNumber a partir de um dicionário.

        Args:
            data (dict): Dicionário contendo 'e164', 'raw_number' ou apenas uma string.
                Exemplo: {'e164': '+5511999999999'} ou {'raw_number': '5511999999999'}

        Returns:
            PhoneNumber: Nova instância de PhoneNumber.

        Raises:
            ValueError: Se o dicionário não contiver informações válidas de telefone.
        """
        if not data:
            raise ValueError("Dados inválidos para criar PhoneNumber.")

        # Verifica se é um dicionário com campos específicos
        # Se for apenas uma string
        if isinstance(data, str):
            return cls(data)

        elif isinstance(data, dict):
            # Tenta obter o número em diferentes formatos
            number = data.get('e164') or data.get('raw_number')

            if not number:
                raise ValueError(
                    "Número de telefone não encontrado nos dados.")

            return cls(number)

        else:
            raise ValueError("Formato inválido para criar PhoneNumber.")

    def format_to_e164(self) -> str:
        """
        Formata o número para o padrão E.164.

        Returns:
            str: Número de telefone no formato E.164.
        """
        if not self.raw_number.startswith('55'):
            return f"+55{self.raw_number}"
        elif not self.raw_number.startswith('+'):
            return f"+{self.raw_number}"
        return self.raw_number

    def get_national(self) -> str:
        """
        Retorna o número sem o código do país no formato (XX) XXXXX-XXXX.

        Returns:
            str: Número de telefone no formato nacional.
        """
        national = self.raw_number[2:]
        if len(national) == 11:  # Móvel
            return f"({national[:2]}) {national[2:7]}-{national[7:]}"
        elif len(national) == 10:  # Fixo
            return f"({national[:2]}) {national[2:6]}-{national[6:]}"
        return national

    def get_digits_only(self) -> str:
        """
        Retorna apenas os dígitos do número sem qualquer formatação.

        Returns:
            str: Número de telefone contendo apenas dígitos.
        """
        return self.raw_number

    def get_e164(self) -> str:
        """
        Retorna o número no formato E.164.

        Returns:
            str: Número de telefone no formato E.164 (+XXXXXXXXXXX).
        """
        return self.e164

    def get_international(self) -> str:
        """
        Retorna o número no formato internacional +XX (XX) XXXXX-XXXX.

        Returns:
            str: Número de telefone no formato internacional.
        """
        if len(self.raw_number) >= 12:  # Tem código do país
            return f"+{self.raw_number[:2]} {self.get_national()}"
        return self.get_national()

    @staticmethod
    def is_valid_number(number: str) -> bool:
        """
        Validação básica para números de telefone brasileiros.

        Args:
            number (str): Número de telefone a ser validado.

        Returns:
            bool: True se o número de telefone for válido, False caso contrário.
        """
        digits = ''.join(filter(str.isdigit, number))

        # Comprimentos válidos para números brasileiros com código do país
        valid_lengths = [12, 13]  # 12 para fixo, 13 para móvel
        if len(digits) not in valid_lengths:
            return False

        # Verifica se começa com o código do país brasileiro
        if not (digits.startswith('55') or number.startswith('+55')):
            return False

        return True


# Exemplo de uso:
'''
try:
    # Criar a partir de diferentes formatos
    phone1 = PhoneNumber("+5511999999999")
    phone2 = PhoneNumber("5511999999999")
    phone3 = PhoneNumber("11999999999")

    # Diferentes formatos de saída
    >>> print(phone1.get_national())        # (11) 99999-9999
    >>> print(phone1.get_digits_only())     # 5511999999999
    >>> print(phone1.get_e164())           # +5511999999999
    >>> print(phone1.get_international())   # +55 (11) 99999-9999

    # Validação
    >>> print(PhoneNumber.is_valid_number("+5511999999999"))  # True
    >>> print(PhoneNumber.is_valid_number("+1234567890"))     # False
except ValueError as e:
    >>> print("Erro:", e)
'''
