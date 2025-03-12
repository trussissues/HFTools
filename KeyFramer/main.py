import os
import csv
import sys

import cv2  # For retrieving FPS

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QToolBar, QLabel, QPushButton,
    QSizePolicy, QFileDialog, QSlider, QInputDialog,
    QListWidget, QListWidgetItem, QMessageBox
)
from PyQt6.QtGui import QKeySequence
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget

# Helper function to format time in hh:mm:ss.mmm
# This uses ms-based timing, does not rely on frame rates.
def format_time(ms: int) -> str:
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    millis = ms % 1000
    return f"{hours:02}:{minutes:02}:{seconds:02}.{millis:03}"  # hh:mm:ss.mmm


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Four Panel Layout with AOI")
        self.setGeometry(100, 100, 1600, 1000)

        # Keep track of the currently loaded session data
        self.current_session_name = None
        self.current_session_data = []  # Will store CSV rows in memory if needed

        # Keep track of the currently loaded AOI
        self.current_AOI= None

        # Keep track of in/out points (in milliseconds)
        self.in_ms = None
        self.out_ms = None

        # Keep track of the video's actual FPS (retrieved via OpenCV)
        self.video_fps = None

        # Ensure "KeyFramer Sessions" folder exists
        self.sessions_folder = os.path.join(os.getcwd(), "KeyFramer Sessions")
        os.makedirs(self.sessions_folder, exist_ok=True)

        # AOI CSV file path
        self.aoi_file = os.path.join(self.sessions_folder, "AOI.csv")
        # If AOI.csv doesn't exist, create it
        if not os.path.exists(self.aoi_file):
            with open(self.aoi_file, "w", newline="") as f:
                pass  # create an empty file

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

        # Sessions list
        self.session_list_widget = QListWidget()
        # Use doubleClicked instead of itemClicked
        self.session_list_widget.itemDoubleClicked.connect(self.on_session_item_double_clicked)
        self.session_panel_layout.addWidget(self.session_list_widget)

        # Spacer
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
        self.player_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

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
        self.one_frame_before_button.setShortcut(QKeySequence.fromString("Left"))


        self.pause_button = QPushButton("Pause")  # will toggle
        self.pause_button.clicked.connect(self.toggle_pause)
        self.pause_button.setShortcut(QKeySequence.fromString("SPACE"))


        self.one_frame_after_button = QPushButton("One Frame Later")
        self.one_frame_after_button.clicked.connect(self.step_frame_after)
        self.one_frame_after_button.setShortcut(QKeySequence.fromString("Right"))

        self.controls_layout.addWidget(self.one_frame_before_button)
        self.controls_layout.addWidget(self.pause_button)
        self.controls_layout.addWidget(self.one_frame_after_button)

        self.timeline_layout.addWidget(self.controls_widget)
        self.timeline_layout.addWidget(self.timeline_slider)
        self.timeline_layout.addWidget(self.time_label)

        # New KeyFrame Buttons container
        self.keyframe_buttons_widget = QWidget()
        self.keyframe_buttons_layout = QHBoxLayout()
        self.keyframe_buttons_widget.setLayout(self.keyframe_buttons_layout)
        self.timeline_layout.addWidget(self.keyframe_buttons_widget)

        # Mark In Point
        self.mark_in_button = QPushButton("Mark In Point")
        self.mark_in_button.clicked.connect(self.mark_in_point)
        # Shortcut I
        self.mark_in_button.setShortcut(QKeySequence("I"))
        self.keyframe_buttons_layout.addWidget(self.mark_in_button)

        # Mark Out Point
        self.mark_out_button = QPushButton("Mark Out Point")
        self.mark_out_button.clicked.connect(self.mark_out_point)
        # Shortcut O
        self.mark_out_button.setShortcut(QKeySequence("O"))
        self.keyframe_buttons_layout.addWidget(self.mark_out_button)

        # Create KeyFrames
        self.create_keyframes_button = QPushButton("Create KeyFrames")
        # Shortcut Command+K on Mac, or Ctrl+K on other platforms
        if sys.platform == "darwin":
            self.create_keyframes_button.setShortcut(QKeySequence("Meta+K"))
        else:
            self.create_keyframes_button.setShortcut(QKeySequence("Ctrl+K"))

        self.create_keyframes_button.setEnabled(False)
        self.create_keyframes_button.clicked.connect(self.create_keyframes)
        self.keyframe_buttons_layout.addWidget(self.create_keyframes_button)

        # ADDED: In/Out labels + Duration label
        # We'll put them below the keyframe buttons
        self.in_label = QLabel("In Point: not set")
        self.in_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.out_label = QLabel("Out Point: not set")
        self.out_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.duration_label = QLabel("Duration: --")
        self.duration_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.timeline_layout.addWidget(self.in_label)
        self.timeline_layout.addWidget(self.out_label)
        self.timeline_layout.addWidget(self.duration_label)
        # END ADDED

        self.video_layout.addWidget(self.player_widget, 7)
        self.video_layout.addWidget(self.timeline_widget, 3)

        # Video Player
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.player_widget)
        self.media_player.positionChanged.connect(self.update_slider)
        self.media_player.positionChanged.connect(self.update_time_label)
        self.media_player.durationChanged.connect(self.set_slider_range)
        self.media_player.playbackStateChanged.connect(self.playback_state_changed)

        # AOI Panel
        self.aoi_panel_widget = QWidget()
        self.aoi_panel_widget.setStyleSheet("background-color: lightgray;")
        self.aoi_panel_widget.setFixedWidth(250)
        self.aoi_panel_layout = QVBoxLayout()
        self.aoi_panel_widget.setLayout(self.aoi_panel_layout)

        self.aoi_label = QLabel("AOI Panel", self)
        self.aoi_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.aoi_panel_layout.addWidget(self.aoi_label)

        self.aoi_list_widget = QListWidget()
        self.aoi_list_widget.itemDoubleClicked.connect(self.on_AOI_double_clicked)
        self.aoi_panel_layout.addWidget(self.aoi_list_widget)

        # Button to create AOI
        self.create_aoi_button = QPushButton("Create AOI")
        self.create_aoi_button.clicked.connect(self.create_aoi)
        self.aoi_panel_layout.addWidget(self.create_aoi_button)

        # KeyFrames Panel
        self.keyframes_panel = QLabel("KeyFrames Panel", self)
        self.keyframes_panel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.keyframes_panel.setStyleSheet("background-color: lightgray;")
        self.keyframes_panel.setFixedWidth(250)

        # Add widgets to layout
        self.main_layout.addWidget(self.session_panel_widget)
        self.main_layout.addWidget(self.video_panel, 3)
        self.main_layout.addWidget(self.aoi_panel_widget)
        self.main_layout.addWidget(self.keyframes_panel)

        # Add buttons to the toolbar
        open_video_btn = QPushButton("Open Video")
        open_video_btn.clicked.connect(self.open_video)

        toggle_sessions_btn = QPushButton("Toggle Sessions")
        toggle_sessions_btn.clicked.connect(self.toggle_session_panel)

        toggle_aois_btn = QPushButton("Toggle AOIs")
        toggle_aois_btn.clicked.connect(self.toggle_aoi_panel)

        toggle_keyframes_btn = QPushButton("Toggle KeyFrames")
        toggle_keyframes_btn.clicked.connect(self.toggle_keyframes_panel)

        toolbar.addWidget(open_video_btn)
        toolbar.addWidget(toggle_sessions_btn)
        toolbar.addWidget(toggle_aois_btn)
        toolbar.addWidget(toggle_keyframes_btn)

        # Refresh session list at startup
        self.refresh_session_list()

        # Also load the AOI list from AOI.csv
        self.load_aoi_list()


    #######################
    # AOI related methods #
    #######################
    def load_aoi_list(self):
        self.aoi_list_widget.clear()
        if not os.path.exists(self.aoi_file):
            return
        with open(self.aoi_file, "r", newline="") as f:
            lines = [line.strip() for line in f if line.strip()]
        if lines:
            for line in lines:
                item = QListWidgetItem(line)
                self.aoi_list_widget.addItem(item)
        else:
            # If empty, show a single disabled item
            empty_item = QListWidgetItem("No AOIs available")
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.aoi_list_widget.addItem(empty_item)

    def create_aoi(self):
        # Prompt user for AOI name
        aoi_name, ok = QInputDialog.getText(self, "Create AOI", "Enter AOI name:")
        if ok and aoi_name.strip():
            # Append the AOI name to AOI.csv
            with open(self.aoi_file, "a", newline="") as f:
                f.write(aoi_name.strip() + "\n")
            # Reload the AOI list
            self.load_aoi_list()

    ###########################
    # Sessions related methods #
    ###########################
    def refresh_session_list(self):
        """Refresh the list of session CSV files in the KeyFramer Sessions folder."""
        self.session_list_widget.clear()
        files = [
            f for f in os.listdir(self.sessions_folder)
            if f.endswith(".csv") and f != "AOI.csv"
        ]
        if not files:
            # If empty except AOI.csv, show a single disabled item
            empty_item = QListWidgetItem("The session list is empty!")
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)  # non-selectable
            self.session_list_widget.addItem(empty_item)
        else:
            for fname in files:
                item = QListWidgetItem(fname)
                self.session_list_widget.addItem(item)

    def on_session_item_double_clicked(self, item):
        """Double-click means the session is selected."""
        if not item.isSelected():
            return
        selected_session = item.text()
        self.current_session_name = selected_session
        self.load_session_csv()

    def on_AOI_double_clicked(self, item):
        """Double-click means the session is selected."""
        if not item.isSelected():
            return
        selected_AOI= item.text()
        self.current_AOI = selected_AOI
        self.load_aoi_list()

    def load_session_csv(self):
        if not self.current_session_name:
            return
        session_path = os.path.join(self.sessions_folder, self.current_session_name)
        if not os.path.exists(session_path):
            return

        self.current_session_data = []
        with open(session_path, "r", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                self.current_session_data.append(row)

        print(f"Loaded session: {self.current_session_name}")
        print("Data:", self.current_session_data)

    def create_session(self):
        session_name, ok = QInputDialog.getText(self, "Create Session", "Enter session name:")
        if ok and session_name.strip():
            csv_path = os.path.join(self.sessions_folder, f"{session_name.strip()}.csv")
            if not os.path.exists(csv_path):
                with open(csv_path, "w", newline="") as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerow(["AOI", "In Time", "Duration", "Out Time"])
            self.refresh_session_list()

    #############################
    # KeyFrame creation methods #
    #############################
    def mark_in_point(self):
        self.in_ms = self.media_player.position()
        # Possibly reset out point if it's earlier
        if self.out_ms is not None and self.out_ms <= self.in_ms:
            self.out_ms = None
        self.update_keyframe_buttons()
        self.update_in_out_labels()  # ADDED

    def mark_out_point(self):
        candidate_out = self.media_player.position()
        if self.in_ms is not None and candidate_out <= self.in_ms:
            QMessageBox.warning(
                self,
                "Invalid Out Point",
                "Out Point must be later than In Point."
            )
            return
        self.out_ms = candidate_out
        self.update_keyframe_buttons()
        self.update_in_out_labels()  # ADDED

    def create_keyframes(self):
        # Only valid if in_ms and out_ms are set, and we have a session
        if not self.current_session_name:
            QMessageBox.warning(
                self,
                "No Session Selected",
                "Please select or create a session first."
            )
            return

        if self.in_ms is None or self.out_ms is None:
            QMessageBox.warning(
                self,
                "Missing Points",
                "You need both In and Out points."
            )
            return

        # Check if AOI is selected
        if not self.current_AOI:
            QMessageBox.warning(
                self,
                "No AOI Selected",
                "Please select or create an AOI first."
            )
            return



        # Calculate times
        in_time_str = format_time(self.in_ms)
        out_time_str = format_time(self.out_ms)
        duration_ms = self.out_ms - self.in_ms
        duration_str = format_time(duration_ms)

        # Write to the current session CSV
        session_path = os.path.join(self.sessions_folder, self.current_session_name)
        with open(session_path, "a", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow([self.current_AOI, in_time_str, duration_str, out_time_str])

        QMessageBox.information(
            self,
            "KeyFrame Created",
            f"KeyFrame successfully created:\n"
            f"AOI: {self.current_AOI}\n"
            f"In: {in_time_str}\n"
            f"Out: {out_time_str}\n"
            f"Duration: {duration_str}"
        )

        # Reset in/out points
        self.in_ms = None
        self.out_ms = None
        self.update_keyframe_buttons()
        self.update_in_out_labels()  # ADDED
        # Optionally reload session
        self.load_session_csv()

    # ADDED: Helper method to show In/Out points and duration
    def update_in_out_labels(self):
        """
        Updates the in_label, out_label, and duration_label
        whenever in_ms or out_ms changes.
        """
        # If we have a valid FPS from OpenCV, we can compute frames accurately
        def ms_to_frame(ms):
            if self.video_fps:
                return int((ms / 1000.0) * self.video_fps)
            return 0

        # Update In Label
        if self.in_ms is not None:
            in_time_str = format_time(self.in_ms)
            in_frame = ms_to_frame(self.in_ms)
            self.in_label.setText(f"In Point: {in_time_str} (Frame {in_frame})")
        else:
            self.in_label.setText("In Point: not set")

        # Update Out Label
        if self.out_ms is not None:
            out_time_str = format_time(self.out_ms)
            out_frame = ms_to_frame(self.out_ms)
            self.out_label.setText(f"Out Point: {out_time_str} (Frame {out_frame})")
        else:
            self.out_label.setText("Out Point: not set")

        # Update Duration Label
        if self.in_ms is not None and self.out_ms is not None and self.out_ms > self.in_ms:
            dur_ms = self.out_ms - self.in_ms
            duration_str = format_time(dur_ms)
            if self.video_fps:
                frames_diff = ms_to_frame(self.out_ms) - ms_to_frame(self.in_ms)
                self.duration_label.setText(f"Duration: {duration_str} ({frames_diff} frames)")
            else:
                self.duration_label.setText(f"Duration: {duration_str}")
        else:
            self.duration_label.setText("Duration: --")
    # END ADDED

    def update_keyframe_buttons(self):
        # create_keyframes_button is only enabled if in_ms and out_ms are set.
        can_create = (self.in_ms is not None) and (self.out_ms is not None)
        self.create_keyframes_button.setEnabled(can_create)

    ###################
    # Video callbacks #
    ###################
    def open_video(self):
        """Open a video with both QMediaPlayer and OpenCV to retrieve FPS accurately."""
        file_dialog = QFileDialog()
        video_path, _ = file_dialog.getOpenFileName(
            self,
            "Open Video File",
            "",
            "Videos (*.mp4 *.avi *.mov *.mkv)"
        )
        if video_path:
            # 1) Set source for QMediaPlayer
            self.media_player.setSource(QUrl.fromLocalFile(video_path))
            self.media_player.play()

            # 2) Use OpenCV to extract FPS
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                self.video_fps = cap.get(cv2.CAP_PROP_FPS)
                if self.video_fps <= 1e-2:  # fallback if invalid or 0
                    self.video_fps = None
                cap.release()
            else:
                self.video_fps = None

    def set_position(self, position):
        self.media_player.setPosition(position)

    def update_slider(self, position):
        self.timeline_slider.setValue(position)

    def update_time_label(self, position):
        time_text = format_time(position)

        # If we have a valid FPS from OpenCV, compute frame accurately
        if self.video_fps:
            # position is in ms; convert to seconds
            pos_seconds = position / 1000.0
            frame_num = int(self.video_fps * pos_seconds)
        else:
            # fallback if no valid FPS found
            frame_num = 0

        self.time_label.setText(f"{time_text} | Frame: {frame_num}")

    def set_slider_range(self, duration):
        self.timeline_slider.setRange(0, duration)

    def playback_state_changed(self, state):
        # If paused, show frame step buttons
        # If playing, hide them
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.pause_button.setText("Pause")
            self.pause_button.setShortcut(QKeySequence.fromString("SPACE"))
            self.one_frame_before_button.hide()
            self.one_frame_after_button.hide()
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.pause_button.setText("Unpause")
            self.pause_button.setShortcut(QKeySequence.fromString("SPACE"))
            self.one_frame_before_button.show()
            self.one_frame_after_button.show()
        else:  # StoppedState
            self.pause_button.setText("Pause")
            self.pause_button.setShortcut(QKeySequence.fromString("SPACE"))
            self.one_frame_before_button.hide()
            self.one_frame_after_button.hide()

    def toggle_pause(self):
        state = self.media_player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.media_player.play()
        else:
            self.media_player.play()

    def step_frame_before(self):
        # If we know the fps, move back precisely one frame in ms
        if self.video_fps:
            frame_duration_ms = 1000.0 / self.video_fps
        else:
            frame_duration_ms = 33.0  # fallback

        pos = self.media_player.position()
        new_pos = max(0, pos - frame_duration_ms)
        self.media_player.setPosition(int(new_pos))

    def step_frame_after(self):
        if self.video_fps:
            frame_duration_ms = 1000.0 / self.video_fps
        else:
            frame_duration_ms = 33.0

        pos = self.media_player.position()
        new_pos = min(self.media_player.duration(), pos + frame_duration_ms)
        self.media_player.setPosition(int(new_pos))

    #######################
    # Panel toggle methods #
    #######################
    def toggle_session_panel(self):
        if self.session_panel_widget.isVisible():
            self.session_panel_widget.hide()
        else:
            self.session_panel_widget.show()
        self.adjust_layout()

    def toggle_aoi_panel(self):
        if self.aoi_panel_widget.isVisible():
            self.aoi_panel_widget.hide()
        else:
            self.aoi_panel_widget.show()
        self.adjust_layout()

    def toggle_keyframes_panel(self):
        if self.keyframes_panel.isVisible():
            self.keyframes_panel.hide()
        else:
            self.keyframes_panel.show()
        self.adjust_layout()

    def adjust_layout(self):
        panels_visible = [
            self.session_panel_widget.isVisible(),
            self.aoi_panel_widget.isVisible(),
            self.keyframes_panel.isVisible()
        ]

        # If all 3 side panels are hidden, expand the video panel
        if not any(panels_visible):
            self.video_panel.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding
            )
        else:
            self.video_panel.setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Preferred
            )
        self.video_panel.update()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
