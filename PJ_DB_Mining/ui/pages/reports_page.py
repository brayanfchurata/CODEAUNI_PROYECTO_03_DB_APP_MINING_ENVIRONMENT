from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from services.export_service import ExportService
from services.analytics_service import AnalyticsService
from services.quality_service import QualityService
from ui.widgets.data_table import DataTable
from ui.widgets.chart_widget import ChartWidget


class ReportsPage(QWidget):
    def __init__(
        self,
        analytics_service: AnalyticsService,
        quality_service: QualityService,
    ):
        super().__init__()
        self.analytics_service = analytics_service
        self.quality_service = quality_service

        self.title_label = QLabel("Reportes analíticos")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.export_excel_button = QPushButton("Exportar reporte a Excel")
        self.toneladas_table = DataTable("Toneladas por etapa")
        self.alertas_table = DataTable("Alertas de calidad")
        self.chart_toneladas = ChartWidget("Toneladas por etapa")

        top_actions = QHBoxLayout()
        top_actions.addWidget(self.title_label)
        top_actions.addStretch()
        top_actions.addWidget(self.export_excel_button)

        layout = QVBoxLayout()
        layout.addLayout(top_actions)
        layout.addWidget(self.chart_toneladas)
        layout.addWidget(self.toneladas_table)
        layout.addWidget(self.alertas_table)
        self.setLayout(layout)

        self.export_excel_button.clicked.connect(self.export_excel_report)

        self.current_toneladas_df = None
        self.current_alertas_df = None

    def refresh(self) -> None:
        toneladas_df = self.analytics_service.get_toneladas_por_etapa()
        alertas_df = self.quality_service.get_alertas()

        self.current_toneladas_df = toneladas_df
        self.current_alertas_df = alertas_df

        self.toneladas_table.load_dataframe(toneladas_df)
        self.alertas_table.load_dataframe(alertas_df)

        if not toneladas_df.empty:
            labels = toneladas_df["etapa"].astype(str).tolist()
            values = toneladas_df["toneladas"].astype(float).tolist()
            self.chart_toneladas.plot_bar(
                labels,
                values,
                x_label="Etapa",
                y_label="Toneladas"
            )
        else:
            self.chart_toneladas.clear_chart()

    def export_excel_report(self) -> None:
        try:
            if self.current_toneladas_df is None or self.current_alertas_df is None:
                QMessageBox.warning(
                    self,
                    "Sin datos",
                    "Primero actualiza la página de reportes."
                )
                return

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar reporte Excel",
                "reporte_mineria.xlsx",
                "Excel (*.xlsx)"
            )

            if not file_path:
                return

            ExportService.ensure_parent_dir(file_path)
            ExportService.export_to_excel(
                {
                    "Toneladas por etapa": self.current_toneladas_df,
                    "Alertas de calidad": self.current_alertas_df,
                },
                file_path,
            )

            QMessageBox.information(
                self,
                "Exportación exitosa",
                f"Reporte guardado en:\n{file_path}"
            )
        except Exception as exc:
            QMessageBox.critical(self, "Error al exportar", str(exc))