# Guia de Estilo do Projeto

Este documento define as convenções de nomenclatura e estilo que devem ser seguidas por todos os desenvolvedores para manter a consistência, clareza e qualidade do código-fonte.

## Tabela de Conteúdos

1. [Introdução](#introdução)
2. [Entidades (Domínio)](#entidades-domínio)
3. [Variáveis Técnicas](#variáveis-técnicas)
4. [Utilitários e Funções de Suporte](#utilitários-e-funções-de-suporte)
5. [Exemplos Práticos](#exemplos-práticos)
6. [Revisão e Atualização](#revisão-e-atualização)


## Introdução

Este guia tem o objetivo de definir padrões claros e consistentes para:

- Nomeação de entidades que refletem conceitos do domínio.
- Nomeação de variáveis que controlam a lógica técnica.
- Nomeação e organização de funções que realizam operações de suporte e utilitárias.

Manter essas convenções facilita a leitura, manutenção e colaboração no código, e promove uma comunicação eficaz entre a equipe.

## Entidades (Domínio)

**Contexto:**
As entidades representam conceitos do domínio, tais como usuários, empresas, produtos, entradas, saídas, etc.

**Convensões:**

- **Idioma:** Use **português**.
- **Formato:** Use `PascalCase` para nomear classes.
- **Singular versus Plural:** Defina as classes com nomes no singular (e as tabelas, se aplicável, podem manter o plural).

**Exemplos:**
- Classes: `Usuario`, `Empresa`, `Produto`, `Estoque`
- Tabelas (quando aplicável no banco de dados): `usuarios`, `empresas`, `produtos`

## Variáveis Técnicas

**Contexto:**
Variáveis técnicas são aquelas que não representam diretamente um conceito de domínio, mas sim elementos da lógica interna, controle de fluxo, ou manipulação de dados.

**Convensões:**

- **Idioma:** Use **inglês** para garantir concisão e clareza.
- **Formato:** Utilize `snake_case`, conforme as recomendações da PEP8.

**Exemplos:**
- `counter`
- `temp`
- `index`
- `user_data` (quando o contexto for técnico e não meramente o domínio)

## Utilitários e Funções de Suporte

**Contexto:**
Funções utilitárias geralmente executam operações genéricas (como conversões, cálculos, manipulação de respostas) e não estão diretamente ligadas ao domínio.

**Convensões:**

- **Idioma:**
  - Se a função está relacionada à entidade ou ao domínio, opte por **português** (mantendo a consistência com as entidades).
  - Se a função é genérica ou não possui significado específico no domínio, pode ser nomeada em **inglês**.

- **Formato:** Use `snake_case`.

**Exemplos:**
- Função ligada ao domínio: `handle_save_usuario`
- Função genérica: `parse_json`, `calculate_total`

## Exemplos Práticos

A seguir, alguns exemplos que demonstram a aplicação das convenções:

```python
# models.py - Entidades do Domínio (português e PascalCase)
class Usuario:
    def __init__(self, nome, email):
        self.nome = nome
        self.email = email

# controllers.py - Manipuladores ligados ao domínio
def handle_save_usuario(request):
    # Extrai dados da requisição e cria a instância de Usuario
    nome = request.get("nome")
    email = request.get("email")
    usuario = Usuario(nome, email)
    salvar_usuario_no_banco(usuario)

# utils.py - Funções de Suporte e Utilitários (inglês e snake_case)
def calculate_total(prices):
    total = sum(prices)
    return total

def parse_json(json_str):
    import json
    return json.loads(json_str)
```

## Revisão e Atualização

Este guia deve ser revisado periodicamente para garantir que continue refletindo as melhores práticas adotadas pela equipe. Sempre que houver mudanças significativas ou novas práticas a serem incorporadas, atualize este documento e comunique a todos os envolvidos.

Seguindo essas diretrizes, garantimos um código mais legível, consistente e fácil de manter. Caso surjam novas dúvidas ou sugestões para aprimorar nossa convenção de nomenclatura, sinta-se à vontade para propor melhorias!