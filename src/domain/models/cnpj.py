class CNPJ:
    def __init__(self, cnpj: str):
        """
        Inicializa o CNPJ com validação e formatação.

        Args:
            cnpj (str): Número bruto do CNPJ.

        # Exemplo de uso
        if __name__ == "__main__":
            try:
                cnpj = CNPJ("12345678000195")
                print(cnpj)  # Imprime CNPJ formatado
            except ValueError as e:
                print(e)

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
        """
        Valida o CNPJ usando as regras oficiais brasileiras.

        Returns:
            bool: True se o CNPJ for válido, False caso contrário.
        """
        digits = self.raw_cnpj

        if len(set(digits)) == 1:
            return False

        # Primeiro dígito verificador
        total = sum((10 - i) * int(digits[i]) for i in range(12))
        first_check = 11 - (total % 11)
        first_check = 0 if first_check >= 10 else first_check

        # Segundo dígito verificador
        total = sum((11 - i) * int(digits[i]) for i in range(13))
        second_check = 11 - (total % 11)
        second_check = 0 if second_check >= 10 else second_check

        return (
            int(digits[12]) == first_check and
            int(digits[13]) == second_check
        )

    def __str__(self) -> str:
        """
        Retorna o CNPJ formatado.

        Returns:
            str: CNPJ formatado.
        """
        return self.formatted_cnpj

"""
"""
