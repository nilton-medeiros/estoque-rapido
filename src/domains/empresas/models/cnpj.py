class CNPJ:
    def __init__(self, cnpj: str):
        """
        Inicializa o CNPJ com validação e formatação.

        Args:
            cnpj (str): Número bruto do CNPJ.

        # Exemplo de uso
        >>> if __name__ == "__main__":
        >>>     try:
        >>>         cnpj = CNPJ("12345678000195")
        >>>         print(cnpj)  # Imprime CNPJ formatado
        >>>     except ValueError as e:
        >>>         print(e)

        """
        self.raw_cnpj = ''.join(filter(str.isdigit, cnpj))
        self.formatted_cnpj = self._format()

        if not self.is_valid():
            raise ValueError("CNPJ inválido")

    def _format(self) -> str:
        """
        Formata o CNPJ.

        Returns:
            str: CNPJ formatado (XX.XXX.XXX/YYYY-ZZ).

        Raises:
            ValueError: Se o CNPJ não contiver 14 dígitos.
        """
        digits = self.raw_cnpj

        if len(digits) != 14:
            raise ValueError("CNPJ deve conter 14 dígitos")

        return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"

    def is_valid(self) -> bool:
        # Remove caracteres não numéricos
        cnpj = self.raw_cnpj

        # Verifica se tem 14 dígitos
        if len(cnpj) != 14:
            return False

        # Verifica se todos os dígitos são iguais
        if cnpj == cnpj[0] * 14:
            return False

        # Cálculo do primeiro dígito verificador
        soma = 0
        peso = 5
        for i in range(12):
            soma += int(cnpj[i]) * peso
            peso = 9 if peso == 2 else peso - 1

        digito1 = 11 - (soma % 11)
        if digito1 > 9:
            digito1 = 0

        # Cálculo do segundo dígito verificador
        soma = 0
        peso = 6
        for i in range(13):
            soma += int(cnpj[i]) * peso
            peso = 9 if peso == 2 else peso - 1

        digito2 = 11 - (soma % 11)
        if digito2 > 9:
            digito2 = 0

        # Verifica se os dígitos verificadores estão corretos
        return cnpj[-2:] == f"{digito1}{digito2}"

    def __str__(self) -> str:
        """
        Returns:
            str: CNPJ formatado.
        """
        return self.formatted_cnpj
