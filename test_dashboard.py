import math
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

import app


WEIGHTED_MODE = "Estimativa ponderada média trimestral"
RAW_MODE = "Registros brutos"


def filtered_copy(df: pd.DataFrame, mask: pd.Series) -> pd.DataFrame:
    filtered = df.loc[mask].copy()
    period_count = app.selected_period_count(df)
    filtered.attrs["selected_period_count"] = period_count
    filtered["_selected_period_count"] = period_count
    return filtered


def assert_close(test_case: unittest.TestCase, actual: float, expected: float, places: int = 6) -> None:
    test_case.assertTrue(
        math.isclose(actual, expected, rel_tol=10 ** -places, abs_tol=10 ** -places),
        f"{actual} != {expected}",
    )


class DashboardCalculationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = app.load_data()
        cls.period_count = app.selected_period_count(cls.df)

    def test_loaded_dataset_has_expected_dashboard_columns(self):
        expected_columns = {
            "periodo",
            "sexo",
            "raca",
            "escolaridade",
            "ocupacao",
            "previdencia",
            "peso",
            "renda_habitual_principal",
            "renda_por_hora",
        }

        self.assertEqual(len(self.df), 209944)
        self.assertEqual(self.period_count, 12)
        self.assertTrue(expected_columns.issubset(self.df.columns))

    def test_missing_categorical_values_are_explicit_filter_options(self):
        display_columns = ["sexo", "raca", "escolaridade", "curso_concluido", "ocupacao", "previdencia"]

        self.assertEqual(int(self.df[display_columns].isna().sum().sum()), 0)
        self.assertIn("Não informada", set(self.df["escolaridade"]))
        self.assertIn("Não informado", set(self.df["curso_concluido"]))
        self.assertIn("Sem informação", set(self.df["ocupacao"]))
        self.assertIn("Sem informação", set(self.df["previdencia"]))

    def test_empty_multiselect_selection_produces_empty_result(self):
        filtered = self.df[self.df["sexo"].isin([])]

        self.assertTrue(filtered.empty)

    def test_impossible_occupation_and_previdencia_combination_is_empty(self):
        filtered = self.df[
            self.df["ocupacao"].eq("Sem informação")
            & self.df["previdencia"].eq("Sim")
        ]

        self.assertTrue(filtered.empty)

    def test_selected_period_count_controls_quarterly_average_denominator(self):
        period = filtered_copy(self.df, self.df["periodo"].eq("2025 T4"))
        period.attrs["selected_period_count"] = 1
        period["_selected_period_count"] = 1

        grouped = app.summarize_volume(period, ["sexo"], WEIGHTED_MODE)

        assert_close(self, grouped["peso"].sum(), period["peso"].sum(), places=4)

    def test_weighted_mean_matches_direct_formula(self):
        women = filtered_copy(self.df, self.df["sexo"].eq("Mulheres"))
        valid = women[["renda_habitual_principal", "peso"]].dropna()
        valid = valid[valid["peso"] > 0]
        expected = (valid["renda_habitual_principal"] * valid["peso"]).sum() / valid["peso"].sum()

        assert_close(self, app.weighted_mean(women, "renda_habitual_principal"), expected)

    def test_income_range_filter_only_keeps_missing_income_on_full_range(self):
        full_range = (
            int(self.df["renda_habitual_principal"].dropna().min()),
            int(self.df["renda_habitual_principal"].dropna().max()),
        )

        full_filtered = app.apply_income_range_filter(self.df, full_range, full_range)
        narrow_filtered = app.apply_income_range_filter(self.df, (290206, 300000), full_range)

        self.assertEqual(len(full_filtered), len(self.df))
        self.assertEqual(len(narrow_filtered), 1)
        self.assertEqual(narrow_filtered["renda_habitual_principal"].iloc[0], 300000)
        self.assertFalse(narrow_filtered["renda_habitual_principal"].isna().any())

    def test_numeric_range_filter_only_keeps_missing_values_on_full_range(self):
        sample = pd.DataFrame({"idade": [None, 10, 30, 80]})

        full_filtered = app.apply_numeric_range_filter(sample, "idade", (0, 100), (0, 100))
        narrow_filtered = app.apply_numeric_range_filter(sample, "idade", (18, 60), (0, 100))

        self.assertEqual(len(full_filtered), 4)
        self.assertEqual(narrow_filtered["idade"].tolist(), [30])

    def test_metric_cards_use_filtered_values(self):
        men = filtered_copy(self.df, self.df["sexo"].eq("Homens"))
        columns = [MagicMock() for _ in range(5)]

        with patch.object(app.st, "columns", return_value=columns):
            app.metric_cards(men)

        columns[0].metric.assert_called_once_with("Registros filtrados", "103.550")
        columns[1].metric.assert_called_once_with("População média estimada", "4.290.950")

        renda_label, renda_value = columns[2].metric.call_args.args
        horas_label, horas_value = columns[3].metric.call_args.args
        previdencia_label, previdencia_value = columns[4].metric.call_args.args

        self.assertEqual(renda_label, "Renda habitual média do trabalho principal")
        self.assertEqual(horas_label, "Horas habituais médias no trabalho principal")
        self.assertEqual(previdencia_label, "Contribui previdência no trabalho principal (informação derivável)")
        self.assertRegex(renda_value, r"^R\$ \d")
        self.assertTrue(horas_value.endswith(" h"))
        self.assertTrue(previdencia_value.endswith("%"))

    def test_period_volume_chart_uses_filtered_raw_records_and_label(self):
        men = filtered_copy(self.df, self.df["sexo"].eq("Homens"))
        fig = app.build_period_volume_chart(men, RAW_MODE)

        total_bars = sum(float(value) for trace in fig.data for value in trace.y)

        self.assertEqual(total_bars, len(men))
        self.assertEqual(fig.layout.yaxis.title.text, "Registros filtrados")
        self.assertEqual(fig.layout.xaxis.title.text, "Período")

    def test_period_volume_chart_uses_filtered_weighted_sum_and_label(self):
        women = filtered_copy(self.df, self.df["sexo"].eq("Mulheres"))
        fig = app.build_period_volume_chart(women, WEIGHTED_MODE)

        total_bars = sum(float(value) for trace in fig.data for value in trace.y)

        assert_close(self, total_bars, women["peso"].sum(), places=4)
        self.assertEqual(fig.layout.yaxis.title.text, "Estimativa ponderada no trimestre")

    def test_gender_share_chart_uses_filtered_values(self):
        men = filtered_copy(self.df, self.df["sexo"].eq("Homens"))
        fig = app.build_gender_share_chart(men, WEIGHTED_MODE)

        labels = list(fig.data[0].labels)
        values = list(fig.data[0].values)

        self.assertEqual(labels, ["Homens"])
        assert_close(self, float(sum(values)), app.average_quarterly_weight(men), places=4)
        self.assertIn("média trimestral", fig.layout.title.text)

    def test_income_gap_table_uses_filtered_sex_data(self):
        men = filtered_copy(self.df, self.df["sexo"].eq("Homens"))
        table = app.build_income_gap_table(men)

        self.assertEqual(table["sexo"].tolist(), ["Homens"])
        self.assertEqual(len(table), 1)
        self.assertNotIn("Mulheres", table["sexo"].tolist())
        self.assertNotIn("Diferença para maior renda", table.columns)

    def test_income_gap_table_matches_manual_grouped_values(self):
        table = app.build_income_gap_table(self.df).set_index("sexo")
        income_col = "Renda média do trabalho principal"

        for sexo, group in self.df.groupby("sexo"):
            expected = app.weighted_mean(group, "renda_habitual_principal")
            assert_close(self, table.loc[sexo, income_col], expected)

        self.assertEqual(table["Diferença para maior renda"].min(), 0)
        self.assertGreater(table["Diferença para maior renda"].max(), 0)

    def test_race_income_chart_respects_race_filter_and_axis_labels(self):
        branca = filtered_copy(self.df, self.df["raca"].eq("Branca"))
        fig = app.build_race_income_chart(branca)

        labels = list(fig.data[0].x)

        self.assertEqual(labels, ["Branca"])
        self.assertEqual(fig.layout.xaxis.title.text, "Cor ou raça")
        self.assertEqual(fig.layout.yaxis.title.text, "Renda média do trabalho principal")

    def test_previdencia_rate_by_occupation_uses_filtered_occupation(self):
        ocupacao = "Empregado do setor público (4)"
        subset = filtered_copy(self.df, self.df["ocupacao"].eq(ocupacao))
        expected = app.weighted_share_among_valid(
            subset,
            subset["previdencia"].eq("Sim"),
            subset["previdencia"].isin(["Sim", "Não"]),
        )

        fig = app.build_previdencia_rate_by_occupation_chart(subset)

        self.assertEqual(list(fig.data[0].x), [ocupacao])
        assert_close(self, float(fig.data[0].y[0]), expected)
        self.assertEqual(
            fig.layout.yaxis.title.text,
            "Contribui previdência no trabalho principal (% com informação derivável)",
        )

    def test_previdencia_rate_omits_occupations_without_valid_answers(self):
        fig = app.build_previdencia_rate_by_occupation_chart(self.df)
        occupations = set(fig.data[0].x)

        self.assertNotIn("Militar das Forças Armadas, polícia militar ou corpo de bombeiros militar (2)", occupations)
        self.assertNotIn("Trabalhador familiar não remunerado (7)", occupations)

    def test_grouped_income_charts_use_portuguese_axis_labels(self):
        fig = app.build_income_by_group_chart(
            self.df,
            "ocupacao",
            "Renda média do trabalho principal por posição na ocupação",
        )

        self.assertEqual(fig.layout.xaxis.title.text, "Posição na ocupação no trabalho principal")
        self.assertEqual(fig.layout.yaxis.title.text, "Renda média do trabalho principal")


if __name__ == "__main__":
    unittest.main()
