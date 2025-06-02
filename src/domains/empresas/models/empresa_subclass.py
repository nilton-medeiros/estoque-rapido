
from enum import Enum


class Status(Enum):
    ACTIVE = "Ativo"
    ARCHIVED = "Arquivado"
    DELETED = "Lixeira"


class Environment(Enum):
    HOMOLOGACAO = "Homologação"
    PRODUCAO = "Produção"


class EmpresaSize(Enum):
    MEI = "Microempreendedor Individual"  # MEI
    MICRO = "Microempresa"  # ME
    SMALL = "Pequena Empresa"  # EPP
    MEDIUM = "Média Empresa"
    LARGE = "Grande Empresa"
    OTHER = "DEMAIS"


class CodigoRegimeTributario(Enum):
    """
    Código Regime tributário (CRT):

    Exemplo de uso (Enum com Tupla):
      crt: CodigoRegimeTributario = CodigoRegimeTributario.SIMPLES_NACIONAL_MEI
      >>> print(crt.name)  # Retorna: SIMPLES_NACIONAL_MEI
      >>> print(crt.value)  # Retorna: (4, "Microempreendedor Individual (MEI)")
      >>> print(crt.value[0])  # Retorna: 4
      >>> print(crt.value[1])  # Retorna: Microempreendedor Individual (MEI)
    """
    SIMPLES_NACIONAL = (1, "Simples Nacional")
    SIMPLES_NACIONAL_EXCESSO_SUB = (2, "Simples Nacional Excesso Sublimite")
    REGIME_NORMAL = (3, "Regime Normal")
    SIMPLES_NACIONAL_MEI = (4, "Microempreendedor Individual (MEI)")
