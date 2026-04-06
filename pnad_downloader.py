# pnad_downloader
# 1. Recebe N links de .zip da pnad contínua
# 2. Orderna os links por ano e titulo
# 3. Baixa os N links e salva na pasta .\temp
# 4. Extrai os N arquivos para a pasta .\temp
# 5. Exclui o arquivo zip e mantém o arquivo .txt

import requests
import shutil
import sys
import os
from pathlib import Path
from functools import cmp_to_key
from variables_dict import variables_dict;
from states_dict import states_dict;
import sqlite3

STATE_POS = 6;

BASE_URL = 'https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Trimestral/Microdados/'

BASE_FOLDER = r'./temp';

BASE_INPUT_FILE = r'inputs/input_PNADC_trimestral.txt';

BASE_SCHEMA_FOLDER = './sql';

BASE_DATABASE_FOLDER = './db';

BASE_SHEMA_STRING = 'CREATE TABLE IF NOT EXISTS pnad(id INTEGER PRIMARY KEY AUTOINCREMENT {fields} );';

BASE_INSERT_STRING = 'INSERT INTO pnad ({columns})';

BASE_VALUES_STRING = 'VALUES ( {values} )'; 

BASE_VALUES_GROUPAGE = 1000;


def main():
    
    state_filter = load_state_filter();

    if len(sys.argv) == 1 or '--download-only' in sys.argv:

        url_set = load_urls_manual();

        if not url_set:
            sys.exit("Erro: a lista de URLS não pode ser vazia");

        create_temp_folder();

        file_path_set = download_url_set(url_set);

        extract_files(file_path_set);

        delete_files(file_path_set);
    
    if len(sys.argv) == 1 or '--sql-only' in sys.argv:

        input_dict = read_input(BASE_INPUT_FILE);

        create_sql_folder();

        create_sql_schema(input_dict);

        add_transaction_begin(f'{BASE_SCHEMA_FOLDER}/values.sql');
        
        create_insert_values(input_dict, f'{BASE_SCHEMA_FOLDER}/values.sql', state_filter);
        
        add_commit(f'{BASE_SCHEMA_FOLDER}/values.sql');

        create_database_folder();
        
        create_database(f'{BASE_SCHEMA_FOLDER}/schema.sql', f'{BASE_SCHEMA_FOLDER}/values.sql');

def create_database(schema_path, values_path):
    print('Inserindo valores no banco de dados.....');
    db_path = f'{BASE_DATABASE_FOLDER}/pnad.db';
    conn = sqlite3.connect(db_path);
    cursor = conn.cursor();
    
    cursor.executescript('DROP TABLE IF EXISTS pnad');

    with open(schema_path, 'r') as f:
        cursor.executescript(f.read());

    with open(values_path, 'r') as f:
        cursor.executescript(f.read());

    conn.commit();
    conn.close();

    print('Concluído!');

    return;



def create_database_folder():
    
    Path(BASE_DATABASE_FOLDER).mkdir(parents=True, exist_ok=True)


def add_transaction_begin(file_path):
    with open(file_path, "w") as f:
        f.write('BEGIN;\n');
    return;

def add_commit(file_path):
    with open(file_path, "a") as f:
        f.write('COMMIT;');
    return;


def compare_file(file1: str, file2: str) -> int:
    file1_date= file1.split('_')[1].replace('.txt', '');
    file2_date = file2.split('_')[1].replace('.txt', '');
    return int(file1_date[2:] + file1_date[0:2]) - int(file2_date[2:] + file2_date[0:2]) ; 


def create_insert_values(input_dict: dict, file_path: str, state_filter: str = ''):
    files = sorted(os.listdir(BASE_FOLDER), key=cmp_to_key(compare_file));
    with open(file_path, "a") as output_file:
        file_counter = 1;
        for file in files:
            with open(f'{BASE_FOLDER}/{file}') as f:
                line_counter = 0;
                for line in f:
                    if state_filter and not (line[ (STATE_POS -1) : (STATE_POS + 1)] == state_filter):
                        continue;

                    fields_array = [];
                    values_array = [];

                    for key in input_dict:
                        fields_array.append(input_dict[key].variable_name);
                        field_value = (line[(input_dict[key].initial_pos - 1) : ((input_dict[key].initial_pos - 1 ) +  input_dict[key].variable_size)]).strip();
                        
                        if not field_value:
                            values_array.append('NULL');
                       
                        else:                            
                            values_array.append(f'\'{field_value}\'');

                    insert_line_string = BASE_INSERT_STRING.replace('{columns}', ','.join(fields_array));
                    values_line_string = BASE_VALUES_STRING.replace('{values}', ','.join(values_array));
                    if(line_counter % (BASE_VALUES_GROUPAGE * 10) == 0):
                        
                        print(f'Linhas lidas ( {file_counter}/{len(files)} ): {line_counter}');

                    if(line_counter % BASE_VALUES_GROUPAGE  == 0):
                        
                        if line_counter:
                            output_file.write(';\n');
                        
                        output_file.write(f'{insert_line_string}\n{values_line_string}');
                    else:
                        output_file.write(f',\n({",".join(values_array)})');

                    line_counter = line_counter + 1;
            if(line_counter % BASE_VALUES_GROUPAGE):
                print(f'Linhas lidas ( {file_counter}/{len(files)} ): {line_counter}');
                output_file.write(';\n');
            
            file_counter = file_counter + 1;
                



def create_sql_schema(input_dict: dict):
    sql_fields = ''.join([f', {input_dict[key].variable_name} VARCHAR({input_dict[key].variable_size})' for key in input_dict]);
    
    with open(f"{BASE_SCHEMA_FOLDER}/schema.sql", "w") as f:
        f.write(BASE_SHEMA_STRING.replace('{fields}', sql_fields));

    return;

def read_input(intput_file_path: str) -> dict:

    input_file  = open(intput_file_path);\
    input_dict = {};
    
    for line in input_file:
        if line.startswith('@'):
            splitted_line = line.split(' ');
            initial_pos = splitted_line[0].replace('@','');
            variable_name = splitted_line[1];
            variable_size = splitted_line[4].replace('.', '').replace('$',''); 
            input_field = InputField(int(initial_pos), variable_name, int(variable_size));
            input_dict[variable_name] = input_field;
        
    return input_dict;

    
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


def create_sql_folder():
    
    Path(BASE_SCHEMA_FOLDER).mkdir(parents=True, exist_ok=True)


def download_url_set(url_set : set) -> set:

    file_path_set = set();
    for url in url_set:
        file_name = url.split('/')[-1];
        file_path_full = f'{BASE_FOLDER}/{file_name}';

        print(f'Baixando: {file_name}');

        response = requests.get(url, stream=True);
        with open(file_path_full, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file);
        
        file_path_set.add(file_path_full);
    
    return file_path_set;

def load_state_filter() -> str:
    while state_filter := input('Insira uma sigla de estado para filtrar (ou aperte enter para continuar sem filtro):\n'):
        if state_filter in states_dict:
            return states_dict[state_filter];

    return '';

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


class InputField(object):

    def __init__(self, initial_pos: int, variable_name: str, variable_size: int):
        self.initial_pos = initial_pos;
        self.variable_name = variable_name;
        self.variable_size = variable_size;


main();