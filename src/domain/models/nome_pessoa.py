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

    def __init__(self, first_name: str, last_name: str = None):
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

        self.first_name = None
        self.last_name = ''

        if first_name:
            self.first_name = first_name.strip().capitalize()
            if last_name:
                self.last_name = last_name.strip().capitalize()
        else:
            self.first_name = last_name.strip().capitalize()

    @property
    def nome_completo(self) -> str:
        """
        Retorna o nome completo do usuário.

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


# Exemplo de uso:
'''
try:
    pessoa = NomePessoa("João", "Silva")
    print("Primeiro nome:", pessoa.first_name)
    print("Último nome:", pessoa.last_name)
    print("Nome completo:", pessoa.nome_completo)
    print("Nome completo em maiúsculo:", pessoa.nome_completo_maiusculo)

    # Testando com nome vazio
    pessoa_invalida = NomePessoa("", "Silva")
except ValueError as e:
    print("Erro:", e)
'''
