from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QPushButton, QFileDialog,
    QVBoxLayout, QWidget, QLabel, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import QTimer
from search_dialog import SearchDialog
from parser import LogProcessingThread
from utils import CustomProgressDialog
from filters import LogFilter

class LogViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.full_logs = []
        self.filtered_logs = []
        self.level_counts = {level: 0 for level in ["INFO", "WARNING", "ERROR", "CRITICAL", "DEBUG"]}
        self.text_edit = None
        self.log_filter = None

        self.initUI()
        self.initialize_log_filter()
        self.center()

    def initUI(self):
        self.setWindowTitle('Checkbox Kasa Log Viewer v0.1.0')
        self.setGeometry(100, 100, 1200, 800)

        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("background-color: #E0E0E0; color: #000; font-size: 12pt;")

        self.open_file_button = self.create_button('Open Log File', self.open_file, "#4CAF50")
        self.reset_button = self.create_button('RESET', self.reset_filter, "#f44336")
        self.search_button = self.create_button('Search Logs', self.open_search_dialog, "#2196F3")

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
            level: self.create_button(level, lambda _, lvl=level: self.log_filter.filter_logs(lvl), color)
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

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.search_button)
        button_layout.addStretch()

        h_layout = QHBoxLayout()
        h_layout.addLayout(file_layout)
        h_layout.addLayout(filter_layout)
        h_layout.addLayout(stats_layout)
        h_layout.addLayout(button_layout)

        main_layout = QVBoxLayout()
        main_layout.addLayout(h_layout)
        main_layout.addWidget(self.text_edit)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def initialize_log_filter(self):
        self.log_filter = LogFilter(self.text_edit, self.level_counts, self.full_logs, self.update_statistics)

    def create_button(self, text, handler, color):
        button = QPushButton(text, self)
        button.setStyleSheet(
            f"background-color: {color}; color: white; font-size: 14pt; padding: 5px; border-radius: 5px;")
        button.clicked.connect(handler)
        return button

    def open_search_dialog(self):
        self.search_dialog = SearchDialog(self)
        self.search_dialog.exec_()

    def filter_logs(self, search_text):
        def log_to_string(log):
            if isinstance(log[0], tuple):
                return ''.join(str(item) for item in log[0])
            else:
                return ''.join(str(item) for item in log[0])

        self.filtered_logs = [
            log for log in self.full_logs
            if search_text.lower() in log_to_string(log).lower()
        ]

        if not self.filtered_logs:
            QMessageBox.information(self, "Search Results", "No results found for the search term.")
            self.text_edit.clear()
        else:
            self.process_filtered_logs()

    def process_filtered_logs(self):
        self.text_edit.clear()
        self.level_counts = {level: 0 for level in self.level_counts}

        for log_parts, level in self.filtered_logs:
            self.log_filter.append_log_parts(log_parts)
            if level in self.level_counts:
                self.level_counts[level] += 1

    def center(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        window_geometry = self.geometry()
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        self.setGeometry(x, y, window_geometry.width(), window_geometry.height())

    def handle_error(self, error_message):
        QMessageBox.critical(self, "Error", f"An error occurred: {error_message}")

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
        self.level_counts = {level: 0 for level in self.level_counts}

        if not self.thread.logs:
            return

        self.full_logs = self.thread.logs.copy()
        self.log_filter.full_logs = self.full_logs
        self.log_filter.current_log_index = 0
        self.log_filter.total_logs = len(self.full_logs)

        self.process_next_batch()

    def process_next_batch(self):
        if self.log_filter.current_log_index >= self.log_filter.total_logs:
            self.hide_update_progress_dialog()
            self.update_statistics()
            return

        batch_size = 20
        end_index = min(self.log_filter.current_log_index + batch_size, self.log_filter.total_logs)

        for idx in range(self.log_filter.current_log_index, end_index):
            log_parts, level = self.full_logs[idx]
            if not self.log_filter.current_filter or level == self.log_filter.current_filter:
                self.log_filter.append_log_parts(log_parts)

            if level in self.level_counts:
                self.level_counts[level] += 1

        progress_value = int(((end_index) / self.log_filter.total_logs) * 100)
        self.update_progress_dialog.progress_bar.setValue(progress_value)

        self.log_filter.current_log_index = end_index

        QTimer.singleShot(0, self.process_next_batch)

    def update_statistics(self):
        button_colors = {
            'INFO': 'green',
            'WARNING': '#FFA500',
            'ERROR': 'red',
            'CRITICAL': 'magenta',
            'DEBUG': '#00B2FF'
        }

        try:
            stats_text = "\n".join(
                f"<span style='color: {button_colors[level]};'>{level}: {count}</span>"
                for level, count in self.level_counts.items()
                if isinstance(count, int) and isinstance(level, str)
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generating stats text: {e}")
            raise

        self.stats_label.setText(f"Log Levels Count:<br>{stats_text}")

    def reset_filter(self):
        if self.log_filter:
            self.log_filter.reset_filter()

if __name__ == '__main__':
    app = QApplication([])
    viewer = LogViewer()
    viewer.show()
    app.exec_()
