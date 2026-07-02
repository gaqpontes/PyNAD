"""
Testes SQL independentes para validar cálculos do dashboard.
Executa queries diretamente no SQLite e compara com valores esperados.
"""
import sqlite3
from pathlib import Path
from typing import Optional
import sys

# Adiciona o diretório atual ao path para importar queries
sys.path.insert(0, str(Path(__file__).parent))

from queries import (
    get_connection,
    query_total_registros,
    query_periodos_distintos,
    query_volume_por_trimestre,
    query_renda_media_por_trimestre,
    query_distribuicao_sexo_media_trimestral,
    query_faixa_etaria_sexo_media_trimestral,
    query_renda_media_geral,
    query_horas_medias_gerais,
    query_renda_por_hora_geral,
    query_previdencia_percentual,
    query_com_ocupacao_percentual,
    query_renda_por_raça,
    query_renda_por_sexo,
    query_taxa_previdencia_por_ocupacao,
)


def format_currency(value: Optional[float]) -> str:
    """Formata valor como moeda brasileira."""
    if value is None:
        return "N/A"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_number(value: Optional[float]) -> str:
    """Formata número com separador de milhar."""
    if value is None:
        return "N/A"
    return f"{value:,.0f}".replace(",", ".")


def format_percent(value: Optional[float]) -> str:
    """Formata percentual."""
    if value is None:
        return "N/A"
    return f"{value:.1f}%".replace(".", ",")


def test_total_registros():
    """Testa contagem total de registros."""
    print("\n" + "="*60)
    print("TESTE: Total de Registros")
    print("="*60)
    
    total = query_total_registros()
    esperado = 209944
    
    print(f"Total de registros: {format_number(total)}")
    print(f"Esperado: {format_number(esperado)}")
    
    if total == esperado:
        print("✓ PASSOU")
        return True
    else:
        print("✗ FALHOU")
        return False


def test_periodos_distintos():
    """Testa contagem de períodos distintos."""
    print("\n" + "="*60)
    print("TESTE: Períodos Distintos")
    print("="*60)
    
    periodos = query_periodos_distintos()
    esperado = 12
    
    print(f"Períodos encontrados: {len(periodos)}")
    print(f"Esperado: {esperado}")
    
    if len(periodos) == esperado:
        print("✓ PASSOU")
        print("\nPeríodos:")
        for ano, trimestre in periodos:
            print(f"  - {ano} T{trimestre}")
        return True
    else:
        print("✗ FALHOU")
        return False


def test_volume_por_trimestre():
    """Testa volume de registros e peso por trimestre."""
    print("\n" + "="*60)
    print("TESTE: Volume por Trimestre")
    print("="*60)
    
    volumes = query_volume_por_trimestre()
    
    print(f"Trimestres encontrados: {len(volumes)}")
    print("\nVolume por trimestre:")
    
    total_registros = 0
    total_peso = 0
    
    for vol in volumes:
        print(f"  {vol['periodo']}: {format_number(vol['registros'])} registros, peso {format_number(vol['peso'])}")
        total_registros += vol['registros']
        total_peso += vol['peso']
    
    print(f"\nTotal de registros: {format_number(total_registros)}")
    print(f"Total de peso: {format_number(total_peso)}")
    
    if total_registros == 209944:
        print("✓ PASSOU")
        return True
    else:
        print("✗ FALHOU")
        return False


def test_renda_media_por_trimestre():
    """Testa renda média ponderada por trimestre."""
    print("\n" + "="*60)
    print("TESTE: Renda Média por Trimestre")
    print("="*60)
    
    rendas = query_renda_media_por_trimestre()
    
    print(f"Trimestres com dados: {len(rendas)}")
    print("\nRenda média por trimestre:")
    
    for renda in rendas:
        print(f"  {renda['periodo']}: {format_currency(renda['renda_media'])}")
    
    if len(rendas) > 0:
        print("✓ PASSOU")
        return True
    else:
        print("✗ FALHOU")
        return False


