from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from config.settings import SettingsManager
from database.connection import DatabaseManager
from database.queries import QueryLibrary
from database.repository import MiningRepository
from services.analytics_service import AnalyticsService
from services.import_service import ImportService
from services.insight_service import InsightService
from services.quality_service import QualityService
from ui.pages.dashboard_page import DashboardPage
from ui.pages.import_page import ImportPage
from ui.pages.insights_page import InsightsPage
from ui.pages.quality_page import QualityPage
from ui.pages.reports_page import ReportsPage
from ui.pages.sql_console_page import SqlConsolePage
from ui.widgets.data_table import DataTable


class HeaderBar(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("topBar")

        title = QLabel("Mineria Intelligence Suite")
        title.setObjectName("topBarTitle")

        subtitle = QLabel(
            "Sistema de análisis para preparación, extracción y refinación."
        )
        subtitle.setObjectName("topBarSubtitle")

        layout = QVBoxLayout()
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(2)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        self.setLayout(layout)


class CompactConnectionCard(QFrame):
    def __init__(self, db: DatabaseManager, on_connected):
        super().__init__()
        self.db = db
        self.on_connected = on_connected
        self.setObjectName("connectionCard")

        title = QLabel("Conexión")
        title.setObjectName("connectionTitle")

        self.server_input = QLineEdit(self.db.config.server)
        self.database_input = QLineEdit(self.db.config.database)
        self.driver_input = QLineEdit(self.db.config.driver)

        self.test_button = QPushButton("Probar")
        self.connect_button = QPushButton("Conectar")
        self.save_button = QPushButton("Guardar")

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(8)
        form.addRow("Servidor", self.server_input)
        form.addRow("Base", self.database_input)
        form.addRow("Driver", self.driver_input)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        buttons.addWidget(self.test_button)
        buttons.addWidget(self.connect_button)
        buttons.addWidget(self.save_button)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        layout.addWidget(title)
        layout.addLayout(form)
        layout.addLayout(buttons)
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


class NavButton(QPushButton):
    def __init__(self, text: str):
        super().__init__(text)
        self.setCheckable(True)
        self.setMinimumHeight(44)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)


class Sidebar(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("sidebar")

        self.section_title = QLabel("Módulos")
        self.section_title.setObjectName("sidebarTitle")

        self.btn_dashboard = NavButton("Dashboard")
        self.btn_indicadores = NavButton("Indicadores")
        self.btn_calidad = NavButton("Calidad")
        self.btn_insights = NavButton("Insights")
        self.btn_reportes = NavButton("Reportes")
        self.btn_importar = NavButton("Importar CSV")
        self.btn_sql = NavButton("Consultas SQL")

        self.buttons = [
            self.btn_dashboard,
            self.btn_indicadores,
            self.btn_calidad,
            self.btn_insights,
            self.btn_reportes,
            self.btn_importar,
            self.btn_sql,
        ]

        layout = QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)
        layout.addWidget(self.section_title)
        layout.addSpacing(6)

        for button in self.buttons:
            layout.addWidget(button)

        layout.addStretch()
        self.setLayout(layout)

    def set_active(self, target_button: QPushButton):
        for button in self.buttons:
            button.setChecked(button is target_button)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Mineria Intelligence Suite")
        self.resize(1680, 980)

        self.db = DatabaseManager(SettingsManager.load())
        self.repository = MiningRepository(self.db)

        self.analytics_service = AnalyticsService(self.repository)
        self.quality_service = QualityService(self.repository)
        self.insight_service = InsightService(self.repository)
        self.import_service = ImportService(self.db)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.header_bar = HeaderBar()
        self.connection_card = CompactConnectionCard(self.db, self.after_connect)
        self.sidebar = Sidebar()

        self.dashboard_page = DashboardPage(self.db)
        self.quality_page = QualityPage(self.quality_service)
        self.insights_page = InsightsPage(self.insight_service)
        self.reports_page = ReportsPage(self.analytics_service, self.quality_service)
        self.import_page = ImportPage(self.import_service, self.refresh_all)
        self.sql_console = SqlConsolePage(self.db)
        self.costos_panel = DataTable("Costos promedio por proceso")

        self.stack = QStackedWidget()
        self.stack.addWidget(self.dashboard_page)   # 0
        self.stack.addWidget(self.costos_panel)     # 1
        self.stack.addWidget(self.quality_page)     # 2
        self.stack.addWidget(self.insights_page)    # 3
        self.stack.addWidget(self.reports_page)     # 4
        self.stack.addWidget(self.import_page)      # 5
        self.stack.addWidget(self.sql_console)      # 6

        self.sidebar.btn_dashboard.clicked.connect(
            lambda: self.switch_page(0, self.sidebar.btn_dashboard)
        )
        self.sidebar.btn_indicadores.clicked.connect(
            lambda: self.switch_page(1, self.sidebar.btn_indicadores)
        )
        self.sidebar.btn_calidad.clicked.connect(
            lambda: self.switch_page(2, self.sidebar.btn_calidad)
        )
        self.sidebar.btn_insights.clicked.connect(
            lambda: self.switch_page(3, self.sidebar.btn_insights)
        )
        self.sidebar.btn_reportes.clicked.connect(
            lambda: self.switch_page(4, self.sidebar.btn_reportes)
        )
        self.sidebar.btn_importar.clicked.connect(
            lambda: self.switch_page(5, self.sidebar.btn_importar)
        )
        self.sidebar.btn_sql.clicked.connect(
            lambda: self.switch_page(6, self.sidebar.btn_sql)
        )

        self.sidebar.set_active(self.sidebar.btn_dashboard)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(14)
        top_layout.addWidget(self.header_bar, 4)
        top_layout.addWidget(self.connection_card, 3)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(14)
        content_layout.addWidget(self.sidebar, 1)
        content_layout.addWidget(self.stack, 5)

        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)
        layout.addLayout(top_layout)
        layout.addLayout(content_layout)
        container.setLayout(layout)
        self.setCentralWidget(container)

        self._build_menu()
        self.status_bar.showMessage("Listo para conectar.")

    def switch_page(self, index: int, button: QPushButton):
        self.stack.setCurrentIndex(index)
        self.sidebar.set_active(button)

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
            self.quality_page.refresh()
            self.insights_page.refresh()
            self.reports_page.refresh()

            costos = self.db.query_df(QueryLibrary.QUERY_COSTO_PROMEDIO_PROCESO)
            self.costos_panel.load_dataframe(costos)

            self.status_bar.showMessage("Datos actualizados correctamente.")
        except Exception as exc:
            QMessageBox.critical(self, "Error al actualizar", str(exc))

    def disconnect(self):
        self.db.disconnect()
        self.status_bar.showMessage("Desconectado.")