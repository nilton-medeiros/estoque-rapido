class CNPJ:
    def __init__(self, cnpj: str):
        """
        Initialize CNPJ with validation and formatting

        Args:
            cnpj (str): Raw CNPJ number
        """
        self.raw_cnpj = ''.join(filter(str.isdigit, cnpj))
        self.formatted_cnpj = self._format()

        if not self.is_valid():
            raise ValueError("CNPJ inválido")

    def _format(self) -> str:
        """
        Returns:
            str: Formatted CNPJ (XX.XXX.XXX/YYYY-ZZ)
        """
        digits = self.raw_cnpj

        if len(digits) != 14:
            raise ValueError("CNPJ deve conter 14 dígitos")

        return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"

    def is_valid(self) -> bool:
        """
        Validate CNPJ using official Brazilian rules

        Returns:
            bool: True if CNPJ is valid, False otherwise
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
        Return formatted CNPJ

        Returns:
            str: Formatted CNPJ
        """
        return self.formatted_cnpj

"""
# Exemplo de uso
if __name__ == "__main__":
    try:
        cnpj = CNPJ("12345678000195")
        print(cnpj)  # Imprime CNPJ formatado
    except ValueError as e:
        print(e)
"""
