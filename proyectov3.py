import sys
from dataclasses import dataclass
from typing import Optional

import pandas as pd
import pyodbc
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

APP_TITLE = "Mineria Intelligence Suite"
DEFAULT_SERVER = r"localhost\SQL_BRAYAN"
DEFAULT_DATABASE = "MineriaBrayanDB"
DEFAULT_DRIVER = "ODBC Driver 17 for SQL Server"

APP_STYLE = """
QMainWindow, QWidget {
    background-color: #0f172a;
    color: #e2e8f0;
    font-family: Segoe UI;
    font-size: 12px;
}
QFrame#heroCard, QFrame#kpiCard, QFrame#panelCard {
    background-color: #111827;
    border: 1px solid #334155;
    border-radius: 16px;
}
QGroupBox {
    border: 1px solid #334155;
    border-radius: 14px;
    margin-top: 10px;
    padding-top: 12px;
    font-weight: 700;
}
QGroupBox::title {
    left: 12px;
    padding: 0 6px;
}
QLabel#heroTitle {
    font-size: 24px;
    font-weight: 800;
    color: #f8fafc;
}
QLabel#heroSubtitle {
    font-size: 12px;
    color: #94a3b8;
}
QPushButton {
    background-color: #2563eb;
    color: white;
    border: none;
    padding: 9px 14px;
    border-radius: 10px;
    font-weight: 700;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
QLineEdit, QTextEdit, QTableWidget {
    background-color: #111827;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 6px;
    color: #e2e8f0;
}
QHeaderView::section {
    background-color: #1e293b;
    color: #e2e8f0;
    border: 1px solid #334155;
    padding: 6px;
}
QTabWidget::pane {
    border: 1px solid #334155;
    border-radius: 14px;
}
QTabBar::tab {
    background: #111827;
    color: #cbd5e1;
    padding: 10px 18px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    margin-right: 4px;
}
QTabBar::tab:selected {
    background: #2563eb;
    color: white;
}
"""


@dataclass
class DbConfig:
    server: str = DEFAULT_SERVER
    database: str = DEFAULT_DATABASE
    driver: str = DEFAULT_DRIVER
    trusted_connection: bool = True
    username: str = ""
    password: str = ""

    def connection_string(self) -> str:
        parts = [
            f"DRIVER={{{self.driver}}}",
            f"SERVER={self.server}",
            f"DATABASE={self.database}",
        ]
        if self.trusted_connection:
            parts.append("Trusted_Connection=yes")
        else:
            parts.append(f"UID={self.username}")
            parts.append(f"PWD={self.password}")
        return ";".join(parts) + ";"


