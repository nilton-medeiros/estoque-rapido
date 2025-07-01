from enum import Enum

class RegistrationStatus(Enum):
    """Status de Registro com labels contextuais."""
    ACTIVE = "Ativo"
    INACTIVE = {"default": "Inativo", "empresa": "Arquivado", "produto": "Descontinuado"}
    DELETED = "Lixeira"

    def get_label(self, context: str = "default") -> str:
        """Retorna o label apropriado para o contexto."""
        if isinstance(self.value, dict):
            return self.value.get(context, self.value.get("default", str(self.value)))
        return self.value

    def __str__(self) -> str:
        """Retorna o label padrão quando convertido para string."""
        return self.get_label()

    @property
    def default_label(self) -> str:
        """Propriedade para acessar o label padrão facilmente."""
        return self.get_label()

    @property
    def empresa_label(self) -> str:
        """Propriedade para acessar o label para empresas facilmente."""
        return self.get_label("empresa")

    @property
    def produto_label(self) -> str:
        """Propriedade para acessar o label para produtos facilmente."""
        return self.get_label("produto")

"""
# Uso muito mais limpo:
status = RegistrationStatus.INACTIVE

print(f"Padrão: {status.get_label()}")                  # "Inativo" (padrão)
print(f"via get_label: {status.get_label("empresa")}")  # "Arquivado"
print(f"via get_label: {status.get_label("produto")}")  # "Descontinuado"
print(f"via str: {str(status)}")                        # "Inativo" (via __str__)
print(f"via property: {status.default_label}")          # "Inativo" (via property)
print(f"via property: {status.empresa_label}")          # "Arquivado" (via property)
print(f"via property: {status.produto_label}")          # "Descontinuado" (via property)

# Comparações funcionam normalmente:
if status == RegistrationStatus.INACTIVE:
    print("Status é INACTIVE")
"""