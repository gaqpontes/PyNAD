# PyNAD - Dashboard PNAD Contínua

Projeto desenvolvido para a disciplina de Estatística Aplicada. O objetivo é automatizar a extração, tratamento e consolidação dos microdados da PNAD Contínua Trimestral do IBGE e disponibilizar um dashboard interativo para análise do mercado de trabalho no Pará.

## Objetivo

O dashboard permite explorar indicadores descritivos da PNAD Contínua com recorte para o estado do Pará, usando dados trimestrais de 2023 a 2025. A aplicação apresenta filtros, estatísticas, tabelas e gráficos para apoiar a análise de renda, ocupação, jornada de trabalho, sexo, raça e contribuição previdenciária.

## Pipeline de Dados

O fluxo implementado na primeira etapa do projeto está em `pnad_downloader.py`:

1. Lê a lista de arquivos da PNAD Contínua em `inputs/input_12.txt`.
2. Baixa os arquivos ZIP do FTP do IBGE.
3. Extrai os microdados em TXT de largura fixa.
4. Lê o dicionário reduzido com 77 variáveis em `inputs/input_PNADC_trimestral.txt`.
5. Filtra automaticamente os registros do Pará (`UF=15`).
6. Gera os scripts SQL em `sql/schema.sql` e `sql/values.sql`.
7. Cria o banco SQLite final em `db/pnad.db`.
8. Exporta uma cópia em CSV para `db/pnad_dados.csv`, quando o `sqlite3` estiver disponível no sistema.

## Banco de Dados

O banco principal é `db/pnad.db`, contendo a tabela `pnad`.

- Registros atuais: 209.944.
- Recorte geográfico: Pará (`UF=15`).
- Período: 1º trimestre de 2023 ao 4º trimestre de 2025.
- Variáveis: 77 campos selecionados da PNAD Contínua mais o campo `id`.
- Peso amostral usado nas estimativas: `V1028`.

## Dashboard Interativo

A interface foi construída em Streamlit com tema escuro e gráficos Plotly.

Principais recursos:

- Filtros por período, sexo, cor ou raça, idade e posição na ocupação.
- Alternância entre registros brutos e estimativas ponderadas médias por trimestre.
- Indicadores de volume, peso amostral, renda média, horas médias e previdência.
- Gráficos de evolução trimestral, demografia, renda, ocupação e jornada de trabalho.
- Aba de metodologia com explicação do pipeline e conclusões.
- Tabela de microdados filtrados com download em CSV.

## Como Rodar Localmente

Instale as dependências:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Execute o pipeline, se o banco ainda não existir:

```bash
python3 pnad_downloader.py
```

Abra o dashboard:

```bash
streamlit run app.py
```

Também é possível usar o script:

```bash
./Ver_Dash.sh
```

## Estrutura do Projeto

- `app.py`: dashboard interativo em Streamlit.
- `pnad_downloader.py`: pipeline de download, tratamento e carga dos microdados.
- `inputs/`: links dos microdados e dicionário reduzido de variáveis.
- `db/pnad.db`: banco SQLite usado pelo dashboard.
- `db/pnad_dados.csv`: exportação CSV do banco.
- `.streamlit/config.toml`: configuração visual do dashboard.
- `requirements.txt`: dependências Python.
- `executar_pnad.sh`: automação do pipeline.
- `Ver_Dash.sh`: inicialização local do dashboard.

## Entrega da Atividade

Itens exigidos no formulário da atividade:

- Nome dos integrantes do grupo.
- Link do repositório no GitHub com o código-fonte.
- Link da aplicação publicada no Streamlit Community Cloud ou plataforma equivalente.
- Vídeo pitch de até 10 minutos.

## Roteiro Sugerido Para o Vídeo

1. Apresentar o objetivo do projeto.
2. Explicar a origem dos dados da PNAD Contínua e o recorte do Pará.
3. Demonstrar o pipeline de extração, tratamento e consolidação.
4. Mostrar a estrutura do banco SQLite e as principais variáveis.
5. Navegar pelo dashboard e seus filtros.
6. Apresentar os principais gráficos e estatísticas descritivas.
7. Destacar insights sobre renda, ocupação, jornada, sexo e raça.
8. Concluir com limitações e possibilidades de evolução.

## Equipe Responsável

- Iuri José
- Ruan Calebe
- Caio Eduardo
- Robson Severiano
- Gabriel Pontes
