from pathlib import Path
import sqlite3

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


DB_PATH = Path("db/pnad.db")
PAGE_BACKGROUND = "#f4fbfa"
CARD_BACKGROUND = "#ffffff"
TEXT_COLOR = "#12312d"
MUTED_TEXT_COLOR = "#46615d"
ACCENT_COLOR = "#0f766e"
ACCENT_COLOR_SOFT = "#14b8a6"
ACCENT_COLOR_ALT = "#0ea5a4"
GRID_COLOR = "#c9ded9"

SEX_MAP = {
    "1": "Homens",
    "2": "Mulheres",
}

RACE_MAP = {
    "1": "Branca",
    "2": "Preta",
    "3": "Amarela",
    "4": "Parda",
    "5": "Indigena",
    "9": "Ignorado",
}

PREVIDENCIA_MAP = {
    "1": "Sim",
    "2": "Nao",
}

OCCUPATION_MAP = {
    "1": "Trabalhador domestico",
    "2": "Militar das Forcas Armadas, policia militar ou corpo de bombeiros militar",
    "3": "Empregado do setor privado",
    "4": "Empregado do setor publico",
    "5": "Empregador",
    "6": "Conta propria",
    "7": "Trabalhador familiar nao remunerado",
}


def format_period(year: str, quarter: str) -> str:
    return f"{year} T{quarter}"


def parse_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def weighted_mean(df: pd.DataFrame, value_col: str, weight_col: str = "peso") -> float | None:
    valid = df[[value_col, weight_col]].dropna()
    valid = valid[valid[weight_col] > 0]
    if valid.empty:
        return None
    return (valid[value_col] * valid[weight_col]).sum() / valid[weight_col].sum()


def weighted_share(df: pd.DataFrame, mask: pd.Series, weight_col: str = "peso") -> float | None:
    total_weight = df[weight_col].dropna().sum()
    if total_weight <= 0:
        return None
    return (df.loc[mask, weight_col].dropna().sum() / total_weight) * 100


def summarize_weighted_mean(df: pd.DataFrame, group_cols: list[str], value_col: str) -> pd.DataFrame:
    rows = []
    for keys, group in df.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        value = weighted_mean(group, value_col)
        if value is None:
            continue
        row = dict(zip(group_cols, keys))
        row["valor"] = value
        rows.append(row)
    return pd.DataFrame(rows)


def summarize_weighted_sum(df: pd.DataFrame, group_cols: list[str], weight_col: str = "peso") -> pd.DataFrame:
    grouped = (
        df.groupby(group_cols, dropna=False, as_index=False)[weight_col]
        .sum()
        .rename(columns={weight_col: "valor"})
    )
    return grouped


def apply_chart_style(fig):
    fig.update_layout(
        font=dict(color=TEXT_COLOR),
        title_font=dict(color=TEXT_COLOR, size=18),
        paper_bgcolor=CARD_BACKGROUND,
        plot_bgcolor=CARD_BACKGROUND,
        coloraxis_colorbar=dict(
            title_font=dict(color=TEXT_COLOR),
            tickfont=dict(color=TEXT_COLOR),
        ),
        legend=dict(
            bgcolor="rgba(255,255,255,0.88)",
            bordercolor=GRID_COLOR,
            borderwidth=1,
            font=dict(color=TEXT_COLOR),
        ),
        margin=dict(l=10, r=10, t=60, b=10),
    )
    fig.update_xaxes(
        showgrid=False,
        linecolor=GRID_COLOR,
        tickfont=dict(color=TEXT_COLOR),
        title_font=dict(color=TEXT_COLOR),
    )
    fig.update_yaxes(
        gridcolor=GRID_COLOR,
        zerolinecolor=GRID_COLOR,
        tickfont=dict(color=TEXT_COLOR),
        title_font=dict(color=TEXT_COLOR),
    )
    return fig


@st.cache_resource
def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH.as_posix(), check_same_thread=False)


