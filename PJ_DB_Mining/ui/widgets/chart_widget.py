from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import QVBoxLayout, QWidget


class ChartWidget(QWidget):
    def __init__(self, title: str = ""):
        super().__init__()
        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)
        self.title = title

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def clear_chart(self):
        self.figure.clear()
        self.canvas.draw()

    def plot_bar(self, labels, values, x_label="", y_label=""):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.bar(labels, values)
        ax.set_title(self.title)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.tick_params(axis="x", rotation=25)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        self.figure.tight_layout()
        self.canvas.draw()

    def plot_line(self, labels, values, x_label="", y_label=""):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(labels, values, marker="o")
        ax.set_title(self.title)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.tick_params(axis="x", rotation=25)
        ax.grid(True, linestyle="--", alpha=0.4)
        self.figure.tight_layout()
        self.canvas.draw()