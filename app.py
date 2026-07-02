from pathlib import Path
import sqlite3

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DB_PATH = Path("db/pnad.db")
PAGE_BACKGROUND = "#07131f"
CARD_BACKGROUND = "#0f1f2e"
TEXT_COLOR = "#e5f4ff"
MUTED_TEXT_COLOR = "#9fb7c9"
ACCENT_COLOR = "#38bdf8"
ACCENT_COLOR_SOFT = "#a78bfa"
ACCENT_COLOR_ALT = "#f59e0b"
GRID_COLOR = "#244154"
SEQUENTIAL_SCALE = ["#172554", "#2563eb", "#38bdf8"]
SEQUENTIAL_SCALE_ALT = ["#1e1b4b", "#7c3aed", "#f59e0b"]

SEX_MAP = {
    "1": "Homens",
    "2": "Mulheres",
}

RACE_MAP = {
    "1": "Branca",
    "2": "Preta",
    "3": "Amarela",
    "4": "Parda",
    "5": "Indígena",
    "9": "Ignorado",
}

PREVIDENCIA_MAP = {
    "1": "Sim",
    "2": "Não",
}

EDUCATION_MAP = {
    "01": "Creche",
    "02": "Pré-escola",
    "03": "Classe de alfabetização",
    "04": "Alfabetização de jovens e adultos",
    "05": "Antigo primário",
    "06": "Antigo ginásio",
    "07": "Ensino fundamental regular",
    "08": "EJA do ensino fundamental",
    "09": "Antigo científico/clássico",
    "10": "Ensino médio regular",
    "11": "EJA do ensino médio",
    "12": "Superior - graduação",
    "13": "Especialização",
    "14": "Mestrado",
    "15": "Doutorado",
}

COURSE_COMPLETION_MAP = {
    "1": "Concluiu",
    "2": "Não concluiu",
}

OCCUPATION_MAP = {
    "1": "Trabalhador doméstico",
    "2": "Militar das Forças Armadas, polícia militar ou corpo de bombeiros militar",
    "3": "Empregado do setor privado",
    "4": "Empregado do setor público",
    "5": "Empregador",
    "6": "Conta própria",
    "7": "Trabalhador familiar não remunerado",
}

GROUP_LABELS = {
    "ocupacao": "Posição na ocupação no trabalho principal",
    "escolaridade": "Grau de escolaridade",
    "raca": "Cor ou raça",
    "sexo": "Sexo",
}


def format_period(year: str, quarter: str) -> str:
    return f"{year} T{quarter}"


def parse_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def derive_previdencia_status(df: pd.DataFrame) -> pd.Series:
    status = pd.Series("Sem informação", index=df.index, dtype="object")
    sim = df["V4029"].eq("1") | df["V4028"].eq("1") | df["V4032"].eq("1")
    nao = df["V4029"].eq("2") | df["V4028"].eq("2") | df["V4032"].eq("2")
    status.loc[nao] = "Não"
    status.loc[sim] = "Sim"
    return status


def format_compact_pt(value: float | int | None) -> str:
    if pd.isna(value):
        return ""
    abs_value = abs(value)
    if abs_value >= 1_000_000:
        return f"{value / 1_000_000:.1f} milhões".replace(".", ",")
    if abs_value >= 1_000:
        return f"{value / 1_000:.1f} mil".replace(".", ",")
    return f"{value:,.0f}".replace(",", ".")


def format_currency_pt(value: float | int | None) -> str:
    if pd.isna(value):
        return ""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_decimal_pt(value: float | int | None, decimals: int = 1) -> str:
    if pd.isna(value):
        return ""
    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


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


def weighted_share_among_valid(
    df: pd.DataFrame,
    positive_mask: pd.Series,
    valid_mask: pd.Series,
    weight_col: str = "peso",
) -> float | None:
    valid = df.loc[valid_mask]
    total_weight = valid[weight_col].dropna().sum()
    if total_weight <= 0:
        return None
    return (df.loc[positive_mask & valid_mask, weight_col].dropna().sum() / total_weight) * 100


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


def selected_period_count(df: pd.DataFrame) -> int:
    if "_selected_period_count" in df.columns and not df["_selected_period_count"].dropna().empty:
        return max(int(df["_selected_period_count"].dropna().iloc[0]), 1)
    if "selected_period_count" in df.attrs:
        return max(int(df.attrs["selected_period_count"]), 1)
    periods = df[["Ano", "Trimestre"]].drop_duplicates()
    return max(len(periods), 1)