@st.cache_data
def load_data() -> pd.DataFrame:
    query = """
        SELECT
            id,
            Ano,
            Trimestre,
            UF,
            V1028,
            V2007,
            V2009,
            V2010,
            V4012,
            V4032,
            V4039,
            V4039C,
            V403312,
            V403412,
            V405012,
            V405112
        FROM pnad
    """
    df = pd.read_sql_query(query, get_connection(), dtype=str)
    df["periodo"] = df.apply(lambda row: format_period(row["Ano"], row["Trimestre"]), axis=1)
    df["idade"] = parse_numeric(df["V2009"])
    df["peso"] = parse_numeric(df["V1028"])
    df["sexo"] = df["V2007"].map(SEX_MAP).fillna("Nao informado")
    df["raca"] = df["V2010"].map(RACE_MAP).fillna("Nao informada")
    df["ocupacao_codigo"] = df["V4012"].fillna("").replace("", "Sem informacao")
    df["ocupacao"] = df["ocupacao_codigo"].apply(
        lambda code: "Sem informacao"
        if code == "Sem informacao"
        else f"{OCCUPATION_MAP.get(code, 'Codigo nao mapeado')} ({code})"
    )
    df["previdencia"] = df["V4032"].map(PREVIDENCIA_MAP).fillna("Sem informacao")
    df["horas_habituais"] = parse_numeric(df["V4039"])
    df["horas_efetivas"] = parse_numeric(df["V4039C"])
    df["renda_habitual_principal"] = parse_numeric(df["V403312"])
    df["renda_efetiva_principal"] = parse_numeric(df["V403412"])
    df["renda_habitual_secundaria"] = parse_numeric(df["V405012"])
    df["renda_efetiva_secundaria"] = parse_numeric(df["V405112"])
    df["faixa_etaria"] = pd.cut(
        df["idade"],
        bins=[0, 17, 24, 34, 44, 59, 120],
        labels=["0-17", "18-24", "25-34", "35-44", "45-59", "60+"],
        include_lowest=True,
    ).astype(str).replace("nan", "Nao informada")
    df["tem_ocupacao"] = df["ocupacao_codigo"].ne("Sem informacao")
    df["tem_renda_principal"] = df["renda_habitual_principal"].notna()
    return df


def filter_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    st.sidebar.header("Filtros")

    periodos = sorted(df["periodo"].dropna().unique().tolist())
    periodos_escolhidos = st.sidebar.multiselect("Periodos", periodos, default=periodos)

    sexos = sorted(df["sexo"].dropna().unique().tolist())
    sexos_escolhidos = st.sidebar.multiselect("Sexo", sexos, default=sexos)

    racas = sorted(df["raca"].dropna().unique().tolist())
    racas_escolhidas = st.sidebar.multiselect("Cor ou raca", racas, default=racas)

    ocupacoes = sorted(df["ocupacao"].dropna().unique().tolist())
    ocupacoes_escolhidas = st.sidebar.multiselect(
        "Posicao na ocupacao",
        ocupacoes,
        default=ocupacoes,
    )

    idade_min = int(df["idade"].min(skipna=True) or 0)
    idade_max = int(df["idade"].max(skipna=True) or 100)
    faixa_idade = st.sidebar.slider(
        "Faixa etaria",
        min_value=idade_min,
        max_value=idade_max,
        value=(idade_min, idade_max),
    )

    contagem_modo = st.sidebar.radio(
        "Escala das contagens",
        options=["Estimativa ponderada", "Registros brutos"],
        index=0,
    )

    filtered = df[
        df["periodo"].isin(periodos_escolhidos)
        & df["sexo"].isin(sexos_escolhidos)
        & df["raca"].isin(racas_escolhidas)
        & df["ocupacao"].isin(ocupacoes_escolhidas)
    ].copy()

    filtered = filtered[
        filtered["idade"].isna()
        | filtered["idade"].between(faixa_idade[0], faixa_idade[1])
    ]

    return filtered, contagem_modo


def value_column_name(mode: str) -> str:
    return "peso" if mode == "Estimativa ponderada" else "registros"


