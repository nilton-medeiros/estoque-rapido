import os
import subprocess

PASTA = "src"
RELATORIO = "relatorio_pylint.txt"

def listar_arquivos_py(diretorio):
    arquivos_py = []
    for raiz, _, arquivos in os.walk(diretorio):
        for nome in arquivos:
            if nome.endswith(".py"):
                caminho_completo = os.path.join(raiz, nome)
                arquivos_py.append(caminho_completo)
    return arquivos_py

def rodar_pylint_arquivo(arquivo):
    try:
        resultado = subprocess.run(
            ["pylint", arquivo],
            capture_output=True,
            text=True
        )
        return resultado.stdout
    except Exception as e:
        return f"Erro ao executar pylint em {arquivo}: {e}"

def gerar_relatorio():
    arquivos = listar_arquivos_py(PASTA)
    print(f"📁 Encontrados {len(arquivos)} arquivos .py para análise.")
    with open(RELATORIO, "w", encoding="utf-8") as relatorio:
        for arquivo in arquivos:
            relatorio.write(f"\n=== Análise: {arquivo} ===\n")
            print(f"🔎 Analisando {arquivo}...")
            saida = rodar_pylint_arquivo(arquivo)
            relatorio.write(saida + "\n")
    print(f"\n✅ Relatório salvo em: {RELATORIO}")

if __name__ == "__main__":
    gerar_relatorio()

"""
Na raiz do projeto estoquerapido/
python verificar_src.py
"""