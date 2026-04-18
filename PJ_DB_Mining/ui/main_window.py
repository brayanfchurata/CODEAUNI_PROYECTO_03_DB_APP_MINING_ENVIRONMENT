from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from config.settings import SettingsManager
from database.connection import DatabaseManager
from database.queries import QueryLibrary
from services.import_service import ImportService
from ui.pages.dashboard_page import DashboardPage
from ui.pages.import_page import ImportPage
from ui.pages.sql_console_page import SqlConsolePage
from ui.widgets.data_table import DataTable


class HeaderCard(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("headerCard")
        self.setStyleSheet(
            """
            QWidget#headerCard {
                background-color: #111827;
                border: 1px solid #334155;
                border-radius: 16px;
            }
            """
        )

        title = QLabel("Mineria Intelligence Suite")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #f8fafc;")

        subtitle = QLabel(
            "Dashboard ejecutivo, calidad de datos, importación de CSV y operación SQL sobre procesos mineros."
        )
        subtitle.setStyleSheet("font-size: 12px; color: #94a3b8;")

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        self.setLayout(layout)


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
        self.save_button = QPushButton("Guardar configuración")

        form = QFormLayout()
        form.addRow("Servidor", self.server_input)
        form.addRow("Base de datos", self.database_input)
        form.addRow("Driver ODBC", self.driver_input)

        actions = QHBoxLayout()
        actions.addWidget(self.test_button)
        actions.addWidget(self.connect_button)
        actions.addWidget(self.save_button)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(actions)
        self.setLayout(layout)

        self.test_button.clicked.connect(self.test_connection)
        self.connect_button.clicked.connect(self.connect_db)
        self.save_button.clicked.connect(self.save_config)

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

    def save_config(self):
        try:
            self._sync_config()
            SettingsManager.save(self.db.config)
            QMessageBox.information(self, "Configuración", "Configuración guardada correctamente.")
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Mineria Intelligence Suite")
        self.resize(1600, 950)

        self.db = DatabaseManager(SettingsManager.load())
        self.import_service = ImportService(self.db)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.header_card = HeaderCard()
        self.connection_panel = ConnectionPanel(self.db, self.after_connect)

        self.dashboard_page = DashboardPage(self.db)
        self.sql_console = SqlConsolePage(self.db)
        self.costos_panel = DataTable("Costos promedio por proceso")
        self.import_page = ImportPage(self.import_service, self.refresh_all)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.dashboard_page, "Dashboard Ejecutivo")
        self.tabs.addTab(self.costos_panel, "Indicadores")
        self.tabs.addTab(self.import_page, "Importar CSV")
        self.tabs.addTab(self.sql_console, "Consultas SQL")

        container = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.header_card)
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