def metric_cards(df: pd.DataFrame) -> None:
    total_registros = len(df)
    populacao_estimada = df["peso"].sum()
    renda_media = weighted_mean(df, "renda_habitual_principal")
    horas_medias = weighted_mean(df, "horas_habituais")
    share_previdencia = weighted_share(df, df["previdencia"].eq("Sim"))

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Registros filtrados", f"{total_registros:,}".replace(",", "."))
    col2.metric("Peso amostral somado", f"{populacao_estimada:,.0f}".replace(",", "."))
    col3.metric(
        "Renda habitual media",
        f"R$ {renda_media:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        if renda_media is not None
        else "Sem dados",
    )
    col4.metric(
        "Horas habituais medias",
        f"{horas_medias:.1f} h" if horas_medias is not None else "Sem dados",
    )
    col5.metric(
        "Contribui previdencia",
        f"{share_previdencia:.1f}%" if share_previdencia is not None else "Sem dados",
    )


def build_period_volume_chart(df: pd.DataFrame, mode: str):
    grouped = (
        df.groupby(["Ano", "Trimestre", "periodo"], as_index=False)
        .agg(registros=("id", "count"), peso=("peso", "sum"))
        .sort_values(["Ano", "Trimestre"])
    )
    y_col = value_column_name(mode)
    label = "Estimativa ponderada" if y_col == "peso" else "Registros"

    fig = px.bar(
        grouped,
        x="periodo",
        y=y_col,
        text_auto=".2s",
        color="peso",
        color_continuous_scale=["#d8f6f1", "#6dd3c4", "#0f766e"],
        labels={"periodo": "Periodo", y_col: label, "peso": "Peso"},
    )
    fig.update_traces(textfont=dict(color=TEXT_COLOR))
    fig.update_layout(title="Volume por trimestre")
    return apply_chart_style(fig)


def build_income_trend_chart(df: pd.DataFrame):
    hab = summarize_weighted_mean(df, ["Ano", "Trimestre", "periodo"], "renda_habitual_principal")
    efet = summarize_weighted_mean(df, ["Ano", "Trimestre", "periodo"], "renda_efetiva_principal")
    if hab.empty and efet.empty:
        fig = go.Figure()
        fig.update_layout(title="Renda media do trabalho principal")
        return apply_chart_style(fig)

    hab["tipo"] = "Renda habitual"
    efet["tipo"] = "Renda efetiva"
    income_df = pd.concat([hab, efet], ignore_index=True).sort_values(["Ano", "Trimestre"])

    fig = px.line(
        income_df,
        x="periodo",
        y="valor",
        color="tipo",
        markers=True,
        color_discrete_sequence=[ACCENT_COLOR, ACCENT_COLOR_SOFT],
        labels={"periodo": "Periodo", "valor": "Valor medio", "tipo": "Indicador"},
    )
    fig.update_traces(line=dict(width=3), marker=dict(size=8))
    fig.update_layout(title="Renda media do trabalho principal")
    return apply_chart_style(fig)


def build_gender_share_chart(df: pd.DataFrame, mode: str):
    grouped = (
        df.groupby("sexo", as_index=False)
        .agg(registros=("id", "count"), peso=("peso", "sum"))
        .sort_values(value_column_name(mode), ascending=False)
    )
    fig = px.pie(
        grouped,
        names="sexo",
        values=value_column_name(mode),
        hole=0.55,
        color_discrete_sequence=["#0f766e", "#5bc9b8", "#99f6e4"],
    )
    fig.update_traces(textposition="inside", textinfo="percent+label", textfont=dict(color="#ffffff"))
    fig.update_layout(title="Distribuicao por sexo", showlegend=False)
    return apply_chart_style(fig)


