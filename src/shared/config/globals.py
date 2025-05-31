
"""
globals.py
No contexto de um servidor Python, variáveis globais são compartilhadas entre todas as requisições dentro do mesmo processo.
Se o seu código está rodando em um servidor web (como Flask ou Django), variáveis globais ficam acessíveis para todas as requisições dos usuários enquanto o servidor estiver ativo.
Isso pode ser problemático porque diferentes usuários podem acabar acessando e modificando os mesmos dados globais, levando a comportamentos inesperados.
Para evitar esse tipo de situação, o ideal é usar mecanismos como:
- Variáveis de sessão (session em Flask ou request.session em Django) para manter dados específicos por usuário.
- Banco de dados ou armazenamento externo, garantindo que cada usuário tenha seu próprio conjunto de informações.
- Contextos de thread ou objetos locais, como threading.local(), para isolar dados por requisição.
"""
ean_gtin_api = {"blocked_until": None, "blocked": False}


"""
# arquivo globals.py
user = None

# Após login
import globals
globals.user = {"uid": "123", "email": "usuario@exemplo.com"}

# Em outra página
import globals
if globals.user:
    print(f"Usuário logado: {globals.user['email']}")
"""
