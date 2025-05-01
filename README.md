# estoque-rapido

## Projeto de Gestão de Estoque, Vendas, Financeiro, Fluxo de Caixa e Emissão de Cupom Fiscal (NFC-e) para lojas de pequeno e médio porte.

# Tecnologias Usadas

### Backend


- <a href="https://www.python.org/"> Python</a><img align="center" alt="Python" height="20" width="30" src="https://logohistory.net/wp-content/uploads/2023/06/Python-Emblem.png">
- <a href="https://firebase.google.com/products/auth/">Google Authentication</a><img align="center" alt="Google Authentication" height="20" width="30" src="https://upload.wikimedia.org/wikipedia/commons/8/84/Google_Authenticator_%28April_2023%29.svg">


  #### Database

  - <a href="https://firebase.google.com/">Firebase Firestore</a><img align="center" alt="Firebase Firestore" height="20" width="30" src="https://www.svgrepo.com/show/353735/firebase.svg">


  #### File Storage
  - <a href="https://aws.amazon.com/pt/s3/">AWS - Amazon S3 </a><img align="center" alt="Amazon S3" height="20" width="30" src="https://www.practical-go-lessons.com/img/amazon_s3.0fd7ad6f.png">


### Frontend


- <a href="https://flet.dev/"> Python</a><img align="center" alt="Flet framework" height="20" width="30" src="https://flet.dev/img/logo.svg">
- <a href="https://flutter.dev/">Flutter</a><img align="center" alt="Flutter" height="20" width="30" src="https://www.svgrepo.com/show/353751/flutter.svg">


<br>

# Como usar

### Primeiro, nós precisamos clonar ou baixar este repositório.

```bash
git clone https://github.com/nilton-medeiros/estoque-rapido.git
```

### Após clonar o repositório, use uma conta do Firebase Firestore

### Crie o Ambiente Virtual

```bash
python -m venv .venv
```

### Ative o Ambiente Virtual

#### Linux command:

```bash
source venv/bin/activate
```

#### Windows command:

```bash
venv\Scripts\activate
```

#### Em alguns Windows: Apenas active na raiz do projeto:

```bash
activate
```

### Atualize o pip

```bash
python.exe -m pip install --upgrade pip
```

### Instale as dependências

```bash
python install -r requirements.txt
```

<br>

# Credits to

### Nilton G. Medeiros

- <a href="https://github.com/nilton-medeiros"> GitHub



## Briefing: Projeto Estoque Rápido

### Informações Gerais
- **Nome do Projeto:** Estoque Rápido
- **Nome do Sistema:** estoquerapido
- **Descrição:** Um sistema ágil e intuitivo voltado para a gestão integrada de pequenas e médias empresas, com foco em controle de estoque, gestão financeira, emissão de notas fiscais e acompanhamento de vendas. Ele visa otimizar processos empresariais, aumentar a eficiência operacional e oferecer uma visão clara do fluxo financeiro.

### Objetivos do Projeto
1. **Facilidade de uso:** Desenvolver uma interface intuitiva e funcional para usuários com diferentes níveis de conhecimento técnico.
2. **Automatização:** Reduzir tarefas manuais, como cálculos financeiros, controle de estoque e emissão de notas fiscais.
3. **Acessibilidade:** Permitir acesso em diferentes dispositivos (web, desktop ou mobile, dependendo do escopo).
4. **Confiabilidade:** Garantir a segurança dos dados financeiros e comerciais.

### Módulos e Funcionalidades
#### 1. Controle de Estoque
- Cadastro de produtos e categorias.
- Registro de entrada e saída de mercadorias.
- Controle de quantidade mínima em estoque.
- Relatórios sobre movimentação de estoque.

#### 2. Pedido de Venda
- Registro de pedidos e emissão de orçamentos.
- Controle de status do pedido (pendente, concluído, cancelado).
- Integração com estoque para baixa automática.
- Geração de notas fiscais (opcional).

#### 3. Contas a Pagar
- Cadastro de despesas fixas e variáveis.
- Gestão de vencimentos e pagamentos efetuados.
- Alertas para contas a vencer.
- Relatórios detalhados sobre gastos.

#### 4. Contas a Receber
- Controle de recebíveis, com registro de clientes e transações.
- Acompanhamento de inadimplências.
- Integração com o módulo de Pedido de Venda.
- Relatórios financeiros de recebimentos.

#### 5. Fluxo de Caixa
- Visão geral de entradas e saídas financeiras.
- Projeções de fluxo de caixa futuro.
- Gráficos de análise financeira.

#### 6. Contas Bancárias
- Cadastro de contas bancárias da empresa.
- Registro de transações bancárias.
- Conciliação bancária.
- Relatórios de saldo e movimentação por conta.

#### 7. Emissão de Nota Fiscal ao Consumidor (NFC-e)
- Integração com prefeituras para emissão de NFS-e.
- Cadastro de clientes com dados fiscais completos.
- Emissão automática de notas vinculadas aos pedidos de venda.
- Geração e envio de notas em formato eletrônico (XML e PDF).
- Histórico de notas emitidas com filtros e relatórios.

### Público-Alvo
Pequenas e médias empresas que necessitam de soluções práticas e acessíveis para gerenciar operações financeiras, comerciais e fiscais.

### Tecnologias Sugeridas
- **Frontend:** React, NextJS, Vue.js ou Flutter através do Flet para acessibilidade multiplataforma (PWA & Mobile).
- **Backend:** Python (Django/FastAPI) ou Node.js.
- **Banco de Dados:** Firestore, PostgreSQL ou MySQL.
- **Outros:**
  - Firebase Auth (autenticação e notificações).
  - Docker (para deploy).
  - APIs REST para integração futura.
  - Integração com APIs específicas para NFS-e, como NuvemFiscal, TecnoSpeed, Nota Control ou WebISS.

### Entrega e Prazos
1. **Fase de Planejamento e Design:** 1 mês.
2. **Desenvolvimento de Módulos:** 5-7 meses.
3. **Testes e Ajustes:** 1-2 meses.
4. **Lançamento Beta:** Após 9 meses.

### Diferenciais do Sistema
- Sistema modular com possibilidade de ativar/desativar funcionalidades.
- Suporte a múltiplos usuários com níveis de permissão.
- Dashboards personalizáveis para monitoramento de KPIs.
- Conformidade com requisitos fiscais, incluindo integração com NFS-e.
