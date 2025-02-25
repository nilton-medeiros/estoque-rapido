class CPF:
    def __init__(self, cpf: str):
        """
        Inicializa o CPF com validação e formatação.

        Args:
            cpf (str): Número bruto do CPF.

        # Exemplo de uso

        if __name__ == "__main__":

            try:
                cpf = CPF("12345678909")
                print(cpf)  # Imprime CPF formatado
            except ValueError as e:
                print(e)

        """
        self.raw_cpf = ''.join(filter(str.isdigit, cpf))
        self.formatted_cpf = self._format()

        if not self.is_valid():
            raise ValueError("CPF inválido")

    def _format(self) -> str:
        """
        Formata o CPF.

        Returns:
            str: CPF formatado (XXX.XXX.XXX-ZZ).

        Raises:
            ValueError: Se o CPF não contiver 14 dígitos.
        """
        digits = self.raw_cpf

        if len(digits) != 11:
            raise ValueError("CPF deve conter 11 dígitos")

        return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"

    def is_valid(self) -> bool:
        """
        Valida o CPF usando as regras oficiais brasileiras.

        Returns:
            bool: True se o CPF for válido, False caso contrário.
        """
        digits = self.raw_cpf

        if len(set(digits)) == 1:
            return False

        # Primeiro dígito verificador
        total = sum((10 - i) * int(digits[i]) for i in range(9))
        first_check = 11 - (total % 11)
        first_check = 0 if first_check >= 10 else first_check

        # Segundo dígito verificador
        total = sum((11 - i) * int(digits[i]) for i in range(10))
        second_check = 11 - (total % 11)
        second_check = 0 if second_check >= 10 else second_check

        return (
            int(digits[9]) == first_check and
            int(digits[10]) == second_check
        )

    def __str__(self) -> str:
        """
        Retorna o CPF formatado.

        Returns:
            str: CPF formatado.
        """
        return self.formatted_cpf
