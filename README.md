# PyNAD - Automação de Microdados PNAD Contínua

Este projeto automatiza o download, processamento e importação dos microdados da **PNAD Contínua Trimestral** (IBGE) para um banco de dados SQLite local.

## Como Executar

Para facilitar a avaliação, o projeto foi configurado para ser executado de forma totalmente automatizada. **Basta dar dois cliques no arquivo abaixo na pasta raiz:**

1.  **Arquivo:** `executar_pnad.sh`
2.  **O que ele faz:** 
    - Cria o ambiente virtual (`venv`) automaticamente.
    - Instala as dependências necessárias (`requests`).
    - Inicia o script principal de download e modelagem.

---
> **Nota:** Se o seu sistema abrir o arquivo como texto em vez de executar, você pode rodá-lo pelo terminal dentro da pasta do projeto:
> ```bash
> chmod +x executar_pnad.sh  # Garante permissão de execução
> ./executar_pnad.sh         # Executa o script
> ```
---

## Modelagem de Dados

Conforme solicitado pelo professor, o banco de dados é gerado utilizando **apenas as 77 variáveis obrigatórias** (Ano, Trimestre, UF, Capital, RM_RIDE, V1008, V1014, V4012, etc.).

O dicionário de dados fatiado está localizado em: `inputs/input_PNADC_trimestral.txt`.

## Fluxo de Funcionamento

1.  **Processamento:**
    - Download e extração automática para `./temp`.
    - Geração do esquema SQL (`./sql/schema.sql`) baseado no dicionário de variáveis.
    - Conversão dos arquivos de largura fixa para comandos SQL (`./sql/values.sql`).
2.  **Banco de Dados:** Criação do banco SQLite em `./db/pnad.db`.

## Estrutura do Projeto

- `pnad_downloader.py`: Motor principal de processamento.
- `executar_pnad.sh`: Script de automação "One-Click" (macOS/Linux).
- `inputs/`: Contém a definição das variáveis solicitadas.
- `db/`: Onde o banco de dados final (`pnad.db`) será criado.
- `sql/`: Scripts SQL gerados durante a execução.

## Consultando os Resultados

Após a execução, o arquivo `db/pnad.db` pode ser aberto em qualquer ferramenta de banco de dados, como **DB Browser for SQLite** ou **DBeaver**.

## Equipe Responsável

- **Iuri José**
- **Ruan Calebe**
- **Caio Eduardo**
- **Robson Severiano**
- **Gabriel Pontes**

---
**Projeto desenvolvido para manipulação de grandes volumes de dados estatísticos.**
