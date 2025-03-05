from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QLabel, QPushButton, QSizePolicy
from PyQt6.QtCore import Qt
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Three Panel Layout")
        self.setGeometry(100, 100, 1200, 800)

        # Create Toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        # Create main widget and layout
        main_widget = QWidget()
        self.main_layout = QHBoxLayout()
        main_widget.setLayout(self.main_layout)
        self.setCentralWidget(main_widget)

        # Left Panel (Session Panel)
        self.session_panel = QLabel("Session Panel", self)
        self.session_panel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.session_panel.setStyleSheet("background-color: lightgray;")
        self.session_panel.setFixedWidth(250)

        # Middle Panel (Video Panel)
        self.video_panel = QLabel("Video Panel", self)
        self.video_panel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_panel.setStyleSheet("background-color: white;")

        # Right Panel (AOI Panel)
        self.aoi_panel = QLabel("AOI Panel", self)
        self.aoi_panel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.aoi_panel.setStyleSheet("background-color: lightgray;")
        self.aoi_panel.setFixedWidth(250)

        # Add widgets to layout
        self.main_layout.addWidget(self.session_panel)
        self.main_layout.addWidget(self.video_panel, 3)  # Middle panel takes more space
        self.main_layout.addWidget(self.aoi_panel)

        # Add buttons to the toolbar
        toggle_sessions_btn = QPushButton("Toggle Sessions")
        toggle_sessions_btn.clicked.connect(self.toggle_session_panel)

        toggle_aois_btn = QPushButton("Toggle AOIs")
        toggle_aois_btn.clicked.connect(self.toggle_aoi_panel)

        toolbar.addWidget(toggle_sessions_btn)
        toolbar.addWidget(toggle_aois_btn)

    def toggle_session_panel(self):
        if self.session_panel.isVisible():
            self.session_panel.hide()
        else:
            self.session_panel.show()
        self.adjust_layout()

    def toggle_aoi_panel(self):
        if self.aoi_panel.isVisible():
            self.aoi_panel.hide()
        else:
            self.aoi_panel.show()
        self.adjust_layout()

    def adjust_layout(self):
        if not self.session_panel.isVisible() and not self.aoi_panel.isVisible():
            self.video_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        else:
            self.video_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.video_panel.update()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