def average_quarterly_weight(df: pd.DataFrame, weight_col: str = "peso") -> float:
    return df[weight_col].sum() / selected_period_count(df)


def summarize_volume(df: pd.DataFrame, group_cols: list[str], mode: str) -> pd.DataFrame:
    grouped = df.groupby(group_cols, dropna=False, as_index=False).agg(
        registros=("id", "count"),
        peso=("peso", "sum"),
    )
    grouped["peso"] = grouped["peso"] / selected_period_count(df)
    return grouped


def apply_chart_style(fig):
    fig.update_layout(
        font=dict(color=TEXT_COLOR),
        title_font=dict(color=TEXT_COLOR, size=18),
        paper_bgcolor=CARD_BACKGROUND,
        plot_bgcolor=CARD_BACKGROUND,
        separators=",.",
        coloraxis_colorbar=dict(
            title_font=dict(color=TEXT_COLOR),
            tickfont=dict(color=TEXT_COLOR),
            tickformat=",.0f",
        ),
        legend=dict(
            bgcolor="rgba(15,31,46,0.88)",
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
        tickformat=",.0f",
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
            V3009A,
            V3014,
            V4012,
            V4028,
            V4029,
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
    df["sexo"] = df["V2007"].map(SEX_MAP).fillna("Não informado")
    df["raca"] = df["V2010"].map(RACE_MAP).fillna("Não informada")
    df["escolaridade"] = df["V3009A"].map(EDUCATION_MAP).fillna("Não informada")
    df["curso_concluido"] = df["V3014"].map(COURSE_COMPLETION_MAP).fillna("Não informado")
    df["ocupacao_codigo"] = df["V4012"].fillna("").replace("", "Sem informação")
    df["ocupacao"] = df["ocupacao_codigo"].apply(
        lambda code: "Sem informação"
        if code == "Sem informação"
        else f"{OCCUPATION_MAP.get(code, 'Código não mapeado')} ({code})"
    )
    df["previdencia"] = derive_previdencia_status(df)
    df["horas_habituais"] = parse_numeric(df["V4039"])
    df["horas_efetivas"] = parse_numeric(df["V4039C"])
    df["renda_habitual_principal"] = parse_numeric(df["V403312"])
    df["renda_efetiva_principal"] = parse_numeric(df["V403412"])
    df["renda_habitual_secundaria"] = parse_numeric(df["V405012"])
    df["renda_efetiva_secundaria"] = parse_numeric(df["V405112"])
    df["renda_por_hora"] = df["renda_habitual_principal"] / (df["horas_habituais"] * 4.33)
    df.loc[df["horas_habituais"].le(0), "renda_por_hora"] = pd.NA
    df["faixa_etaria"] = pd.cut(
        df["idade"],
        bins=[0, 17, 24, 34, 44, 59, 120],
        labels=["0-17", "18-24", "25-34", "35-44", "45-59", "60+"],
        include_lowest=True,
    ).astype(str).replace("nan", "Não informada")
    df["tem_ocupacao"] = df["ocupacao_codigo"].ne("Sem informação")
    df["tem_renda_principal"] = df["renda_habitual_principal"].notna()
    return df


def filter_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    st.sidebar.header("Filtros")

    periodos = sorted(df["periodo"].dropna().unique().tolist())
    periodos_escolhidos = st.sidebar.multiselect("Períodos", periodos, default=periodos)
    selected_period_total = max(len(periodos_escolhidos), 1)

    sexos = sorted(df["sexo"].dropna().unique().tolist())
    sexos_escolhidos = st.sidebar.multiselect("Sexo", sexos, default=sexos)

    racas = sorted(df["raca"].dropna().unique().tolist())
    racas_escolhidas = st.sidebar.multiselect("Cor ou raça", racas, default=racas)

    ocupacoes = sorted(df["ocupacao"].dropna().unique().tolist())
    ocupacoes_escolhidas = st.sidebar.multiselect(
        "Posição na ocupação no trabalho principal",
        ocupacoes,
        default=ocupacoes,
    )

    previdencias = sorted(df["previdencia"].dropna().unique().tolist())
    previdencias_escolhidas = st.sidebar.multiselect(
        "Previdência no trabalho principal",
        previdencias,
        default=previdencias,
    )

    escolaridades = ordered_options(df["escolaridade"], list(EDUCATION_MAP.values()) + ["Não informada"])
    escolaridades_escolhidas = st.sidebar.multiselect(
        "Grau de escolaridade",
        escolaridades,
        default=escolaridades,
    )

    conclusoes = sorted(df["curso_concluido"].dropna().unique().tolist())
    conclusoes_escolhidas = st.sidebar.multiselect(
        "Conclusão do curso",
        conclusoes,
        default=conclusoes,
    )

    idade_min = int(df["idade"].min(skipna=True) or 0)
    idade_max = int(df["idade"].max(skipna=True) or 100)
    idade_full_range = (idade_min, idade_max)
    faixa_idade = st.sidebar.slider(
        "Faixa etária",
        min_value=idade_min,
        max_value=idade_max,
        value=idade_full_range,
    )

    contagem_modo = st.sidebar.radio(
        "Escala das contagens",
        options=["Estimativa ponderada média trimestral", "Registros brutos"],
        index=0,
    )

    filtered = df[
        df["periodo"].isin(periodos_escolhidos)
        & df["sexo"].isin(sexos_escolhidos)
        & df["raca"].isin(racas_escolhidas)
        & df["ocupacao"].isin(ocupacoes_escolhidas)
        & df["previdencia"].isin(previdencias_escolhidas)
        & df["escolaridade"].isin(escolaridades_escolhidas)
        & df["curso_concluido"].isin(conclusoes_escolhidas)
    ].copy()

    filtered = apply_numeric_range_filter(filtered, "idade", faixa_idade, idade_full_range)

    renda_valida = df["renda_habitual_principal"].dropna()
    if not renda_valida.empty:
        renda_min = int(renda_valida.min())
        renda_max = int(renda_valida.max())
        renda_full_range = (renda_min, renda_max)
        faixa_renda = st.sidebar.slider(
            "Faixa de renda habitual do trabalho principal",
            min_value=renda_min,
            max_value=renda_max,
            value=renda_full_range,
            step=100,
            format="R$ %d",
        )
        filtered = apply_income_range_filter(filtered, faixa_renda, renda_full_range)

    filtered.attrs["selected_period_count"] = selected_period_total
    filtered["_selected_period_count"] = selected_period_total
    return filtered, contagem_modo


def value_column_name(mode: str) -> str:
    return "peso" if mode == "Estimativa ponderada média trimestral" else "registros"


def volume_axis_label(mode: str) -> str:
    return "Estimativa média trimestral" if value_column_name(mode) == "peso" else "Registros"


def volume_title_suffix(mode: str) -> str:
    return " - média trimestral" if value_column_name(mode) == "peso" else " - registros brutos"


def group_label(group_col: str) -> str:
    return GROUP_LABELS.get(group_col, group_col.replace("_", " ").title())


def ordered_options(values: pd.Series, preferred_order: list[str]) -> list[str]:
    available = set(values.dropna().unique().tolist())
    ordered = [option for option in preferred_order if option in available]
    remaining = sorted(available - set(ordered))
    return ordered + remaining


def apply_numeric_range_filter(
    df: pd.DataFrame,
    column: str,
    selected_range: tuple[int, int],
    full_range: tuple[int, int],
) -> pd.DataFrame:
    if selected_range == full_range:
        return df[df[column].isna() | df[column].between(selected_range[0], selected_range[1])]
    return df[df[column].between(selected_range[0], selected_range[1])]


def apply_income_range_filter(
    df: pd.DataFrame,
    income_range: tuple[int, int],
    full_range: tuple[int, int],
) -> pd.DataFrame:
    return apply_numeric_range_filter(df, "renda_habitual_principal", income_range, full_range)


def metric_cards(df: pd.DataFrame) -> None:
    """Exibe cards de métricas principais respeitando os filtros ativos."""
    total_registros = len(df)
    populacao_estimada = average_quarterly_weight(df)
    renda_media = weighted_mean(df, "renda_habitual_principal")
    horas_medias = weighted_mean(df, "horas_habituais")
    share_previdencia = weighted_share_among_valid(
        df,
        df["previdencia"].eq("Sim"),
        df["previdencia"].isin(["Sim", "Não"]),
    )

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Registros filtrados", f"{total_registros:,}".replace(",", "."))
    col2.metric("População média estimada", f"{populacao_estimada:,.0f}".replace(",", "."))
    col3.metric(
        "Renda habitual média do trabalho principal",
        format_currency_pt(renda_media)
        if renda_media is not None
        else "Sem dados",
    )
    col4.metric(
        "Horas habituais médias no trabalho principal",
        f"{horas_medias:.1f} h" if horas_medias is not None else "Sem dados",
    )
    col5.metric(
        "Contribui previdência no trabalho principal (informação derivável)",
        f"{share_previdencia:.1f}%" if share_previdencia is not None else "Sem dados",
    )


def build_period_volume_chart(df: pd.DataFrame, mode: str):
    """Constrói gráfico de volume por trimestre respeitando os filtros ativos."""
    grouped = df.groupby(["Ano", "Trimestre", "periodo"], as_index=False).agg(
        registros=("id", "count"),
        peso=("peso", "sum"),
    )
    grouped = grouped.sort_values(["Ano", "Trimestre"])

    y_col = value_column_name(mode)
    label = "Estimativa ponderada no trimestre" if y_col == "peso" else "Registros filtrados"

    fig = px.bar(
        grouped,
        x="periodo",
        y=y_col,
        text=grouped[y_col].apply(format_compact_pt),
        color=y_col,
        color_continuous_scale=SEQUENTIAL_SCALE,
        labels={"periodo": "Período", y_col: label},
    )
    fig.update_traces(textfont=dict(color=TEXT_COLOR))
    fig.update_layout(title="Volume por trimestre")
    return apply_chart_style(fig)


def build_income_trend_chart(df: pd.DataFrame):
    """Constrói gráfico de tendência de renda respeitando os filtros ativos."""
    income_df = summarize_weighted_mean(df, ["Ano", "Trimestre", "periodo"], "renda_habitual_principal")

    if income_df.empty:
        fig = go.Figure()
        fig.update_layout(title="Renda média do trabalho principal")
        return apply_chart_style(fig)

    income_df = income_df.rename(columns={"valor": "renda_media"}).sort_values(["Ano", "Trimestre"])
    income_df["tipo"] = "Renda habitual"

    fig = px.line(
        income_df,
        x="periodo",
        y="renda_media",
        color="tipo",
        markers=True,
        color_discrete_sequence=[ACCENT_COLOR, ACCENT_COLOR_SOFT],
        labels={"periodo": "Período", "renda_media": "Renda média do trabalho principal", "tipo": "Indicador"},
    )
    fig.update_traces(line=dict(width=3), marker=dict(size=8))
    fig.update_layout(title="Renda média do trabalho principal")
    return apply_chart_style(fig)


def build_gender_share_chart(df: pd.DataFrame, mode: str):
    """Constrói gráfico de distribuição por sexo respeitando os filtros ativos."""
    grouped = summarize_volume(df, ["sexo"], mode).sort_values(value_column_name(mode), ascending=False)
    values_col = value_column_name(mode)

    fig = px.pie(
        grouped,
        names="sexo",
        values=values_col,
        hole=0.55,
        color_discrete_sequence=[ACCENT_COLOR, ACCENT_COLOR_SOFT, ACCENT_COLOR_ALT],
    )
    fig.update_traces(textposition="inside", textinfo="percent+label", textfont=dict(color="#ffffff"))
    fig.update_layout(title=f"Distribuição por sexo{volume_title_suffix(mode)}", showlegend=False)
    return apply_chart_style(fig)


def build_sex_race_heatmap(df: pd.DataFrame, mode: str):
    grouped = summarize_volume(df, ["sexo", "raca"], mode)
    matrix = grouped.pivot(index="sexo", columns="raca", values=value_column_name(mode)).fillna(0)
    fig = px.imshow(
        matrix,
        color_continuous_scale=SEQUENTIAL_SCALE,
        labels=dict(x="Cor ou raça", y="Sexo", color=volume_axis_label(mode)),
    )
    text_matrix = matrix.apply(lambda column: column.map(format_compact_pt))
    fig.update_traces(text=text_matrix.values, texttemplate="%{text}")
    fig.update_layout(title=f"Cruzamento de sexo e cor ou raça{volume_title_suffix(mode)}")
    return apply_chart_style(fig)


def build_age_sex_chart(df: pd.DataFrame, mode: str):
    grouped = summarize_volume(df, ["faixa_etaria", "sexo"], mode)
    fig = px.bar(
        grouped,
        x="faixa_etaria",
        y=value_column_name(mode),
        color="sexo",
        barmode="group",
        color_discrete_sequence=[ACCENT_COLOR, ACCENT_COLOR_SOFT],
        labels={"faixa_etaria": "Faixa etária", value_column_name(mode): volume_axis_label(mode)},
    )
    fig.update_layout(title=f"Faixa etária por sexo{volume_title_suffix(mode)}")
    return apply_chart_style(fig)


def build_education_distribution_chart(df: pd.DataFrame, mode: str):
    grouped = summarize_volume(df, ["escolaridade"], mode).sort_values(value_column_name(mode), ascending=False)
    fig = px.bar(
        grouped,
        x="escolaridade",
        y=value_column_name(mode),
        text=grouped[value_column_name(mode)].apply(format_compact_pt),
        color=value_column_name(mode),
        color_continuous_scale=SEQUENTIAL_SCALE,
        labels={"escolaridade": "Grau de escolaridade", value_column_name(mode): volume_axis_label(mode)},
    )
    fig.update_traces(textfont=dict(color=TEXT_COLOR))
    fig.update_layout(title=f"Distribuição por grau de escolaridade{volume_title_suffix(mode)}")
    return apply_chart_style(fig)


def build_race_income_chart(df: pd.DataFrame):
    """Constrói gráfico de renda por raça respeitando os filtros ativos."""
    income = summarize_weighted_mean(df, ["raca"], "renda_habitual_principal")

    if income.empty:
        fig = go.Figure()
        fig.update_layout(title="Renda média do trabalho principal por cor ou raça")
        return apply_chart_style(fig)

    income = income.rename(columns={"valor": "renda_media"}).sort_values("renda_media", ascending=False)
    
    fig = px.bar(
        income,
        x="raca",
        y="renda_media",
        text=income["renda_media"].apply(format_currency_pt),
        color="renda_media",
        color_continuous_scale=SEQUENTIAL_SCALE_ALT,
        labels={"raca": "Cor ou raça", "renda_media": "Renda média do trabalho principal"},
    )
    fig.update_traces(textfont=dict(color=TEXT_COLOR))
    fig.update_layout(title="Renda média do trabalho principal por cor ou raça")
    return apply_chart_style(fig)


def build_occupation_distribution_chart(df: pd.DataFrame, mode: str):
    grouped = summarize_volume(df[df["tem_ocupacao"]], ["ocupacao"], mode).sort_values(value_column_name(mode), ascending=False)
    fig = px.bar(
        grouped,
        x="ocupacao",
        y=value_column_name(mode),
        text=grouped[value_column_name(mode)].apply(format_compact_pt),
        color=value_column_name(mode),
        color_continuous_scale=SEQUENTIAL_SCALE,
        labels={"ocupacao": "Posição na ocupação no trabalho principal", value_column_name(mode): volume_axis_label(mode)},
    )
    fig.update_traces(textfont=dict(color=TEXT_COLOR))
    fig.update_layout(title=f"Distribuição da posição na ocupação no trabalho principal{volume_title_suffix(mode)}")
    return apply_chart_style(fig)


def build_previdencia_occupation_chart(df: pd.DataFrame, mode: str):
    grouped = summarize_volume(
        df[(df["tem_ocupacao"]) & (df["previdencia"] != "Sem informação")],
        ["ocupacao", "previdencia"],
        mode,
    )
    fig = px.bar(
        grouped,
        x="ocupacao",
        y=value_column_name(mode),
        color="previdencia",
        barmode="stack",
        color_discrete_sequence=[ACCENT_COLOR, "#f59e0b"],
        labels={"ocupacao": "Posição na ocupação no trabalho principal", value_column_name(mode): volume_axis_label(mode)},
    )
    fig.update_layout(title=f"Previdência no trabalho principal por posição na ocupação{volume_title_suffix(mode)}")
    return apply_chart_style(fig)


def build_hours_trend_chart(df: pd.DataFrame):
    hab = summarize_weighted_mean(df, ["Ano", "Trimestre", "periodo"], "horas_habituais")
    efe = summarize_weighted_mean(df, ["Ano", "Trimestre", "periodo"], "horas_efetivas")
    if hab.empty and efe.empty:
        fig = go.Figure()
        fig.update_layout(title="Horas médias no trabalho principal")
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
        labels={"periodo": "Período", "valor": "Horas médias no trabalho principal", "tipo": "Indicador"},
    )
    fig.update_traces(line=dict(width=3), marker=dict(size=8))
    fig.update_layout(title="Horas médias no trabalho principal")
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
        text=income["valor"].apply(format_currency_pt),
        color="valor",
        color_continuous_scale=SEQUENTIAL_SCALE_ALT,
        labels={group_col: group_label(group_col), "valor": "Renda média do trabalho principal"},
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
        fig.update_layout(title="Renda média do trabalho principal por sexo ao longo do tempo")
        return apply_chart_style(fig)
    chart_df = chart_df.sort_values(["Ano", "Trimestre"])
    fig = px.line(
        chart_df,
        x="periodo",
        y="valor",
        color="sexo",
        markers=True,
        color_discrete_sequence=[ACCENT_COLOR, ACCENT_COLOR_SOFT],
        labels={"periodo": "Período", "valor": "Renda média do trabalho principal", "sexo": "Sexo"},
    )
    fig.update_layout(title="Renda média do trabalho principal por sexo ao longo do tempo")
    return apply_chart_style(fig)


def build_income_gap_table(df: pd.DataFrame) -> pd.DataFrame:
    """Constrói tabela de gap de renda por sexo respeitando os filtros ativos."""
    table = summarize_weighted_mean(df, ["sexo"], "renda_habitual_principal")

    if table.empty:
        return pd.DataFrame()

    income_col = "Renda média do trabalho principal"
    table = table.rename(columns={"valor": income_col})
    table = table.sort_values(income_col, ascending=False)
    
    if len(table) >= 2:
        maior_renda = table[income_col].max()
        table["Diferença para maior renda"] = ((maior_renda - table[income_col]) / maior_renda) * 100
    
    return table


def build_income_gap_chart(df: pd.DataFrame):
    """Constrói gráfico de gap de renda por sexo respeitando os filtros ativos."""
    table = build_income_gap_table(df)
    
    if table.empty:
        fig = go.Figure()
        fig.update_layout(title="Gap de renda média do trabalho principal por sexo")
        return apply_chart_style(fig)
    
    fig = px.bar(
        table,
        x="sexo",
        y="Renda média do trabalho principal",
        text=table["Renda média do trabalho principal"].apply(format_currency_pt),
        color="Renda média do trabalho principal",
        color_continuous_scale=SEQUENTIAL_SCALE_ALT,
        labels={"sexo": "Sexo", "Renda média do trabalho principal": "Renda média do trabalho principal"},
    )
    fig.update_traces(textfont=dict(color=TEXT_COLOR))
    fig.update_layout(title="Gap de renda média do trabalho principal por sexo")
    return apply_chart_style(fig)


def build_hourly_income_by_group_chart(df: pd.DataFrame, group_col: str, title: str):
    hourly = summarize_weighted_mean(df, [group_col], "renda_por_hora").sort_values("valor", ascending=False)
    if hourly.empty:
        fig = go.Figure()
        fig.update_layout(title=title)
        return apply_chart_style(fig)
    fig = px.bar(
        hourly,
        x=group_col,
        y="valor",
        text=hourly["valor"].apply(lambda value: f"{format_currency_pt(value)}/h"),
        color="valor",
        color_continuous_scale=SEQUENTIAL_SCALE_ALT,
        labels={group_col: group_label(group_col), "valor": "Renda por hora aproximada do trabalho principal"},
    )
    fig.update_traces(textfont=dict(color=TEXT_COLOR))
    fig.update_layout(title=title)
    return apply_chart_style(fig)


def build_previdencia_rate_by_occupation_chart(df: pd.DataFrame):
    """Constrói gráfico de taxa de previdência por ocupação respeitando os filtros ativos."""
    rows = []
    for ocupacao, group in df[df["tem_ocupacao"]].groupby("ocupacao", dropna=False):
        taxa = weighted_share_among_valid(
            group,
            group["previdencia"].eq("Sim"),
            group["previdencia"].isin(["Sim", "Não"]),
        )
        if taxa is None:
            continue
        rows.append({"ocupacao": ocupacao, "taxa": taxa})

    chart_df = pd.DataFrame(rows)

    if chart_df.empty:
        fig = go.Figure()
        fig.update_layout(title="Taxa de contribuição previdenciária no trabalho principal por ocupação")
        return apply_chart_style(fig)

    chart_df = chart_df.sort_values("taxa", ascending=False)
    
    fig = px.bar(
        chart_df,
        x="ocupacao",
        y="taxa",
        text=chart_df["taxa"].apply(lambda value: f"{format_decimal_pt(value)}%"),
        color="taxa",
        color_continuous_scale=SEQUENTIAL_SCALE,
        labels={
            "ocupacao": "Posição na ocupação no trabalho principal",
            "taxa": "Contribui previdência no trabalho principal (% com informação derivável)",
        },
    )
    fig.update_traces(textfont=dict(color=TEXT_COLOR))
    fig.update_layout(title="Taxa de contribuição previdenciária no trabalho principal por ocupação")
    return apply_chart_style(fig)


def render_microdata_table(df: pd.DataFrame) -> None:
    preview = df[
        [
            "Ano",
            "Trimestre",
            "sexo",
            "idade",
            "faixa_etaria",
            "raca",
            "escolaridade",
            "curso_concluido",
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
            "faixa_etaria": "Faixa etária",
            "raca": "Cor ou raça",
            "escolaridade": "Grau de escolaridade",
            "curso_concluido": "Conclusão do curso",
            "ocupacao": "Posição na ocupação no trabalho principal",
            "previdencia": "Previdência no trabalho principal",
            "horas_habituais": "Horas habituais no trabalho principal",
            "renda_habitual_principal": "Renda habitual do trabalho principal",
            "renda_efetiva_principal": "Renda efetiva do trabalho principal",
        }
    )
    st.dataframe(preview, use_container_width=True, hide_index=True)
    st.download_button(
        "Baixar dados filtrados em CSV",
        data=preview.to_csv(index=False).encode("utf-8"),
        file_name="pnad_filtrada.csv",
        mime="text/csv",
    )


def render_methodology(df: pd.DataFrame) -> None:
    min_year = df["Ano"].min()
    max_year = df["Ano"].max()
    total_rows = f"{len(df):,}".replace(",", ".")

    st.subheader("Metodologia e Base de Dados")
    st.markdown(
        f"""
        Este painel utiliza os microdados trimestrais da PNAD Contínua do IBGE, com recorte para o Pará (UF 15).
        A base carregada possui **{total_rows} registros** entre **{min_year} e {max_year}**, consolidados em SQLite pelo pipeline da primeira etapa do projeto.

        O fluxo de dados é: lista de links do FTP do IBGE, download dos arquivos ZIP, extração dos TXT de largura fixa,
        leitura das 77 variáveis selecionadas, filtro do estado do Pará, geração dos comandos SQL e carga final em `db/pnad.db`.
        """
    )
    st.markdown(
        "As médias de renda e horas usam variáveis do trabalho principal (`V403312` e `V4039`). "
        "As taxas de previdência combinam contribuição declarada (`V4032`), carteira assinada (`V4029`) e servidor estatutário (`V4028`). "
        "Os indicadores são calculados com o peso amostral `V1028`, quando disponível. "
        "As contagens podem ser alternadas entre registros brutos e estimativas ponderadas médias por trimestre na barra lateral."
    )


def render_insights(df: pd.DataFrame) -> None:
    renda_media = weighted_mean(df, "renda_habitual_principal")
    horas_medias = weighted_mean(df, "horas_habituais")
    renda_hora = weighted_mean(df, "renda_por_hora")
    previdencia = weighted_share_among_valid(
        df,
        df["previdencia"].eq("Sim"),
        df["previdencia"].isin(["Sim", "Não"]),
    )
    ocupados = weighted_share(df, df["tem_ocupacao"])

    st.subheader("Insights e Conclusões")
    st.markdown(
        """
        A leitura do painel deve considerar que a PNAD é uma pesquisa amostral. Por isso, os pesos amostrais são essenciais
        para transformar os registros em estimativas populacionais e para reduzir distorções na comparação entre grupos.
        """
    )

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Renda média filtrada do trabalho principal", format_currency_pt(renda_media) if renda_media is not None else "Sem dados")
    col2.metric("Horas médias no trabalho principal", f"{horas_medias:.1f} h" if horas_medias is not None else "Sem dados")
    col3.metric("Renda por hora aproximada no trabalho principal", f"{format_currency_pt(renda_hora)}/h" if renda_hora is not None else "Sem dados")
    col4.metric("Com posição ocupacional informada", f"{ocupados:.1f}%" if ocupados is not None else "Sem dados")
    col5.metric("Contribui previdência no trabalho principal (informação derivável)", f"{previdencia:.1f}%" if previdencia is not None else "Sem dados")


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
                    radial-gradient(circle at top left, rgba(56, 189, 248, 0.18), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(167, 139, 250, 0.14), transparent 28%),
                    linear-gradient(180deg, #07131f 0%, #0b1724 100%);
                color: #e5f4ff;
            }
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            h1, h2, h3, p, label, span, div {
                color: #e5f4ff;
            }
            section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, #0b1724 0%, #102235 100%);
                border-right: 1px solid rgba(56, 189, 248, 0.18);
            }
            div[data-testid="stMetric"] {
                background: rgba(15, 31, 46, 0.92);
                border: 1px solid rgba(56, 189, 248, 0.18);
                border-radius: 18px;
                padding: 0.8rem 1rem;
                box-shadow: 0 12px 34px rgba(0, 0, 0, 0.28);
            }
            div[data-testid="stMetricLabel"] p,
            div[data-testid="stMetricValue"] div {
                color: #e5f4ff;
            }
            div[data-testid="stTabs"] button {
                color: #9fb7c9;
            }
            div[data-testid="stTabs"] button[aria-selected="true"] {
                color: #38bdf8;
            }
            div[data-testid="stDataFrame"] {
                border: 1px solid rgba(56, 189, 248, 0.18);
                border-radius: 14px;
                overflow: hidden;
            }
            div[data-testid="stAlert"] {
                background: rgba(15, 31, 46, 0.92);
                border: 1px solid rgba(56, 189, 248, 0.18);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("PyNAD Dashboard")
    st.caption(
        "Painel analítico da PNAD Contínua para o Pará, com leitura do SQLite local e cruzamentos interativos."
    )

    if not DB_PATH.exists():
        st.error("Banco de dados não encontrado em db/pnad.db. Execute o pipeline antes de abrir o dashboard.")
        st.stop()

    df = load_data()
    filtered, count_mode = filter_dataframe(df)

    if filtered.empty:
        st.warning("Os filtros atuais não retornaram registros.")
        st.stop()

    metric_cards(filtered)

    st.info(
        "As contagens podem ser vistas como registros brutos ou estimativas ponderadas médias por trimestre. Médias de renda e horas usam o peso amostral V1028 quando há dados disponíveis e se referem ao trabalho principal."
    )

    tabs = st.tabs(["Visão Geral", "Demografia", "Trabalho", "Renda", "Metodologia", "Microdados"])

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
        st.plotly_chart(build_education_distribution_chart(filtered, count_mode), use_container_width=True)

    with tabs[2]:
        col1, col2 = st.columns([1.15, 1.05])
        col1.plotly_chart(build_occupation_distribution_chart(filtered, count_mode), use_container_width=True)
        col2.plotly_chart(build_previdencia_occupation_chart(filtered, count_mode), use_container_width=True)
        st.plotly_chart(build_previdencia_rate_by_occupation_chart(filtered), use_container_width=True)
        st.plotly_chart(build_hours_trend_chart(filtered), use_container_width=True)

    with tabs[3]:
        col1, col2 = st.columns([1, 1])
        col1.plotly_chart(build_income_gap_chart(filtered), use_container_width=True)
        col2.plotly_chart(build_income_by_group_chart(filtered, "ocupacao", "Renda média do trabalho principal por posição na ocupação"), use_container_width=True)
        st.plotly_chart(build_income_by_group_chart(filtered, "escolaridade", "Renda média do trabalho principal por grau de escolaridade"), use_container_width=True)
        st.plotly_chart(build_hourly_income_by_group_chart(filtered, "ocupacao", "Renda por hora aproximada do trabalho principal por posição na ocupação"), use_container_width=True)
        st.plotly_chart(build_income_by_sex_period_chart(filtered), use_container_width=True)
        st.dataframe(build_income_gap_table(filtered), use_container_width=True, hide_index=True)

    with tabs[4]:
        render_methodology(df)
        render_insights(filtered)

    with tabs[5]:
        render_microdata_table(filtered)


if __name__ == "__main__":
    main()