def build_sex_race_heatmap(df: pd.DataFrame, mode: str):
    grouped = (
        df.groupby(["sexo", "raca"], as_index=False)
        .agg(registros=("id", "count"), peso=("peso", "sum"))
    )
    matrix = grouped.pivot(index="sexo", columns="raca", values=value_column_name(mode)).fillna(0)
    fig = px.imshow(
        matrix,
        text_auto=".2s",
        color_continuous_scale=["#ecfeff", "#67e8f9", "#0f766e"],
        labels=dict(x="Cor ou raca", y="Sexo", color="Volume"),
    )
    fig.update_layout(title="Cruzamento de sexo e cor ou raca")
    return apply_chart_style(fig)


def build_age_sex_chart(df: pd.DataFrame, mode: str):
    grouped = (
        df.groupby(["faixa_etaria", "sexo"], as_index=False)
        .agg(registros=("id", "count"), peso=("peso", "sum"))
    )
    fig = px.bar(
        grouped,
        x="faixa_etaria",
        y=value_column_name(mode),
        color="sexo",
        barmode="group",
        color_discrete_sequence=[ACCENT_COLOR, ACCENT_COLOR_SOFT],
        labels={"faixa_etaria": "Faixa etaria", value_column_name(mode): "Volume"},
    )
    fig.update_layout(title="Faixa etaria por sexo")
    return apply_chart_style(fig)


def build_race_income_chart(df: pd.DataFrame):
    income = summarize_weighted_mean(df, ["raca"], "renda_habitual_principal").sort_values("valor", ascending=False)
    if income.empty:
        fig = go.Figure()
        fig.update_layout(title="Renda media por cor ou raca")
        return apply_chart_style(fig)
    fig = px.bar(
        income,
        x="raca",
        y="valor",
        text_auto=".2f",
        color="valor",
        color_continuous_scale=["#d8f6f1", "#6dd3c4", "#0f766e"],
        labels={"raca": "Cor ou raca", "valor": "Renda media"},
    )
    fig.update_traces(textfont=dict(color=TEXT_COLOR))
    fig.update_layout(title="Renda media por cor ou raca")
    return apply_chart_style(fig)


def build_occupation_distribution_chart(df: pd.DataFrame, mode: str):
    grouped = (
        df[df["tem_ocupacao"]]
        .groupby("ocupacao", as_index=False)
        .agg(registros=("id", "count"), peso=("peso", "sum"))
        .sort_values(value_column_name(mode), ascending=False)
    )
    fig = px.bar(
        grouped,
        x="ocupacao",
        y=value_column_name(mode),
        text_auto=".2s",
        color=value_column_name(mode),
        color_continuous_scale=["#d8f6f1", "#6dd3c4", "#0f766e"],
        labels={"ocupacao": "Posicao na ocupacao", value_column_name(mode): "Volume"},
    )
    fig.update_traces(textfont=dict(color=TEXT_COLOR))
    fig.update_layout(title="Distribuicao da posicao na ocupacao")
    return apply_chart_style(fig)


def build_previdencia_occupation_chart(df: pd.DataFrame, mode: str):
    grouped = (
        df[(df["tem_ocupacao"]) & (df["previdencia"] != "Sem informacao")]
        .groupby(["ocupacao", "previdencia"], as_index=False)
        .agg(registros=("id", "count"), peso=("peso", "sum"))
    )
    fig = px.bar(
        grouped,
        x="ocupacao",
        y=value_column_name(mode),
        color="previdencia",
        barmode="stack",
        color_discrete_sequence=[ACCENT_COLOR, "#f59e0b"],
        labels={"ocupacao": "Posicao na ocupacao", value_column_name(mode): "Volume"},
    )
    fig.update_layout(title="Previdencia por posicao na ocupacao")
    return apply_chart_style(fig)


