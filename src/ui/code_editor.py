from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt 

class CodeEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont('Consolas', 12))
        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        
        self.auto_pairs = {
            '(': ')',
            '[': ']',
            '{': '}',
            '"': '"',
            "'": "'"
        }
        
        self.textChanged.connect(self.on_text_changed)
        self.cursorPositionChanged.connect(self.on_cursor_position_changed)
        
    def on_text_changed(self):
        """Make sure scroll position is updated when text changes"""
        self.verticalScrollBar().valueChanged.emit(self.verticalScrollBar().value())
        
    def on_cursor_position_changed(self):
        """Ensure cursor is visible and scrolled to when position changes"""
        self.ensureCursorVisible()
        
    def keyPressEvent(self, event):
        cursor = self.textCursor()
        text = event.text()
        
        if text in self.auto_pairs:
            cursor.insertText(text)
            cursor.insertText(self.auto_pairs[text])
            cursor.movePosition(cursor.MoveOperation.Left, cursor.MoveMode.MoveAnchor, 1)
            self.setTextCursor(cursor)
        elif event.key() == Qt.Key.Key_Backspace and not cursor.hasSelection():
            current_pos = cursor.position()
            if current_pos > 0:
                cursor.movePosition(cursor.MoveOperation.Left, cursor.MoveMode.KeepAnchor, 1)
                left_char = cursor.selectedText()
                cursor.movePosition(cursor.MoveOperation.Right, cursor.MoveMode.MoveAnchor, 1)
                
                if current_pos < len(self.toPlainText()) and left_char in self.auto_pairs:
                    cursor.movePosition(cursor.MoveOperation.Right, cursor.MoveMode.KeepAnchor, 1)
                    right_char = cursor.selectedText()
                    if right_char == self.auto_pairs[left_char]:
                        cursor.removeSelectedText()
                        cursor.deletePreviousChar()
                        return
            super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
        
        
        
        
