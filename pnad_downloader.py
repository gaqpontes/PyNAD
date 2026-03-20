# pnad_downloader
# 1. Recebe N links de .zip da pnad contínua
# 2. Orderna os links por ano e titulo
# 3. Baixa os N links e salva na pasta .\temp
# 4. Extrai os N arquivos para a pasta .\temp
# 5. Exclui o arquivo zip e mantém o arquivo .txt

import urllib.request
import shutil
import sys
import os
from pathlib import Path

BASE_URL = 'https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Trimestral/Microdados/'

BASE_FOLDER = r'./temp';

def main():
    url_set = load_urls_manual();

    if not url_set:
        sys.exit("Erro: a lista de URLS não pode ser vazia");
    
    create_temp_folder();

    file_path_set = download_url_set(url_set);

    extract_files(file_path_set);

    delete_files(file_path_set);


def delete_files(file_path_set):
    for file_path in file_path_set:
        
        print(f'Apagando arquivo: {file_path}');
        os.remove(file_path);
    
    return;


def extract_files(file_path_set):
    for file_path in file_path_set:
        print(f'Extraindo arquivo: {file_path}');
        shutil.unpack_archive(file_path, BASE_FOLDER, 'zip');
    
    return;


def create_temp_folder():
    
    Path(BASE_FOLDER).mkdir(parents=True, exist_ok=True)


def download_url_set(url_set : set) -> set:

    file_path_set = set();
    for url in url_set:
        file_name = url.split('/')[-1];
        file_path_full = f'{BASE_FOLDER}/{file_name}';

        print(f'Baixando: {file_name}');

        with urllib.request.urlopen(url) as response, open(file_path_full, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
            out_file.close();
        
        file_path_set.add(file_path_full);
    
    return file_path_set;


def load_urls_manual() -> set:

    url_set = set();
    
    while url_pnad := input('Insira um link .zip do pnad (ou aperte enter para encerrar): \n'):
        url_validated = validate_url(url_pnad);
        if( url_validated and url_validated.startswith(BASE_URL) and url_validated.endswith('.zip') ):

            url_set.add(url_validated);
        
        else:

            print('Url inválida, tente novamente\n')

    return url_set;


def validate_url(url_pnad: str) -> str:

    return url_pnad;

main();