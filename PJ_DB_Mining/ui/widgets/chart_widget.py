from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class ChartWidget(QFrame):
    def __init__(self, title: str = "", subtitle: str = ""):
        super().__init__()
        self.setObjectName("chartCard")

        self.title_label = QLabel(title)
        self.title_label.setObjectName("panelTitle")

        self.subtitle_label = QLabel(subtitle if subtitle else "Indicador visual")
        self.subtitle_label.setObjectName("panelSubtitle")

        self.figure = Figure(figsize=(5, 3.2), dpi=100)
        self.canvas = FigureCanvas(self.figure)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def _prepare_axes(self):
        self.figure.clear()
        self.figure.patch.set_facecolor("#111827")
        ax = self.figure.add_subplot(111)
        ax.set_facecolor("#111827")

        for spine in ax.spines.values():
            spine.set_color("#334155")

        ax.tick_params(colors="#cbd5e1")
        ax.xaxis.label.set_color("#e2e8f0")
        ax.yaxis.label.set_color("#e2e8f0")
        ax.title.set_color("#f8fafc")
        ax.grid(color="#334155", linestyle="--", alpha=0.30)

        return ax

    def clear_chart(self, message: str = "Sin datos disponibles"):
        ax = self._prepare_axes()
        ax.text(
            0.5, 0.5, message,
            ha="center", va="center",
            color="#94a3b8", fontsize=12,
            transform=ax.transAxes
        )
        ax.set_xticks([])
        ax.set_yticks([])
        self.figure.tight_layout()
        self.canvas.draw()

    def plot_bar(self, labels, values, x_label="", y_label=""):
        if not labels or not values:
            self.clear_chart()
            return

        ax = self._prepare_axes()
        ax.bar(labels, values, color="#3b82f6", edgecolor="#60a5fa")
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.tick_params(axis="x", rotation=20)
        self.figure.tight_layout()
        self.canvas.draw()

    def plot_horizontal_bar(self, labels, values, x_label="", y_label=""):
        if not labels or not values:
            self.clear_chart()
            return

        ax = self._prepare_axes()
        ax.barh(labels, values, color="#22c55e", edgecolor="#4ade80")
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        self.figure.tight_layout()
        self.canvas.draw()

    def plot_line(self, labels, values, x_label="", y_label=""):
        if not labels or not values:
            self.clear_chart()
            return

        ax = self._prepare_axes()
        ax.plot(labels, values, marker="o", linewidth=2, color="#f59e0b")
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.tick_params(axis="x", rotation=20)
        self.figure.tight_layout()
        self.canvas.draw()