def test_distribuicao_sexo():
    """Testa distribuição por sexo com média trimestral."""
    print("\n" + "="*60)
    print("TESTE: Distribuição por Sexo (Média Trimestral)")
    print("="*60)
    
    distribuicao = query_distribuicao_sexo_media_trimestral()
    
    print("\nDistribuição por sexo (média trimestral ponderada):")
    
    for item in distribuicao:
        print(f"  {item['sexo']}: {format_number(item['peso_medio'])}")
    
    # Validação específica para homens 0-17
    print("\n" + "="*60)
    print("VALIDAÇÃO CRÍTICA: Homens 0-17")
    print("="*60)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Conta períodos
    cursor.execute("SELECT COUNT(DISTINCT Ano || '-' || Trimestre) FROM pnad")
    num_periodos = cursor.fetchone()[0]
    
    # Soma acumulada (ERRADO)
    cursor.execute("""
        SELECT SUM(CAST(V1028 AS REAL))
        FROM pnad
        WHERE V2007 = '1' AND CAST(V2009 AS INTEGER) BETWEEN 0 AND 17
    """)
    soma_acumulada = cursor.fetchone()[0]
    
    # Média trimestral (CORRETO)
    media_trimestral = soma_acumulada / num_periodos
    
    conn.close()
    
    print(f"Número de períodos: {num_periodos}")
    print(f"Soma acumulada (ERRADO): {format_number(soma_acumulada)}")
    print(f"Média trimestral (CORRETO): {format_number(media_trimestral)}")
    
    if abs(media_trimestral - 1316701) < 1000:  # Tolerância de 1000
        print("✓ PASSOU - Média trimestral está correta")
        return True
    else:
        print("✗ FALHOU - Média trimestral incorreta")
        return False


def test_faixa_etaria_sexo():
    """Testa distribuição por faixa etária e sexo."""
    print("\n" + "="*60)
    print("TESTE: Faixa Etária por Sexo (0-17 anos)")
    print("="*60)
    
    distribuicao = query_faixa_etaria_sexo_media_trimestral(0, 17)
    
    print("\nDistribuição 0-17 anos (média trimestral):")
    
    for item in distribuicao:
        print(f"  {item['sexo']}: {format_number(item['peso_medio'])}")
    
    # Validação específica
    homens = next((item for item in distribuicao if item['sexo'] == 'Homens'), None)
    mulheres = next((item for item in distribuicao if item['sexo'] == 'Mulheres'), None)
    
    if homens and mulheres:
        if abs(homens['peso_medio'] - 1316701) < 1000:
            print(f"✓ Homens 0-17: {format_number(homens['peso_medio'])} - CORRETO")
        else:
            print(f"✗ Homens 0-17: {format_number(homens['peso_medio'])} - INCORRETO")
            return False
        
        if abs(mulheres['peso_medio'] - 1230448) < 1000:
            print(f"✓ Mulheres 0-17: {format_number(mulheres['peso_medio'])} - CORRETO")
        else:
            print(f"✗ Mulheres 0-17: {format_number(mulheres['peso_medio'])} - INCORRETO")
            return False
        
        print("✓ PASSOU")
        return True
    else:
        print("✗ FALHOU - Dados incompletos")
        return False


def test_metricas_cards():
    """Testa métricas dos cards principais."""
    print("\n" + "="*60)
    print("TESTE: Métricas dos Cards")
    print("="*60)
    
    renda_media = query_renda_media_geral()
    horas_medias = query_horas_medias_gerais()
    renda_por_hora = query_renda_por_hora_geral()
    previdencia = query_previdencia_percentual()
    com_ocupacao = query_com_ocupacao_percentual()
    
    print(f"\nRenda habitual média do trabalho principal: {format_currency(renda_media)}")
    print(f"Horas habituais médias no trabalho principal: {horas_medias:.1f} h" if horas_medias else "Horas: N/A")
    print(f"Renda por hora aproximada do trabalho principal: {format_currency(renda_por_hora)}/h")
    print(f"Contribui previdência no trabalho principal (informação derivável): {format_percent(previdencia)}")
    print(f"Com posição ocupacional informada: {format_percent(com_ocupacao)}")
    
    # Validações
    validacoes = []
    
    if renda_media and abs(renda_media - 2250.16) < 10:
        print("✓ Renda média correta")
        validacoes.append(True)
    else:
        print(f"✗ Renda média incorreta: {renda_media}")
        validacoes.append(False)
    
    if horas_medias and abs(horas_medias - 37.1) < 0.5:
        print("✓ Horas médias corretas")
        validacoes.append(True)
    else:
        print(f"✗ Horas médias incorretas: {horas_medias}")
        validacoes.append(False)
    
    if renda_por_hora and abs(renda_por_hora - 14.37) < 0.5:
        print("✓ Renda por hora correta")
        validacoes.append(True)
    else:
        print(f"✗ Renda por hora incorreta: {renda_por_hora}")
        validacoes.append(False)
    
    if previdencia and abs(previdencia - 44.14) < 0.5:
        print("✓ Percentual de previdência no trabalho principal com informação derivável correto")
        validacoes.append(True)
    else:
        print(f"✗ Percentual de previdência no trabalho principal com informação derivável incorreto: {previdencia}")
        validacoes.append(False)
    
    if com_ocupacao and abs(com_ocupacao - 43.2) < 0.5:
        print("✓ Percentual com posição ocupacional informada correto")
        validacoes.append(True)
    else:
        print(f"✗ Percentual com posição ocupacional informada incorreto: {com_ocupacao}")
        validacoes.append(False)
    
    if all(validacoes):
        print("\n✓ PASSOU")
        return True
    else:
        print("\n✗ FALHOU")
        return False


