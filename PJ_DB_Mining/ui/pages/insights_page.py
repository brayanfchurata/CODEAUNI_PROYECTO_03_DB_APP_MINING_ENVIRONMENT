from PySide6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget

from services.insight_service import InsightService


class InsightsPage(QWidget):
    def __init__(self, insight_service: InsightService):
        super().__init__()
        self.insight_service = insight_service

        self.title_label = QLabel("Insights automáticos")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addWidget(self.text_area)
        self.setLayout(layout)

    def refresh(self) -> None:
        insights = self.insight_service.build_insights()
        contenido = "\n\n".join([f"- {item}" for item in insights])
        self.text_area.setPlainText(contenido)