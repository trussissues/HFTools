import os
import csv
import sys

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QToolBar, QLabel, QPushButton,
                             QSizePolicy, QFileDialog, QSlider, QInputDialog)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget

# Helper function to format time in hh:mm:ss.mmm
def format_time(ms: int) -> str:
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    millis = ms % 1000
    return f"{hours:02}:{minutes:02}:{seconds:02}.{millis:03}"  # hh:mm:ss.mmm

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Three Panel Layout")
        self.setGeometry(100, 100, 1200, 800)

        # Ensure "KeyFramer Sessions" folder exists
        self.sessions_folder = os.path.join(os.getcwd(), "KeyFramer Sessions")
        os.makedirs(self.sessions_folder, exist_ok=True)

        # Create Toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        # Create main widget and layout
        main_widget = QWidget()
        self.main_layout = QHBoxLayout()
        main_widget.setLayout(self.main_layout)
        self.setCentralWidget(main_widget)

        # Left Panel (Session Panel)
        self.session_panel_widget = QWidget()
        self.session_panel_widget.setStyleSheet("background-color: lightgray;")
        self.session_panel_widget.setFixedWidth(250)
        self.session_panel_layout = QVBoxLayout()
        self.session_panel_widget.setLayout(self.session_panel_layout)

        # Label at top of session panel
        self.session_panel_label = QLabel("Session Panel", self)
        self.session_panel_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.session_panel_layout.addWidget(self.session_panel_label)

        # Spacer in middle
        self.session_panel_layout.addStretch()

        # Create Session button at bottom
        self.create_session_button = QPushButton("Create Session")
        self.create_session_button.clicked.connect(self.create_session)
        self.session_panel_layout.addWidget(self.create_session_button)

        # Middle Panel (Video Panel)
        self.video_panel = QWidget()
        self.video_layout = QVBoxLayout()
        self.video_panel.setLayout(self.video_layout)

        self.player_widget = QVideoWidget(self)
        self.player_widget.setSizePolicy(QSizePolicy.Policy.Expanding,
                                         QSizePolicy.Policy.Expanding)

        # Timeline with playhead
        self.timeline_layout = QVBoxLayout()
        self.timeline_widget = QWidget()
        self.timeline_widget.setLayout(self.timeline_layout)

        self.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.setRange(0, 100)
        self.timeline_slider.sliderMoved.connect(self.set_position)

        # Time and frame display
        self.time_label = QLabel("00:00:00.000 | Frame: 0", self)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Controls above time_label: one frame before, pause/unpause, one frame later
        self.controls_widget = QWidget()
        self.controls_layout = QHBoxLayout()
        self.controls_widget.setLayout(self.controls_layout)

        self.one_frame_before_button = QPushButton("One Frame Before")
        self.one_frame_before_button.clicked.connect(self.step_frame_before)

        self.pause_button = QPushButton("Pause")  # will toggle
        self.pause_button.clicked.connect(self.toggle_pause)

        self.one_frame_after_button = QPushButton("One Frame Later")
        self.one_frame_after_button.clicked.connect(self.step_frame_after)

        self.controls_layout.addWidget(self.one_frame_before_button)
        self.controls_layout.addWidget(self.pause_button)
        self.controls_layout.addWidget(self.one_frame_after_button)

        self.timeline_layout.addWidget(self.controls_widget)
        self.timeline_layout.addWidget(self.timeline_slider)
        self.timeline_layout.addWidget(self.time_label)

        self.video_layout.addWidget(self.player_widget, 7)
        self.video_layout.addWidget(self.timeline_widget, 3)

        # Video Player
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.player_widget)
        self.media_player.positionChanged.connect(self.update_slider)
        self.media_player.positionChanged.connect(self.update_time_label)
        self.media_player.durationChanged.connect(self.set_slider_range)
        self.media_player.playbackStateChanged.connect(self.playback_state_changed)

        # Right Panel (AOI Panel)
        self.aoi_panel = QLabel("AOI Panel", self)
        self.aoi_panel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.aoi_panel.setStyleSheet("background-color: lightgray;")
        self.aoi_panel.setFixedWidth(250)

        # Add widgets to layout
        self.main_layout.addWidget(self.session_panel_widget)
        self.main_layout.addWidget(self.video_panel, 3)
        self.main_layout.addWidget(self.aoi_panel)

        # Add buttons to the toolbar
        open_video_btn = QPushButton("Open Video")
        open_video_btn.clicked.connect(self.open_video)

        toggle_sessions_btn = QPushButton("Toggle Sessions")
        toggle_sessions_btn.clicked.connect(self.toggle_session_panel)

        toggle_aois_btn = QPushButton("Toggle AOIs")
        toggle_aois_btn.clicked.connect(self.toggle_aoi_panel)

        toolbar.addWidget(open_video_btn)
        toolbar.addWidget(toggle_sessions_btn)
        toolbar.addWidget(toggle_aois_btn)

    def create_session(self):
        # Prompt user for session name
        session_name, ok = QInputDialog.getText(self, "Create Session", "Enter session name:")
        if ok and session_name.strip():
            # Create a CSV file under KeyFramer Sessions with table heads
            csv_path = os.path.join(self.sessions_folder, f"{session_name.strip()}.csv")
            # Write headers if file doesn't exist
            if not os.path.exists(csv_path):
                with open(csv_path, "w", newline="") as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerow(["AOI", "In Time", "Duration", "Out Time"])

    def open_video(self):
        file_dialog = QFileDialog()
        video_path, _ = file_dialog.getOpenFileName(
            self, "Open Video File", "", "Videos (*.mp4 *.avi *.mov *.mkv)")
        if video_path:
            self.media_player.setSource(QUrl.fromLocalFile(video_path))
            self.media_player.play()

    def set_position(self, position):
        self.media_player.setPosition(position)

    def update_slider(self, position):
        self.timeline_slider.setValue(position)

    def update_time_label(self, position):
        time_text = format_time(position)
        # This is a naive frame calculation that assumes ~30 fps.
        # A more robust method would involve analyzing the actual frame rate.
        frame_num = position // 33
        self.time_label.setText(f"{time_text} | Frame: {frame_num}")

    def set_slider_range(self, duration):
        self.timeline_slider.setRange(0, duration)

    def playback_state_changed(self, state):
        # If paused, show frame step buttons
        # If playing, hide them
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.pause_button.setText("Pause")
            self.one_frame_before_button.hide()
            self.one_frame_after_button.hide()
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.pause_button.setText("Unpause")
            self.one_frame_before_button.show()
            self.one_frame_after_button.show()
        else: # StoppedState
            self.pause_button.setText("Pause")
            self.one_frame_before_button.hide()
            self.one_frame_after_button.hide()

    def toggle_pause(self):
        # If playing, pause
        # If paused, unpause
        state = self.media_player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.media_player.play()
        else: # StoppedState
            # let's just start playing
            self.media_player.play()

    def step_frame_before(self):
        # Move ~1 frame back, assume ~30 FPS => 33ms per frame
        pos = self.media_player.position()
        new_pos = max(0, pos - 33)
        self.media_player.setPosition(new_pos)

    def step_frame_after(self):
        # Move ~1 frame forward, assume ~30 FPS => 33ms per frame
        pos = self.media_player.position()
        new_pos = min(self.media_player.duration(), pos + 33)
        self.media_player.setPosition(new_pos)

    def toggle_session_panel(self):
        if self.session_panel_widget.isVisible():
            self.session_panel_widget.hide()
        else:
            self.session_panel_widget.show()
        self.adjust_layout()

    def toggle_aoi_panel(self):
        if self.aoi_panel.isVisible():
            self.aoi_panel.hide()
        else:
            self.aoi_panel.show()
        self.adjust_layout()

    def adjust_layout(self):
        if not self.session_panel_widget.isVisible() and not self.aoi_panel.isVisible():
            self.video_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        else:
            self.video_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.video_panel.update()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
