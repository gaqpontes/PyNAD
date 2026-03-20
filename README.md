# PNAD Contínua Downloader - Projeto Estatística 2026.2 (IFPE Campus Paulista)

Este projeto automatiza o download e a extração dos microdados da **Pesquisa Nacional por Amostra de Domicílios (PNAD) Contínua** do IBGE.

O script `pnad_downloader.py` realiza as seguintes etapas:
1. Recebe links de arquivos `.zip` do servidor FTP do IBGE.
2. Baixa os arquivos para a pasta local `./temp`.
3. Extrai o conteúdo (arquivos de dados `.txt`).
4. Remove os arquivos compactados (`.zip`) após a extração.

---

## 🛠️ Configuração Inicial

### 1. Ambiente Virtual (Recomendado)

**No Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**No Linux/macOS (Bash/Zsh):**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Dependências
Este script utiliza apenas a biblioteca padrão do Python. O arquivo `requirements.txt` está atualmente vazio, mas você pode garantir que o ambiente está atualizado com:
```bash
pip install -r requirements.txt
```

---

## 🚀 Como Rodar

Existem duas formas de executar o downloader:

### Modo 1: Manual (Interativo)
O script solicitará que você cole os links um por um.
```bash
# Windows
python .\pnad_downloader.py

# Linux/macOS
python3 pnad_downloader.py
```

### Modo 2: Usando arquivos de entrada (Batch)
Você pode usar os arquivos `inputs/input_01.txt` ou `inputs/input_12.txt` para baixar vários arquivos automaticamente.

**No Windows (PowerShell):**
```powershell
Get-Content inputs/input_12.txt | python .\pnad_downloader.py
```

**No Linux/macOS (Bash/Zsh):**
```bash
cat inputs/input_12.txt | python3 pnad_downloader.py
```

---

## 📁 Estrutura do Projeto

- `pnad_downloader.py`: Script principal em Python.
- `inputs/input_01.txt`: Exemplo de entrada com 1 link de microdados.
- `inputs/input_12.txt`: Exemplo de entrada com 12 links (ano de 2023 a 2025).
- `temp/`: Pasta onde os arquivos baixados e extraídos serão armazenados (criada automaticamente).
- `requirements.txt`: Lista de dependências do projeto.
- `.gitignore`: Configuração para ignorar arquivos temporários e ambiente virtual no Git.

---
**Nota:** Os links utilizados devem apontar para o servidor oficial do IBGE: `https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Trimestral/Microdados/`

---

## 📝 TODO / Próximos Passos (Aprendizado)

- [ ] **Converter para Argumentos de Linha de Comando:** Substituir o uso de `input()` pelo módulo `argparse` ou `sys.argv` para facilitar a automação.
- [ ] **Documentar Funções:** Adicionar *Docstrings* (comentários padronizados) em todas as funções explicando parâmetros e retornos.
- [ ] **Tratamento de Erros:** Implementar blocos `try...except` para lidar com falhas de conexão, links inválidos ou falta de espaço em disco.

---

> **Nota:** Este arquivo `README.md` foi estruturado e gerado com o auxílio de Inteligência Artificial (Gemini CLI), enquanto o código-fonte original do projeto foi desenvolvido integralmente pelo autor como parte de seus estudos.
