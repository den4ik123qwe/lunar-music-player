#demo version
import sys
import json
import os
import math
import random
import webbrowser

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QSlider,
    QInputDialog,
    QFrame,
    QDialog,
    QDialogButtonBox,
    QSplitter,
    QScrollArea,
    QGridLayout,
    QComboBox,
)

from PySide6.QtCore import Qt, QUrl, QPropertyAnimation, QEasingCurve, QSize, QPoint, QPointF, QTimer
from PySide6.QtGui import QPixmap, QPainter, QColor, QBrush, QIcon, QPen, QFont, QPainterPath
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest

from styles import STYLE
from api import get_tracks_with_full_audio, test_api_connection


# ================= USERS =================

USERS_DIR = "users_data"

def ensure_users_dir():
    if not os.path.exists(USERS_DIR):
        os.makedirs(USERS_DIR)

def get_user_file(username):
    return os.path.join(USERS_DIR, f"{username}.json")

def load_user_data(username):
    ensure_users_dir()
    user_file = get_user_file(username)
    if os.path.exists(user_file):
        try:
            with open(user_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"playlists": {"Любимое": []}, "recent": [], "settings": {}}
    else:
        return {"playlists": {"Любимое": []}, "recent": [], "settings": {}}

def save_user_data(username, data):
    ensure_users_dir()
    user_file = get_user_file(username)
    with open(user_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_users_list():
    ensure_users_dir()
    users = []
    for file in os.listdir(USERS_DIR):
        if file.endswith(".json") and file != "credentials.json":
            username = file[:-5]
            users.append(username)
    return users

def save_user_credentials(username, password):
    cred_file = os.path.join(USERS_DIR, "credentials.json")
    credentials = {}
    if os.path.exists(cred_file):
        with open(cred_file, "r", encoding="utf-8") as f:
            credentials = json.load(f)
    credentials[username] = password
    with open(cred_file, "w", encoding="utf-8") as f:
        json.dump(credentials, f, indent=4, ensure_ascii=False)

def check_user_credentials(username, password):
    cred_file = os.path.join(USERS_DIR, "credentials.json")
    if not os.path.exists(cred_file):
        return False
    with open(cred_file, "r", encoding="utf-8") as f:
        credentials = json.load(f)
    return credentials.get(username) == password

def user_exists(username):
    users = load_users_list()
    return username in users


# ================= USER MENU DIALOG =================

class UserMenuDialog(QDialog):
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.username = username
        self.parent_app = parent
        self.setWindowTitle("Аккаунт")
        self.resize(280, 420)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                border: 1px solid #2a2a2a;
                border-radius: 12px;
            }
            QPushButton {
                background-color: #2d2d2d;
                border: none;
                border-radius: 8px;
                padding: 10px;
                text-align: center;
                font-size: 13px;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
            QLabel {
                color: #e0e0e0;
                padding: 5px;
            }
            QFrame {
                background-color: transparent;
            }
            QListWidget {
                background-color: #252525;
                border: 1px solid #2a2a2a;
                border-radius: 8px;
                color: #e0e0e0;
                font-size: 13px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 6px;
            }
            QListWidget::item:hover {
                background-color: #3d3d3d;
            }
            QListWidget::item:selected {
                background-color: #4a8bc2;
                color: white;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        user_frame = QFrame()
        user_frame.setStyleSheet("""
            QFrame {
                background-color: #252525;
                border-radius: 10px;
                padding: 12px;
                border: 1px solid #4a8bc2;
            }
        """)
        user_layout = QVBoxLayout(user_frame)
        user_layout.setSpacing(5)
        current_label = QLabel("Текущий пользователь")
        current_label.setStyleSheet("font-size: 11px; color: #888888;")
        current_label.setAlignment(Qt.AlignCenter)
        username_label = QLabel(self.username)
        username_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #4a8bc2;")
        username_label.setAlignment(Qt.AlignCenter)
        user_layout.addWidget(current_label)
        user_layout.addWidget(username_label)
        layout.addWidget(user_frame)

        other_users_label = QLabel("Другие аккаунты")
        other_users_label.setStyleSheet("font-size: 12px; color: #aaaaaa; margin-top: 5px;")
        layout.addWidget(other_users_label)

        self.users_list = QListWidget()
        self.users_list.setMaximumHeight(150)
        self.users_list.itemClicked.connect(self.switch_to_user)
        layout.addWidget(self.users_list)
        self.load_users_list()

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #2a2a2a; max-height: 1px; margin: 5px 0;")
        layout.addWidget(separator)

        add_account_btn = QPushButton("Новый аккаунт")
        add_account_btn.setCursor(Qt.PointingHandCursor)
        add_account_btn.setStyleSheet("background-color: #4a8bc2; text-align: center;")
        add_account_btn.clicked.connect(self.add_new_account)
        layout.addWidget(add_account_btn)

        logout_btn = QPushButton("Выйти")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setStyleSheet("background-color: #8b3a3a; text-align: center;")
        logout_btn.clicked.connect(self.logout)
        layout.addWidget(logout_btn)

        close_btn = QPushButton("Закрыть")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("background-color: #2d2d2d; text-align: center;")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def load_users_list(self):
        self.users_list.clear()
        users = load_users_list()
        for user in users:
            if user != self.username:
                item = QListWidgetItem(user)
                item.setData(Qt.UserRole, user)
                item.setToolTip("Нажмите для переключения")
                self.users_list.addItem(item)
        if self.users_list.count() == 0:
            item = QListWidgetItem("Нет других аккаунтов")
            item.setFlags(Qt.NoItemFlags)
            item.setForeground(QColor(136, 136, 136))
            self.users_list.addItem(item)

    def switch_to_user(self, item):
        new_username = item.data(Qt.UserRole)
        if new_username and new_username != self.username:
            reply = QMessageBox.question(self, "Смена аккаунта", f"Переключиться на аккаунт '{new_username}'?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.accept()
                self.parent_app.switch_to_account(new_username)

    def add_new_account(self):
        self.accept()
        self.parent_app.switch_account()

    def logout(self):
        reply = QMessageBox.question(self, "Выход", "Вы уверены, что хотите выйти из аккаунта?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.accept()
            self.parent_app.logout()


# ================= ADD TO PLAYLIST DIALOG =================

class AddToPlaylistDialog(QDialog):
    def __init__(self, track_data, playlists, parent=None):
        super().__init__(parent)
        
        self.track_data = track_data
        self.playlists = playlists
        self.parent_app = parent
        self.selected_playlist = None
        
        self.setWindowTitle("Добавить в плейлист")
        self.resize(350, 250)
        self.setMinimumWidth(300)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                border-radius: 12px;
            }
            QLabel {
                color: #e0e0e0;
            }
            QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 10px;
                color: #e0e0e0;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                color: #e0e0e0;
            }
            QPushButton {
                background-color: #4a8bc2;
                border: none;
                border-radius: 8px;
                padding: 10px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a9bd2;
            }
            QPushButton#cancel {
                background-color: #2d2d2d;
            }
            QPushButton#cancel:hover {
                background-color: #3d3d3d;
            }
        """)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        info_label = QLabel("Добавить трек в плейлист:")
        info_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(info_label)
        
        track_name = QLabel(f"{self.track_data.get('title', 'Unknown')} - {self.track_data.get('artist', 'Unknown')}")
        track_name.setWordWrap(True)
        track_name.setStyleSheet("color: #4a8bc2; padding: 5px; background-color: #2a2a2a; border-radius: 6px;")
        layout.addWidget(track_name)
        
        layout.addSpacing(10)
        
        playlist_label = QLabel("Выберите плейлист:")
        layout.addWidget(playlist_label)
        
        self.playlist_combo = QComboBox()
        for playlist_name in self.playlists.keys():
            self.playlist_combo.addItem(playlist_name)
        
        if self.playlist_combo.count() > 0:
            self.playlist_combo.setCurrentIndex(0)
        
        layout.addWidget(self.playlist_combo)
        
        layout.addStretch()
        
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setObjectName("cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        
        add_btn = QPushButton("Добавить")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self.add_track_to_playlist)
        
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(add_btn)
        
        layout.addLayout(buttons_layout)
    
    def add_track_to_playlist(self):
        self.selected_playlist = self.playlist_combo.currentText()
        
        track_to_add = {
            "text": f"{self.track_data['title']} - {self.track_data['artist']}",
            "url": self.track_data.get("url"),
            "title": self.track_data['title'],
            "artist": self.track_data['artist'],
            "cover": self.track_data.get('cover_medium', '')
        }
        
        current_tracks = self.playlists[self.selected_playlist]
        
        for track in current_tracks:
            if track.get("url") == track_to_add["url"]:
                QMessageBox.warning(self, "Ошибка", "Этот трек уже есть в выбранном плейлисте!")
                return
        
        self.accept()


# ================= ICON FUNCTIONS =================

def make_play_icon():
    pix = QPixmap(24, 24)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QBrush(QColor(200, 200, 200)))
    painter.setPen(Qt.NoPen)
    points = [QPoint(8, 6), QPoint(8, 18), QPoint(18, 12)]
    painter.drawPolygon(points)
    painter.end()
    return QIcon(pix)

def make_pause_icon():
    pix = QPixmap(24, 24)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QBrush(QColor(200, 200, 200)))
    painter.setPen(Qt.NoPen)
    painter.drawRect(7, 6, 3, 12)
    painter.drawRect(14, 6, 3, 12)
    painter.end()
    return QIcon(pix)

def make_previous_icon():
    pix = QPixmap(24, 24)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QBrush(QColor(200, 200, 200)))
    painter.setPen(Qt.NoPen)
    points1 = [QPoint(14, 8), QPoint(8, 12), QPoint(14, 16)]
    painter.drawPolygon(points1)
    points2 = [QPoint(18, 8), QPoint(12, 12), QPoint(18, 16)]
    painter.drawPolygon(points2)
    painter.end()
    return QIcon(pix)

def make_next_icon():
    pix = QPixmap(24, 24)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QBrush(QColor(200, 200, 200)))
    painter.setPen(Qt.NoPen)
    points1 = [QPoint(10, 8), QPoint(16, 12), QPoint(10, 16)]
    painter.drawPolygon(points1)
    points2 = [QPoint(6, 8), QPoint(12, 12), QPoint(6, 16)]
    painter.drawPolygon(points2)
    painter.end()
    return QIcon(pix)

def make_add_to_playlist_icon():
    pix = QPixmap(24, 24)
    pix.fill(Qt.transparent)
    
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor(200, 200, 200), 2))
    painter.setBrush(QBrush(QColor(200, 200, 200)))
    
    painter.drawLine(12, 4, 12, 20)
    painter.drawLine(4, 12, 20, 12)
    
    painter.end()
    return QIcon(pix)

def make_favorite_icon(is_favorite=False):
    pix = QPixmap(20, 20)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    if is_favorite:
        painter.setBrush(QBrush(QColor(255, 100, 100)))
        painter.setPen(QPen(QColor(255, 100, 100), 1))
    else:
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(200, 200, 200), 1.5))
    center_x, center_y = 10, 10
    outer_radius, inner_radius = 8, 3.5
    points = []
    for i in range(5):
        angle = (i * 72 - 90) * math.pi / 180
        x = center_x + outer_radius * math.cos(angle)
        y = center_y + outer_radius * math.sin(angle)
        points.append(QPointF(x, y))
        angle = ((i + 0.5) * 72 - 90) * math.pi / 180
        x = center_x + inner_radius * math.cos(angle)
        y = center_y + inner_radius * math.sin(angle)
        points.append(QPointF(x, y))
    path = QPainterPath()
    path.moveTo(points[0])
    for point in points[1:]:
        path.lineTo(point)
    path.closeSubpath()
    painter.drawPath(path)
    painter.end()
    return QIcon(pix)

def make_arrow_icon(direction="right"):
    pix = QPixmap(24, 24)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor(200, 200, 200), 2))
    painter.setBrush(Qt.NoBrush)
    if direction == "left":
        painter.drawLine(18, 12, 6, 12)
        painter.drawLine(10, 6, 6, 12)
        painter.drawLine(10, 18, 6, 12)
    elif direction == "right":
        painter.drawLine(6, 12, 18, 12)
        painter.drawLine(14, 6, 18, 12)
        painter.drawLine(14, 18, 18, 12)
    elif direction == "double-left":
        painter.drawLine(18, 12, 6, 12)
        painter.drawLine(10, 6, 6, 12)
        painter.drawLine(10, 18, 6, 12)
        painter.drawLine(14, 6, 10, 12)
        painter.drawLine(14, 18, 10, 12)
    elif direction == "double-right":
        painter.drawLine(6, 12, 18, 12)
        painter.drawLine(14, 6, 18, 12)
        painter.drawLine(14, 18, 18, 12)
        painter.drawLine(10, 6, 14, 12)
        painter.drawLine(10, 18, 14, 12)
    painter.end()
    return QIcon(pix)

def make_avatar(letter: str):
    pix = QPixmap(40, 40)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QBrush(QColor(80, 120, 255)))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, 40, 40)
    painter.setPen(Qt.white)
    painter.drawText(pix.rect(), Qt.AlignCenter, letter.upper())
    painter.end()
    return pix


# ================= GENRES =================

GENRES = [
    "Rock", "Pop", "Electronic", "Hip Hop", 
    "Jazz", "Classical", "Metal", "Ambient",
    "Folk", "Blues", "Reggae", "Punk"
]

# ================= TRACK CARD WIDGET =================

class TrackCardWidget(QFrame):
    def __init__(self, track_info, parent=None):
        super().__init__(parent)
        self.track_info = track_info
        self.parent_app = parent
        self.setFixedSize(180, 200)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border-radius: 12px;
            }
            QFrame:hover {
                background-color: #2a2a2a;
            }
            QLabel {
                background-color: transparent;
            }
            QPushButton {
                background-color: #4a8bc2;
                border-radius: 16px;
                font-size: 11px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #5a9bd2;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(100, 100)
        self.cover_label.setStyleSheet("background-color: #2a2a2a; border-radius: 10px; font-size: 48px; qproperty-alignment: AlignCenter;")
        self.cover_label.setText("🎵")
        self.cover_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.cover_label, alignment=Qt.AlignCenter)

        title_label = QLabel(self.track_info.get('title', 'Unknown')[:25])
        title_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        artist_label = QLabel(self.track_info.get('artist', 'Unknown')[:20])
        artist_label.setStyleSheet("font-size: 10px; color: #888888;")
        artist_label.setWordWrap(True)
        layout.addWidget(artist_label)

        play_btn = QPushButton("Play")
        play_btn.setCursor(Qt.PointingHandCursor)
        play_btn.clicked.connect(self.play_track)
        layout.addWidget(play_btn)

    def play_track(self):
        if self.parent_app:
            self.parent_app.play_track_from_data({
                'url': self.track_info.get('preview'),
                'text': f"{self.track_info.get('title')} - {self.track_info.get('artist')}",
                'title': self.track_info.get('title'),
                'artist': self.track_info.get('artist'),
                'cover': self.track_info.get('cover_medium', '')
            })


# ================= LOGIN WINDOW =================

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lunar Login")
        self.resize(300, 180)
        layout = QVBoxLayout(self)
        self.login = QLineEdit()
        self.login.setPlaceholderText("Логин")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Пароль")
        self.password.setEchoMode(QLineEdit.Password)
        btn = QPushButton("Войти / Регистрация")
        btn.clicked.connect(self.auth)
        layout.addWidget(QLabel("Lunar Access"))
        layout.addWidget(self.login)
        layout.addWidget(self.password)
        layout.addWidget(btn)

    def auth(self):
        username = self.login.text().strip()
        password = self.password.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Заполни поля")
            return
        if user_exists(username):
            if check_user_credentials(username, password):
                self.main = Lunar(username)
                self.main.show()
                self.close()
            else:
                QMessageBox.warning(self, "Ошибка", "Неверный пароль")
        else:
            save_user_credentials(username, password)
            user_data = {"playlists": {"Любимое": []}, "recent": [], "settings": {}}
            save_user_data(username, user_data)
            QMessageBox.information(self, "Успех", "Регистрация прошла успешно!")
            self.main = Lunar(username)
            self.main.show()
            self.close()


# ================= PLAYLIST MANAGER DIALOG =================

class PlaylistManagerDialog(QDialog):
    def __init__(self, playlist_name, tracks, parent=None):
        super().__init__(parent)
        self.playlist_name = playlist_name
        self.tracks = tracks
        self.parent_app = parent
        self.setWindowTitle(f"Управление плейлистом - {playlist_name}")
        self.resize(900, 650)
        self.setMinimumSize(800, 550)
        self.setStyleSheet("""
            QDialog {
                background-color: #121212;
            }
            QLabel {
                color: #e0e0e0;
            }
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #2a2a2a;
                border-radius: 6px;
                color: #e0e0e0;
                padding: 5px;
                outline: none;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #2a2a2a;
            }
            QListWidget::item:selected {
                background-color: #3a6ea5;
                color: white;
            }
            QLineEdit {
                background-color: #1e1e1e;
                border: 1px solid #2a2a2a;
                border-radius: 4px;
                padding: 8px;
                color: #e0e0e0;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #4a8bc2;
            }
            QPushButton {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 8px 16px;
                color: #e0e0e0;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton:pressed {
                background-color: #1e1e1e;
            }
            QFrame {
                background-color: transparent;
            }
            QSplitter::handle {
                background-color: #2a2a2a;
                width: 2px;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #1a1a1a; border-radius: 8px; padding: 12px;")
        header_layout = QHBoxLayout(header_frame)
        title_label = QLabel(f"Плейлист: {self.playlist_name}")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #4a8bc2;")
        self.track_count_label = QLabel(f"Всего треков: {len(self.tracks)}")
        self.track_count_label.setStyleSheet("color: #888888; font-size: 12px; padding: 4px 12px; background-color: #121212; border-radius: 12px;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.track_count_label)
        layout.addWidget(header_frame)

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setHandleWidth(2)

        left_panel = QFrame()
        left_panel.setStyleSheet("background-color: #1a1a1a; border-radius: 8px; padding: 12px;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(12)
        left_header = QLabel("Добавление треков")
        left_header_font = QFont()
        left_header_font.setPointSize(13)
        left_header_font.setBold(True)
        left_header.setFont(left_header_font)
        left_header.setStyleSheet("color: #4a8bc2;")
        left_layout.addWidget(left_header)

        search_frame = QFrame()
        search_frame.setStyleSheet("background-color: #121212; border-radius: 6px;")
        search_layout = QVBoxLayout(search_frame)
        search_layout.setSpacing(8)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Название трека или исполнитель...")
        self.search_input.returnPressed.connect(self.search_tracks)
        search_btn = QPushButton("Найти")
        search_btn.setCursor(Qt.PointingHandCursor)
        search_btn.setStyleSheet("background-color: #4a8bc2; border: none; border-radius: 6px; padding: 8px; font-weight: bold;")
        search_btn.clicked.connect(self.search_tracks)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        left_layout.addWidget(search_frame)

        results_label = QLabel("Результаты поиска")
        results_label.setStyleSheet("color: #888888; font-size: 11px;")
        left_layout.addWidget(results_label)
        self.search_results = QListWidget()
        self.search_results.setMinimumHeight(350)
        self.search_results.itemDoubleClicked.connect(self.add_track)
        left_layout.addWidget(self.search_results)

        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: #1a1a1a; border-radius: 8px; padding: 12px;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(12)
        right_header = QLabel("Треки в плейлисте")
        right_header_font = QFont()
        right_header_font.setPointSize(13)
        right_header_font.setBold(True)
        right_header.setFont(right_header_font)
        right_header.setStyleSheet("color: #4a8bc2;")
        right_layout.addWidget(right_header)
        self.tracks_list = QListWidget()
        self.tracks_list.setMinimumHeight(350)
        self.tracks_list.itemDoubleClicked.connect(self.play_track)
        right_layout.addWidget(self.tracks_list)

        buttons_frame = QFrame()
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setSpacing(8)
        remove_btn = QPushButton("Удалить выбранный")
        remove_btn.setCursor(Qt.PointingHandCursor)
        remove_btn.setStyleSheet("background-color: #8b3a3a; border: none; border-radius: 6px;")
        remove_btn.clicked.connect(self.remove_track)
        clear_btn = QPushButton("Очистить все")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet("background-color: #8b6b3a; border: none; border-radius: 6px;")
        clear_btn.clicked.connect(self.clear_playlist)
        delete_btn = QPushButton("Удалить плейлист")
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setStyleSheet("background-color: #6b2a2a; border: none; border-radius: 6px; font-weight: bold;")
        delete_btn.clicked.connect(self.delete_playlist)
        buttons_layout.addWidget(remove_btn)
        buttons_layout.addWidget(clear_btn)
        buttons_layout.addWidget(delete_btn)
        buttons_layout.addStretch()
        right_layout.addWidget(buttons_frame)

        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([400, 500])
        layout.addWidget(main_splitter)

        bottom_frame = QFrame()
        bottom_frame.setStyleSheet("background-color: #1a1a1a; border-radius: 8px; padding: 10px;")
        bottom_layout = QHBoxLayout(bottom_frame)
        info_label = QLabel("Двойной клик для добавления или воспроизведения")
        info_label.setStyleSheet("color: #666666; font-size: 11px;")
        bottom_layout.addWidget(info_label)
        bottom_layout.addStretch()
        close_btn = QPushButton("Закрыть")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFixedWidth(100)
        close_btn.setStyleSheet("background-color: #2a2a2a; border: 1px solid #3a3a3a; border-radius: 6px; padding: 6px 16px;")
        close_btn.clicked.connect(self.accept)
        bottom_layout.addWidget(close_btn)
        layout.addWidget(bottom_frame)

        self.load_tracks()

    def search_tracks(self):
        q = self.search_input.text()
        if not q:
            return
        tracks = get_tracks_with_full_audio(q)
        self.search_results.clear()
        for t in tracks:
            audio_url = t.get('preview')
            if audio_url:
                item = QListWidgetItem(f"{t['title']} - {t['artist']}")
                item.setData(Qt.UserRole, t)
                self.search_results.addItem(item)

    def add_track(self, item):
        track_data = item.data(Qt.UserRole)
        for track in self.tracks:
            if track.get("url") == track_data.get("preview"):
                QMessageBox.warning(self, "Ошибка", "Этот трек уже есть в плейлисте!")
                return
        new_track = {
            "text": f"{track_data['title']} - {track_data['artist']}",
            "url": track_data.get("preview"),
            "title": track_data['title'],
            "artist": track_data['artist'],
            "cover": track_data.get('cover_medium', '')
        }
        self.tracks.append(new_track)
        self.load_tracks()
        self.save_changes()
        self.track_count_label.setText(f"Всего треков: {len(self.tracks)}")
        QMessageBox.information(self, "Успех", f"Трек '{track_data['title']}' добавлен в плейлист!")
        self.search_input.clear()
        self.search_results.clear()

    def remove_track(self):
        current_row = self.tracks_list.currentRow()
        if current_row >= 0:
            track = self.tracks[current_row]
            reply = QMessageBox.question(self, "Подтверждение", f"Удалить трек '{track['title']}' из плейлиста?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.tracks.pop(current_row)
                self.load_tracks()
                self.save_changes()
                self.track_count_label.setText(f"Всего треков: {len(self.tracks)}")

    def clear_playlist(self):
        if not self.tracks:
            return
        reply = QMessageBox.question(self, "Подтверждение", f"Очистить весь плейлист '{self.playlist_name}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.tracks.clear()
            self.load_tracks()
            self.save_changes()
            self.track_count_label.setText(f"Всего треков: {len(self.tracks)}")

    def delete_playlist(self):
        reply = QMessageBox.question(self, "Подтверждение", f"Удалить плейлист '{self.playlist_name}'? Все треки будут потеряны!",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.parent_app.delete_playlist(self.playlist_name)
            self.accept()

    def play_track(self, item):
        track = self.tracks[self.tracks_list.currentRow()]
        self.parent_app.play_track_from_data(track)

    def load_tracks(self):
        self.tracks_list.clear()
        for i, track in enumerate(self.tracks, 1):
            item = QListWidgetItem(f"{i:02d}. {track['title']} - {track['artist']}")
            self.tracks_list.addItem(item)

    def save_changes(self):
        self.parent_app.update_playlist(self.playlist_name, self.tracks)


# ================= HOME PAGE WIDGET (АДАПТИВНЫЙ) =================

class HomePageWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.init_ui()

    def init_ui(self):
        # Основной скролл-контейнер
        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        main_scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #4a8bc2;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #5a9bd2;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Контент внутри скролла
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setSpacing(25)
        self.content_layout.setContentsMargins(0, 10, 0, 20)
        
        main_scroll.setWidget(content_widget)
        
        # Основной layout для виджета
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(main_scroll)
        
        # Заполняем контент
        self.build_content()
    
    def build_content(self):
        # Очищаем существующий контент
        self.clear_layout(self.content_layout)
        
        # Приветствие
        welcome_label = QLabel(f"Добро пожаловать, {self.parent_app.username}!")
        welcome_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4a8bc2; margin-left: 10px;")
        self.content_layout.addWidget(welcome_label)
        
        # Подборка дня
        daily_tracks_data = self.parent_app.get_daily_tracks()
        self.add_section("Подборка дня", daily_tracks_data)
        
        # Недавно прослушанные
        self.add_section("Недавно прослушанные", self.parent_app.get_recent_tracks())
        
        # Рекомендации
        self.add_section("На основе ваших предпочтений", self.parent_app.get_recommended_tracks())
        
        # Популярные жанры
        genres_label = QLabel("Популярные жанры")
        genres_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px; margin-left: 10px;")
        self.content_layout.addWidget(genres_label)
        
        # Жанры в обтекаемом layout
        genres_wrapper = QWidget()
        genres_layout = QGridLayout(genres_wrapper)
        genres_layout.setSpacing(10)
        genres_layout.setContentsMargins(10, 5, 10, 5)
        
        row = 0
        col = 0
        cols = 6
        
        for genre in GENRES:
            genre_btn = QPushButton(genre)
            genre_btn.setCursor(Qt.PointingHandCursor)
            genre_btn.setMinimumWidth(100)
            genre_btn.setStyleSheet("background-color: #2a2a2a; border-radius: 20px; padding: 8px 16px; font-size: 12px;")
            genre_btn.clicked.connect(lambda checked, g=genre: self.parent_app.search_by_genre(g))
            genres_layout.addWidget(genre_btn, row, col)
            
            col += 1
            if col >= cols:
                col = 0
                row += 1
        
        self.content_layout.addWidget(genres_wrapper)
        self.content_layout.addStretch()
    
    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())
    
    def add_section(self, title, tracks):
        section_label = QLabel(title)
        section_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px; margin-left: 10px;")
        self.content_layout.addWidget(section_label)
        
        if not tracks:
            empty_label = QLabel("Нет треков для отображения")
            empty_label.setStyleSheet("color: #888888; margin-left: 15px;")
            self.content_layout.addWidget(empty_label)
            return
        
        tracks_wrapper = QWidget()
        tracks_grid = QGridLayout(tracks_wrapper)
        tracks_grid.setSpacing(15)
        tracks_grid.setContentsMargins(10, 10, 10, 10)
        
        row = 0
        col = 0
        cols = self.calculate_columns()
        
        for track in tracks[:10]:
            card = TrackCardWidget(track, self.parent_app)
            tracks_grid.addWidget(card, row, col)
            
            col += 1
            if col >= cols:
                col = 0
                row += 1
        
        self.content_layout.addWidget(tracks_wrapper)
    
    def calculate_columns(self):
        width = self.width()
        if width < 800:
            return 2
        elif width < 1100:
            return 3
        elif width < 1400:
            return 4
        elif width < 1700:
            return 5
        else:
            return 6
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.build_content()


# ================= MAIN APP =================

class Lunar(QWidget):
    VK_LINK = "https://vk.com/club239129057"
    
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.current_track_index = -1
        self.current_playlist_tracks = []
        self.current_track_data = None
        self.current_volume = 50
        self.showing_search = False
        self.search_results_data = []

        self.setWindowTitle(f"Lunar - {username}")
        self.resize(1400, 850)

        self.player = QMediaPlayer()
        self.audio = QAudioOutput()
        self.player.setAudioOutput(self.audio)

        self.user_data = load_user_data(username)
        self.playlists = self.user_data.get("playlists", {"Любимое": []})
        self.recent_tracks = self.user_data.get("recent", [])
        self.current_playlist = "Любимое"

        self.eq_open = True
        self.playlist_open = True
        
        self.left_widget_width = 320
        self.right_widget_width = 320

        self.setup_ui()
        self.load_playlists()

        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)
        self.player.mediaStatusChanged.connect(self.on_media_status_changed)

        self.left_anim = QPropertyAnimation(self.left_widget, b"maximumWidth")
        self.left_anim.setDuration(200)
        self.left_anim.setEasingCurve(QEasingCurve.InOutQuad)
        
        self.right_anim = QPropertyAnimation(self.right_widget, b"maximumWidth")
        self.right_anim.setDuration(200)
        self.right_anim.setEasingCurve(QEasingCurve.InOutQuad)

        api_status, api_message = test_api_connection()
        print(f"API Status: {api_message}")
        self.audio.setVolume(0.5)

    def get_daily_tracks(self):
        """Получает треки для подборки дня"""
        return get_tracks_with_full_audio("popular", 10)

    def show_premium_message(self, feature_name=""):
        msg = f"🔒 Функция '{feature_name}' доступна только в полной версии!\n\nНапишите нам в ВКонтакте для приобретения лицензии."
        reply = QMessageBox.question(self, "Требуется полная версия", 
                                     msg + "\n\nОткрыть сообщество ВКонтакте?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            webbrowser.open(self.VK_LINK)

    def format_time(self, ms):
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def btn(self, text):
        b = QPushButton(text)
        b.setMinimumHeight(34)
        b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet("border-radius: 8px;")
        return b

    def icon_btn(self, icon, tooltip=""):
        b = QPushButton()
        b.setIcon(icon)
        b.setIconSize(QSize(24, 24))
        b.setFixedSize(40, 40)
        b.setCursor(Qt.PointingHandCursor)
        b.setToolTip(tooltip)
        b.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        return b

    def setup_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(20)

        # ЛЕВАЯ ПАНЕЛЬ
        left = QVBoxLayout()

        self.avatar_btn = QPushButton()
        self.avatar_btn.setFixedSize(40, 40)
        self.avatar_btn.setCursor(Qt.PointingHandCursor)
        self.avatar_btn.clicked.connect(self.show_user_menu)
        self.avatar_btn.setIcon(make_avatar(self.username[0]))
        self.avatar_btn.setIconSize(self.avatar_btn.size())
        self.avatar_btn.setStyleSheet("border-radius: 20px;")

        self.left_toggle_btn = QPushButton()
        self.left_toggle_btn.setFixedSize(32, 32)
        self.left_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.left_toggle_btn.clicked.connect(self.toggle_left_panel)
        self.left_toggle_btn.setIcon(make_arrow_icon("left"))
        self.left_toggle_btn.setIconSize(QSize(20, 20))
        self.left_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 16px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)

        self.eq_panel = QFrame()
        self.eq_panel.setFixedWidth(260)
        eq_layout = QVBoxLayout(self.eq_panel)

        premium_label = QLabel("✨ ЭКВАЛАЙЗЕР\n(Премиум-функция)")
        premium_label.setStyleSheet("font-size: 14px; font-weight: bold; color: gold; background-color: #1a1a1a; border-radius: 8px; padding: 20px;")
        premium_label.setAlignment(Qt.AlignCenter)
        eq_layout.addWidget(premium_label)
        
        upgrade_btn = QPushButton("Купить полную версию")
        upgrade_btn.setCursor(Qt.PointingHandCursor)
        upgrade_btn.setStyleSheet("background-color: gold; color: black; font-weight: bold; border-radius: 8px; padding: 10px;")
        upgrade_btn.clicked.connect(lambda: self.show_premium_message("Эквалайзер"))
        eq_layout.addWidget(upgrade_btn)
        eq_layout.addStretch()

        left.addWidget(self.avatar_btn, alignment=Qt.AlignTop)
        left.addWidget(self.left_toggle_btn, alignment=Qt.AlignHCenter)
        left.addSpacing(10)
        left.addWidget(self.eq_panel)
        left.addStretch()

        self.left_widget = QWidget()
        self.left_widget.setLayout(left)
        self.left_widget.setMinimumWidth(60)
        self.left_widget.setMaximumWidth(self.left_widget_width)

        # ЦЕНТРАЛЬНАЯ ПАНЕЛЬ
        center = QVBoxLayout()
        center.setSpacing(15)

        top = QHBoxLayout()
        self.home_btn = self.btn("Главная")
        self.home_btn.clicked.connect(self.show_home)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск трека...")
        self.search_input.returnPressed.connect(self.search_music)

        search_btn = self.btn("Поиск")
        search_btn.clicked.connect(self.search_music)

        top.addWidget(self.home_btn)
        top.addWidget(self.search_input)
        top.addWidget(search_btn)

        center.addLayout(top)

        self.content_stack = QVBoxLayout()
        self.content_stack.setSpacing(15)
        self.home_page = HomePageWidget(self)
        self.content_stack.addWidget(self.home_page)
        self.results = QListWidget()
        self.results.itemClicked.connect(self.on_result_clicked)
        self.results.setVisible(False)
        self.content_stack.addWidget(self.results)
        center.addLayout(self.content_stack, 1)

        # ПЛЕЕР
        player_wrapper = QHBoxLayout()
        player_wrapper.addStretch()
        player_container = QVBoxLayout()
        player_container.setSpacing(10)
        player_container.setContentsMargins(0, 10, 0, 10)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.set_position)
        self.slider.setMinimumHeight(30)
        self.slider.setFixedWidth(600)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background-color: #2a2a2a;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background-color: #4a8bc2;
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
            QSlider::sub-page:horizontal {
                background-color: #4a8bc2;
                border-radius: 2px;
            }
        """)
        player_container.addWidget(self.slider, alignment=Qt.AlignCenter)

        track_info_layout = QHBoxLayout()
        self.track_label = QLabel("Ничего не играет")
        self.track_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.track_label.setFixedWidth(350)
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: #888888; font-size: 12px;")
        self.time_label.setFixedWidth(100)
        track_info_layout.addStretch()
        track_info_layout.addWidget(self.track_label)
        track_info_layout.addStretch()
        track_info_layout.addWidget(self.time_label)
        track_info_layout.addStretch()
        player_container.addLayout(track_info_layout)

        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(15)
        nav_layout.addStretch()
        self.prev_btn = self.icon_btn(make_previous_icon(), "Предыдущий трек")
        self.prev_btn.clicked.connect(self.previous_track)
        nav_layout.addWidget(self.prev_btn)
        self.play_pause_btn = self.icon_btn(make_play_icon(), "Воспроизвести")
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        nav_layout.addWidget(self.play_pause_btn)
        self.next_btn = self.icon_btn(make_next_icon(), "Следующий трек")
        self.next_btn.clicked.connect(self.next_track)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addStretch()
        player_container.addLayout(nav_layout)

        # Эффекты
        effects_layout = QHBoxLayout()
        effects_layout.setSpacing(20)
        effects_layout.addStretch()

        # Громкость
        volume_layout = QHBoxLayout()
        volume_layout.setSpacing(8)
        volume_label = QLabel("🔊")
        volume_label.setStyleSheet("font-size: 14px;")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(self.update_volume)
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_slider)
        effects_layout.addLayout(volume_layout)

        # Избранное
        self.fav_btn = self.icon_btn(make_favorite_icon(False), "Добавить в избранное")
        self.fav_btn.clicked.connect(self.toggle_favorite)
        effects_layout.addWidget(self.fav_btn)
        
        # Добавить в плейлист
        self.add_to_playlist_btn = self.icon_btn(make_add_to_playlist_icon(), "Добавить в плейлист")
        self.add_to_playlist_btn.clicked.connect(self.show_add_to_playlist_dialog)
        effects_layout.addWidget(self.add_to_playlist_btn)

        effects_layout.addStretch()
        player_container.addLayout(effects_layout)

        player_widget = QWidget()
        player_widget.setLayout(player_container)
        player_widget.setFixedWidth(700)
        player_wrapper.addWidget(player_widget)
        player_wrapper.addStretch()
        center.addLayout(player_wrapper)

        center_widget = QWidget()
        center_widget.setLayout(center)

        # ПРАВАЯ ПАНЕЛЬ
        right = QVBoxLayout()
        self.right_toggle_btn = QPushButton()
        self.right_toggle_btn.setFixedSize(32, 32)
        self.right_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.right_toggle_btn.clicked.connect(self.toggle_right_panel)
        self.right_toggle_btn.setIcon(make_arrow_icon("right"))
        self.right_toggle_btn.setIconSize(QSize(20, 20))
        self.right_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 16px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)

        self.right_content = QWidget()
        right_content_layout = QVBoxLayout(self.right_content)
        right_content_layout.setSpacing(10)

        self.playlist_selector = QListWidget()
        self.playlist_selector.itemDoubleClicked.connect(self.open_playlist_manager)
        self.playlist_view = QListWidget()
        self.playlist_view.itemDoubleClicked.connect(self.play_playlist_track)

        create_btn = self.btn("Создать плейлист")
        create_btn.clicked.connect(self.create_playlist)
        manage_btn = self.btn("Управление плейлистом")
        manage_btn.clicked.connect(self.open_playlist_manager)
        manage_btn.setStyleSheet("background-color: #4a8bc2; border-radius: 8px;")

        right_content_layout.addWidget(QLabel("Плейлисты"))
        right_content_layout.addWidget(self.playlist_selector)
        right_content_layout.addWidget(create_btn)
        right_content_layout.addWidget(manage_btn)
        right_content_layout.addWidget(QLabel("Треки в плейлисте"))
        right_content_layout.addWidget(self.playlist_view)

        right.addWidget(self.right_toggle_btn, alignment=Qt.AlignHCenter)
        right.addSpacing(10)
        right.addWidget(self.right_content)
        right.addStretch()

        self.right_widget = QWidget()
        self.right_widget.setLayout(right)
        self.right_widget.setMinimumWidth(60)
        self.right_widget.setMaximumWidth(self.right_widget_width)

        root.addWidget(self.left_widget)
        root.addWidget(center_widget, 1)
        root.addWidget(self.right_widget)

        self.setStyleSheet(STYLE)

    # ================= VOLUME CONTROL =================
    def update_volume(self, value):
        self.current_volume = value
        self.audio.setVolume(value / 100.0)

    # ================= MUSIC CONTROL =================
    def show_home(self):
        self.showing_search = False
        self.home_page.setVisible(True)
        self.results.setVisible(False)
        self.search_input.clear()

    def show_search_results(self):
        self.showing_search = True
        self.home_page.setVisible(False)
        self.results.setVisible(True)

    def get_recent_tracks(self):
        return self.recent_tracks[:10]

    def add_recent_track(self, track):
        self.recent_tracks = [t for t in self.recent_tracks if t.get('url') != track.get('url')]
        self.recent_tracks.insert(0, track)
        self.recent_tracks = self.recent_tracks[:20]
        self.save_user_data()

    def get_recommended_tracks(self):
        favorite_tracks = self.playlists.get("Любимое", [])
        if favorite_tracks:
            artists = list(set([t.get('artist', '') for t in favorite_tracks[:3]]))
            if artists:
                query = random.choice(artists)
                return get_tracks_with_full_audio(query, 5)
        return get_tracks_with_full_audio("popular", 5)

    def search_by_genre(self, genre):
        self.search_input.setText(genre)
        self.search_music()

    def on_result_clicked(self, item):
        self.play_track(item)

    def toggle_favorite(self):
        if not hasattr(self, 'current_track_data') or not self.current_track_data:
            QMessageBox.information(self, "Информация", "Сначала воспроизведите трек")
            return
        favorite_playlist = "Любимое"
        track_url = self.current_track_data["url"]
        found_index = -1
        for i, track in enumerate(self.playlists[favorite_playlist]):
            if track.get("url") == track_url:
                found_index = i
                break
        if found_index != -1:
            del self.playlists[favorite_playlist][found_index]
            self.fav_btn.setIcon(make_favorite_icon(False))
            self.fav_btn.setToolTip("Добавить в избранное")
        else:
            self.playlists[favorite_playlist].append(self.current_track_data)
            self.fav_btn.setIcon(make_favorite_icon(True))
            self.fav_btn.setToolTip("Удалить из избранного")
        self.save_user_data()
        if self.current_playlist == favorite_playlist:
            self.load_playlist_view()
    
    def show_add_to_playlist_dialog(self):
        if not hasattr(self, 'current_track_data') or not self.current_track_data:
            QMessageBox.information(self, "Информация", "Сначала воспроизведите трек")
            return
        
        # Проверка лимита плейлистов для demo версии
        user_playlists_count = len([p for p in self.playlists.keys() if p != "Любимое"])
        if user_playlists_count >= 3 and len(self.playlists) > 1:
            self.show_premium_message("Создание более 3 плейлистов")
            return
        
        if len(self.playlists) <= 1 and "Любимое" in self.playlists and len(self.playlists) == 1:
            if QMessageBox.question(self, "Нет плейлистов", 
                                   "У вас нет дополнительных плейлистов. Создать новый?",
                                   QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                self.create_playlist()
            return
        
        dialog = AddToPlaylistDialog(self.current_track_data, self.playlists, self)
        if dialog.exec() == QDialog.Accepted:
            selected_playlist = dialog.selected_playlist
            
            track_to_add = {
                "text": f"{self.current_track_data['title']} - {self.current_track_data['artist']}",
                "url": self.current_track_data["url"],
                "title": self.current_track_data['title'],
                "artist": self.current_track_data['artist'],
                "cover": self.current_track_data.get('cover', '')
            }
            
            self.playlists[selected_playlist].append(track_to_add)
            self.save_user_data()
            
            if selected_playlist == self.current_playlist:
                self.load_playlist_view()
            
            QMessageBox.information(self, "Успех", f"Трек добавлен в плейлист '{selected_playlist}'!")

    def toggle_play_pause(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_pause_btn.setIcon(make_play_icon())
            self.play_pause_btn.setToolTip("Воспроизвести")
        else:
            self.player.play()
            self.play_pause_btn.setIcon(make_pause_icon())
            self.play_pause_btn.setToolTip("Пауза")

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.next_track()

    def previous_track(self):
        if self.current_playlist_tracks and self.current_track_index > 0:
            self.current_track_index -= 1
            self.play_track_by_index(self.current_track_index)

    def next_track(self):
        if self.current_playlist_tracks and self.current_track_index < len(self.current_playlist_tracks) - 1:
            self.current_track_index += 1
            self.play_track_by_index(self.current_track_index)

    def play_track_by_index(self, index):
        if 0 <= index < len(self.current_playlist_tracks):
            track = self.current_playlist_tracks[index]
            self.player.setSource(QUrl(track["url"]))
            self.player.play()
            self.track_label.setText(track["text"])
            self.play_pause_btn.setIcon(make_pause_icon())
            self.play_pause_btn.setToolTip("Пауза")
            self.current_track_data = track
            self.update_favorite_icon()
            self.add_recent_track(track)

    def update_favorite_icon(self):
        if not self.current_track_data:
            return
        is_fav = False
        for t in self.playlists.get("Любимое", []):
            if t.get("url") == self.current_track_data["url"]:
                is_fav = True
                break
        self.fav_btn.setIcon(make_favorite_icon(is_fav))
        self.fav_btn.setToolTip("Удалить из избранного" if is_fav else "Добавить в избранное")

    def show_user_menu(self):
        menu = UserMenuDialog(self.username, self)
        pos = self.avatar_btn.mapToGlobal(QPoint(0, self.avatar_btn.height()))
        menu.move(pos)
        menu.exec()

    def switch_to_account(self, new_username):
        self.save_user_data()
        self.username = new_username
        self.user_data = load_user_data(new_username)
        self.playlists = self.user_data.get("playlists", {"Любимое": []})
        self.recent_tracks = self.user_data.get("recent", [])
        self.current_playlist = "Любимое"
        self.setWindowTitle(f"Lunar - {new_username}")
        self.avatar_btn.setIcon(make_avatar(new_username[0]))
        self.load_playlists()
        self.player.stop()
        self.track_label.setText("Ничего не играет")
        self.play_pause_btn.setIcon(make_play_icon())
        self.play_pause_btn.setToolTip("Воспроизвести")
        self.time_label.setText("00:00 / 00:00")
        self.slider.setRange(0, 0)
        self.volume_slider.setValue(50)
        
        # Правильно обновляем главную страницу
        old_home = self.home_page
        self.home_page = HomePageWidget(self)
        
        # Находим индекс домашней страницы в content_stack
        for i in range(self.content_stack.count()):
            widget = self.content_stack.itemAt(i).widget()
            if widget == old_home:
                self.content_stack.insertWidget(i, self.home_page)
                self.content_stack.removeWidget(old_home)
                break
        
        old_home.deleteLater()
        self.home_page.setVisible(True)
        self.results.setVisible(False)
        self.showing_search = False
        
        # Принудительно перестраиваем контент после небольшой задержки
        QTimer.singleShot(100, lambda: self.home_page.build_content())
        
        QMessageBox.information(self, "Смена аккаунта", f"Вы вошли как {new_username}")

    def switch_account(self):
        self.close()
        self.login = LoginWindow()
        self.login.show()

    def logout(self):
        self.close()
        self.login = LoginWindow()
        self.login.show()

    def toggle_left_panel(self):
        self.left_anim.stop()
        if self.left_widget.maximumWidth() == self.left_widget_width:
            new_width = 60
            self.left_toggle_btn.setIcon(make_arrow_icon("double-right"))
        else:
            new_width = self.left_widget_width
            self.left_toggle_btn.setIcon(make_arrow_icon("left"))
        self.left_anim.setStartValue(self.left_widget.maximumWidth())
        self.left_anim.setEndValue(new_width)
        self.left_anim.start()
        self.eq_panel.setVisible(new_width == self.left_widget_width)

    def toggle_right_panel(self):
        self.right_anim.stop()
        if self.right_widget.maximumWidth() == self.right_widget_width:
            new_width = 60
            self.right_toggle_btn.setIcon(make_arrow_icon("double-left"))
        else:
            new_width = self.right_widget_width
            self.right_toggle_btn.setIcon(make_arrow_icon("right"))
        self.right_anim.setStartValue(self.right_widget.maximumWidth())
        self.right_anim.setEndValue(new_width)
        self.right_anim.start()
        self.right_content.setVisible(new_width == self.right_widget_width)

    def save_user_data(self):
        user_data = {
            "playlists": self.playlists,
            "recent": self.recent_tracks,
            "settings": {}
        }
        save_user_data(self.username, user_data)

    def open_playlist_manager(self):
        if not self.current_playlist:
            QMessageBox.warning(self, "Ошибка", "Выберите плейлист для управления")
            return
        tracks = self.playlists.get(self.current_playlist, [])
        dialog = PlaylistManagerDialog(self.current_playlist, tracks.copy(), self)
        dialog.exec()

    def update_playlist(self, playlist_name, tracks):
        self.playlists[playlist_name] = tracks
        self.save_user_data()
        if playlist_name == self.current_playlist:
            self.load_playlist_view()
            if playlist_name == "Любимое" and self.current_track_data:
                self.update_favorite_icon()

    def delete_playlist(self, playlist_name):
        if playlist_name in self.playlists:
            del self.playlists[playlist_name]
            self.save_user_data()
            if self.current_playlist == playlist_name:
                if self.playlists:
                    self.current_playlist = list(self.playlists.keys())[0]
                else:
                    self.playlists["Любимое"] = []
                    self.current_playlist = "Любимое"
                    self.save_user_data()
            self.load_playlists()
            QMessageBox.information(self, "Успех", f"Плейлист '{playlist_name}' удален")

    def play_track_from_data(self, track):
        self.player.setSource(QUrl(track["url"]))
        self.player.play()
        self.track_label.setText(track["text"])
        self.play_pause_btn.setIcon(make_pause_icon())
        self.play_pause_btn.setToolTip("Пауза")
        self.current_track_data = track
        self.update_favorite_icon()
        self.add_recent_track(track)

    def load_playlists(self):
        self.playlist_selector.clear()
        for k in self.playlists:
            item = QListWidgetItem(k)
            if k == self.current_playlist:
                item.setSelected(True)
            self.playlist_selector.addItem(item)
        
        self.playlist_selector.itemSelectionChanged.connect(self.on_playlist_selected)
        self.load_playlist_view()
    
    def on_playlist_selected(self):
        selected_items = self.playlist_selector.selectedItems()
        if selected_items:
            self.current_playlist = selected_items[0].text()
            self.load_playlist_view()

    def search_music(self):
        q = self.search_input.text()
        if not q:
            return
        tracks = get_tracks_with_full_audio(q)
        self.search_results_data = tracks
        self.results.clear()
        for t in tracks:
            audio_url = t.get('preview')
            if audio_url:
                item = QListWidgetItem(f"{t['title']} - {t['artist']}")
                item.setData(Qt.UserRole, audio_url)
                item.setData(Qt.UserRole + 1, item.text())
                item.setData(Qt.UserRole + 2, t)
                self.results.addItem(item)
        if self.results.count() == 0:
            item = QListWidgetItem("Треки не найдены. Попробуйте другой запрос.")
            self.results.addItem(item)
        self.show_search_results()

    def play_track(self, item):
        track_url = item.data(Qt.UserRole)
        track_text = item.data(Qt.UserRole + 1)
        track_data = item.data(Qt.UserRole + 2)
        self.player.setSource(QUrl(track_url))
        self.player.play()
        self.track_label.setText(track_text)
        self.play_pause_btn.setIcon(make_pause_icon())
        self.play_pause_btn.setToolTip("Пауза")
        self.current_playlist_tracks = [{"url": track_url, "text": track_text, "title": track_data['title'], "artist": track_data['artist']}]
        self.current_track_index = 0
        self.current_track_data = {"url": track_url, "text": track_text, "title": track_data['title'], "artist": track_data['artist']}
        self.update_favorite_icon()
        self.add_recent_track(self.current_track_data)

    def play_playlist_track(self, item):
        track_index = self.playlist_view.currentRow()
        self.current_playlist_tracks = self.playlists.get(self.current_playlist, [])
        if 0 <= track_index < len(self.current_playlist_tracks):
            self.current_track_index = track_index
            track = self.current_playlist_tracks[track_index]
            self.player.setSource(QUrl(track["url"]))
            self.player.play()
            self.track_label.setText(track["text"])
            self.play_pause_btn.setIcon(make_pause_icon())
            self.play_pause_btn.setToolTip("Пауза")
            self.current_track_data = track
            self.update_favorite_icon()
            self.add_recent_track(track)

    def set_position(self, p):
        self.player.setPosition(p)

    def update_position(self, p):
        if not self.slider.isSliderDown():
            self.slider.setValue(p)
            current = self.format_time(p)
            total = self.format_time(self.player.duration())
            self.time_label.setText(f"{current} / {total}")

    def update_duration(self, d):
        self.slider.setRange(0, d)
        current = self.format_time(self.player.position())
        total = self.format_time(d)
        self.time_label.setText(f"{current} / {total}")

    def create_playlist(self):
        user_playlists_count = len([p for p in self.playlists.keys() if p != "Любимое"])
        if user_playlists_count >= 3:
            self.show_premium_message("Создание более 3 плейлистов")
            return

        name, ok = QInputDialog.getText(self, "Создать плейлист", "Введите название плейлиста:")
        if ok and name:
            if name in self.playlists:
                QMessageBox.warning(self, "Ошибка", "Плейлист с таким названием уже существует!")
                return
            self.playlists[name] = []
            self.save_user_data()
            self.load_playlists()
            self.current_playlist = name
            QMessageBox.information(self, "Успех", f"Плейлист '{name}' создан!")

    def load_playlist_view(self):
        self.playlist_view.clear()
        tracks = self.playlists.get(self.current_playlist, [])
        for i, t in enumerate(tracks, 1):
            item = QListWidgetItem(f"{i:02d}. {t['title']} - {t['artist']}")
            item.setData(Qt.UserRole, t["url"])
            self.playlist_view.addItem(item)


# ================= RUN =================

app = QApplication(sys.argv)
login = LoginWindow()
login.show()
sys.exit(app.exec())