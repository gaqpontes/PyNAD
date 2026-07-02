"""
Queries SQL para cálculos do dashboard PNAD.
Estas funções podem ser usadas tanto pelo Streamlit quanto por testes independentes.
"""
import sqlite3
from pathlib import Path
from typing import Optional


DB_PATH = Path("db/pnad.db")


def get_connection() -> sqlite3.Connection:
    """Retorna conexão com o banco de dados."""
    return sqlite3.connect(DB_PATH)


def query_total_registros(conn: Optional[sqlite3.Connection] = None) -> int:
    """Conta total de registros na base."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM pnad")
        return cursor.fetchone()[0]
    finally:
        if close_conn:
            conn.close()


def query_periodos_distintos(conn: Optional[sqlite3.Connection] = None) -> list[tuple[str, str]]:
    """Retorna lista de (Ano, Trimestre) distintos."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT Ano, Trimestre 
            FROM pnad 
            ORDER BY Ano, Trimestre
        """)
        return cursor.fetchall()
    finally:
        if close_conn:
            conn.close()


def query_volume_por_trimestre(conn: Optional[sqlite3.Connection] = None) -> list[dict]:
    """Retorna volume de registros e peso por trimestre."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                Ano,
                Trimestre,
                COUNT(*) as registros,
                SUM(CAST(V1028 AS REAL)) as peso
            FROM pnad
            GROUP BY Ano, Trimestre
            ORDER BY Ano, Trimestre
        """)
        return [
            {
                "Ano": row[0],
                "Trimestre": row[1],
                "periodo": f"{row[0]} T{row[1]}",
                "registros": row[2],
                "peso": row[3]
            }
            for row in cursor.fetchall()
        ]
    finally:
        if close_conn:
            conn.close()


def query_renda_media_por_trimestre(conn: Optional[sqlite3.Connection] = None) -> list[dict]:
    """Retorna renda média ponderada por trimestre."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                Ano,
                Trimestre,
                SUM(CAST(V403312 AS REAL) * CAST(V1028 AS REAL)) / SUM(CAST(V1028 AS REAL)) as renda_media
            FROM pnad
            WHERE V403312 IS NOT NULL 
              AND V1028 IS NOT NULL 
              AND CAST(V1028 AS REAL) > 0
            GROUP BY Ano, Trimestre
            ORDER BY Ano, Trimestre
        """)
        return [
            {
                "Ano": row[0],
                "Trimestre": row[1],
                "periodo": f"{row[0]} T{row[1]}",
                "renda_media": row[2]
            }
            for row in cursor.fetchall()
        ]
    finally:
        if close_conn:
            conn.close()


def query_distribuicao_sexo_media_trimestral(conn: Optional[sqlite3.Connection] = None) -> list[dict]:
    """Retorna distribuição por sexo usando média trimestral ponderada."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    
    try:
        cursor = conn.cursor()
        # Conta períodos distintos
        cursor.execute("SELECT COUNT(DISTINCT Ano || '-' || Trimestre) FROM pnad")
        num_periodos = cursor.fetchone()[0]
        
        # Calcula média trimestral por sexo
        cursor.execute("""
            SELECT 
                V2007 as sexo,
                SUM(CAST(V1028 AS REAL)) / ? as peso_medio
            FROM pnad
            WHERE V2007 IS NOT NULL
            GROUP BY V2007
            ORDER BY peso_medio DESC
        """, (num_periodos,))
        
        sexo_map = {"1": "Homens", "2": "Mulheres"}
        return [
            {
                "sexo": sexo_map.get(row[0], row[0]),
                "peso_medio": row[1]
            }
            for row in cursor.fetchall()
        ]
    finally:
        if close_conn:
            conn.close()