class DatabaseManager:
    def __init__(self, config: Optional[DbConfig] = None):
        self.config = config or DbConfig()
        self.connection: Optional[pyodbc.Connection] = None

    def connect(self):
        if self.connection is None:
            self.connection = pyodbc.connect(self.config.connection_string(), timeout=5)
        return self.connection

    def disconnect(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def test_connection(self) -> bool:
        conn = pyodbc.connect(self.config.connection_string(), timeout=5)
        conn.close()
        return True

    def query_df(self, sql: str) -> pd.DataFrame:
        if self.connection is None:
            self.connect()
        return pd.read_sql(sql, self.connection)


class QueryLibrary:
    KPI_TOTAL_TONELADAS = """
    SELECT CAST(SUM(total_toneladas) AS DECIMAL(18,2)) AS total_toneladas
    FROM (
        SELECT SUM(toneladas_procesadas) AS total_toneladas FROM preparacion_minerales
        UNION ALL
        SELECT SUM(toneladas_procesadas) AS total_toneladas FROM extraccion_metales
        UNION ALL
        SELECT SUM(toneladas_procesadas) AS total_toneladas FROM refinacion_metales
    ) t;
    """

    KPI_COSTO_TOTAL = """
    SELECT CAST(SUM(costo_total) AS DECIMAL(18,2)) AS costo_total_usd
    FROM (
        SELECT SUM(toneladas_procesadas * costo_tonelada_usd) AS costo_total FROM preparacion_minerales
        UNION ALL
        SELECT SUM(costo_operacion_usd) AS costo_total FROM extraccion_metales
        UNION ALL
        SELECT SUM(costo_total_usd) AS costo_total FROM refinacion_metales
    ) t;
    """

    KPI_CONSUMO_TOTAL = """
    SELECT CAST(SUM(consumo_total) AS DECIMAL(18,2)) AS consumo_total
    FROM (
        SELECT SUM(consumo_energia_kwh) AS consumo_total FROM preparacion_minerales
        UNION ALL
        SELECT SUM(consumo_electrico_kwh) AS consumo_total FROM refinacion_metales
    ) t;
    """

    QUERY_TONELADAS_POR_ETAPA = """
    SELECT etapa, CAST(SUM(toneladas_procesadas) AS DECIMAL(18,2)) AS toneladas
    FROM (
        SELECT 'Preparacion' AS etapa, toneladas_procesadas FROM preparacion_minerales
        UNION ALL
        SELECT 'Extraccion' AS etapa, toneladas_procesadas FROM extraccion_metales
        UNION ALL
        SELECT 'Refinacion' AS etapa, toneladas_procesadas FROM refinacion_metales
    ) t
    GROUP BY etapa
    ORDER BY toneladas DESC;
    """

    QUERY_COSTO_PROMEDIO_PROCESO = """
    SELECT dp.proceso, dp.tipo_proceso,
           CAST(AVG(CASE WHEN dp.tipo_proceso = 'Preparacion' THEN pm.costo_tonelada_usd END) AS DECIMAL(18,2)) AS costo_promedio_preparacion,
           CAST(AVG(CASE WHEN dp.tipo_proceso = 'Extraccion' THEN em.costo_operacion_usd END) AS DECIMAL(18,2)) AS costo_promedio_extraccion,
           CAST(AVG(CASE WHEN dp.tipo_proceso = 'Refinacion' THEN rm.costo_total_usd END) AS DECIMAL(18,2)) AS costo_promedio_refinacion
    FROM dim_procesos dp
    LEFT JOIN preparacion_minerales pm ON dp.id_proceso = pm.id_proceso
    LEFT JOIN extraccion_metales em ON dp.id_proceso = em.id_proceso
    LEFT JOIN refinacion_metales rm ON dp.id_proceso = rm.id_proceso
    GROUP BY dp.proceso, dp.tipo_proceso
    ORDER BY dp.tipo_proceso, dp.proceso;
    """

    QUERY_ALERTAS = """
    SELECT 'Preparacion' AS etapa, id, fecha, id_proceso, 'porcentaje_recuperacion fuera de rango' AS alerta
    FROM preparacion_minerales
    WHERE porcentaje_recuperacion < 0 OR porcentaje_recuperacion > 100
    UNION ALL
    SELECT 'Preparacion', id, fecha, id_proceso, 'tiempo_operacion_horas negativo'
    FROM preparacion_minerales
    WHERE tiempo_operacion_horas < 0
    UNION ALL
    SELECT 'Extraccion', id, fecha, id_proceso, 'porcentaje_extraccion fuera de rango'
    FROM extraccion_metales
    WHERE porcentaje_extraccion < 0 OR porcentaje_extraccion > 100
    UNION ALL
    SELECT 'Extraccion', id, fecha, id_proceso, 'temperatura_procesos_celcius negativa'
    FROM extraccion_metales
    WHERE temperatura_procesos_celcius < 0
    ORDER BY fecha;
    """


class HeroCard(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("heroCard")
        title = QLabel("Mineria Intelligence Suite")
        title.setObjectName("heroTitle")
        subtitle = QLabel(
            "Panel ejecutivo para procesos mineros con foco en impacto visual, lectura rápida y análisis operativo."
        )
        subtitle.setObjectName("heroSubtitle")
        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        self.setLayout(layout)


class CompactConnectionPanel(QGroupBox):
    def __init__(self, db: DatabaseManager, on_connected):
        super().__init__("Conexión")
        self.db = db
        self.on_connected = on_connected

        self.server_input = QLineEdit(self.db.config.server)
        self.database_input = QLineEdit(self.db.config.database)
        self.driver_input = QLineEdit(self.db.config.driver)
        self.test_button = QPushButton("Probar")
        self.connect_button = QPushButton("Conectar")

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.addRow("Servidor", self.server_input)
        form.addRow("Base", self.database_input)
        form.addRow("Driver", self.driver_input)

        buttons = QHBoxLayout()
        buttons.addWidget(self.test_button)
        buttons.addWidget(self.connect_button)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(buttons)
        self.setLayout(layout)

        self.test_button.clicked.connect(self.test_connection)
        self.connect_button.clicked.connect(self.connect_db)

    def _sync_config(self):
        self.db.config.server = self.server_input.text().strip()
        self.db.config.database = self.database_input.text().strip()
        self.db.config.driver = self.driver_input.text().strip()

    def test_connection(self):
        try:
            self._sync_config()
            self.db.test_connection()
            QMessageBox.information(self, "Conexión correcta", "La conexión fue exitosa.")
        except Exception as exc:
            QMessageBox.critical(self, "Error de conexión", str(exc))

    def connect_db(self):
        try:
            self._sync_config()
            self.db.connect()
            self.on_connected()
        except Exception as exc:
            QMessageBox.critical(self, "Error de conexión", str(exc))


class KpiCard(QFrame):
    def __init__(self, title: str, accent_color: str):
        super().__init__()
        self.setObjectName("kpiCard")
        self.setStyleSheet(
            f"QFrame#kpiCard {{ border-left: 5px solid {accent_color}; }}"
        )
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 12px; color: #94a3b8; font-weight: 700;")
        self.value_label = QLabel("--")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("font-size: 30px; font-weight: 800; color: #f8fafc; padding: 6px;")
        self.footer_label = QLabel("Indicador actualizado")
        self.footer_label.setStyleSheet("font-size: 11px; color: #64748b;")

        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.footer_label)
        self.setLayout(layout)

    def set_value(self, value: str):
        self.value_label.setText(value)


class ChartWidget(QFrame):
    def __init__(self, title: str):
        super().__init__()
        self.setObjectName("panelCard")
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 16px; font-weight: 800; color: #f8fafc;")
        self.figure = Figure(figsize=(5, 2.8))
        self.canvas = FigureCanvas(self.figure)

        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def clear_chart(self):
        self.figure.clear()
        self.canvas.draw()

    def plot_bar(self, labels, values, x_label="", y_label=""):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.bar(labels, values)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.tick_params(axis="x", rotation=20)
        ax.grid(axis="y", linestyle="--", alpha=0.35)
        self.figure.tight_layout()
        self.canvas.draw()


class TablePanel(QFrame):
    def __init__(self, title: str):
        super().__init__()
        self.setObjectName("panelCard")
        self.current_df = pd.DataFrame()

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 16px; font-weight: 800; color: #f8fafc;")
        self.table = QTableWidget()
        self.export_button = QPushButton("Exportar CSV")

        header = QHBoxLayout()
        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.export_button)

        layout = QVBoxLayout()
        layout.addLayout(header)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.export_button.clicked.connect(self.export_csv)

    def load_dataframe(self, df: pd.DataFrame):
        self.current_df = df.copy()
        self.table.clear()
        self.table.setRowCount(len(df.index))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels([str(c) for c in df.columns])

        for row in range(len(df.index)):
            for col in range(len(df.columns)):
                value = "" if pd.isna(df.iat[row, col]) else str(df.iat[row, col])
                self.table.setItem(row, col, QTableWidgetItem(value))

        self.table.resizeColumnsToContents()

    def export_csv(self):
        if self.current_df.empty:
            QMessageBox.information(self, "Sin datos", "No hay datos para exportar.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Guardar CSV", "reporte.csv", "CSV (*.csv)")
        if not path:
            return
        self.current_df.to_csv(path, index=False, encoding="utf-8-sig")
        QMessageBox.information(self, "Exportado", f"Archivo guardado en:\n{path}")


