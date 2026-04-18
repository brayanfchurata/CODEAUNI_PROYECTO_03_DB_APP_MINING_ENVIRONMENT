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


class BrandPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("brandPanel")

        app_name = QLabel("Mineria Intelligence Suite")
        app_name.setObjectName("brandTitle")

        app_subtitle = QLabel(
            "Software de analítica minera para carga, control de calidad, consultas SQL y reportes."
        )
        app_subtitle.setObjectName("brandSubtitle")
        app_subtitle.setWordWrap(True)

        app_context = QLabel("Preparación · Extracción · Refinación")
        app_context.setObjectName("brandContext")

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        layout.addWidget(app_name)
        layout.addWidget(app_subtitle)
        layout.addWidget(app_context)
        self.setLayout(layout)


class SidebarNavButton(QPushButton):
    def __init__(self, text: str):
        super().__init__(text)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(46)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setObjectName("sidebarNavButton")


class ConnectionFooterCard(QFrame):
    def __init__(self, db: DatabaseManager, on_connected):
        super().__init__()
        self.db = db
        self.on_connected = on_connected
        self.setObjectName("connectionFooterCard")

        title = QLabel("Conexión SQL Server")
        title.setObjectName("connectionCardTitle")

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

        actions = QHBoxLayout()
        actions.setSpacing(8)
        actions.addWidget(self.test_button)
        actions.addWidget(self.connect_button)
        actions.addWidget(self.save_button)

        layout = QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        layout.addWidget(title)
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


class Sidebar(QWidget):
    def __init__(self, db: DatabaseManager, on_connected):
        super().__init__()
        self.setObjectName("sidebar")

        self.brand_panel = BrandPanel()

        self.section_label = QLabel("Módulos")
        self.section_label.setObjectName("sidebarSectionLabel")

        self.btn_dashboard = SidebarNavButton("Dashboard Ejecutivo")
        self.btn_indicadores = SidebarNavButton("Indicadores")
        self.btn_calidad = SidebarNavButton("Calidad")
        self.btn_insights = SidebarNavButton("Insights")
        self.btn_reportes = SidebarNavButton("Reportes")
        self.btn_importar = SidebarNavButton("Importar CSV")
        self.btn_sql = SidebarNavButton("Consultas SQL")

        self.buttons = [
            self.btn_dashboard,
            self.btn_indicadores,
            self.btn_calidad,
            self.btn_insights,
            self.btn_reportes,
            self.btn_importar,
            self.btn_sql,
        ]

        self.connection_card = ConnectionFooterCard(db, on_connected)

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        layout.addWidget(self.brand_panel)
        layout.addWidget(self.section_label)

        for button in self.buttons:
            layout.addWidget(button)

        layout.addStretch()
        layout.addWidget(self.connection_card)
        self.setLayout(layout)

    def set_active(self, target_button: QPushButton):
        for button in self.buttons:
            button.setChecked(button is target_button)