def build_hours_trend_chart(df: pd.DataFrame):
    hab = summarize_weighted_mean(df, ["Ano", "Trimestre", "periodo"], "horas_habituais")
    efe = summarize_weighted_mean(df, ["Ano", "Trimestre", "periodo"], "horas_efetivas")
    if hab.empty and efe.empty:
        fig = go.Figure()
        fig.update_layout(title="Horas medias de trabalho")
        return apply_chart_style(fig)
    hab["tipo"] = "Horas habituais"
    efe["tipo"] = "Horas efetivas"
    chart_df = pd.concat([hab, efe], ignore_index=True).sort_values(["Ano", "Trimestre"])
    fig = px.line(
        chart_df,
        x="periodo",
        y="valor",
        color="tipo",
        markers=True,
        color_discrete_sequence=[ACCENT_COLOR, ACCENT_COLOR_ALT],
        labels={"periodo": "Periodo", "valor": "Horas medias", "tipo": "Indicador"},
    )
    fig.update_traces(line=dict(width=3), marker=dict(size=8))
    fig.update_layout(title="Horas medias de trabalho")
    return apply_chart_style(fig)


def build_income_by_group_chart(df: pd.DataFrame, group_col: str, title: str):
    income = summarize_weighted_mean(df, [group_col], "renda_habitual_principal").sort_values("valor", ascending=False)
    if income.empty:
        fig = go.Figure()
        fig.update_layout(title=title)
        return apply_chart_style(fig)
    fig = px.bar(
        income,
        x=group_col,
        y="valor",
        text_auto=".2f",
        color="valor",
        color_continuous_scale=["#d8f6f1", "#6dd3c4", "#0f766e"],
        labels={group_col: group_col.replace("_", " ").title(), "valor": "Renda media"},
    )
    fig.update_traces(textfont=dict(color=TEXT_COLOR))
    fig.update_layout(title=title)
    return apply_chart_style(fig)


def build_income_by_sex_period_chart(df: pd.DataFrame):
    rows = []
    for keys, group in df.groupby(["Ano", "Trimestre", "periodo", "sexo"], dropna=False):
        value = weighted_mean(group, "renda_habitual_principal")
        if value is None:
            continue
        rows.append(
            {
                "Ano": keys[0],
                "Trimestre": keys[1],
                "periodo": keys[2],
                "sexo": keys[3],
                "valor": value,
            }
        )
    chart_df = pd.DataFrame(rows)
    if chart_df.empty:
        fig = go.Figure()
        fig.update_layout(title="Renda media por sexo ao longo do tempo")
        return apply_chart_style(fig)
    chart_df = chart_df.sort_values(["Ano", "Trimestre"])
    fig = px.line(
        chart_df,
        x="periodo",
        y="valor",
        color="sexo",
        markers=True,
        color_discrete_sequence=[ACCENT_COLOR, ACCENT_COLOR_SOFT],
        labels={"periodo": "Periodo", "valor": "Renda media", "sexo": "Sexo"},
    )
    fig.update_layout(title="Renda media por sexo ao longo do tempo")
    return apply_chart_style(fig)


def build_income_gap_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sexo, group in df.groupby("sexo", dropna=False):
        renda = weighted_mean(group, "renda_habitual_principal")
        if renda is None:
            continue
        rows.append({"Sexo": sexo, "Renda media": renda})
    table = pd.DataFrame(rows).sort_values("Renda media", ascending=False)
    return table


def render_microdata_table(df: pd.DataFrame) -> None:
    preview = df[
        [
            "Ano",
            "Trimestre",
            "sexo",
            "idade",
            "faixa_etaria",
            "raca",
            "ocupacao",
            "previdencia",
            "horas_habituais",
            "renda_habitual_principal",
            "renda_efetiva_principal",
        ]
    ].rename(
        columns={
            "sexo": "Sexo",
            "idade": "Idade",
            "faixa_etaria": "Faixa etaria",
            "raca": "Cor ou raca",
            "ocupacao": "Posicao ocupacao",
            "previdencia": "Previdencia",
            "horas_habituais": "Horas habituais",
            "renda_habitual_principal": "Renda habitual principal",
            "renda_efetiva_principal": "Renda efetiva principal",
        }
    )
    st.dataframe(preview, use_container_width=True, hide_index=True)
    st.download_button(
        "Baixar dados filtrados em CSV",
        data=preview.to_csv(index=False).encode("utf-8"),
        file_name="pnad_filtrada.csv",
        mime="text/csv",
    )


