from dataclasses import dataclass
from decimal import Decimal
from typing import Self, Union  # Adicionar Union para compatibilidade se precisar


@dataclass(frozen=True)
class Money:
    """
    Representa um valor monetário com precisão, evitando problemas de ponto flutuante.

    Armazena o valor em centavos como um número inteiro para garantir exatidão
    e associa um símbolo de moeda. As instâncias de Money são imutáveis.

    Args:
        amount_cents (int): O valor monetário em centavos (ex: R$ 100,00 é 10000 centavos).
        currency_symbol (str): O símbolo da moeda (ex: "R$", "$", "€").

    Class Methods:
        mint(amount: Union[Decimal, str], currency_symbol: str = "R$") -> Self:
            Cria uma nova instância de Money a partir de um valor decimal ou string.
            Este é o método preferencial para criar objetos Money, garantindo a
            conversão segura para centavos.

    Magic Methods (Operadores):
        Permite operações aritméticas e comparações entre instâncias de Money,
        garantindo que as moedas sejam compatíveis.
        - `+` (__add__): Soma dois valores Money.
        - `-` (__sub__): Subtrai dois valores Money.
        - `*` (__mul__): Multiplica um valor Money por um inteiro ou Decimal.
        - `/` (__truediv__): Divide um valor Money por um inteiro ou Decimal.
        - `<`, `<=`, `>`, `>=` (__lt__, __le__, __gt__, __ge__): Compara valores Money.
        - `==` (__eq__): Compara igualdade entre dois valores Money.
        - `str` (__str__): Retorna a representação formatada do valor (ex: "R$100.00").

    Raises:
        ValueError: Se tentar realizar operações (soma, subtração, comparação)
                    entre valores de moedas diferentes.
        ZeroDivisionError: Se tentar dividir por zero.

    Example Usage:
        >>> # Criação de valores monetários
        >>> balance = Money.mint("100.00", "R$")  # Saldo inicial de R$ 100,00
        >>> withdrawal = Money.mint(Decimal("42.37"), "R$") # Saque de R$ 42,37
        >>> deposit = Money.mint("0.10") # Depósito de R$ 0,10 (assume R$ por padrão)

        >>> # Operações aritméticas
        >>> result = balance - withdrawal + deposit
        >>> print(f"{balance} - {withdrawal} + {deposit} = {result}")
        R$100,00 - R$42,37 + R$0,10 = R$57,73

        >>> # Multiplicação e Divisão
        >>> total_price = Money.mint("15.50", "R$") * 3
        >>> print(f"Preço total de 3 itens: {total_price}")
        Preço total de 3 itens: R$46,50

        >>> half_value = Money.mint("50.00", "USD") / 2
        >>> print(f"Metade do valor: {half_value}")
        Metade do valor: $25.00

        >>> # Comparações
        >>> print(f"Saldo é maior que o saque? {balance > withdrawal}")
        Saldo é maior que o saque? True

        >>> # Tentativa de operação com moedas diferentes (resultará em erro)
        >>> try:
        ...     Money.mint("10", "R$") + Money.mint("5", "$")
        ... except ValueError as e:
        ...     print(e)
        Não é possível adicionar dinheiro com moedas diferentes: R$ vs $
    """
    amount_cents: int
    currency_symbol: str

    @classmethod
    def mint(cls, amount: Union[Decimal, str], currency_symbol: str = "R$") -> Self:
        # "mint" vem da ideia de "cunhar" moedas
        if isinstance(amount, str):
            amount = Decimal(amount)
        amount = amount.quantize(Decimal("0.01"))  # Garante precisão de 2 casas decimais
        return cls(int(amount * 100), currency_symbol)

    def __str__(self):
        formatted_amount = f"{Decimal(self.amount_cents) / 100:.2f}"
        if self.currency_symbol in ("R$", "BRL"):
            formatted_amount = formatted_amount.replace('.', ',')
        return f"{self.currency_symbol} {formatted_amount}"

    def get_decimal(self):
        return Decimal(self.amount_cents) / 100

    def get_int(self):
        return self.amount_cents

    def __add__(self, other: Self) -> Self:
        if not isinstance(other, Money):
            return NotImplemented

        if self.currency_symbol != other.currency_symbol:
            raise ValueError(
                f"Não é possível adicionar dinheiro com moedas diferentes: {self.currency_symbol} vs {other.currency_symbol}")

        return self.__class__(self.amount_cents + other.amount_cents, self.currency_symbol)

    def __sub__(self, other: Self) -> Self:
        if not isinstance(other, Money):
            return NotImplemented

        if self.currency_symbol != other.currency_symbol:
            raise ValueError(
                f"Não é possível subtrair dinheiro com moedas diferentes: {self.currency_symbol} vs {other.currency_symbol}")

        return self.__class__(self.amount_cents - other.amount_cents, self.currency_symbol)

    def __mul__(self, other: Union[int, Decimal]) -> Self:
        if isinstance(other, (int, Decimal)):
            temp_amount = Decimal(self.amount_cents) * other
            return self.__class__(int(temp_amount), self.currency_symbol)
        return NotImplemented

    def __truediv__(self, other: Union[int, Decimal]) -> Self:
        if isinstance(other, (int, Decimal)):
            if other == 0:
                raise ZeroDivisionError("Não é possível dividir dinheiro por zero")
            temp_amount = Decimal(self.amount_cents) / other
            return self.__class__(int(temp_amount), self.currency_symbol)
        return NotImplemented

    def __lt__(self, other: Self) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency_symbol != other.currency_symbol:
            raise ValueError("Não é possível comparar dinheiro com moedas diferentes")
        return self.amount_cents < other.amount_cents

    def __le__(self, other: Self) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency_symbol != other.currency_symbol:
            raise ValueError("Não é possível comparar dinheiro com moedas diferentes")
        return self.amount_cents <= other.amount_cents

    def __gt__(self, other: Self) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency_symbol != other.currency_symbol:
            raise ValueError("Não é possível comparar dinheiro com moedas diferentes")
        return self.amount_cents > other.amount_cents

    def __ge__(self, other: Self) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency_symbol != other.currency_symbol:
            raise ValueError("Não é possível comparar dinheiro com moedas diferentes")
        return self.amount_cents >= other.amount_cents

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount_cents == other.amount_cents and self.currency_symbol == other.currency_symbol

    def to_dict(self) -> dict:
        """Exporta a instância de Money para um dicionário compatível com Firestore."""
        return {
            "amount_cents": self.amount_cents,
            "currency_symbol": self.currency_symbol
        }

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Cria uma instância de Money a partir de um dicionário do Firestore."""
        # Podemos usar o construtor direto já que amount_cents e currency_symbol
        # são os campos que serão lidos do Firestore.
        amount: int = data["amount_cents"]  # No Firestore o amount_cents é armazenado como inteiro (15.75 => 1575)
        return cls(amount_cents=amount, currency_symbol=data.get("currency_symbol", "R$"))