class ContentHeader(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("contentHeader")

        self.title_label = QLabel("Dashboard Ejecutivo")
        self.title_label.setObjectName("contentHeaderTitle")

        self.subtitle_label = QLabel(
            "Vista consolidada para monitorear producción, costos, consumo y calidad."
        )
        self.subtitle_label.setObjectName("contentHeaderSubtitle")
        self.subtitle_label.setWordWrap(True)

        self.status_pill = QLabel("Sin conexión")
        self.status_pill.setObjectName("contentStatusPill")
        self.status_pill.setAlignment(Qt.AlignCenter)

        left_layout = QVBoxLayout()
        left_layout.setSpacing(4)
        left_layout.addWidget(self.title_label)
        left_layout.addWidget(self.subtitle_label)

        layout = QHBoxLayout()
        layout.setContentsMargins(18, 14, 18, 14)
        layout.addLayout(left_layout)
        layout.addStretch()
        layout.addWidget(self.status_pill)
        self.setLayout(layout)

    def set_page_info(self, title: str, subtitle: str):
        self.title_label.setText(title)
        self.subtitle_label.setText(subtitle)

    def set_connection_status(self, connected: bool, server: str = "", database: str = ""):
        if connected:
            self.status_pill.setText(f"Conectado: {server} / {database}")
            self.status_pill.setProperty("connected", True)
        else:
            self.status_pill.setText("Sin conexión")
            self.status_pill.setProperty("connected", False)

        self.style().unpolish(self.status_pill)
        self.style().polish(self.status_pill)
        self.status_pill.update()


class MainWindow(QMainWindow):
    PAGE_METADATA = {
        0: (
            "Dashboard Ejecutivo",
            "Vista consolidada para monitorear producción, costos, consumo y calidad."
        ),
        1: (
            "Indicadores",
            "Explora tablas de soporte y métricas analíticas derivadas del modelo de datos."
        ),
        2: (
            "Calidad",
            "Revisa reglas, alertas y anomalías detectadas en los datos cargados."
        ),
        3: (
            "Insights",
            "Hallazgos clave y lectura ejecutiva de los resultados obtenidos."
        ),
        4: (
            "Reportes",
            "Generación y exportación de resultados para evidencia y entrega final."
        ),
        5: (
            "Importar CSV",
            "Carga archivos fuente hacia SQL Server y valida el proceso de importación."
        ),
        6: (
            "Consultas SQL",
            "Ejecuta consultas personalizadas sobre la base de datos del proyecto."
        ),
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mineria Intelligence Suite")
        self.resize(1720, 980)

        self.db = DatabaseManager(SettingsManager.load())
        self.repository = MiningRepository(self.db)

        self.analytics_service = AnalyticsService(self.repository)
        self.quality_service = QualityService(self.repository)
        self.insight_service = InsightService(self.repository)
        self.import_service = ImportService(self.db)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.sidebar = Sidebar(self.db, self.after_connect)
        self.content_header = ContentHeader()

        self.dashboard_page = DashboardPage(self.db)
        self.quality_page = QualityPage(self.quality_service)
        self.insights_page = InsightsPage(self.insight_service)
        self.reports_page = ReportsPage(self.analytics_service, self.quality_service)
        self.import_page = ImportPage(self.import_service, self.refresh_all)
        self.sql_console_page = SqlConsolePage(self.db)
        self.indicadores_page = DataTable("Costos promedio por proceso")

        self.stack = QStackedWidget()
        self.stack.addWidget(self.dashboard_page)      # 0
        self.stack.addWidget(self.indicadores_page)   # 1
        self.stack.addWidget(self.quality_page)       # 2
        self.stack.addWidget(self.insights_page)      # 3
        self.stack.addWidget(self.reports_page)       # 4
        self.stack.addWidget(self.import_page)        # 5
        self.stack.addWidget(self.sql_console_page)   # 6

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
        self.content_header.set_page_info(*self.PAGE_METADATA[0])
        self.content_header.set_connection_status(False)

        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)
        right_layout.addWidget(self.content_header)
        right_layout.addWidget(self.stack)
        right_panel.setLayout(right_layout)

        central = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(14)
        main_layout.addWidget(self.sidebar, 0)
        main_layout.addWidget(right_panel, 1)
        central.setLayout(main_layout)

        self.setCentralWidget(central)
        self._build_menu()
        self.status_bar.showMessage("Listo para conectar.")

    def switch_page(self, index: int, button: QPushButton):
        self.stack.setCurrentIndex(index)
        self.sidebar.set_active(button)

        title, subtitle = self.PAGE_METADATA.get(index, ("Módulo", ""))
        self.content_header.set_page_info(title, subtitle)

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
        self.content_header.set_connection_status(
            True,
            self.db.config.server,
            self.db.config.database,
        )
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
            self.indicadores_page.load_dataframe(costos)

            self.status_bar.showMessage("Datos actualizados correctamente.")
        except Exception as exc:
            QMessageBox.critical(self, "Error al actualizar", str(exc))

    def disconnect(self):
        self.db.disconnect()
        self.content_header.set_connection_status(False)
        self.status_bar.showMessage("Desconectado.")