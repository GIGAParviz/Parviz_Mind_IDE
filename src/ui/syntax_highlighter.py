from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
import re

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6")) 
        keyword_format.setFontWeight(QFont.Weight.Bold)
        keywords = ["def", "class", "import", "from", "if", "else", "elif",
                   "try", "except", "finally", "for", "while", "return", "yield",
                   "and", "or", "not", "in", "parviz", "self" , "__init__" , "is", "None",
                   "print" , "len",   "True", "False", "with", "as"]
        
        for word in keywords:
            pattern = f"\\b{word}\\b"
            self.highlighting_rules.append((pattern, keyword_format))

        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#DCDCAA")) 
        self.highlighting_rules.append((r"\b[A-Za-z0-9_]+(?=\s*\()", function_format))
        
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178")) 
        self.highlighting_rules.append((r"\".*?\"", string_format))
        self.highlighting_rules.append((r"\'.*?\'", string_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))  
        self.highlighting_rules.append((r"#[^\n]*", comment_format))
        
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#B5CEA8")) 
        self.highlighting_rules.append((r"\b[0-9]+\b", number_format))
        
        class_format = QTextCharFormat()
        class_format.setForeground(QColor("#4EC9B0"))  
        class_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((r"\bclass\s+([A-Za-z0-9_]+)", class_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), format) 