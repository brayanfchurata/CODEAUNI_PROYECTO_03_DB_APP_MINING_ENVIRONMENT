from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QPushButton,
    QHBoxLayout,
    QWidget,
)


class FilterBar(QGroupBox):
    def __init__(self, title: str = "Filtros"):
        super().__init__(title)

        self.etapa_combo = QComboBox()
        self.etapa_combo.addItems(["Todas", "Preparacion", "Extraccion", "Refinacion"])

        self.proceso_combo = QComboBox()
        self.proceso_combo.addItem("Todos")

        self.apply_button = QPushButton("Aplicar filtros")
        self.clear_button = QPushButton("Limpiar")

        form = QFormLayout()
        form.addRow("Etapa", self.etapa_combo)
        form.addRow("Proceso", self.proceso_combo)

        buttons = QHBoxLayout()
        buttons.addWidget(self.apply_button)
        buttons.addWidget(self.clear_button)

        layout = QFormLayout()
        container = QWidget()
        container_layout = QHBoxLayout()
        container_layout.addLayout(form)
        container_layout.addLayout(buttons)
        container.setLayout(container_layout)

        wrapper = QHBoxLayout()
        wrapper.addWidget(container)
        self.setLayout(wrapper)

        self.clear_button.clicked.connect(self.reset_filters)

    def reset_filters(self):
        self.etapa_combo.setCurrentText("Todas")
        self.proceso_combo.setCurrentText("Todos")

    def current_filters(self) -> dict:
        return {
            "etapa": self.etapa_combo.currentText(),
            "proceso": self.proceso_combo.currentText(),
        }

    def set_processes(self, processes: list[str]):
        current = self.proceso_combo.currentText()

        self.proceso_combo.blockSignals(True)
        self.proceso_combo.clear()
        self.proceso_combo.addItem("Todos")

        for process in processes:
            self.proceso_combo.addItem(process)

        index = self.proceso_combo.findText(current)
        self.proceso_combo.setCurrentIndex(index if index >= 0 else 0)
        self.proceso_combo.blockSignals(False)