class SqlConsole(QWidget):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Escribe una consulta SQL aquí...")
        self.run_button = QPushButton("Ejecutar SQL")
        self.result_panel = TablePanel("Resultado de la consulta")

        layout = QVBoxLayout()
        layout.addWidget(self.editor)
        layout.addWidget(self.run_button, alignment=Qt.AlignRight)
        layout.addWidget(self.result_panel)
        self.setLayout(layout)

        self.run_button.clicked.connect(self.run_sql)

    def run_sql(self):
        sql = self.editor.toPlainText().strip()
        if not sql:
            QMessageBox.warning(self, "Consulta vacía", "Escribe una consulta SQL primero.")
            return
        try:
            df = self.db.query_df(sql)
            self.result_panel.load_dataframe(df)
        except Exception as exc:
            QMessageBox.critical(self, "Error SQL", str(exc))


class DashboardPage(QWidget):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db

        self.kpi_toneladas = KpiCard("Toneladas totales", "#22c55e")
        self.kpi_costo = KpiCard("Costo total estimado", "#f59e0b")
        self.kpi_consumo = KpiCard("Consumo energético total", "#3b82f6")
        self.kpi_alertas = KpiCard("Alertas detectadas", "#ef4444")

        self.chart_toneladas = ChartWidget("Toneladas por etapa")
        self.chart_costos = ChartWidget("Costo promedio por proceso")
        self.alertas_panel = TablePanel("Alertas de calidad de datos")
        self.resumen_panel = TablePanel("Resumen por etapa")

        cards_layout = QGridLayout()
        cards_layout.setHorizontalSpacing(14)
        cards_layout.setVerticalSpacing(14)
        cards_layout.addWidget(self.kpi_toneladas, 0, 0)
        cards_layout.addWidget(self.kpi_costo, 0, 1)
        cards_layout.addWidget(self.kpi_consumo, 0, 2)
        cards_layout.addWidget(self.kpi_alertas, 0, 3)

        charts_layout = QHBoxLayout()
        charts_layout.addWidget(self.chart_toneladas)
        charts_layout.addWidget(self.chart_costos)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.resumen_panel, 1)
        bottom_layout.addWidget(self.alertas_panel, 1)

        layout = QVBoxLayout()
        layout.setSpacing(14)
        layout.addLayout(cards_layout)
        layout.addLayout(charts_layout)
        layout.addLayout(bottom_layout)
        self.setLayout(layout)

    def refresh(self):
        total_ton = self.db.query_df(QueryLibrary.KPI_TOTAL_TONELADAS)
        total_cost = self.db.query_df(QueryLibrary.KPI_COSTO_TOTAL)
        total_cons = self.db.query_df(QueryLibrary.KPI_CONSUMO_TOTAL)
        toneladas = self.db.query_df(QueryLibrary.QUERY_TONELADAS_POR_ETAPA)
        alertas = self.db.query_df(QueryLibrary.QUERY_ALERTAS)
        costos = self.db.query_df(QueryLibrary.QUERY_COSTO_PROMEDIO_PROCESO)

        self.kpi_toneladas.set_value(str(total_ton.iloc[0, 0]))
        self.kpi_costo.set_value(f"USD {total_cost.iloc[0, 0]}")
        self.kpi_consumo.set_value(str(total_cons.iloc[0, 0]))
        self.kpi_alertas.set_value(str(len(alertas.index)))

        self.resumen_panel.load_dataframe(toneladas)
        self.alertas_panel.load_dataframe(alertas)

        if not toneladas.empty:
            self.chart_toneladas.plot_bar(
                toneladas["etapa"].astype(str).tolist(),
                toneladas["toneladas"].astype(float).tolist(),
                "Etapa",
                "Toneladas",
            )
        else:
            self.chart_toneladas.clear_chart()

        if not costos.empty:
            plot_df = costos.copy()
            plot_df["costo_plot"] = (
                plot_df["costo_promedio_preparacion"].fillna(0)
                + plot_df["costo_promedio_extraccion"].fillna(0)
                + plot_df["costo_promedio_refinacion"].fillna(0)
            )
            plot_df = plot_df.sort_values("costo_plot", ascending=False).head(8)
            self.chart_costos.plot_bar(
                plot_df["proceso"].astype(str).tolist(),
                plot_df["costo_plot"].astype(float).tolist(),
                "Proceso",
                "Costo promedio",
            )
        else:
            self.chart_costos.clear_chart()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1500, 900)

        self.db = DatabaseManager()
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.hero_card = HeroCard()
        self.connection_panel = CompactConnectionPanel(self.db, self.after_connect)
        self.dashboard_page = DashboardPage(self.db)
        self.sql_console = SqlConsole(self.db)
        self.costos_panel = TablePanel("Costos promedio por proceso")

        self.tabs = QTabWidget()
        self.tabs.addTab(self.dashboard_page, "Dashboard Ejecutivo")
        self.tabs.addTab(self.costos_panel, "Indicadores")
        self.tabs.addTab(self.sql_console, "Consultas SQL")

        top_row = QHBoxLayout()
        top_row.addWidget(self.hero_card, 2)
        top_row.addWidget(self.connection_panel, 1)

        container = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(14)
        layout.addLayout(top_row)
        layout.addWidget(self.tabs)
        container.setLayout(layout)
        self.setCentralWidget(container)

        self._build_menu()
        self.status_bar.showMessage("Listo para conectar.")
        QApplication.instance().setStyleSheet(APP_STYLE)

    def _build_menu(self):
        refresh_action = QAction("Actualizar", self)
        refresh_action.triggered.connect(self.refresh_all)

        disconnect_action = QAction("Desconectar", self)
        disconnect_action.triggered.connect(self.disconnect)

        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)

        menu = self.menuBar().addMenu("Archivo")
        menu.addAction(refresh_action)
        menu.addAction(disconnect_action)
        menu.addSeparator()
        menu.addAction(exit_action)

    def after_connect(self):
        self.status_bar.showMessage(
            f"Conectado a {self.db.config.server} / {self.db.config.database}"
        )
        self.refresh_all()

    def refresh_all(self):
        try:
            self.dashboard_page.refresh()
            costos = self.db.query_df(QueryLibrary.QUERY_COSTO_PROMEDIO_PROCESO)
            self.costos_panel.load_dataframe(costos)
            self.status_bar.showMessage("Datos actualizados correctamente.")
        except Exception as exc:
            QMessageBox.critical(self, "Error al actualizar", str(exc))

    def disconnect(self):
        self.db.disconnect()
        self.status_bar.showMessage("Desconectado.")


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
