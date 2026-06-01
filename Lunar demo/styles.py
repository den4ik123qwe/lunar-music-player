STYLE = """
QWidget {
    background-color: #121212;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
}

QPushButton {
    background-color: #2a2a2a;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #3a3a3a;
}

QPushButton:pressed {
    background-color: #1a1a1a;
}

QLineEdit {
    background-color: #1e1e1e;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    padding: 8px;
}

QLineEdit:focus {
    border: 1px solid #4a8bc2;
}

QListWidget {
    background-color: #1e1e1e;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    outline: none;
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

QSlider::handle:horizontal:hover {
    background-color: #5a9bd2;
}

QSlider::sub-page:horizontal {
    background-color: #4a8bc2;
    border-radius: 2px;
}

QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #3a3a3a;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4a4a4a;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QMenu {
    background-color: #252525;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
}

QMenu::item {
    padding: 6px 20px;
    background-color: transparent;
}

QMenu::item:selected {
    background-color: #3a6ea5;
}

QToolTip {
    background-color: #252525;
    color: #e0e0e0;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    padding: 4px;
}
"""