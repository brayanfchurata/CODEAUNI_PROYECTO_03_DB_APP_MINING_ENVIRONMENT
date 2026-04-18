from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from services.import_service import ImportService
from ui.widgets.data_table import DataTable


class ImportPage(QWidget):
    def __init__(self, import_service: ImportService, on_import_finished=None):
        super().__init__()
        self.import_service = import_service
        self.on_import_finished = on_import_finished

        self.file_input = QLineEdit()
        self.file_input.setReadOnly(True)

        self.browse_button = QPushButton("Seleccionar CSV")
        self.table_combo = QComboBox()
        self.table_combo.addItems(self.import_service.get_supported_tables())

        self.preview_button = QPushButton("Vista previa")
        self.import_button = QPushButton("Importar a SQL Server")

        self.info_label = QLabel(
            "Selecciona un archivo CSV, revisa la vista previa y luego impórtalo a la tabla destino."
        )
        self.info_label.setStyleSheet("color: #94a3b8;")

        self.preview_table = DataTable("Vista previa del CSV")

        file_row = QHBoxLayout()
        file_row.addWidget(self.file_input)
        file_row.addWidget(self.browse_button)

        form = QFormLayout()
        form.addRow("Archivo CSV", file_row)
        form.addRow("Tabla destino", self.table_combo)

        actions = QHBoxLayout()
        actions.addWidget(self.preview_button)
        actions.addWidget(self.import_button)
        actions.addStretch()

        layout = QVBoxLayout()
        layout.addWidget(self.info_label)
        layout.addLayout(form)
        layout.addLayout(actions)
        layout.addWidget(self.preview_table)
        self.setLayout(layout)

        self.browse_button.clicked.connect(self.select_csv)
        self.preview_button.clicked.connect(self.load_preview)
        self.import_button.clicked.connect(self.import_csv)

    def select_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar CSV",
            "",
            "CSV (*.csv)"
        )
        if path:
            self.file_input.setText(path)

    def load_preview(self):
        try:
            path = self.file_input.text().strip()
            if not path:
                raise ValueError("Selecciona primero un archivo CSV.")

            df = self.import_service.read_csv_preview(path)
            self.preview_table.load_dataframe(df)
        except Exception as exc:
            QMessageBox.critical(self, "Error de lectura", str(exc))

    def import_csv(self):
        try:
            path = self.file_input.text().strip()
            if not path:
                raise ValueError("Selecciona primero un archivo CSV.")

            table_name = self.table_combo.currentText()
            total = self.import_service.import_csv_to_table(path, table_name)

            QMessageBox.information(
                self,
                "Importación exitosa",
                f"Se importaron {total} registros en {table_name}."
            )

            if self.on_import_finished:
                self.on_import_finished()

        except Exception as exc:
            QMessageBox.critical(self, "Error al importar", str(exc))