from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from services.quality_service import QualityService
from ui.widgets.data_table import DataTable
from ui.widgets.kpi_card import KpiCard


class QualityPage(QWidget):
    def __init__(self, quality_service: QualityService):
        super().__init__()
        self.quality_service = quality_service

        self.kpi_total_alertas = KpiCard("Total alertas")
        self.kpi_prep = KpiCard("Alertas preparación")
        self.kpi_ext = KpiCard("Alertas extracción")
        self.kpi_ref = KpiCard("Alertas refinación")

        self.alertas_table = DataTable("Registros con anomalías")

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.kpi_total_alertas)
        top_layout.addWidget(self.kpi_prep)
        top_layout.addWidget(self.kpi_ext)
        top_layout.addWidget(self.kpi_ref)

        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(self.alertas_table)
        self.setLayout(layout)

    def refresh(self) -> None:
        summary = self.quality_service.get_quality_summary()
        alertas = self.quality_service.get_alertas()

        self.kpi_total_alertas.set_value(str(summary["total_alertas"]))
        self.kpi_prep.set_value(str(summary["alertas_preparacion"]))
        self.kpi_ext.set_value(str(summary["alertas_extraccion"]))
        self.kpi_ref.set_value(str(summary["alertas_refinacion"]))

        self.alertas_table.load_dataframe(alertas)