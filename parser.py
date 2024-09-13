from PyQt5.QtCore import QThread, pyqtSignal
import time
import json

from PyQt5.QtWidgets import QApplication
from utils import parse_log

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
                self.progress.emit(int(((idx + 1) / total_lines * 50) + 0))
                QApplication.processEvents()

            self.finished.emit()
            end_time = time.time()

        except Exception as e:
            self.error.emit(str(e))
