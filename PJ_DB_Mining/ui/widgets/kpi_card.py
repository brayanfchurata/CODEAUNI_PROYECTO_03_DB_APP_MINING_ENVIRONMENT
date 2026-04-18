from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class KpiCard(QFrame):
    def __init__(self, title: str, accent_color: str = "#2563eb"):
        super().__init__()

        self.setObjectName("kpiCard")
        self.setStyleSheet(
            f"""
            QFrame#kpiCard {{
                background-color: #111827;
                border: 1px solid #334155;
                border-left: 5px solid {accent_color};
                border-radius: 14px;
            }}
            """
        )

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            "font-size: 12px; color: #94a3b8; font-weight: 700;"
        )

        self.value_label = QLabel("--")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet(
            "font-size: 28px; font-weight: 800; color: #f8fafc; padding: 10px;"
        )

        self.footer_label = QLabel("Indicador actualizado")
        self.footer_label.setStyleSheet(
            "font-size: 11px; color: #64748b;"
        )

        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.footer_label)
        self.setLayout(layout)

    def set_value(self, value: str):
        self.value_label.setText(value)