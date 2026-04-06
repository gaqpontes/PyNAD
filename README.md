# PNAD Contínua Downloader

Ferramenta para download, extração e importação de microdados da **Pesquisa Nacional por Amostra de Domicílios (PNAD) Contínua** do IBGE para banco de dados SQLite.

## O que faz

1. Recebe links de arquivos `.zip` do [FTP do IBGE](https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Trimestral/Microdados/)
2. Baixa e extrai os microdados para `./temp`
3. Gera o esquema SQL (`./sql/schema.sql`)
4. Converte os dados brutos em comandos SQL (`./sql/values.sql`)
5. Cria o banco SQLite (`./db/pnad.db`) e importa os dados

## Uso

```bash
python pnad_downloader.py
```

O script pergunta:
- **Sigla do estado** para filtrar (ex: `SP`, `PE`) ou Enter para todos
- **Links dos arquivos .zip** do IBGE (um por vez, Enter para finalizar)

### Modos de execução

```bash
python pnad_downloader.py              # Completo: download + SQL + banco
python pnad_downloader.py --download-only  # Apenas download e extração
python pnad_downloader.py --sql-only       # Apenas geração do SQL e banco
```

## Estrutura do projeto

```
PyNAD/
├── pnad_downloader.py    # Script principal
├── states_dict.py        # Mapeamento sigla → código IBGE
├── variables_dict.py     # Descrição das variáveis da PNAD
├── requirements.txt      # Dependências Python
├── inputs/               # Dicionários de dados da PNAD
├── temp/                 # Arquivos .txt brutos (extraídos)
├── sql/                  # Arquivos SQL gerados
│   ├── schema.sql
│   └── values.sql
└── db/                   # Banco SQLite gerado
    └── pnad.db
```

## Dependências

```bash
pip install requests
```

## Consultar os dados

O banco é gerado em `./db/pnad.db`. Use qualquer cliente SQLite:

- [DB Browser for SQLite](https://sqlitebrowser.org/) (grátis, recomendado)
- [SQLiteStudio](https://sqlitestudio.pl/) (grátis)
- [DBeaver](https://dbeaver.io/) (grátis)

## Estados disponíveis

| Sigla | Código | Estado |
|-------|--------|--------|
| RO | 11 | Rondônia |
| AC | 12 | Acre |
| AM | 13 | Amazonas |
| RR | 14 | Roraima |
| PA | 15 | Pará |
| AP | 16 | Amapá |
| TO | 17 | Tocantins |
| MA | 21 | Maranhão |
| PI | 22 | Piauí |
| CE | 23 | Ceará |
| RN | 24 | Rio Grande do Norte |
| PB | 25 | Paraíba |
| PE | 26 | Pernambuco |
| AL | 27 | Alagoas |
| SE | 28 | Sergipe |
| BA | 29 | Bahia |
| MG | 31 | Minas Gerais |
| ES | 32 | Espírito Santo |
| RJ | 33 | Rio de Janeiro |
| SP | 35 | São Paulo |
| PR | 41 | Paraná |
| SC | 42 | Santa Catarina |
| RS | 43 | Rio Grande do Sul |
| MS | 50 | Mato Grosso do Sul |
| MT | 51 | Mato Grosso |
| GO | 52 | Goiás |
| DF | 53 | Distrito Federal |

---

Projeto educacional - Manipulação de grandes volumes de dados estatísticos.
