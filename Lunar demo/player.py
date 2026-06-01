import json

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
)

from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from styles import STYLE
from api import search_tracks


class Lunar(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("🌙 Lunar")
        self.resize(1400, 850)

        self.player = QMediaPlayer()

        self.audio = QAudioOutput()

        self.player.setAudioOutput(self.audio)

        self.init_ui()

        self.load_playlist()

    def init_ui(self):
        root = QHBoxLayout(self)

        root.setContentsMargins(20, 20, 20, 20)

        root.setSpacing(20)

        # LEFT PANEL

        sidebar_layout = QVBoxLayout()

        sidebar_layout.setSpacing(15)

        logo = QLabel("🌙 Lunar")

        logo.setObjectName("logo")

        home_btn = QPushButton("Home")

        playlist_btn = QPushButton("Playlist")

        favorites_btn = QPushButton("Favorites")

        sidebar_layout.addWidget(logo)

        sidebar_layout.addWidget(home_btn)

        sidebar_layout.addWidget(playlist_btn)

        sidebar_layout.addWidget(favorites_btn)

        sidebar_layout.addStretch()

        sidebar_widget = QWidget()

        sidebar_widget.setObjectName("sidebar")

        sidebar_widget.setLayout(sidebar_layout)

        sidebar_widget.setFixedWidth(230)

        # CENTER

        center_layout = QVBoxLayout()

        center_layout.setSpacing(20)

        top_layout = QHBoxLayout()

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText("Search music...")

        search_btn = QPushButton("Search")

        search_btn.clicked.connect(self.search_music)

        top_layout.addWidget(self.search_input)

        top_layout.addWidget(search_btn)

        self.results = QListWidget()

        self.results.itemClicked.connect(self.play_track)

        center_layout.addLayout(top_layout)

        center_layout.addWidget(self.results)

        # BOTTOM PLAYER

        bottom_layout = QHBoxLayout()

        self.track_label = QLabel("No track playing")

        play_btn = QPushButton("▶")

        pause_btn = QPushButton("⏸")

        play_btn.clicked.connect(self.resume_music)

        pause_btn.clicked.connect(self.pause_music)

        bottom_layout.addWidget(self.track_label)

        bottom_layout.addStretch()

        bottom_layout.addWidget(play_btn)

        bottom_layout.addWidget(pause_btn)

        bottom_widget = QWidget()

        bottom_widget.setObjectName("bottomPlayer")

        bottom_widget.setLayout(bottom_layout)

        bottom_widget.setFixedHeight(90)

        content_layout = QVBoxLayout()

        content_layout.addLayout(center_layout)

        content_layout.addWidget(bottom_widget)

        # RIGHT PANEL

        right_layout = QVBoxLayout()

        right_layout.setSpacing(15)

        playlist_title = QLabel("My Playlist")

        playlist_title.setObjectName("playlistTitle")

        self.playlist = QListWidget()

        self.playlist.itemClicked.connect(
            self.play_playlist_track
        )

        remove_btn = QPushButton("Remove Track")

        remove_btn.clicked.connect(self.remove_track)

        right_layout.addWidget(playlist_title)

        right_layout.addWidget(self.playlist)

        right_layout.addWidget(remove_btn)

        right_widget = QWidget()

        right_widget.setObjectName("rightPanel")

        right_widget.setLayout(right_layout)

        right_widget.setFixedWidth(320)

        root.addWidget(sidebar_widget)

        root.addLayout(content_layout)

        root.addWidget(right_widget)

        self.setStyleSheet(STYLE)

    def search_music(self):
        query = self.search_input.text()

        if not query:
            return

        tracks = search_tracks(query)

        self.results.clear()

        for track in tracks:
            text = (
                f"{track['title']} — "
                f"{track['artist']}"
            )

            item = QListWidgetItem(text)

            item.setData(
                Qt.UserRole,
                track["preview"]
            )

            item.setData(
                Qt.UserRole + 1,
                text
            )

            self.results.addItem(item)

    def play_track(self, item):
        preview = item.data(Qt.UserRole)

        text = item.data(Qt.UserRole + 1)

        self.player.setSource(QUrl(preview))

        self.player.play()

        self.track_label.setText(text)

        result = QMessageBox.question(
            self,
            "Playlist",
            "Add track to playlist?",
            QMessageBox.Yes | QMessageBox.No
        )

        if result == QMessageBox.Yes:
            self.add_to_playlist(item)

    def add_to_playlist(self, item):
        text = item.data(Qt.UserRole + 1)

        preview = item.data(Qt.UserRole)

        playlist_item = QListWidgetItem(text)

        playlist_item.setData(
            Qt.UserRole,
            preview
        )

        playlist_item.setData(
            Qt.UserRole + 1,
            text
        )

        self.playlist.addItem(playlist_item)

        self.save_playlist()

    def play_playlist_track(self, item):
        preview = item.data(Qt.UserRole)

        text = item.data(Qt.UserRole + 1)

        self.player.setSource(QUrl(preview))

        self.player.play()

        self.track_label.setText(text)

    def pause_music(self):
        self.player.pause()

    def resume_music(self):
        self.player.play()

    def remove_track(self):
        row = self.playlist.currentRow()

        if row >= 0:
            self.playlist.takeItem(row)

            self.save_playlist()

    def save_playlist(self):
        tracks = []

        for i in range(self.playlist.count()):
            item = self.playlist.item(i)

            tracks.append({
                "text": item.data(
                    Qt.UserRole + 1
                ),
                "preview": item.data(
                    Qt.UserRole
                )
            })

        with open(
            "playlists.json",
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                tracks,
                file,
                indent=4
            )

    def load_playlist(self):
        try:
            with open(
                "playlists.json",
                "r",
                encoding="utf-8"
            ) as file:

                tracks = json.load(file)

            for track in tracks:
                item = QListWidgetItem(
                    track["text"]
                )

                item.setData(
                    Qt.UserRole,
                    track["preview"]
                )

                item.setData(
                    Qt.UserRole + 1,
                    track["text"]
                )

                self.playlist.addItem(item)

        except:
            pass