def main() -> None:
    st.set_page_config(
        page_title="PyNAD Dashboard",
        page_icon=":bar_chart:",
        layout="wide",
    )

    st.markdown(
        """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(13, 148, 136, 0.16), transparent 32%),
                    radial-gradient(circle at bottom right, rgba(8, 145, 178, 0.18), transparent 28%),
                    linear-gradient(180deg, #f4fbfa 0%, #ecf7f5 100%);
                color: #12312d;
            }
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            h1, h2, h3, p, label, span, div {
                color: #12312d;
            }
            section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, #eff9f7 0%, #e2f1ee 100%);
                border-right: 1px solid rgba(15, 118, 110, 0.12);
            }
            div[data-testid="stMetric"] {
                background: rgba(255, 255, 255, 0.94);
                border: 1px solid rgba(15, 118, 110, 0.12);
                border-radius: 18px;
                padding: 0.8rem 1rem;
                box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
            }
            div[data-testid="stMetricLabel"] p,
            div[data-testid="stMetricValue"] div {
                color: #12312d;
            }
            div[data-testid="stTabs"] button {
                color: #46615d;
            }
            div[data-testid="stTabs"] button[aria-selected="true"] {
                color: #0f766e;
            }
            div[data-testid="stDataFrame"] {
                border: 1px solid rgba(15, 118, 110, 0.10);
                border-radius: 14px;
                overflow: hidden;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("PyNAD Dashboard")
    st.caption(
        "Painel analitico da PNAD Continua para o Para, com leitura do SQLite local e cruzamentos interativos."
    )

    if not DB_PATH.exists():
        st.error("Banco de dados nao encontrado em db/pnad.db. Execute o pipeline antes de abrir o dashboard.")
        st.stop()

    df = load_data()
    filtered, count_mode = filter_dataframe(df)

    if filtered.empty:
        st.warning("Os filtros atuais nao retornaram registros.")
        st.stop()

    metric_cards(filtered)

    st.info(
        "As contagens podem ser vistas como registros brutos ou estimativas ponderadas. Medias de renda e horas usam o peso amostral V1028 quando ha dados disponiveis."
    )

    tabs = st.tabs(["Visao Geral", "Demografia", "Trabalho", "Renda", "Microdados"])

    with tabs[0]:
        col1, col2 = st.columns([1.4, 1])
        col1.plotly_chart(build_period_volume_chart(filtered, count_mode), use_container_width=True)
        col2.plotly_chart(build_gender_share_chart(filtered, count_mode), use_container_width=True)

        col3, col4 = st.columns([1.3, 1.1])
        col3.plotly_chart(build_income_trend_chart(filtered), use_container_width=True)
        col4.plotly_chart(build_race_income_chart(filtered), use_container_width=True)

    with tabs[1]:
        col1, col2 = st.columns([1.1, 1.1])
        col1.plotly_chart(build_sex_race_heatmap(filtered, count_mode), use_container_width=True)
        col2.plotly_chart(build_age_sex_chart(filtered, count_mode), use_container_width=True)

    with tabs[2]:
        col1, col2 = st.columns([1.15, 1.05])
        col1.plotly_chart(build_occupation_distribution_chart(filtered, count_mode), use_container_width=True)
        col2.plotly_chart(build_previdencia_occupation_chart(filtered, count_mode), use_container_width=True)
        st.plotly_chart(build_hours_trend_chart(filtered), use_container_width=True)

    with tabs[3]:
        col1, col2 = st.columns([1, 1])
        col1.plotly_chart(build_income_by_group_chart(filtered, "sexo", "Renda media por sexo"), use_container_width=True)
        col2.plotly_chart(build_income_by_group_chart(filtered, "ocupacao", "Renda media por posicao na ocupacao"), use_container_width=True)
        st.plotly_chart(build_income_by_sex_period_chart(filtered), use_container_width=True)
        st.dataframe(build_income_gap_table(filtered), use_container_width=True, hide_index=True)

    with tabs[4]:
        render_microdata_table(filtered)


if __name__ == "__main__":
    main()
