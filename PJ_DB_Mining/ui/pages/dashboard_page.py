from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from database.connection import DatabaseManager
from database.queries import QueryLibrary
from ui.widgets.chart_widget import ChartWidget
from ui.widgets.data_table import DataTable
from ui.widgets.kpi_card import KpiCard


class InsightMiniCard(QFrame):
    def __init__(self, title: str):
        super().__init__()
        self.setObjectName("miniInsightCard")

        self.title_label = QLabel(title)
        self.title_label.setObjectName("miniInsightTitle")

        self.value_label = QLabel("--")
        self.value_label.setObjectName("miniInsightValue")
        self.value_label.setWordWrap(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(6)
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        self.setLayout(layout)

    def set_value(self, text: str):
        self.value_label.setText(text)


class DashboardPage(QWidget):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db

        self.kpi_toneladas = KpiCard("Toneladas totales procesadas", "#22c55e")
        self.kpi_costo = KpiCard("Costo total estimado", "#f59e0b")
        self.kpi_consumo = KpiCard("Consumo energético total", "#3b82f6")
        self.kpi_alertas = KpiCard("Alertas detectadas", "#ef4444")

        self.chart_toneladas = ChartWidget(
            "Toneladas por etapa",
            "Comparación del volumen total por etapa minera."
        )
        self.chart_costos = ChartWidget(
            "Top procesos por costo promedio",
            "Procesos con mayor impacto económico."
        )

        self.resumen_panel = DataTable("Resumen por etapa")
        self.alertas_panel = DataTable("Alertas de calidad de datos")

        self.insight_stage = InsightMiniCard("Etapa dominante")
        self.insight_cost = InsightMiniCard("Proceso más costoso")
        self.insight_alerts = InsightMiniCard("Situación de calidad")

        header = QVBoxLayout()
        title = QLabel("Dashboard Ejecutivo")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "Vista consolidada para monitorear producción, costos, consumo y calidad de los procesos mineros."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        header.addWidget(title)
        header.addWidget(subtitle)

        cards_layout = QGridLayout()
        cards_layout.setHorizontalSpacing(14)
        cards_layout.setVerticalSpacing(14)
        cards_layout.addWidget(self.kpi_toneladas, 0, 0)
        cards_layout.addWidget(self.kpi_costo, 0, 1)
        cards_layout.addWidget(self.kpi_consumo, 0, 2)
        cards_layout.addWidget(self.kpi_alertas, 0, 3)

        left_column = QVBoxLayout()
        left_column.setSpacing(14)
        left_column.addWidget(self.chart_toneladas, 3)
        left_column.addWidget(self.resumen_panel, 2)

        right_insights = QVBoxLayout()
        right_insights.setSpacing(10)
        right_insights.addWidget(self.insight_stage)
        right_insights.addWidget(self.insight_cost)
        right_insights.addWidget(self.insight_alerts)

        right_column = QVBoxLayout()
        right_column.setSpacing(14)
        right_column.addLayout(right_insights)
        right_column.addWidget(self.chart_costos, 3)
        right_column.addWidget(self.alertas_panel, 2)

        body_layout = QHBoxLayout()
        body_layout.setSpacing(14)
        body_layout.addLayout(left_column, 7)
        body_layout.addLayout(right_column, 5)

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(14)
        layout.addLayout(header)
        layout.addLayout(cards_layout)
        layout.addLayout(body_layout)
        self.setLayout(layout)

    def refresh(self):
        total_ton = self.db.query_df(QueryLibrary.KPI_TOTAL_TONELADAS)
        total_cost = self.db.query_df(QueryLibrary.KPI_COSTO_TOTAL)
        total_cons = self.db.query_df(QueryLibrary.KPI_CONSUMO_TOTAL)
        toneladas = self.db.query_df(QueryLibrary.QUERY_TONELADAS_POR_ETAPA)
        alertas = self.db.query_df(QueryLibrary.QUERY_ALERTAS)
        costos = self.db.query_df(QueryLibrary.QUERY_COSTO_PROMEDIO_PROCESO)

        total_alertas = len(alertas.index)

        self.kpi_toneladas.set_value(str(total_ton.iloc[0, 0]))
        self.kpi_costo.set_value(f"USD {total_cost.iloc[0, 0]}")
        self.kpi_consumo.set_value(str(total_cons.iloc[0, 0]))
        self.kpi_alertas.set_value(str(total_alertas))

        self.resumen_panel.load_dataframe(toneladas)
        self.alertas_panel.load_dataframe(alertas)

        if not toneladas.empty:
            self.chart_toneladas.plot_bar(
                toneladas["etapa"].astype(str).tolist(),
                toneladas["toneladas"].astype(float).tolist(),
                "Etapa",
                "Toneladas",
            )

            etapa_top = toneladas.sort_values("toneladas", ascending=False).iloc[0]
            self.insight_stage.set_value(
                f"{etapa_top['etapa']} lidera con {etapa_top['toneladas']} toneladas."
            )
        else:
            self.chart_toneladas.clear_chart()
            self.insight_stage.set_value("No hay datos suficientes.")

        if not costos.empty:
            plot_df = costos.copy()
            plot_df["costo_plot"] = (
                plot_df["costo_promedio_preparacion"].fillna(0)
                + plot_df["costo_promedio_extraccion"].fillna(0)
                + plot_df["costo_promedio_refinacion"].fillna(0)
            )
            plot_df = plot_df[plot_df["costo_plot"] > 0]
            plot_df = plot_df.sort_values("costo_plot", ascending=False).head(8)

            if not plot_df.empty:
                self.chart_costos.plot_horizontal_bar(
                    plot_df["proceso"].astype(str).tolist(),
                    plot_df["costo_plot"].astype(float).tolist(),
                    "Costo promedio",
                    "Proceso",
                )
                top_cost = plot_df.iloc[0]
                self.insight_cost.set_value(
                    f"{top_cost['proceso']} presenta el mayor costo promedio."
                )
            else:
                self.chart_costos.clear_chart("No hay costos válidos para graficar")
                self.insight_cost.set_value("No hay costos válidos disponibles.")
        else:
            self.chart_costos.clear_chart()
            self.insight_cost.set_value("No hay información de costos.")

        if total_alertas == 0:
            self.insight_alerts.set_value("No se detectaron alertas con las reglas actuales.")
        else:
            self.insight_alerts.set_value(f"Se detectaron {total_alertas} alertas de calidad.")