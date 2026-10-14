"""全局扁平化 QSS 样式。

设计要点：
- 浅色底 + 白色圆角卡片，无渐变、无立体边框
- 主题色 #4A7CF7，选中态用浅色底 + 主题色文字
"""

ACCENT = "#4A7CF7"
ACCENT_DARK = "#3B68D9"
ACCENT_SOFT = "#EEF3FF"
BG = "#F5F6FA"
CARD = "#FFFFFF"
BORDER = "#E6E9F0"
TEXT = "#2A3042"
MUTED = "#8A93A6"

QSS = f"""
* {{
    font-family: "Microsoft YaHei UI", "Segoe UI", "PingFang SC", sans-serif;
    font-size: 13px;
}}
QMainWindow, QWidget {{
    background: {BG};
    color: {TEXT};
}}

/* ---------- 侧边栏 ---------- */
QWidget#sidebar {{
    background: {CARD};
    border-right: 1px solid {BORDER};
}}
QLabel#brand {{
    font-size: 16px;
    font-weight: 700;
    color: {TEXT};
    padding: 4px 18px 16px 18px;
}}
QLabel#ver {{
    color: #A6AEC0;
    font-size: 11px;
}}
QListWidget#nav {{
    background: transparent;
    border: none;
    outline: none;
}}
QListWidget#nav::item {{
    min-height: 44px;
    padding-left: 14px;
    color: #5A6376;
    border: none;
    border-radius: 8px;
    margin: 2px 10px;
}}
QListWidget#nav::item:hover {{
    background: #F3F5FA;
    color: {TEXT};
}}
QListWidget#nav::item:selected {{
    background: {ACCENT_SOFT};
    color: {ACCENT};
    font-weight: 600;
}}

/* ---------- 页面 ---------- */
QLabel#pageTitle {{
    font-size: 20px;
    font-weight: 700;
    color: {TEXT};
}}
QLabel#pageSub {{
    color: {MUTED};
    font-size: 12px;
}}
QLabel#hint {{
    color: {MUTED};
    font-size: 12px;
}}
QLabel#dropTitle {{
    font-size: 14px;
    font-weight: 600;
    color: #5A6376;
}}

QFrame#card {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
}}
QFrame#dropzone {{
    background: #FAFBFE;
    border: 2px dashed #C9D4F0;
    border-radius: 12px;
}}
QFrame#dropzone:hover {{
    border-color: {ACCENT};
    background: #F2F6FF;
}}

/* ---------- 按钮 ---------- */
QPushButton {{
    background: {CARD};
    color: {TEXT};
    border: 1px solid #D9DEE8;
    border-radius: 6px;
    padding: 7px 18px;
}}
QPushButton:hover {{
    border-color: {ACCENT};
    color: {ACCENT};
}}
QPushButton:pressed {{
    background: #F0F3FA;
}}
QPushButton:disabled {{
    background: #F2F4F8;
    color: #B3BAC7;
    border-color: {BORDER};
}}
QPushButton#primary {{
    background: {ACCENT};
    color: #FFFFFF;
    border: none;
    font-weight: 600;
}}
QPushButton#primary:hover {{
    background: {ACCENT_DARK};
    color: #FFFFFF;
}}
QPushButton#primary:pressed {{
    background: #3560C8;
}}
QPushButton#primary:disabled {{
    background: #B9CDF8;
    color: #FFFFFF;
}}

/* ---------- 输入控件 ---------- */
QLineEdit, QComboBox, QSpinBox {{
    background: {CARD};
    border: 1px solid #D9DEE8;
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border-color: {ACCENT};
}}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled {{
    background: #F2F4F8;
    color: #B3BAC7;
}}
QComboBox::drop-down {{
    border: none;
    width: 26px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {MUTED};
    margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 4px;
    selection-background-color: {ACCENT_SOFT};
    selection-color: {ACCENT};
    outline: none;
}}

/* ---------- 单选框 / 复选框 ---------- */
QRadioButton, QCheckBox {{
    spacing: 6px;
    color: #5A6376;
}}
QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 2px solid #C2CAD8;
    background: {CARD};
}}
QRadioButton::indicator:checked {{
    border: 5px solid {ACCENT};
    background: {CARD};
}}
QRadioButton:checked, QCheckBox:checked {{
    color: {ACCENT};
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 2px solid #C2CAD8;
    background: {CARD};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}

/* ---------- 列表 ---------- */
QListWidget#files {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 4px;
    outline: none;
}}
QListWidget#files::item {{
    padding: 6px 8px;
    border-radius: 5px;
}}
QListWidget#files::item:selected {{
    background: {ACCENT_SOFT};
    color: {ACCENT};
}}

/* ---------- 进度条 ---------- */
QProgressBar {{
    background: #EDF0F6;
    border: none;
    border-radius: 5px;
    min-height: 8px;
    max-height: 8px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: {ACCENT};
    border-radius: 5px;
}}

/* ---------- 日志 ---------- */
QPlainTextEdit#log {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 8px;
    color: #5A6376;
    font-family: Consolas, "Microsoft YaHei UI", monospace;
    font-size: 12px;
    padding: 4px;
}}

/* ---------- 滚动条 ---------- */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: #D3D9E4;
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: #B9C2D2;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
    margin: 2px;
}}
QScrollBar::handle:horizontal {{
    background: #D3D9E4;
    border-radius: 5px;
    min-width: 30px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

QToolTip {{
    background: {TEXT};
    color: #FFFFFF;
    border: none;
    padding: 6px 8px;
    border-radius: 4px;
}}
"""
