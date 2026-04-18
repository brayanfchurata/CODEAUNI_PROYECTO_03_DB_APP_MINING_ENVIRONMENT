from PySide6.QtWidgets import QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget

from database.connection import DatabaseManager
from ui.widgets.data_table import DataTable


class SqlConsolePage(QWidget):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db

        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Escribe una consulta SQL aquí...")

        self.run_button = QPushButton("Ejecutar SQL")
        self.result_table = DataTable("Resultado de la consulta")

        layout = QVBoxLayout()
        layout.addWidget(self.editor)
        layout.addWidget(self.run_button)
        layout.addWidget(self.result_table)
        self.setLayout(layout)

        self.run_button.clicked.connect(self.run_sql)

    def run_sql(self) -> None:
        sql = self.editor.toPlainText().strip()

        if not sql:
            QMessageBox.warning(self, "Consulta vacía", "Escribe una consulta SQL primero.")
            return

        try:
            df = self.db.query_df(sql)
            self.result_table.load_dataframe(df)
        except Exception as exc:
            QMessageBox.critical(self, "Error SQL", str(exc))