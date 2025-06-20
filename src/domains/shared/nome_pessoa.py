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
        if not first_name and not last_name:
            raise ValueError("Os nomes não podem ser vazios.")

        palavras_excecoes = {'da', 'das', 'de', 'do', 'dos'}

        self.first_name = None
        self.last_name = ''

        if first_name:
            # Se o primeiro nome no args first_name não é vazio ""
            self.first_name = ' '.join(
                name.lower() if name.lower() in palavras_excecoes else name.capitalize()
                for name in first_name.split()
            )
            if last_name:
                self.last_name = ' '.join(
                    name.lower() if name.lower() in palavras_excecoes else name.capitalize()
                    for name in last_name.split()
                )
        elif last_name:
            # Se o primeiro nome no args first_name é vazio ""
            self.first_name = ' '.join(
                name.lower() if name.lower() in palavras_excecoes else name.capitalize()
                for name in last_name.split()
            )
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

    @property
    def nome_completo(self) -> str:
        """
        Retorna o nome completo do usuário capitalizado em cada palavra.

        Returns:
            str: Nome completo do usuário.
        """
        return f"{self.first_name} {self.last_name}"

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
        palavras_ignoradas = {'da', 'das', 'de', 'do', 'dos'}
        palavras = self.nome_completo
        iniciais = [palavra[0]
                    for palavra in palavras if palavra not in palavras_ignoradas]
        return ''.join(iniciais)

    @property
    def primeiro_e_ultimo_nome(self) -> str:
        """
        Retorna a primeira palavra do primeiro nome e a última palavra do último nome.

        Returns:
            str: Primeira palavra do primeiro nome e última palavra do último nome.
        """
        primeiro_nome_palavras = self.first_name.split() if self.first_name else []
        ultimo_nome_palavras = self.last_name.split()

        primeiro = primeiro_nome_palavras[0] if primeiro_nome_palavras else ""
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
