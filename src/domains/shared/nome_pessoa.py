class NomePessoa:
    """
    Classe para padronizar o nome dos usuários.

    Esta classe lida com a padronização do nome dos usuários, garantindo que
    os nomes sejam formatados corretamente e fornecendo funcionalidades adicionais
    para manipulação dos nomes.

    Attributes:
        first_name (str): Primeiro nome do usuário.
        last_name (str): Último nome do usuário.

    Example:
        Exemplo de como instanciar e usar a classe:
        >>> pessoa = NomePessoa("João", "Silva")
        >>> print(pessoa.nome_completo)  # Imprime: João Silva
    """

    def __init__(self, first_name: str | None = None, last_name: str | None = None):
        """
        Inicializa a instância de NomePessoa com validação e formatação.

        Args:
            first_name (str): Primeiro nome do usuário.
            last_name (str, opcional): Último nome do usuário. Default é None.

        Raises:
            ValueError: Se ambos os nomes (primeiro e último) forem vazios.
        """
        def _format_name_part(name_part: str | None) -> str | None:
            """Formata uma parte do nome, capitalizando e tratando exceções."""
            if not name_part or not name_part.strip():
                return None

            palavras_excecoes = {'da', 'das', 'de', 'do', 'dos', 'e'}
            return ' '.join(
                word.lower() if word.lower() in palavras_excecoes else word.capitalize()
                for word in name_part.split()
            )

        self.first_name = _format_name_part(first_name)
        self.last_name = _format_name_part(last_name)

        # Validação final para garantir que o primeiro nome é obrigatório.
        if not self.first_name:
            raise ValueError("O primeiro nome (first_name) é obrigatório e não pode ser vazio.")

    @classmethod
    def from_dict(cls, data: dict) -> 'NomePessoa':
        """
        Cria uma instância de NomePessoa a partir de um dicionário.

        Args:
            data (dict): Dicionário contendo 'first_name' e opcionalmente 'last_name'.
                Exemplo: {'first_name': 'João', 'last_name': 'Silva'}

        Returns:
            NomePessoa: Nova instância de NomePessoa.

        Raises:
            ValueError: Se o dicionário não contiver 'first_name' nem 'last_name'.
        """
        if not data:
            raise ValueError("Dados inválidos para criar NomePessoa.")

        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')

        return cls(first_name, last_name)


    def to_dict(self) -> dict:
        return {
            "first_name": self.first_name,
            "last_name": self.last_name
        }


    @property
    def nome_completo(self) -> str:
        """
        Retorna o nome completo do usuário capitalizado em cada palavra.

        Returns:
            str: Nome completo do usuário.
        """
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return ' '.join(parts).strip()

    @property
    def nome_completo_maiusculo(self) -> str:
        """
        Retorna o nome completo do usuário em maiúsculas.

        Returns:
            str: Nome completo do usuário em maiúsculas.
        """
        return self.nome_completo.upper()

    @property
    def nome_completo_minusculo(self) -> str:
        """
        Retorna o nome completo do usuário em minúsculo.

        Returns:
            str: Nome completo do usuário em minúsculo.
        """
        return self.nome_completo.lower()

    @property
    def iniciais(self) -> str:
        """Retorna as iniciais do nome completo"""
        palavras_ignoradas = {'da', 'das', 'de', 'do', 'dos', 'e'}
        palavras = self.nome_completo.split()
        iniciais = [palavra[0]
                    for palavra in palavras if palavra.lower() not in palavras_ignoradas]
        return ''.join(iniciais)

    @property
    def primeiro_e_ultimo_nome(self) -> str:
        """
        Retorna a primeira palavra do primeiro nome e a última palavra do último nome.

        Returns:
            str: Primeira palavra do primeiro nome e última palavra do último nome.
        """
        # O __init__ garante que self.first_name nunca será None se o objeto for criado com sucesso.
        # Usamos 'assert' para informar ao Pylance que self.first_name é uma string neste ponto.
        assert self.first_name is not None, "first_name não deveria ser None aqui."

        primeiro_nome_palavras = self.first_name.split() # Agora Pylance não reclama
        ultimo_nome_palavras = self.last_name.split() if self.last_name else []

        primeiro = primeiro_nome_palavras[0] # first_name.split() sempre terá pelo menos um elemento
        ultimo = ultimo_nome_palavras[-1] if ultimo_nome_palavras else ""

        if primeiro and ultimo:
            return f"{primeiro} {ultimo}"
        elif primeiro:
            return primeiro
        return ultimo

# Exemplo de uso:
'''
try:
    pessoa = NomePessoa("João", "Silva")
    >>> print("Primeiro nome:", pessoa.first_name)
    >>> print("Último nome:", pessoa.last_name)
    >>> print("Nome completo:", pessoa.nome_completo)
    >>> print("Nome completo em maiúsculo:", pessoa.nome_completo_maiusculo)

    # Testando com nome vazio
>>>     pessoa_invalida = NomePessoa("", "Silva")
>>> except ValueError as e:
>>>     print("Erro:", e)
'''
