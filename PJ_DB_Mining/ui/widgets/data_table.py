import pandas as pd
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)


class DataTable(QWidget):
    def __init__(self, title: str):
        super().__init__()
        self.current_df = pd.DataFrame()

        self.container = QFrame()
        self.container.setObjectName("panelCard")

        self.title_label = QLabel(title)
        self.title_label.setObjectName("panelTitle")

        self.subtitle_label = QLabel("Visualización tabular y exportación")
        self.subtitle_label.setObjectName("panelSubtitle")

        self.export_button = QPushButton("Exportar CSV")

        left_header = QVBoxLayout()
        left_header.setSpacing(2)
        left_header.addWidget(self.title_label)
        left_header.addWidget(self.subtitle_label)

        header_layout = QHBoxLayout()
        header_layout.addLayout(left_header)
        header_layout.addStretch()
        header_layout.addWidget(self.export_button)

        self.table = QTableWidget()
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(False)

        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(16, 16, 16, 16)
        container_layout.setSpacing(12)
        container_layout.addLayout(header_layout)
        container_layout.addWidget(self.table)
        self.container.setLayout(container_layout)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.container)
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