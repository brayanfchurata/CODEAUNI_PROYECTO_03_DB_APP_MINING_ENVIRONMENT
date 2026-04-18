import sys
from dataclasses import dataclass
from typing import Optional

import pandas as pd
import pyodbc
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
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


APP_TITLE = "Mineria Analytics Desktop"
DEFAULT_SERVER = r"localhost\SQL_BRAYAN"
DEFAULT_DATABASE = "MineriaBrayanDB"
DEFAULT_DRIVER = "ODBC Driver 17 for SQL Server"


@dataclass
class DbConfig:
    server: str = DEFAULT_SERVER
    database: str = DEFAULT_DATABASE
    driver: str = DEFAULT_DRIVER
    trusted_connection: bool = True
    username: str = ""
    password: str = ""

    def connection_string(self) -> str:
        base = [
            f"DRIVER={{{self.driver}}}",
            f"SERVER={self.server}",
            f"DATABASE={self.database}",
        ]
        if self.trusted_connection:
            base.append("Trusted_Connection=yes")
        else:
            base.append(f"UID={self.username}")
            base.append(f"PWD={self.password}")
        return ";".join(base) + ";"


class DatabaseManager:
    def __init__(self, config: Optional[DbConfig] = None):
        self.config = config or DbConfig()
        self.connection: Optional[pyodbc.Connection] = None

    def connect(self):
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
           CAST(AVG(CASE
               WHEN dp.tipo_proceso = 'Preparacion' THEN pm.costo_tonelada_usd
               ELSE NULL
           END) AS DECIMAL(18,2)) AS costo_promedio_preparacion,
           CAST(AVG(CASE
               WHEN dp.tipo_proceso = 'Extraccion' THEN em.costo_operacion_usd
               ELSE NULL
           END) AS DECIMAL(18,2)) AS costo_promedio_extraccion,
           CAST(AVG(CASE
               WHEN dp.tipo_proceso = 'Refinacion' THEN rm.costo_total_usd
               ELSE NULL
           END) AS DECIMAL(18,2)) AS costo_promedio_refinacion
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


class KpiCard(QGroupBox):
    def __init__(self, title: str):
        super().__init__(title)
        self.value_label = QLabel("--")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("font-size: 24px; font-weight: bold; padding: 12px;")
        layout = QVBoxLayout()
        layout.addWidget(self.value_label)
        self.setLayout(layout)

    def set_value(self, value: str):
        self.value_label.setText(value)


class TablePanel(QWidget):
    def __init__(self, title: str):
        super().__init__()
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.table = QTableWidget()
        self.export_button = QPushButton("Exportar a CSV")

        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addWidget(self.table)
        layout.addWidget(self.export_button, alignment=Qt.AlignRight)
        self.setLayout(layout)

        self.current_df = pd.DataFrame()
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

        self.kpi_toneladas = KpiCard("Toneladas totales")
        self.kpi_costo = KpiCard("Costo total estimado")
        self.kpi_consumo = KpiCard("Consumo energético total")

        self.toneladas_panel = TablePanel("Toneladas por etapa")
        self.alertas_panel = TablePanel("Alertas de calidad de datos")

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.kpi_toneladas)
        top_layout.addWidget(self.kpi_costo)
        top_layout.addWidget(self.kpi_consumo)

        splitter = QSplitter(Qt.Vertical)
        toneladas_container = QWidget()
        toneladas_layout = QVBoxLayout()
        toneladas_layout.addWidget(self.toneladas_panel)
        toneladas_container.setLayout(toneladas_layout)

        alertas_container = QWidget()
        alertas_layout = QVBoxLayout()
        alertas_layout.addWidget(self.alertas_panel)
        alertas_container.setLayout(alertas_layout)

        splitter.addWidget(toneladas_container)
        splitter.addWidget(alertas_container)
        splitter.setSizes([350, 250])

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def refresh(self):
        total_ton = self.db.query_df(QueryLibrary.KPI_TOTAL_TONELADAS)
        total_cost = self.db.query_df(QueryLibrary.KPI_COSTO_TOTAL)
        total_cons = self.db.query_df(QueryLibrary.KPI_CONSUMO_TOTAL)
        toneladas = self.db.query_df(QueryLibrary.QUERY_TONELADAS_POR_ETAPA)
        alertas = self.db.query_df(QueryLibrary.QUERY_ALERTAS)

        self.kpi_toneladas.set_value(str(total_ton.iloc[0, 0]))
        self.kpi_costo.set_value(f"USD {total_cost.iloc[0, 0]}")
        self.kpi_consumo.set_value(str(total_cons.iloc[0, 0]))
        self.toneladas_panel.load_dataframe(toneladas)
        self.alertas_panel.load_dataframe(alertas)


class ConnectionPanel(QGroupBox):
    def __init__(self, db: DatabaseManager, on_connected):
        super().__init__("Conexión a SQL Server")
        self.db = db
        self.on_connected = on_connected

        self.server_input = QLineEdit(self.db.config.server)
        self.database_input = QLineEdit(self.db.config.database)
        self.driver_input = QLineEdit(self.db.config.driver)
        self.test_button = QPushButton("Probar conexión")
        self.connect_button = QPushButton("Conectar")

        form = QFormLayout()
        form.addRow("Servidor", self.server_input)
        form.addRow("Base de datos", self.database_input)
        form.addRow("Driver ODBC", self.driver_input)

        actions = QHBoxLayout()
        actions.addWidget(self.test_button)
        actions.addWidget(self.connect_button)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(actions)
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
            QMessageBox.information(self, "Conectado", "Conexión establecida correctamente.")
            self.on_connected()
        except Exception as exc:
            QMessageBox.critical(self, "Error de conexión", str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1400, 850)

        self.db = DatabaseManager()
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.connection_panel = ConnectionPanel(self.db, self.after_connect)
        self.dashboard_page = DashboardPage(self.db)
        self.sql_console = SqlConsole(self.db)
        self.costos_panel = TablePanel("Costos promedio por proceso")

        self.tabs = QTabWidget()
        self.tabs.addTab(self.dashboard_page, "Dashboard")
        self.tabs.addTab(self.costos_panel, "Indicadores")
        self.tabs.addTab(self.sql_console, "Consultas SQL")

        container = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.connection_panel)
        layout.addWidget(self.tabs)
        container.setLayout(layout)
        self.setCentralWidget(container)

        self._build_menu()
        self.status_bar.showMessage("Listo para conectar.")

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
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