def test_renda_por_raca():
    """Testa renda média do trabalho principal por raça/cor."""
    print("\n" + "="*60)
    print("TESTE: Renda Média do Trabalho Principal por Raça/Cor")
    print("="*60)
    
    rendas = query_renda_por_raça()
    
    print("\nRenda média do trabalho principal por raça/cor:")
    
    for item in rendas:
        print(f"  {item['raca']}: {format_currency(item['renda_media'])}")
    
    # Validação da ordem (deve ser decrescente)
    valores = [item['renda_media'] for item in rendas]
    if valores == sorted(valores, reverse=True):
        print("✓ PASSOU - Ordem decrescente correta")
        return True
    else:
        print("✗ FALHOU - Ordem incorreta")
        return False


def test_renda_por_sexo():
    """Testa renda média do trabalho principal por sexo."""
    print("\n" + "="*60)
    print("TESTE: Renda Média do Trabalho Principal por Sexo")
    print("="*60)
    
    rendas = query_renda_por_sexo()
    
    print("\nRenda média do trabalho principal por sexo:")
    
    for item in rendas:
        print(f"  {item['sexo']}: {format_currency(item['renda_media'])}")
    
    # Validação: homens devem ter renda maior
    homens = next((item for item in rendas if item['sexo'] == 'Homens'), None)
    mulheres = next((item for item in rendas if item['sexo'] == 'Mulheres'), None)
    
    if homens and mulheres and homens['renda_media'] > mulheres['renda_media']:
        diferenca = homens['renda_media'] - mulheres['renda_media']
        print(f"\nDiferença: {format_currency(diferenca)}")
        print("✓ PASSOU")
        return True
    else:
        print("✗ FALHOU")
        return False


def test_taxa_previdencia_por_ocupacao():
    """Testa taxa de contribuição previdenciária no trabalho principal por ocupação."""
    print("\n" + "="*60)
    print("TESTE: Taxa de Previdência no Trabalho Principal por Ocupação")
    print("="*60)
    
    taxas = query_taxa_previdencia_por_ocupacao()
    
    print("\nTaxa de contribuição previdenciária no trabalho principal por ocupação (informação derivável):")
    
    for item in taxas:
        print(f"  {item['ocupacao']}: {format_percent(item['taxa'])}")
    
    ocupacoes = {item["ocupacao"] for item in taxas}
    if (
        len(taxas) == 5
        and "Militar das Forças Armadas, polícia militar ou corpo de bombeiros militar" not in ocupacoes
        and "Trabalhador familiar não remunerado" not in ocupacoes
    ):
        print("✓ PASSOU")
        return True
    else:
        print("✗ FALHOU - Dados incompletos")
        return False


def executar_todos_testes():
    """Executa todos os testes e retorna relatório."""
    print("\n" + "="*80)
    print("VALIDAÇÃO SQL INDEPENDENTE - DASHBOARD PNAD")
    print("="*80)
    
    testes = [
        ("Total de Registros", test_total_registros),
        ("Períodos Distintos", test_periodos_distintos),
        ("Volume por Trimestre", test_volume_por_trimestre),
        ("Renda Média por Trimestre", test_renda_media_por_trimestre),
        ("Distribuição por Sexo", test_distribuicao_sexo),
        ("Faixa Etária por Sexo", test_faixa_etaria_sexo),
        ("Métricas dos Cards", test_metricas_cards),
        ("Renda do Trabalho Principal por Raça", test_renda_por_raca),
        ("Renda do Trabalho Principal por Sexo", test_renda_por_sexo),
        ("Taxa Previdência no Trabalho Principal por Ocupação", test_taxa_previdencia_por_ocupacao),
    ]
    
    resultados = []
    
    for nome, teste_func in testes:
        try:
            resultado = teste_func()
            resultados.append((nome, resultado))
        except Exception as e:
            print(f"\n✗ ERRO no teste '{nome}': {e}")
            resultados.append((nome, False))
    
    # Relatório final
    print("\n" + "="*80)
    print("RELATÓRIO FINAL")
    print("="*80)
    
    passou = sum(1 for _, r in resultados if r)
    total = len(resultados)
    
    for nome, resultado in resultados:
        status = "✓ PASSOU" if resultado else "✗ FALHOU"
        print(f"{status}: {nome}")
    
    print(f"\nTotal: {passou}/{total} testes passaram")
    
    if passou == total:
        print("\n✓✓✓ TODOS OS TESTES PASSARAM ✓✓✓")
        return True
    else:
        print(f"\n✗✗✗ {total - passou} TESTE(S) FALHARAM ✗✗✗")
        return False


if __name__ == "__main__":
    sucesso = executar_todos_testes()
    sys.exit(0 if sucesso else 1)