def query_faixa_etaria_sexo_media_trimestral(
    idade_min: int, 
    idade_max: int,
    conn: Optional[sqlite3.Connection] = None
) -> list[dict]:
    """Retorna distribuição por faixa etária e sexo usando média trimestral."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    
    try:
        cursor = conn.cursor()
        # Conta períodos distintos
        cursor.execute("SELECT COUNT(DISTINCT Ano || '-' || Trimestre) FROM pnad")
        num_periodos = cursor.fetchone()[0]
        
        # Calcula média trimestral
        cursor.execute("""
            SELECT 
                V2007 as sexo,
                SUM(CAST(V1028 AS REAL)) / ? as peso_medio
            FROM pnad
            WHERE V2007 IS NOT NULL
              AND CAST(V2009 AS INTEGER) BETWEEN ? AND ?
            GROUP BY V2007
            ORDER BY peso_medio DESC
        """, (num_periodos, idade_min, idade_max))
        
        sexo_map = {"1": "Homens", "2": "Mulheres"}
        return [
            {
                "sexo": sexo_map.get(row[0], row[0]),
                "idade_min": idade_min,
                "idade_max": idade_max,
                "peso_medio": row[1]
            }
            for row in cursor.fetchall()
        ]
    finally:
        if close_conn:
            conn.close()


def query_renda_media_geral(conn: Optional[sqlite3.Connection] = None) -> Optional[float]:
    """Retorna renda habitual média ponderada do trabalho principal."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM(CAST(V403312 AS REAL) * CAST(V1028 AS REAL)) / SUM(CAST(V1028 AS REAL))
            FROM pnad
            WHERE V403312 IS NOT NULL 
              AND V1028 IS NOT NULL 
              AND CAST(V1028 AS REAL) > 0
        """)
        result = cursor.fetchone()[0]
        return result
    finally:
        if close_conn:
            conn.close()


def query_horas_medias_gerais(conn: Optional[sqlite3.Connection] = None) -> Optional[float]:
    """Retorna horas habituais médias ponderadas no trabalho principal."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM(CAST(V4039 AS REAL) * CAST(V1028 AS REAL)) / SUM(CAST(V1028 AS REAL))
            FROM pnad
            WHERE V4039 IS NOT NULL 
              AND V1028 IS NOT NULL 
              AND CAST(V1028 AS REAL) > 0
        """)
        result = cursor.fetchone()[0]
        return result
    finally:
        if close_conn:
            conn.close()


def query_renda_por_hora_geral(conn: Optional[sqlite3.Connection] = None) -> Optional[float]:
    """Retorna renda por hora aproximada do trabalho principal."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM((CAST(V403312 AS REAL) / (CAST(V4039 AS REAL) * 4.33)) * CAST(V1028 AS REAL)) 
                   / SUM(CAST(V1028 AS REAL))
            FROM pnad
            WHERE V403312 IS NOT NULL 
              AND V4039 IS NOT NULL 
              AND CAST(V4039 AS REAL) > 0
              AND V1028 IS NOT NULL 
              AND CAST(V1028 AS REAL) > 0
        """)
        result = cursor.fetchone()[0]
        return result
    finally:
        if close_conn:
            conn.close()


def query_previdencia_percentual(conn: Optional[sqlite3.Connection] = None) -> Optional[float]:
    """Retorna percentual que contribui para previdência entre casos deriváveis."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            WITH base AS (
                SELECT
                    V1028,
                    CASE
                        WHEN V4029 = '1' OR V4028 = '1' OR V4032 = '1' THEN 'Sim'
                        WHEN V4029 = '2' OR V4028 = '2' OR V4032 = '2' THEN 'Não'
                        ELSE 'Sem informação'
                    END AS previdencia
                FROM pnad
                WHERE V1028 IS NOT NULL 
                  AND CAST(V1028 AS REAL) > 0
            )
            SELECT 
                SUM(CASE WHEN previdencia = 'Sim' THEN CAST(V1028 AS REAL) ELSE 0 END) 
                / SUM(CASE WHEN previdencia IN ('Sim', 'Não') THEN CAST(V1028 AS REAL) ELSE 0 END) * 100
            FROM base
            WHERE previdencia IN ('Sim', 'Não')
        """)
        result = cursor.fetchone()[0]
        return result
    finally:
        if close_conn:
            conn.close()


def query_com_ocupacao_percentual(conn: Optional[sqlite3.Connection] = None) -> Optional[float]:
    """Retorna percentual com posição na ocupação do trabalho principal informada."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN V4012 IS NOT NULL AND TRIM(V4012) != '' THEN CAST(V1028 AS REAL) ELSE 0 END) 
                / SUM(CAST(V1028 AS REAL)) * 100
            FROM pnad
            WHERE V1028 IS NOT NULL AND CAST(V1028 AS REAL) > 0
        """)
        result = cursor.fetchone()[0]
        return result
    finally:
        if close_conn:
            conn.close()


def query_renda_por_raça(conn: Optional[sqlite3.Connection] = None) -> list[dict]:
    """Retorna renda habitual média ponderada do trabalho principal por raça/cor."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                V2010 as raca,
                SUM(CAST(V403312 AS REAL) * CAST(V1028 AS REAL)) / SUM(CAST(V1028 AS REAL)) as renda_media
            FROM pnad
            WHERE V403312 IS NOT NULL 
              AND V1028 IS NOT NULL 
              AND CAST(V1028 AS REAL) > 0
              AND V2010 IS NOT NULL
            GROUP BY V2010
            ORDER BY renda_media DESC
        """)
        
        raca_map = {
            "1": "Branca",
            "2": "Preta",
            "3": "Amarela",
            "4": "Parda",
            "5": "Indígena",
            "9": "Ignorado"
        }
        
        return [
            {
                "raca": raca_map.get(row[0], row[0]),
                "renda_media": row[1]
            }
            for row in cursor.fetchall()
        ]
    finally:
        if close_conn:
            conn.close()


def query_renda_por_sexo(conn: Optional[sqlite3.Connection] = None) -> list[dict]:
    """Retorna renda habitual média ponderada do trabalho principal por sexo."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                V2007 as sexo,
                SUM(CAST(V403312 AS REAL) * CAST(V1028 AS REAL)) / SUM(CAST(V1028 AS REAL)) as renda_media
            FROM pnad
            WHERE V403312 IS NOT NULL 
              AND V1028 IS NOT NULL 
              AND CAST(V1028 AS REAL) > 0
              AND V2007 IS NOT NULL
            GROUP BY V2007
            ORDER BY renda_media DESC
        """)
        
        sexo_map = {"1": "Homens", "2": "Mulheres"}
        
        return [
            {
                "sexo": sexo_map.get(row[0], row[0]),
                "renda_media": row[1]
            }
            for row in cursor.fetchall()
        ]
    finally:
        if close_conn:
            conn.close()


def query_taxa_previdencia_por_ocupacao(conn: Optional[sqlite3.Connection] = None) -> list[dict]:
    """Retorna taxa de contribuição previdenciária por ocupação entre casos deriváveis."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            WITH base AS (
                SELECT
                    V4012,
                    V1028,
                    CASE
                        WHEN V4029 = '1' OR V4028 = '1' OR V4032 = '1' THEN 'Sim'
                        WHEN V4029 = '2' OR V4028 = '2' OR V4032 = '2' THEN 'Não'
                        ELSE 'Sem informação'
                    END AS previdencia
                FROM pnad
                WHERE V4012 IS NOT NULL 
                  AND TRIM(V4012) != ''
                  AND V1028 IS NOT NULL 
                  AND CAST(V1028 AS REAL) > 0
            )
            SELECT 
                V4012 as ocupacao,
                SUM(CASE WHEN previdencia = 'Sim' THEN CAST(V1028 AS REAL) ELSE 0 END) 
                / SUM(CASE WHEN previdencia IN ('Sim', 'Não') THEN CAST(V1028 AS REAL) ELSE 0 END) * 100 as taxa
            FROM base
            WHERE previdencia IN ('Sim', 'Não')
            GROUP BY V4012
            ORDER BY taxa DESC
        """)
        
        ocupacao_map = {
            "1": "Trabalhador doméstico",
            "2": "Militar das Forças Armadas, polícia militar ou corpo de bombeiros militar",
            "3": "Empregado do setor privado",
            "4": "Empregado do setor público",
            "5": "Empregador",
            "6": "Conta própria",
            "7": "Trabalhador familiar não remunerado"
        }
        
        return [
            {
                "ocupacao": ocupacao_map.get(row[0], row[0]),
                "taxa": row[1]
            }
            for row in cursor.fetchall()
        ]
    finally:
        if close_conn:
            conn.close()
