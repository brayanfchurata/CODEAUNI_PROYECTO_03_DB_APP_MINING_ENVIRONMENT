import json
import os
import sys
from dataclasses import dataclass, asdict
from typing import Optional

import pandas as pd
import pyodbc
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
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
DEFAULT_DATABASE = "SQL_PROJECT_B"
DEFAULT_DRIVER = "ODBC Driver 17 for SQL Server"
SETTINGS_FILE = "mineria_app_settings.json"

STYLE = """
QMainWindow, QWidget {
    background-color: #0f172a;
    color: #e2e8f0;
    font-family: Segoe UI;
    font-size: 12px;
}
QGroupBox {
    border: 1px solid #334155;
    border-radius: 10px;
    margin-top: 10px;
    padding-top: 12px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
}
QPushButton {
    background-color: #2563eb;
    color: white;
    border: none;
    padding: 8px 14px;
    border-radius: 8px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
QPushButton:disabled {
    background-color: #475569;
}
QLineEdit, QTextEdit, QComboBox, QTableWidget {
    background-color: #111827;
    border: 1px solid #334155;
    border-radius: 8px;
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
    border-radius: 10px;
}
QTabBar::tab {
    background: #111827;
    color: #cbd5e1;
    padding: 8px 16px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 3px;
}
QTabBar::tab:selected {
    background: #1d4ed8;
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


class SettingsManager:
    @staticmethod
    def load() -> DbConfig:
        if not os.path.exists(SETTINGS_FILE):
            return DbConfig()
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
            return DbConfig(**data)
        except Exception:
            return DbConfig()

    @staticmethod
    def save(config: DbConfig):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
            json.dump(asdict(config), file, indent=2, ensure_ascii=False)


class DatabaseManager:
    def __init__(self, config: Optional[DbConfig] = None):
        self.config = config or DbConfig()
        self.connection: Optional[pyodbc.Connection] = None

    def connect(self):
        self.disconnect()
        self.connection = pyodbc.connect(self.config.connection_string(), timeout=8)
        return self.connection

    def disconnect(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def test_connection(self):
        conn = pyodbc.connect(self.config.connection_string(), timeout=5)
        conn.close()
        return True

    def query_df(self, sql: str, params: Optional[list] = None) -> pd.DataFrame:
        if self.connection is None:
            self.connect()
        return pd.read_sql(sql, self.connection, params=params or [])


class QueryRepository:
    @staticmethod
    def filtros_where(etapa: str, proceso: str):
        etapa_filter = ""
        proceso_filter = ""
        params = []
        if etapa != "Todas":
            etapa_filter = " AND etapa = ? "
            params.append(etapa)
        if proceso != "Todos":
            proceso_filter = " AND proceso = ? "
            params.append(proceso)
        return etapa_filter, proceso_filter, params

    @staticmethod
    def vista_consolidada():
        return """
        SELECT *
        FROM (
            SELECT
                'Preparacion' AS etapa,
                pm.fecha,
                dp.proceso,
                dp.tipo_proceso,
                pm.id_encargado,
                pm.toneladas_procesadas,
                pm.porcentaje_recuperacion AS eficiencia_pct,
                pm.tiempo_operacion_horas AS tiempo_horas,
                pm.consumo_energia_kwh AS consumo_energia,
                pm.costo_tonelada_usd AS costo_unitario,
                CAST(pm.toneladas_procesadas * pm.costo_tonelada_usd AS DECIMAL(18,2)) AS costo_total
            FROM dbo.preparacion_minerales pm
            INNER JOIN dbo.dim_procesos dp ON dp.id_proceso = pm.id_proceso

            UNION ALL

            SELECT
                'Extraccion' AS etapa,
                em.fecha,
                dp.proceso,
                dp.tipo_proceso,
                em.id_encargado,
                em.toneladas_procesadas,
                em.porcentaje_extraccion AS eficiencia_pct,
                NULL AS tiempo_horas,
                em.consumo_reactivos_kg AS consumo_energia,
                NULL AS costo_unitario,
                em.costo_operacion_usd AS costo_total
            FROM dbo.extraccion_metales em
            INNER JOIN dbo.dim_procesos dp ON dp.id_proceso = em.id_proceso

            UNION ALL

            SELECT
                'Refinacion' AS etapa,
                rm.fecha,
                dp.proceso,
                dp.tipo_proceso,
                NULL AS id_encargado,
                rm.toneladas_procesadas,
                (rm.pureza_final_pct - rm.pureza_inicial_pct) AS eficiencia_pct,
                rm.tiempo_refinacion_hrs AS tiempo_horas,
                rm.consumo_electrico_kwh AS consumo_energia,
                NULL AS costo_unitario,
                rm.costo_total_usd AS costo_total
            FROM dbo.refinacion_metales rm
            INNER JOIN dbo.dim_procesos dp ON dp.id_proceso = rm.id_proceso
        ) q
        """

    @staticmethod
    def procesos_catalogo():
        return "SELECT proceso FROM dbo.dim_procesos ORDER BY proceso"

    @staticmethod
    def kpis(etapa: str, proceso: str):
        etapa_filter, proceso_filter, params = QueryRepository.filtros_where(etapa, proceso)
        sql = f"""
        WITH base AS (
            {QueryRepository.vista_consolidada()}
        )
        SELECT
            CAST(SUM(toneladas_procesadas) AS DECIMAL(18,2)) AS toneladas_totales,
            CAST(SUM(costo_total) AS DECIMAL(18,2)) AS costo_total_usd,
            CAST(AVG(eficiencia_pct) AS DECIMAL(18,2)) AS eficiencia_promedio,
            CAST(AVG(consumo_energia) AS DECIMAL(18,2)) AS consumo_promedio
        FROM base
        WHERE 1 = 1 {etapa_filter} {proceso_filter}
        """
        return sql, params

    @staticmethod
    def toneladas_por_etapa(proceso: str):
        params = []
        proceso_filter = ""
        if proceso != "Todos":
            proceso_filter = " WHERE proceso = ? "
            params.append(proceso)
        sql = f"""
        WITH base AS (
            {QueryRepository.vista_consolidada()}
        )
        SELECT etapa, CAST(SUM(toneladas_procesadas) AS DECIMAL(18,2)) AS toneladas
        FROM base
        {proceso_filter}
        GROUP BY etapa
        ORDER BY toneladas DESC
        """
        return sql, params

    @staticmethod
    def costo_por_proceso(etapa: str):
        params = []
        etapa_filter = ""
        if etapa != "Todas":
            etapa_filter = " WHERE etapa = ? "
            params.append(etapa)
        sql = f"""
        WITH base AS (
            {QueryRepository.vista_consolidada()}
        )
        SELECT proceso, etapa, CAST(SUM(costo_total) AS DECIMAL(18,2)) AS costo_total_usd
        FROM base
        {etapa_filter}
        GROUP BY proceso, etapa
        ORDER BY costo_total_usd DESC
        """
        return sql, params

    @staticmethod
    def eficiencia_por_proceso(etapa: str):
        params = []
        etapa_filter = ""
        if etapa != "Todas":
            etapa_filter = " WHERE etapa = ? "
            params.append(etapa)
        sql = f"""
        WITH base AS (
            {QueryRepository.vista_consolidada()}
        )
        SELECT proceso, etapa, CAST(AVG(eficiencia_pct) AS DECIMAL(18,2)) AS eficiencia_promedio
        FROM base
        {etapa_filter}
        GROUP BY proceso, etapa
        ORDER BY eficiencia_promedio DESC
        """
        return sql, params

    @staticmethod
    def tabla_detalle(etapa: str, proceso: str):
        etapa_filter, proceso_filter, params = QueryRepository.filtros_where(etapa, proceso)
        sql = f"""
        WITH base AS (
            {QueryRepository.vista_consolidada()}
        )
        SELECT TOP 500 *
        FROM base
        WHERE 1 = 1 {etapa_filter} {proceso_filter}
        ORDER BY fecha DESC
        """
        return sql, params

    @staticmethod
    def alertas_calidad():
        return """
        SELECT 'Preparacion' AS etapa, id, fecha, id_proceso, 'porcentaje_recuperacion fuera de rango' AS alerta
        FROM dbo.preparacion_minerales
        WHERE porcentaje_recuperacion < 0 OR porcentaje_recuperacion > 100
        UNION ALL
        SELECT 'Preparacion', id, fecha, id_proceso, 'tiempo_operacion_horas negativo'
        FROM dbo.preparacion_minerales
        WHERE tiempo_operacion_horas < 0
        UNION ALL
        SELECT 'Extraccion', id, fecha, id_proceso, 'porcentaje_extraccion fuera de rango'
        FROM dbo.extraccion_metales
        WHERE porcentaje_extraccion < 0 OR porcentaje_extraccion > 100
        UNION ALL
        SELECT 'Extraccion', id, fecha, id_proceso, 'temperatura_procesos_celcius negativa'
        FROM dbo.extraccion_metales
        WHERE temperatura_procesos_celcius < 0
        UNION ALL
        SELECT 'Refinacion', NULL, fecha, id_proceso, 'pureza_final menor que pureza_inicial'
        FROM dbo.refinacion_metales
        WHERE pureza_final_pct < pureza_inicial_pct
        ORDER BY fecha DESC
        """


class KpiCard(QFrame):
    def __init__(self, title: str, accent: str):
        super().__init__()
        self.setStyleSheet(
            f"QFrame {{ background-color: #111827; border: 1px solid #334155; border-left: 5px solid {accent}; border-radius: 12px; }}"
        )
        self.title = QLabel(title)
        self.title.setStyleSheet("font-size: 12px; color: #94a3b8; font-weight: bold;")
        self.value = QLabel("--")
        self.value.setStyleSheet("font-size: 26px; font-weight: 700; color: white;")
        self.subtitle = QLabel("Indicador actualizado")
        self.subtitle.setStyleSheet("font-size: 11px; color: #64748b;")

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.value)
        layout.addWidget(self.subtitle)
        self.setLayout(layout)

    def set_value(self, value: str):
        self.value.setText(value)


class DataTable(QWidget):
    def __init__(self, title: str):
        super().__init__()
        self.current_df = pd.DataFrame()
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.table = QTableWidget()
        self.btn_export_csv = QPushButton("Exportar CSV")
        self.btn_export_excel = QPushButton("Exportar Excel")

        top = QHBoxLayout()
        top.addWidget(self.title_label)
        top.addStretch()
        top.addWidget(self.btn_export_csv)
        top.addWidget(self.btn_export_excel)

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.btn_export_csv.clicked.connect(self.export_csv)
        self.btn_export_excel.clicked.connect(self.export_excel)

    def load_dataframe(self, df: pd.DataFrame):
        self.current_df = df.copy()
        self.table.clear()
        self.table.setRowCount(len(df.index))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels([str(c) for c in df.columns])

        for r in range(len(df.index)):
            for c in range(len(df.columns)):
                value = "" if pd.isna(df.iat[r, c]) else str(df.iat[r, c])
                self.table.setItem(r, c, QTableWidgetItem(value))
        self.table.resizeColumnsToContents()

    def export_csv(self):
        if self.current_df.empty:
            QMessageBox.information(self, "Sin datos", "No hay información para exportar.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Guardar CSV", "reporte.csv", "CSV (*.csv)")
        if path:
            self.current_df.to_csv(path, index=False, encoding="utf-8-sig")
            QMessageBox.information(self, "Exportado", f"CSV guardado en:\n{path}")

    def export_excel(self):
        if self.current_df.empty:
            QMessageBox.information(self, "Sin datos", "No hay información para exportar.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Guardar Excel", "reporte.xlsx", "Excel (*.xlsx)")
        if path:
            self.current_df.to_excel(path, index=False)
            QMessageBox.information(self, "Exportado", f"Excel guardado en:\n{path}")


class MplChart(QWidget):
    def __init__(self, title: str):
        super().__init__()
        self.title = QLabel(title)
        self.title.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def plot_bar(self, df: pd.DataFrame, category_col: str, value_col: str, rotation: int = 0):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        if df.empty:
            ax.text(0.5, 0.5, "Sin datos", ha="center", va="center")
            ax.axis("off")
        else:
            ax.bar(df[category_col].astype(str), df[value_col].astype(float))
            ax.set_title(self.title.text())
            ax.tick_params(axis="x", rotation=rotation)
            ax.grid(alpha=0.25)
        self.figure.tight_layout()
        self.canvas.draw()


class FilterBar(QGroupBox):
    def __init__(self):
        super().__init__("Filtros analíticos")
        self.cmb_etapa = QComboBox()
        self.cmb_etapa.addItems(["Todas", "Preparacion", "Extraccion", "Refinacion"])
        self.cmb_proceso = QComboBox()
        self.cmb_proceso.addItem("Todos")
        self.btn_apply = QPushButton("Actualizar análisis")

        form = QFormLayout()
        form.addRow("Etapa", self.cmb_etapa)
        form.addRow("Proceso", self.cmb_proceso)

        layout = QHBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.btn_apply)
        self.setLayout(layout)


class ConnectionPanel(QGroupBox):
    def __init__(self, db: DatabaseManager, on_connected):
        super().__init__("Conexión a SQL Server")
        self.db = db
        self.on_connected = on_connected

        self.server_input = QLineEdit(self.db.config.server)
        self.database_input = QLineEdit(self.db.config.database)
        self.driver_input = QLineEdit(self.db.config.driver)
        self.btn_test = QPushButton("Probar")
        self.btn_connect = QPushButton("Conectar")
        self.btn_save = QPushButton("Guardar configuración")

        form = QFormLayout()
        form.addRow("Servidor", self.server_input)
        form.addRow("Base de datos", self.database_input)
        form.addRow("Driver ODBC", self.driver_input)

        actions = QHBoxLayout()
        actions.addWidget(self.btn_test)
        actions.addWidget(self.btn_connect)
        actions.addWidget(self.btn_save)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(actions)
        self.setLayout(layout)

        self.btn_test.clicked.connect(self.test_connection)
        self.btn_connect.clicked.connect(self.connect_db)
        self.btn_save.clicked.connect(self.save_config)

    def sync_config(self):
        self.db.config.server = self.server_input.text().strip()
        self.db.config.database = self.database_input.text().strip()
        self.db.config.driver = self.driver_input.text().strip()

    def test_connection(self):
        try:
            self.sync_config()
            self.db.test_connection()
            QMessageBox.information(self, "Conexión correcta", "La conexión fue exitosa.")
        except Exception as exc:
            QMessageBox.critical(self, "Error de conexión", str(exc))

    def connect_db(self):
        try:
            self.sync_config()
            self.db.connect()
            self.on_connected()
            QMessageBox.information(self, "Conectado", "Conexión establecida correctamente.")
        except Exception as exc:
            QMessageBox.critical(self, "Error de conexión", str(exc))

    def save_config(self):
        self.sync_config()
        SettingsManager.save(self.db.config)
        QMessageBox.information(self, "Configuración", "Configuración guardada correctamente.")


class DashboardPage(QWidget):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.filters = FilterBar()
        self.kpi_ton = KpiCard("Toneladas totales", "#22c55e")
        self.kpi_cost = KpiCard("Costo total USD", "#f59e0b")
        self.kpi_eff = KpiCard("Eficiencia promedio", "#3b82f6")
        self.kpi_cons = KpiCard("Consumo promedio", "#a855f7")
        self.chart_ton = MplChart("Toneladas por etapa")
        self.chart_cost = MplChart("Costo total por proceso")
        self.detail_table = DataTable("Detalle consolidado")
        self.alert_table = DataTable("Alertas de calidad")

        cards = QGridLayout()
        cards.addWidget(self.kpi_ton, 0, 0)
        cards.addWidget(self.kpi_cost, 0, 1)
        cards.addWidget(self.kpi_eff, 0, 2)
        cards.addWidget(self.kpi_cons, 0, 3)

        charts = QSplitter(Qt.Horizontal)
        left = QWidget()
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.chart_ton)
        left.setLayout(left_layout)
        right = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.chart_cost)
        right.setLayout(right_layout)
        charts.addWidget(left)
        charts.addWidget(right)
        charts.setSizes([600, 600])

        bottom = QSplitter(Qt.Vertical)
        detail_wrap = QWidget()
        detail_layout = QVBoxLayout()
        detail_layout.addWidget(self.detail_table)
        detail_wrap.setLayout(detail_layout)
        alert_wrap = QWidget()
        alert_layout = QVBoxLayout()
        alert_layout.addWidget(self.alert_table)
        alert_wrap.setLayout(alert_layout)
        bottom.addWidget(detail_wrap)
        bottom.addWidget(alert_wrap)
        bottom.setSizes([420, 220])

        layout = QVBoxLayout()
        layout.addWidget(self.filters)
        layout.addLayout(cards)
        layout.addWidget(charts)
        layout.addWidget(bottom)
        self.setLayout(layout)

    def load_processes(self):
        df = self.db.query_df(QueryRepository.procesos_catalogo())
        current = self.filters.cmb_proceso.currentText()
        self.filters.cmb_proceso.blockSignals(True)
        self.filters.cmb_proceso.clear()
        self.filters.cmb_proceso.addItem("Todos")
        for value in df["proceso"].tolist():
            self.filters.cmb_proceso.addItem(str(value))
        idx = self.filters.cmb_proceso.findText(current)
        self.filters.cmb_proceso.setCurrentIndex(max(0, idx))
        self.filters.cmb_proceso.blockSignals(False)

    def refresh(self):
        etapa = self.filters.cmb_etapa.currentText()
        proceso = self.filters.cmb_proceso.currentText()
        sql, params = QueryRepository.kpis(etapa, proceso)
        kpis = self.db.query_df(sql, params)
        row = kpis.iloc[0]
        self.kpi_ton.set_value(str(row["toneladas_totales"] or 0))
        self.kpi_cost.set_value(f"USD {row['costo_total_usd'] or 0}")
        self.kpi_eff.set_value(f"{row['eficiencia_promedio'] or 0} %")
        self.kpi_cons.set_value(str(row["consumo_promedio"] or 0))

        sql, params = QueryRepository.toneladas_por_etapa(proceso)
        self.chart_ton.plot_bar(self.db.query_df(sql, params), "etapa", "toneladas")

        sql, params = QueryRepository.costo_por_proceso(etapa)
        self.chart_cost.plot_bar(self.db.query_df(sql, params).head(10), "proceso", "costo_total_usd", rotation=25)

        sql, params = QueryRepository.tabla_detalle(etapa, proceso)
        self.detail_table.load_dataframe(self.db.query_df(sql, params))
        self.alert_table.load_dataframe(self.db.query_df(QueryRepository.alertas_calidad()))


class InsightsPage(QWidget):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.filters = FilterBar()
        self.chart_eff = MplChart("Eficiencia por proceso")
        self.chart_rank = MplChart("Ranking de costos")
        self.table = DataTable("Indicadores comparativos")

        layout = QVBoxLayout()
        layout.addWidget(self.filters)
        charts = QSplitter(Qt.Horizontal)
        left = QWidget()
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.chart_eff)
        left.setLayout(left_layout)
        right = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.chart_rank)
        right.setLayout(right_layout)
        charts.addWidget(left)
        charts.addWidget(right)
        charts.setSizes([600, 600])
        layout.addWidget(charts)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def load_processes(self, processes_df: pd.DataFrame):
        self.filters.cmb_proceso.blockSignals(True)
        self.filters.cmb_proceso.clear()
        self.filters.cmb_proceso.addItem("Todos")
        for value in processes_df["proceso"].tolist():
            self.filters.cmb_proceso.addItem(str(value))
        self.filters.cmb_proceso.blockSignals(False)

    def refresh(self):
        etapa = self.filters.cmb_etapa.currentText()
        sql, params = QueryRepository.eficiencia_por_proceso(etapa)
        eff_df = self.db.query_df(sql, params)
        self.chart_eff.plot_bar(eff_df.head(10), "proceso", "eficiencia_promedio", rotation=25)

        sql, params = QueryRepository.costo_por_proceso(etapa)
        cost_df = self.db.query_df(sql, params)
        self.chart_rank.plot_bar(cost_df.head(10), "proceso", "costo_total_usd", rotation=25)

        self.table.load_dataframe(cost_df.merge(eff_df, on=["proceso", "etapa"], how="outer"))


class SqlConsolePage(QWidget):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.cmb_presets = QComboBox()
        self.cmb_presets.addItems([
            "Seleccione una consulta",
            "Alertas de calidad",
            "Vista consolidada",
            "Costos por proceso",
            "Eficiencia por proceso",
        ])
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Escribe una consulta SQL o usa una consulta predefinida.")
        self.btn_run = QPushButton("Ejecutar")
        self.result_table = DataTable("Resultado SQL")

        top = QHBoxLayout()
        top.addWidget(QLabel("Consultas rápidas"))
        top.addWidget(self.cmb_presets)
        top.addStretch()
        top.addWidget(self.btn_run)

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addWidget(self.editor)
        layout.addWidget(self.result_table)
        self.setLayout(layout)

        self.cmb_presets.currentTextChanged.connect(self.apply_preset)
        self.btn_run.clicked.connect(self.run_query)

    def apply_preset(self, text: str):
        mapping = {
            "Alertas de calidad": QueryRepository.alertas_calidad(),
            "Vista consolidada": QueryRepository.vista_consolidada(),
            "Costos por proceso": QueryRepository.costo_por_proceso("Todas")[0],
            "Eficiencia por proceso": QueryRepository.eficiencia_por_proceso("Todas")[0],
        }
        if text in mapping:
            self.editor.setPlainText(mapping[text])

    def run_query(self):
        sql = self.editor.toPlainText().strip()
        if not sql:
            QMessageBox.warning(self, "Consulta vacía", "Escribe una consulta SQL primero.")
            return
        try:
            self.result_table.load_dataframe(self.db.query_df(sql))
        except Exception as exc:
            QMessageBox.critical(self, "Error SQL", str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1600, 940)
        self.setStyleSheet(STYLE)

        self.db = DatabaseManager(SettingsManager.load())
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.connection_panel = ConnectionPanel(self.db, self.after_connect)
        self.dashboard_page = DashboardPage(self.db)
        self.insights_page = InsightsPage(self.db)
        self.sql_page = SqlConsolePage(self.db)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.dashboard_page, "Dashboard Ejecutivo")
        self.tabs.addTab(self.insights_page, "Inteligencia Analítica")
        self.tabs.addTab(self.sql_page, "SQL Studio")

        central = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.connection_panel)
        layout.addWidget(self.tabs)
        central.setLayout(layout)
        self.setCentralWidget(central)

        self._build_menu()
        self._bind_events()
        self.status_bar.showMessage("Listo para conectar a SQL Server.")

    def _bind_events(self):
        self.dashboard_page.filters.btn_apply.clicked.connect(self.refresh_all)
        self.insights_page.filters.btn_apply.clicked.connect(self.insights_page.refresh)

    def _build_menu(self):
        menu = self.menuBar().addMenu("Archivo")
        refresh_action = QAction("Actualizar todo", self)
        refresh_action.triggered.connect(self.refresh_all)
        disconnect_action = QAction("Desconectar", self)
        disconnect_action.triggered.connect(self.disconnect)
        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        menu.addAction(refresh_action)
        menu.addAction(disconnect_action)
        menu.addSeparator()
        menu.addAction(exit_action)

    def after_connect(self):
        self.status_bar.showMessage(f"Conectado a {self.db.config.server} / {self.db.config.database}")
        self.refresh_all()

    def refresh_all(self):
        try:
            process_df = self.db.query_df(QueryRepository.procesos_catalogo())
            self.dashboard_page.load_processes()
            self.dashboard_page.refresh()
            self.insights_page.load_processes(process_df)
            self.insights_page.refresh()
            self.status_bar.showMessage("Dashboard actualizado correctamente.")
        except Exception as exc:
            QMessageBox.critical(self, "Error al actualizar", str(exc))

    def disconnect(self):
        self.db.disconnect()
        self.status_bar.showMessage("Sesión desconectada.")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
