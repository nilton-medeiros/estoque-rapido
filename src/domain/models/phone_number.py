class PhoneNumber:
    def __init__(self, number: str):
        """
        Initialize a PhoneNumber object.
        Accepts a phone number in E.164 format (e.g. +5511999999999)
        """
        # Remove todos os caracteres não numéricos
        # self.raw_number = re.sub(r'\D', '', number) # usando Regex - Requer import re
        self.raw_number = ''.join(filter(str.isdigit, number))

        if not self.raw_number:
            raise ValueError("O número de telefone não pode estar vazio")

        self.e164 = self.format_to_e164()

    def format_to_e164(self):
        """
        Formata o número para o padrão E.164.
        """
        if not self.raw_number.startswith('55'):
            return f"+55{self.raw_number}"
        elif not self.raw_number.startswith('+'):
            return f"+{self.raw_number}"
        return self.raw_number

    def get_national(self) -> str:
        """Returns number without country code in format (XX) XXXXX-XXXX"""
        # Remove country code (assuming Brazilian numbers)
        national = self.raw_number[2:]
        if len(national) == 11:  # Mobile
            return f"({national[:2]}) {national[2:7]}-{national[7:]}"
        elif len(national) == 10:  # Landline
            return f"({national[:2]}) {national[2:6]}-{national[6:]}"
        return national

    def get_digits_only(self) -> str:
        """Returns just the digits without any formatting"""
        return self.raw_number

    def get_e164(self) -> str:
        """Returns the number in E.164 format (+XXXXXXXXXXX)"""
        return self.e164

    def get_international(self) -> str:
        """Returns number in international format +XX (XX) XXXXX-XXXX"""
        if len(self.raw_number) >= 12:  # Has country code
            return f"+{self.raw_number[:2]} {self.get_national()}"
        return self.get_national()

    @staticmethod
    def is_valid_number(number: str) -> bool:
        """
        Basic validation for Brazilian phone numbers
        """
        digits = ''.join(filter(str.isdigit, number))

        # Valid lengths for Brazilian numbers with country code
        valid_lengths = [12, 13]  # 12 for landline, 13 for mobile
        if len(digits) not in valid_lengths:
            return False

        # Check if starts with Brazilian country code
        if not (digits.startswith('55') or number.startswith('+55')):
            return False

        return True


'''
# Exemplo de uso:
if __name__ == "__main__":
    # Criar a partir de diferentes formatos
    phone1 = PhoneNumber("+5511999999999")
    phone2 = PhoneNumber("5511999999999")
    phone3 = PhoneNumber("11999999999")

    # Diferentes formatos de saída
    print(phone1.get_national())        # (11) 99999-9999
    print(phone1.get_digits_only())     # 5511999999999
    print(phone1.get_e164())           # +5511999999999
    print(phone1.get_international())   # +55 (11) 99999-9999

    # Validação
    print(PhoneNumber.is_valid_number("+5511999999999"))  # True
    print(PhoneNumber.is_valid_number("+1234567890"))     # False
'''