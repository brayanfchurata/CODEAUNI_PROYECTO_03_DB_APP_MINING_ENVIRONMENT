import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class DataTable(QWidget):
    def __init__(self, title: str):
        super().__init__()

        self.current_df = pd.DataFrame()

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            "font-size: 16px; font-weight: 800; color: #f8fafc;"
        )

        self.table = QTableWidget()
        self.export_button = QPushButton("Exportar CSV")

        header_layout = QHBoxLayout()
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.export_button)

        layout = QVBoxLayout()
        layout.addLayout(header_layout)
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

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar CSV",
            "reporte.csv",
            "CSV (*.csv)"
        )

        if not path:
            return

        self.current_df.to_csv(path, index=False, encoding="utf-8-sig")
        QMessageBox.information(self, "Exportado", f"Archivo guardado en:\n{path}")