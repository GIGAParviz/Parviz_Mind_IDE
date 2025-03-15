from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                           QLineEdit, QPushButton, QLabel, QMessageBox)
from PyQt6.QtGui import QFont

class ChatPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = QLabel("  AI ASSISTANT")
        header.setStyleSheet("background-color: #252526; padding: 5px; font-size: 11px;")
        layout.addWidget(header)
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont('Consolas', 10))
        self.chat_display.setStyleSheet("border: none; padding: 10px;")
        layout.addWidget(self.chat_display)
        
        input_container = QWidget()
        input_container.setStyleSheet("background-color: #252526; border-top: 1px solid #3E3E3E;")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(10, 5, 10, 5)
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask the AI about your code...")
        self.chat_input.setStyleSheet("padding: 5px;")
        self.chat_input.returnPressed.connect(self.send_chat)
        input_layout.addWidget(self.chat_input)
        
        self.send_btn = QPushButton('Send')
        self.send_btn.clicked.connect(self.send_chat)
        input_layout.addWidget(self.send_btn)
        
        layout.addWidget(input_container)
        
    def send_chat(self):
        query = self.chat_input.text().strip()
        if not query:
            return
            
        self.chat_display.append(f"<div style='margin-bottom: 10px;'><span style='color: #569CD6; font-weight: bold;'>You:</span> {query}</div>")
        self.chat_input.clear()
        
        if hasattr(self.parent, 'send_chat'):
            self.parent.query = query
            self.parent.send_chat() 