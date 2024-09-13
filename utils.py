import json
from datetime import datetime

from PyQt5.QtWidgets import QDialog, QProgressBar, QLabel, QVBoxLayout
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt

class CustomProgressDialog(QDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setStyleSheet("background-color: #E0E0E0;")
        self.setFixedSize(300, 100)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet(
            "QProgressBar {border: 2px solid gray; border-radius: 5px; padding: 1px; text-align: center;} "
            "QProgressBar::chunk {background: #4CAF50; width: 20px;}"
        )

        layout = QVBoxLayout()
        layout.addWidget(QLabel(message, self))
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

def format_timestamp(timestamp_str):
    if timestamp_str.endswith('Z'):
        timestamp_str = timestamp_str[:-1] + '+00:00'
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    except ValueError:
        return timestamp_str

def parse_log(log_str):
    try:
        log = json.loads(log_str)
        record = log.get('record', {})

        timestamp = format_timestamp(record.get('time', {}).get('repr', 'Unknown time'))
        level = record.get('level', {}).get('name', 'UNKNOWN')
        message = record.get('message', 'No message')

        level_formats = {
            "INFO": (QColor('green'), QColor('#E0E0E0')),
            "WARNING": (QColor('white'), QColor('#FFA500')),
            "ERROR": (QColor('white'), QColor('red')),
            "CRITICAL": (QColor('white'), QColor('magenta')),
            "DEBUG": (QColor('#00B2FF'), QColor('#E0E0E0'))
        }
        fg_color, bg_color = level_formats.get(level, (QColor('black'), QColor('#E0E0E0')))

        output_parts = [
            ("Timestamp: ", QColor('blue'), QColor('#E0E0E0')),
            (f"{timestamp}\n", QColor('black'), QColor('#E0E0E0')),
            ("Level: ", QColor('blue'), QColor('#E0E0E0')),
            (f"{level}\n", fg_color, bg_color),
            ("Message: ", QColor('blue'), QColor('#E0E0E0')),
            (f"{message}\n", QColor('black'), QColor('#E0E0E0'))
        ]

        extra = record.get('extra', {})
        if extra:
            for key, value in extra.items():
                output_parts.extend([
                    (f"  {key}: ", QColor('blue'), QColor('#E0E0E0')),
                    (json.dumps(value, indent=4, ensure_ascii=False) + "\n", QColor('black'), QColor('#E0E0E0'))
                ])

        return output_parts, level
    except json.JSONDecodeError as e:
        return [(f"Error parsing log string: {e}", QColor('red'), QColor('#E0E0E0'))], 'ERROR'
    except KeyError as e:
        return [(f"Missing expected key: {e}", QColor('red'), QColor('#E0E0E0'))], 'ERROR'
    except Exception as e:
        return [(f"An unexpected error occurred: {e}", QColor('red'), QColor('#E0E0E0'))], 'ERROR'
