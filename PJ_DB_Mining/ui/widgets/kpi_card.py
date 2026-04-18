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
                border: 1px solid #1f2937;
                border-left: 5px solid {accent_color};
                border-radius: 18px;
            }}
            """
        )

        self.title_label = QLabel(title)
        self.title_label.setObjectName("kpiTitle")
        self.title_label.setWordWrap(True)

        self.value_label = QLabel("--")
        self.value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.value_label.setObjectName("kpiValue")

        self.footer_label = QLabel("Indicador actualizado")
        self.footer_label.setObjectName("kpiFooter")

        layout = QVBoxLayout()
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)
        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.value_label)
        layout.addWidget(self.footer_label)
        self.setLayout(layout)

    def set_value(self, value: str):
        self.value_label.setText(value)