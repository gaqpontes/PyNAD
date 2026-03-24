# PNAD Contínua Downloader - Projeto Estatística 2026.2 (IFPE Campus Paulista)

Este projeto automatiza o download, a extração e a preparação de microdados da **Pesquisa Nacional por Amostra de Domicílios (PNAD) Contínua** do IBGE para bancos de dados SQL.

O script `pnad_downloader.py` realiza as seguintes etapas:
1. Recebe links de arquivos `.zip` do servidor FTP do IBGE.
2. Baixa e extrai os microdados para a pasta local `./temp`.
3. Gera automaticamente o esquema do banco de dados (`sql/schema.sql`).
4. Converte os microdados brutos em comandos SQL de inserção em massa (`sql/values.sql`).

---

## 🛠️ Funcionalidades Implementadas

### 1. Processamento de Dados Inteligente
- **Mapeamento de Campos:** Lê arquivos de dicionário (inputs) para definir tipos e tamanhos das colunas SQL.
- **Tratamento de NULL:** Identifica campos vazios nos microdados e os converte corretamente para `NULL` no SQL.

### 2. Otimização de Performance para Grandes Volumes
- **Transações SQL:** Utiliza `BEGIN;` e `COMMIT;` para acelerar a inserção de centenas de milhares de registros.
- **Inserção em Lote (Batching):** Agrupa registros em blocos de 1000 valores por comando `INSERT`, reduzindo o overhead do banco de dados.
- **Feedback de Progresso:** Monitora e exibe o progresso do processamento em tempo real no console.

### 3. Interface de Linha de Comando (CLI)
Suporta execução modular através de flags:
- `--download-only`: Realiza apenas o download e extração dos arquivos.
- `--sql-only`: Pula o download e foca apenas na geração dos scripts SQL (útil se você já tem os arquivos no `./temp`).

---

## 🚀 Como Rodar

### Modo Completo (Padrão)
Executa todas as etapas: download, extração e geração de SQL.
```bash
python .\pnad_downloader.py
```

### Modo Especializado
```bash
# Apenas baixar e extrair
python .\pnad_downloader.py --download-only

# Apenas gerar os scripts SQL
python .\pnad_downloader.py --sql-only
```

---

## 📁 Estrutura do Projeto

- `pnad_downloader.py`: Script principal.
- `inputs/`: Contém os dicionários de dados da PNAD.
- `temp/`: Armazena arquivos `.txt` brutos (extraídos do IBGE).
- `sql/`: 
    - `schema.sql`: Estrutura da tabela `pnad`.
    - `values.sql`: Dados convertidos prontos para serem importados.

---

## 📝 TODO / Próximos Passos (Aprendizado)

- [x] **Argumentos de Linha de Comando:** Implementado via `sys.argv`.
- [ ] **Integração Direta com SQLite:** Inserir os dados diretamente em um arquivo `.db` usando a biblioteca `sqlite3` do Python, sem precisar de arquivos `.sql` intermediários.
- [ ] **Tratamento de Exceções Robusto:** Adicionar blocos `try...except` para conexões de rede instáveis.
- [ ] **Refatoração para Performance:** Otimizar loops de strings constantes para reduzir uso de CPU.

---
**Nota:** Desenvolvido como ferramenta educacional para manipulação de grandes volumes de dados estatísticos.
