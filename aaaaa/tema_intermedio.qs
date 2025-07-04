* {
    font-family: 'Segoe UI', sans-serif;
    font-size: {font_size};
}

QMainWindow {
    background-color: #f5f2eb;
    color: #333;
}

QMenuBar, QMenu {
    background-color: #e8e6dc;
    color: #333;
}

QMenu::item:selected {
    background-color: #d7d3c8;
}

QToolBar {
    background-color: #e8e6dc;
}

QDialog, QDockWidget, QWidget {
    background-color: #f5f2eb;
    color: #333;
}

QLabel, QListWidget, QLineEdit, QTextEdit, QSpinBox, QTableWidget, QPushButton {
    background-color: #ffffff;
    color: #333;
    border: 1px solid #ccc;
    padding: 4px;
}

QLineEdit:focus, QTextEdit:focus, QSpinBox:focus {
    border: 1px solid {accent_color};
}

QPushButton {
    border-radius: 4px;
    padding: 4px 8px;
    background-color: {accent_color};
    color: white;
}

QPushButton:hover {
    background-color: #ddd;
}

QHeaderView::section {
    background-color: #e0ddd3;
    color: #333;
    padding: 6px;
    font-weight: bold;
}

QTableWidget {
    gridline-color: #bbb;
    selection-background-color: #c9c5bb;
    selection-color: #000;
    alternate-background-color: #eae6de;
}

QTableWidget::item {
    padding: 6px;
}
