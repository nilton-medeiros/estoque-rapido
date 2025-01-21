class NomePessoa:
    def __init__(self, first_name: str, last_name: str = None):
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
        return f"{self.first_name} {self.last_name}"

    @property
    def nome_completo_maiusculo(self) -> str:
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
