#!/bin/bash

# Mudar para o diretório onde o script está localizado
cd "$(dirname "$0")"

# Cores para facilitar a leitura no terminal
VERDE='\033[0;32m'
AZUL='\033[0;34m'
NC='\033[0m'

echo -e "${AZUL}== Iniciando Configuração do PyNAD (macOS) ==${NC}"

# 1. Verificar se o Python 3 está instalado
if ! command -v python3 &> /dev/null; then
    echo "Erro: Python 3 não encontrado. Por favor, instale o Python ou use 'brew install python'."
    exit 1
fi

# 2. Criar ambiente venv
if [ ! -d "venv" ]; then
    echo -e "${VERDE}Criando ambiente virtual...${NC}"
    python3 -m venv venv
fi

# 3. Ativar ambiente e instalar dependências
source venv/bin/activate
echo -e "${VERDE}Instalando/Atualizando dependências (requests)...${NC}"
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# 4. Executar o script principal
echo -e "${AZUL}== Iniciando PNAD Downloader ==${NC}"
echo -e "Dica: Tenha os links do FTP do IBGE em mãos."
python3 pnad_downloader.py

# 5. Exportar banco de dados para CSV
if command -v sqlite3 &> /dev/null; then
    echo -e "${VERDE}Exportando banco de dados para CSV...${NC}"
    sqlite3 -header -csv db/pnad.db "SELECT * FROM pnad;" > db/pnad_dados.csv
    echo -e "CSV gerado com sucesso em: ${VERDE}db/pnad_dados.csv${NC}"
else
    echo "Aviso: sqlite3 não encontrado. O CSV não foi gerado automaticamente."
fi

# 6. Desativação
deactivate
echo -e "${AZUL}== Processo Finalizado ==${NC}"
