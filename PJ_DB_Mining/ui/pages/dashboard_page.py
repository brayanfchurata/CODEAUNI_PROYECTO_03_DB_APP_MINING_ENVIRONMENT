from PySide6.QtWidgets import QGridLayout, QSplitter, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

from database.connection import DatabaseManager
from database.queries import QueryLibrary
from ui.widgets.data_table import DataTable
from ui.widgets.kpi_card import KpiCard


class DashboardPage(QWidget):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db

        self.kpi_toneladas = KpiCard("Toneladas totales", "#22c55e")
        self.kpi_costo = KpiCard("Costo total estimado", "#f59e0b")
        self.kpi_consumo = KpiCard("Consumo energético total", "#3b82f6")
        self.kpi_alertas = KpiCard("Alertas detectadas", "#ef4444")

        self.toneladas_panel = DataTable("Toneladas por etapa")
        self.alertas_panel = DataTable("Alertas de calidad de datos")

        cards_layout = QGridLayout()
        cards_layout.addWidget(self.kpi_toneladas, 0, 0)
        cards_layout.addWidget(self.kpi_costo, 0, 1)
        cards_layout.addWidget(self.kpi_consumo, 0, 2)
        cards_layout.addWidget(self.kpi_alertas, 0, 3)

        splitter = QSplitter(Qt.Horizontal)

        left_container = QWidget()
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.toneladas_panel)
        left_container.setLayout(left_layout)

        right_container = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.alertas_panel)
        right_container.setLayout(right_layout)

        splitter.addWidget(left_container)
        splitter.addWidget(right_container)
        splitter.setSizes([700, 700])

        layout = QVBoxLayout()
        layout.addLayout(cards_layout)
        layout.addWidget(splitter)
        self.setLayout(layout)

    def refresh(self):
        total_ton = self.db.query_df(QueryLibrary.KPI_TOTAL_TONELADAS)
        total_cost = self.db.query_df(QueryLibrary.KPI_COSTO_TOTAL)
        total_cons = self.db.query_df(QueryLibrary.KPI_CONSUMO_TOTAL)
        toneladas = self.db.query_df(QueryLibrary.QUERY_TONELADAS_POR_ETAPA)
        alertas = self.db.query_df(QueryLibrary.QUERY_ALERTAS)

        self.kpi_toneladas.set_value(str(total_ton.iloc[0, 0]))
        self.kpi_costo.set_value(f"USD {total_cost.iloc[0, 0]}")
        self.kpi_consumo.set_value(str(total_cons.iloc[0, 0]))
        self.kpi_alertas.set_value(str(len(alertas.index)))

        self.toneladas_panel.load_dataframe(toneladas)
        self.alertas_panel.load_dataframe(alertas)