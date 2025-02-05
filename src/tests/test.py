import locale
import io
import json
import sys

# Ajustar a codificação de stdout e stderr para UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

# Garantir que o locale esteja configurado corretamente
locale.setlocale(locale.LC_ALL, '')

# Função para abrir arquivos com codificação UTF-8
def open_utf8(filename, mode):
    return open(filename, mode, encoding='utf-8')

# Abrindo e lendo o arquivo manifest.json com codificação UTF-8
with open_utf8('assets/manifest.json', 'r') as file:
    data = json.load(file)

print(sys.getdefaultencoding())
print(locale.getpreferredencoding())
