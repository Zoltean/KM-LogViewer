from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QPushButton, QFileDialog,
    QVBoxLayout, QWidget, QMessageBox, QLabel, QHBoxLayout, QDialog, QProgressBar, QTableWidget, QTableWidgetItem
)
from PyQt5.QtGui import QTextCharFormat, QColor, QTextCursor
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
import json
from datetime import datetime
import sys
import time

class FilterProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filtering Logs")
        self.setStyleSheet("background-color: #E0E0E0;")
        self.setFixedSize(300, 100)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("QProgressBar {border: 2px solid gray; border-radius: 5px; padding: 1px; text-align: center;} QProgressBar::chunk {background: #4CAF50; width: 20px;}")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Filtering logs, please wait...", self))
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)


class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processing")
        self.setStyleSheet("background-color: #E0E0E0;")
        self.setFixedSize(300, 100)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("QProgressBar {border: 2px solid gray; border-radius: 5px; padding: 1px; text-align: center;} QProgressBar::chunk {background: #4CAF50; width: 20px;}")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Processing log file, please wait...", self))
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

class UpdateProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Updating Display")
        self.setStyleSheet("background-color: #E0E0E0;")
        self.setFixedSize(300, 100)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("QProgressBar {border: 2px solid gray; border-radius: 5px; padding: 1px; text-align: center;} QProgressBar::chunk {background: #4CAF50; width: 20px;}")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Updating log display, please wait...", self))
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

class LogProcessingThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.logs = []

    def run(self):
        try:
            start_time = time.time()
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            for idx, line in enumerate(lines):
                if line.strip():
                    log_parts, level = parse_log(line.strip())
                    self.logs.append((log_parts, level))
                # Emit combined progress
                self.progress.emit(int(((idx + 1) / total_lines * 50) + 0))
                QApplication.processEvents()
            

            self.finished.emit()
            end_time = time.time()
            
        except Exception as e:
            self.error.emit(str(e))

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

class LogViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_filter = None
        self.full_logs = []
        self.level_counts = {level: 0 for level in ["INFO", "WARNING", "ERROR", "CRITICAL", "DEBUG"]}
        self.progress_dialog = None
        self.update_progress_dialog = None
        self.filter_progress_dialog = None
        self.initUI()
        self.center()
        
    def initUI(self):
        self.setWindowTitle('Checkbox Kasa Log Viewer v0.0.2')
        self.setGeometry(100, 100, 1200, 800)
        
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("background-color: #E0E0E0; color: #000; font-size: 12pt;")
        
        self.open_file_button = QPushButton('Open Log File', self)
        self.open_file_button.clicked.connect(self.open_file)
        self.open_file_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14pt; padding: 5px; border-radius: 5px;")
        
        self.reset_button = QPushButton('RESET', self)
        self.reset_button.clicked.connect(self.reset_filter)
        self.reset_button.setStyleSheet("background-color: #f44336; color: white; font-size: 14pt; padding: 5px; border-radius: 5px;")
        
        self.stats_label = QLabel(self)
        self.stats_label.setStyleSheet("font-size: 16px; padding: 5px;")
        self.update_statistics()
        
        button_colors = {
            'INFO': 'green',
            'WARNING': '#FFA500',
            'ERROR': 'red',
            'CRITICAL': 'magenta',
            'DEBUG': '#00B2FF'
        }
        
        filter_buttons = {}
        for level, color in button_colors.items():
            button = QPushButton(level, self)
            button.clicked.connect(lambda _, lvl=level: self.filter_logs(lvl))
            button.setStyleSheet(f"background-color: {color}; color: white; font-size: 12pt; padding: 5px; border-radius: 5px;")
            filter_buttons[level] = button
        
        self.filter_buttons = filter_buttons
        
        file_layout = QVBoxLayout()
        file_layout.addWidget(self.open_file_button)
        file_layout.addWidget(self.reset_button)
        
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        for button in self.filter_buttons.values():
            filter_layout.addWidget(button)
        
        stats_layout = QVBoxLayout()
        stats_layout.addWidget(self.stats_label)
        
        h_layout = QHBoxLayout()
        h_layout.addLayout(file_layout)
        h_layout.addLayout(filter_layout)
        h_layout.addLayout(stats_layout)
        h_layout.addStretch()
        
        main_layout = QVBoxLayout()
        main_layout.addLayout(h_layout)
        main_layout.addWidget(self.text_edit)
        
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
    
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Log File", "", "Log Files (*.log)")
        if file_path:
            self.show_progress_dialog()
            self.thread = LogProcessingThread(file_path)
            self.thread.progress.connect(self.update_progress)
            self.thread.finished.connect(self.finish_processing)
            self.thread.error.connect(self.handle_error)
            self.thread.start()
    
    def show_progress_dialog(self):
        if self.progress_dialog is None:
            self.progress_dialog = ProgressDialog(self)
        self.progress_dialog.show()
        QApplication.processEvents()
    
    def hide_progress_dialog(self):
        if self.progress_dialog:
            self.progress_dialog.hide()
    
    def update_progress(self, value):
        if self.progress_dialog:
            self.progress_dialog.progress_bar.setValue(value)
    
    def finish_processing(self):
        self.hide_progress_dialog()
        self.show_update_progress_dialog()
        self.process_logs()
    
    def show_update_progress_dialog(self):
        if self.update_progress_dialog is None:
            self.update_progress_dialog = UpdateProgressDialog(self)
        self.update_progress_dialog.show()
        QApplication.processEvents()
    
    def hide_update_progress_dialog(self):
        if self.update_progress_dialog:
            self.update_progress_dialog.hide()
    
    def process_logs(self):
        self.text_edit.clear()
        self.full_logs.clear()
        self.level_counts = {level: 0 for level in self.level_counts}

        total_logs = len(self.thread.logs)
        self.current_log_index = 0
        self.total_logs = total_logs

        self.full_logs = self.thread.logs.copy()

        self.process_next_batch()

    
    def process_next_batch(self):
        if self.current_log_index >= self.total_logs:
            self.hide_update_progress_dialog()
            self.update_statistics()
            return

        
        batch_size = 10
        end_index = min(self.current_log_index + batch_size, self.total_logs)

        for idx in range(self.current_log_index, end_index):
            log_parts, level = self.thread.logs[idx]
            if not self.current_filter or level == self.current_filter:
                self.append_log_parts(log_parts)
        
            if level in self.level_counts:
                self.level_counts[level] += 1

        # Оновлюємо прогрес
        progress_value = int(((end_index) / self.total_logs) * 100)
        if self.update_progress_dialog:
            self.update_progress_dialog.progress_bar.setValue(progress_value)

        self.current_log_index = end_index

        QTimer.singleShot(0, self.process_next_batch)
    
    def append_log_parts(self, log_parts):
        cursor = self.text_edit.textCursor()
        for text, fg_color, bg_color in log_parts:
            cursor.movePosition(QTextCursor.End)
            char_format = self.create_char_format(fg_color, bg_color)
            cursor.insertText(text, char_format)
        cursor.insertText("\n" + "-"*80 + "\n", self.create_char_format(QColor('black'), QColor('#E0E0E0')))
        self.text_edit.verticalScrollBar().setValue(self.text_edit.verticalScrollBar().maximum())
    
    def filter_logs(self, level):
        if not self.full_logs:
            QMessageBox.warning(self, "No Logs Loaded", "No logs have been loaded. Please open a log file first.")
            return
        
        self.current_filter = level
        self.show_filter_progress_dialog()
        self.text_edit.clear()
        
        total_logs = len(self.full_logs)
        self.current_log_index = 0
        self.total_logs = total_logs
        
        QTimer.singleShot(0, self.process_filtered_logs)
    
    def show_filter_progress_dialog(self):
        if self.filter_progress_dialog is None:
            self.filter_progress_dialog = FilterProgressDialog(self)
        self.filter_progress_dialog.show()
        QApplication.processEvents()
    
    def hide_filter_progress_dialog(self):
        if self.filter_progress_dialog:
            self.filter_progress_dialog.hide()
    
    def process_filtered_logs(self):
        if self.current_log_index >= self.total_logs:
            self.hide_filter_progress_dialog()
            self.update_statistics()
            return

        batch_size = 10
        end_index = min(self.current_log_index + batch_size, self.total_logs)

        for idx in range(self.current_log_index, end_index):
            log_parts, level = self.full_logs[idx]
            if self.current_filter is None or level == self.current_filter:
                self.append_log_parts(log_parts)

            if level in self.level_counts:
                self.level_counts[level] += 1

        progress_value = int(((end_index) / self.total_logs) * 100)
        if self.filter_progress_dialog:
            self.filter_progress_dialog.progress_bar.setValue(progress_value)

        self.current_log_index = end_index

        QTimer.singleShot(0, self.process_filtered_logs)
    
    def reset_filter(self):
        if not self.full_logs:
            QMessageBox.warning(self, "No Logs Loaded", "No logs have been loaded. Please open a log file first.")
            return
        
        self.current_filter = None
        self.show_filter_progress_dialog()
        self.text_edit.clear()

        self.current_log_index = 0
        self.total_logs = len(self.full_logs)
        
        QTimer.singleShot(0, self.process_filtered_logs)
    
    def update_statistics(self):
        button_colors = {
            'INFO': 'green',
            'WARNING': '#FFA500',
            'ERROR': 'red',
            'CRITICAL': 'magenta',
            'DEBUG': '#00B2FF'
        }
        
        stats_text = "\n".join(f"<span style='color: {button_colors[level]};'>{level}: {count}</span>" for level, count in self.level_counts.items())
        self.stats_label.setText(f"Log Levels Count:<br>{stats_text}")

    def create_char_format(self, fg_color, bg_color):
        char_format = QTextCharFormat()
        char_format.setForeground(fg_color)
        char_format.setBackground(bg_color)
        
        font = char_format.font()
        font.setPointSize(12)
        char_format.setFont(font)
        
        return char_format
    
    def center(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        window_geometry = self.geometry()
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        self.setGeometry(x, y, window_geometry.width(), window_geometry.height())

    def handle_error(self, error_message):
        QMessageBox.critical(self, "Error", f"An error occurred: {error_message}")
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = LogViewer()
    viewer.show()
    sys.exit(app.exec_())
