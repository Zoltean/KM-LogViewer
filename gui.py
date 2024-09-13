from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QPushButton, QFileDialog,
    QVBoxLayout, QWidget, QLabel, QHBoxLayout, QDialog, QProgressBar, QMessageBox
)
from PyQt5.QtGui import QTextCharFormat, QColor, QTextCursor
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from parser import LogProcessingThread
from utils import CustomProgressDialog, format_timestamp, parse_log

class LogViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_filter = None
        self.full_logs = []
        self.level_counts = {level: 0 for level in ["INFO", "WARNING", "ERROR", "CRITICAL", "DEBUG"]}
        self.initUI()
        self.center()

    def initUI(self):
        self.setWindowTitle('Checkbox Kasa Log Viewer v0.0.3')
        self.setGeometry(100, 100, 1200, 800)

        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("background-color: #E0E0E0; color: #000; font-size: 12pt;")

        self.open_file_button = self.create_button('Open Log File', self.open_file, "#4CAF50")
        self.reset_button = self.create_button('RESET', self.reset_filter, "#f44336")

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

        filter_buttons = {
            level: self.create_button(level, lambda _, lvl=level: self.filter_logs(lvl), color)
            for level, color in button_colors.items()
        }

        file_layout = QVBoxLayout()
        file_layout.addWidget(self.open_file_button)
        file_layout.addWidget(self.reset_button)

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        for button in filter_buttons.values():
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

    def create_button(self, text, handler, color):
        button = QPushButton(text, self)
        button.setStyleSheet(f"background-color: {color}; color: white; font-size: 14pt; padding: 5px; border-radius: 5px;")
        button.clicked.connect(handler)
        return button

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
        self.progress_dialog = CustomProgressDialog("Processing", "Processing log file, please wait...", self)
        self.progress_dialog.show()
        QApplication.processEvents()

    def hide_progress_dialog(self):
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.hide()

    def update_progress(self, value):
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.progress_bar.setValue(value)

    def finish_processing(self):
        self.hide_progress_dialog()
        self.show_update_progress_dialog()
        self.process_logs()

    def show_update_progress_dialog(self):
        self.update_progress_dialog = CustomProgressDialog("Updating Display", "Updating log display, please wait...", self)
        self.update_progress_dialog.show()
        QApplication.processEvents()

    def hide_update_progress_dialog(self):
        if hasattr(self, 'update_progress_dialog') and self.update_progress_dialog:
            self.update_progress_dialog.hide()

    def process_logs(self):
        self.text_edit.clear()
        self.full_logs.clear()
        self.reset_statistics()  # Сброс статистики перед подсчетом

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

        self.update_progress_dialog.progress_bar.setValue(int(((end_index) / self.total_logs) * 100))

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
        self.reset_statistics()  # Сброс статистики перед применением фильтра
        self.show_filter_progress_dialog()
        self.text_edit.clear()

        self.current_log_index = 0
        self.total_logs = len(self.full_logs)

        QTimer.singleShot(0, self.process_filtered_logs)

    def show_filter_progress_dialog(self):
        self.filter_progress_dialog = CustomProgressDialog("Filtering Logs", "Filtering logs, please wait...", self)
        self.filter_progress_dialog.show()
        QApplication.processEvents()

    def hide_filter_progress_dialog(self):
        if hasattr(self, 'filter_progress_dialog') and self.filter_progress_dialog:
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

        self.filter_progress_dialog.progress_bar.setValue(int(((end_index) / self.total_logs) * 100))

        self.current_log_index = end_index

        QTimer.singleShot(0, self.process_filtered_logs)

    def reset_filter(self):
        if not self.full_logs:
            QMessageBox.warning(self, "No Logs Loaded", "No logs have been loaded. Please open a log file first.")
            return

        self.current_filter = None
        self.reset_statistics()  # Сброс статистики при сбросе фильтра
        self.show_filter_progress_dialog()
        self.text_edit.clear()

        self.current_log_index = 0
        self.total_logs = len(self.full_logs)

        QTimer.singleShot(0, self.process_filtered_logs)

    def reset_statistics(self):
        """Сбрасывает счетчики статистики логов."""
        self.level_counts = {level: 0 for level in ["INFO", "WARNING", "ERROR", "CRITICAL", "DEBUG"]}

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
    app = QApplication([])
    viewer = LogViewer()
    viewer.show()
    app.exec_()
