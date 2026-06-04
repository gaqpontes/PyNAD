#!/bin/bash

cd "$(dirname "$0")" || exit 1

URL="http://localhost:8501"

if [ -d "venv" ]; then
    # Usa o ambiente virtual do projeto quando ele existir.
    source venv/bin/activate
fi

if ! command -v streamlit >/dev/null 2>&1; then
    echo "Erro: streamlit nao encontrado. Instale as dependencias com 'pip install -r requirements.txt'."
    exit 1
fi

echo "Iniciando dashboard em ${URL}..."

(
    sleep 3
    if command -v open >/dev/null 2>&1; then
        open "${URL}"
    elif command -v xdg-open >/dev/null 2>&1; then
        xdg-open "${URL}"
    fi
) &

streamlit run app.py
