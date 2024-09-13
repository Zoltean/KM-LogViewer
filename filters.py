from PyQt5.QtGui import QTextCursor, QColor, QTextCharFormat
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer
from utils import CustomProgressDialog

class LogFilter:
    def __init__(self, text_edit, level_counts, full_logs, update_statistics):
        self.text_edit = text_edit
        self.level_counts = level_counts
        self.full_logs = full_logs
        self.update_statistics = update_statistics
        self.current_filter = None
        self.current_log_index = 0
        self.total_logs = 0
        self.filter_progress_dialog = None

    def filter_logs(self, level):
        if not self.full_logs:
            QMessageBox.warning(None, "No Logs Loaded", "No logs have been loaded. Please open a log file first.")
            print("DEBUG: No logs loaded. self.full_logs is empty.")
            return

        self.current_filter = level
        self.reset_statistics()
        self.show_filter_progress_dialog()
        self.text_edit.clear()

        self.current_log_index = 0
        self.total_logs = len(self.full_logs)
        print(f"DEBUG: Filtering logs for level: {self.current_filter}, total logs: {self.total_logs}")

        QTimer.singleShot(0, self.process_filtered_logs)

    def show_filter_progress_dialog(self):
        self.filter_progress_dialog = CustomProgressDialog("Filtering Logs", "Filtering logs, please wait...", None)
        self.filter_progress_dialog.show()

    def hide_filter_progress_dialog(self):
        if self.filter_progress_dialog:
            self.filter_progress_dialog.hide()

    def process_filtered_logs(self):
        if self.current_log_index >= self.total_logs:
            self.hide_filter_progress_dialog()
            return

        batch_size = 10
        end_index = min(self.current_log_index + batch_size, self.total_logs)

        for idx in range(self.current_log_index, end_index):
            log_parts, level = self.full_logs[idx]
            if self.current_filter is None or level == self.current_filter:
                self.append_log_parts(log_parts)

        self.filter_progress_dialog.progress_bar.setValue(int(((end_index) / self.total_logs) * 100))

        self.current_log_index = end_index

        QTimer.singleShot(0, self.process_filtered_logs)

    def reset_filter(self):
        if not self.full_logs:
            QMessageBox.warning(None, "No Logs Loaded", "No logs have been loaded. Please open a log file first.")
            return

        self.current_filter = None
        self.reset_statistics()
        self.show_filter_progress_dialog()
        self.text_edit.clear()

        self.current_log_index = 0
        self.total_logs = len(self.full_logs)
        print(f"DEBUG: Resetting filter, total logs: {self.total_logs}")

        QTimer.singleShot(0, self.process_filtered_logs)

    def reset_statistics(self):
        """Resets log statistics counters."""
        self.level_counts = {level: 0 for level in ["INFO", "WARNING", "ERROR", "CRITICAL", "DEBUG"]}

    def append_log_parts(self, log_parts):
        cursor = self.text_edit.textCursor()
        for text, fg_color, bg_color in log_parts:
            cursor.movePosition(QTextCursor.End)
            char_format = self.create_char_format(fg_color, bg_color)
            cursor.insertText(text, char_format)
        cursor.insertText("\n" + "-" * 80 + "\n", self.create_char_format(QColor('black'), QColor('#E0E0E0')))
        self.text_edit.verticalScrollBar().setValue(self.text_edit.verticalScrollBar().maximum())

    def create_char_format(self, fg_color, bg_color):
        char_format = QTextCharFormat()
        char_format.setForeground(fg_color)
        char_format.setBackground(bg_color)

        font = char_format.font()
        font.setPointSize(12)
        char_format.setFont(font)

        return char_format
