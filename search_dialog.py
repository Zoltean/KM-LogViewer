from PyQt5.QtWidgets import QDialog, QLineEdit, QPushButton, QVBoxLayout, QLabel, QHBoxLayout, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt

class SearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Search Logs')
        self.setModal(True)
        self.setFixedSize(400, 120)
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()

        # Title Label
        self.search_label = QLabel('Enter search term:')
        self.search_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #333;")
        self.layout.addWidget(self.search_label, alignment=Qt.AlignCenter)

        input_layout = QHBoxLayout()

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText('Type search term here...')
        self.search_input.setStyleSheet("font-size: 14pt; border: 1px solid #ccc; border-radius: 5px;")
        self.search_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Make it expand horizontally
        input_layout.addWidget(self.search_input)

        self.search_button = QPushButton('Search', self)
        self.search_button.setStyleSheet(
            "background-color: #4CAF50; color: white; font-size: 14pt; padding: 10px; border-radius: 5px;")
        self.search_button.clicked.connect(self.perform_search)
        input_layout.addWidget(self.search_button)

        self.layout.addLayout(input_layout)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(spacer)

        self.setLayout(self.layout)

    def perform_search(self):
        search_text = self.search_input.text()
        if search_text:
            self.parent().filter_logs(search_text)
        self.accept()
