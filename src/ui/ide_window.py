from PyQt6.QtWidgets import (QMainWindow, QTextEdit, QVBoxLayout, 
                           QHBoxLayout, QWidget, QPushButton, QFileDialog, 
                           QMessageBox, QTreeView, QSplitter, QTabWidget,
                           QLineEdit, QLabel, QComboBox, QDialog, QFormLayout,
                           QRadioButton, QGroupBox)
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import (Qt, QAbstractItemModel, QModelIndex, QVariant, QDir, 
                        QThread, pyqtSignal)
import os
import re
from .code_editor import CodeEditor
from .syntax_highlighter import PythonHighlighter
from .file_system_model import SimpleFileSystemModel
from ..services.llm_service import AIModelWorker

def get_file_system_model():
    """Get the appropriate file system model for the file explorer"""
    try:
        try:
            from PyQt6.QtWidgets import QFileSystemModel
            return QFileSystemModel
        except ImportError:
            try:
                from PyQt6.QtCore import QFileSystemModel
                return QFileSystemModel
            except ImportError:
                try:
                    from PyQt6.QtGui import QFileSystemModel
                    return QFileSystemModel
                except ImportError:
                    return None
    except Exception as e:
        print(f"Error importing QFileSystemModel: {str(e)}")
        return None

class SimpleIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file = None
        # Settings for LLM model
        self.model_settings = {
            "use_groq": True,
            "groq_model": "deepseek-r1-distill-llama-70b",
            "groq_api_key": "",
            "use_local": False,
            "local_model": "deepseek-r1:8b"
        }
        self.initUI()
        self.chat_history = []
        
    def initUI(self):
        self.setWindowTitle('Parviz Mind IDE')
        self.setGeometry(100, 100, 1400, 900)
        
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1E1E1E;
                color: #D4D4D4;
            }
            QTextEdit, QLineEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #3E3E3E;
                border-radius: 2px;
                padding: 2px;
                selection-background-color: #264F78;
            }
            QPushButton {
                background-color: #0E639C;
                color: white;
                border: none;
                border-radius: 2px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #1177BB;
            }
            QPushButton:pressed {
                background-color: #0D5C91;
            }
            QTreeView {
                background-color: #252526;
                color: #D4D4D4;
                border: none;
                alternate-background-color: #2D2D2D;
            }
            QTreeView::item:selected {
                background-color: #094771;
            }
            QSplitter::handle {
                background-color: #3E3E3E;
            }
            QLabel {
                color: #D4D4D4;
                font-weight: bold;
            }
        """)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(main_splitter)
        
        code_widget = QWidget()
        code_layout = QVBoxLayout(code_widget)
        code_layout.setContentsMargins(0, 0, 0, 0)
        code_layout.setSpacing(0)
        main_splitter.addWidget(code_widget)
        
        editor_splitter = QSplitter(Qt.Orientation.Horizontal)
        code_layout.addWidget(editor_splitter)

        file_tree_widget = QWidget()
        file_tree_layout = QVBoxLayout(file_tree_widget)
        file_tree_layout.setContentsMargins(0, 0, 0, 0)
        
        explorer_header = QWidget()
        explorer_header.setStyleSheet("background-color: #252526;")
        explorer_header_layout = QHBoxLayout(explorer_header)
        explorer_header_layout.setContentsMargins(5, 5, 5, 5)
        
        explorer_label = QLabel("EXPLORER")
        explorer_label.setStyleSheet("font-size: 11px;")
        explorer_header_layout.addWidget(explorer_label)
        
        explorer_header_layout.addStretch()
        
        self.explorer_toggle_btn = QPushButton("◀")
        self.explorer_toggle_btn.setMaximumWidth(25)
        self.explorer_toggle_btn.setToolTip("Hide Explorer")
        self.explorer_toggle_btn.clicked.connect(self.toggle_explorer)
        explorer_header_layout.addWidget(self.explorer_toggle_btn)
        
        refresh_btn = QPushButton("⟳")
        refresh_btn.setMaximumWidth(25)
        refresh_btn.setToolTip("Refresh Explorer")
        refresh_btn.clicked.connect(self.refresh_file_tree)
        explorer_header_layout.addWidget(refresh_btn)
        
        folder_btn = QPushButton("📁")
        folder_btn.setMaximumWidth(25)
        folder_btn.setToolTip("Change Folder")
        folder_btn.clicked.connect(self.change_root_folder)
        explorer_header_layout.addWidget(folder_btn)
        
        file_tree_layout.addWidget(explorer_header)
        self.file_tree = QTreeView()
        self.file_tree.setHeaderHidden(True)  
        self.file_tree.setAnimated(True)
        self.file_tree.setIndentation(15)
        
        self.file_tree.setStyleSheet("""
            QTreeView {
                background-color: #252526; 
                color: #D4D4D4;
                border: none;
                font-family: 'Segoe UI', sans-serif;
                font-size: 9pt;
            }
            QTreeView::item {
                padding: 3px 0px;
                border: none;
            }
            QTreeView::item:selected {
                background-color: #094771;
            }
            QTreeView::item:hover {
                background-color: #2A2D2E;
            }
        """)
        
        QFileSystemModelClass = get_file_system_model()
        
        try:
            if QFileSystemModelClass:
                self.file_model = QFileSystemModelClass()
                current_dir = os.path.dirname(os.path.abspath(__file__))
                self.file_model.setRootPath(current_dir)
                
                for i in range(1, self.file_model.columnCount()):
                    self.file_tree.hideColumn(i)
                    
                self.file_tree.setRootIndex(self.file_model.index(current_dir))
                self.using_qt_model = True
            else:
                self.file_model = SimpleFileSystemModel()
                current_dir = os.path.dirname(os.path.abspath(__file__))
                self.file_model.setRootPath(current_dir)
                self.file_tree.setRootIndex(self.file_model.index(0, 0))
                self.using_qt_model = False
        except Exception as e:
            print(f"Error initializing file system model: {str(e)}")
            self.file_model = SimpleFileSystemModel()
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.file_model.setRootPath(current_dir)
            self.file_tree.setRootIndex(self.file_model.index(0, 0))
            self.using_qt_model = False
            
        self.file_tree.setModel(self.file_model)
        
        self.file_tree.setRootIsDecorated(True)
        self.file_tree.setItemsExpandable(True)  
        self.file_tree.setUniformRowHeights(True) 
        self.file_tree.setAlternatingRowColors(False) 
        self.file_tree.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers) 
        self.file_tree.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)  
        
        self.file_tree.setExpanded(self.file_tree.rootIndex(), False)
        
        self.file_tree.doubleClicked.connect(self.file_tree_double_clicked)
        
        file_tree_layout.addWidget(self.file_tree)
        
        editor_splitter.addWidget(file_tree_widget)

        editor_container = QWidget()
        editor_container_layout = QVBoxLayout(editor_container)
        editor_container_layout.setContentsMargins(0, 0, 0, 0)
        editor_container_layout.setSpacing(0)
        
        self.file_header = QLabel("Untitled")
        self.file_header.setStyleSheet("background-color: #2D2D30; padding: 5px; border-bottom: 1px solid #3E3E3E;")
        editor_container_layout.addWidget(self.file_header)
        
        editor_with_line_numbers = QWidget()
        editor_with_line_numbers_layout = QHBoxLayout(editor_with_line_numbers)
        editor_with_line_numbers_layout.setContentsMargins(0, 0, 0, 0)
        editor_with_line_numbers_layout.setSpacing(0)
        
        self.line_numbers = QTextEdit()
        self.line_numbers.setReadOnly(True)
        self.line_numbers.setMaximumWidth(50)
        self.line_numbers.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.line_numbers.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.line_numbers.setStyleSheet("background-color: #1E1E1E; color: #858585; border-right: 1px solid #3E3E3E; padding-right: 5px; text-align: right;")
        editor_with_line_numbers_layout.addWidget(self.line_numbers)
        
        self.editor = CodeEditor()
        self.editor.textChanged.connect(self.update_line_numbers)
        
        self.editor.verticalScrollBar().valueChanged.connect(self.sync_line_numbers_scroll)
        
        editor_with_line_numbers_layout.addWidget(self.editor)
        
        editor_container_layout.addWidget(editor_with_line_numbers)
        
        self.highlighter = PythonHighlighter(self.editor.document())
        
        button_bar = QWidget()
        button_bar.setStyleSheet("background-color: #252526; border-top: 1px solid #3E3E3E;")
        button_layout = QHBoxLayout(button_bar)
        button_layout.setContentsMargins(10, 5, 10, 5)
        
        self.new_btn = QPushButton('New')
        self.open_btn = QPushButton('Open')
        self.save_btn = QPushButton('Save')
        self.run_btn = QPushButton('Run')
        self.settings_btn = QPushButton('Settings')

        button_layout.addWidget(self.new_btn)
        button_layout.addWidget(self.open_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.run_btn)
        button_layout.addWidget(self.settings_btn)
        button_layout.addStretch()

        self.new_btn.clicked.connect(self.new_file)
        self.open_btn.clicked.connect(self.open_file)
        self.save_btn.clicked.connect(self.save_file)
        self.run_btn.clicked.connect(self.run_code)
        self.settings_btn.clicked.connect(self.show_settings_dialog)
        
        editor_container_layout.addWidget(button_bar)
        editor_splitter.addWidget(editor_container)
        
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        main_splitter.addWidget(chat_widget)
        
        chat_header = QWidget()
        chat_header.setStyleSheet("background-color: #252526;")
        chat_header_layout = QHBoxLayout(chat_header)
        chat_header_layout.setContentsMargins(5, 5, 5, 5)
        
        chat_label = QLabel("AI ASSISTANT")
        chat_label.setStyleSheet("font-size: 11px;")
        chat_header_layout.addWidget(chat_label)
        
        chat_header_layout.addStretch()
        
        self.chat_toggle_btn = QPushButton("▶")
        self.chat_toggle_btn.setMaximumWidth(25)
        self.chat_toggle_btn.setToolTip("Hide Chat")
        self.chat_toggle_btn.clicked.connect(self.toggle_chat)
        chat_header_layout.addWidget(self.chat_toggle_btn)
        
        chat_layout.addWidget(chat_header)
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont('Consolas', 10))
        self.chat_display.setStyleSheet("border: none; padding: 10px;")
        chat_layout.addWidget(self.chat_display)
        
        file_selection_container = QWidget()
        file_selection_container.setStyleSheet("background-color: #252526; border-top: 1px solid #3E3E3E;")
        file_selection_layout = QVBoxLayout(file_selection_container)
        file_selection_layout.setContentsMargins(10, 5, 10, 5)
        
        file_selection_header = QWidget()
        file_selection_header_layout = QHBoxLayout(file_selection_header)
        file_selection_header_layout.setContentsMargins(0, 0, 0, 0)
        
        file_selection_label = QLabel("Files for Context:")
        file_selection_header_layout.addWidget(file_selection_label)
        
        file_selection_header_layout.addStretch()
        
        self.add_file_btn = QPushButton("Add File")
        self.add_file_btn.clicked.connect(self.add_file_to_context)
        file_selection_header_layout.addWidget(self.add_file_btn)
        
        self.clear_files_btn = QPushButton("Clear All")
        self.clear_files_btn.clicked.connect(self.clear_context_files)
        file_selection_header_layout.addWidget(self.clear_files_btn)
        
        file_selection_layout.addWidget(file_selection_header)
        
        self.file_list = QTextEdit()
        self.file_list.setReadOnly(True)
        self.file_list.setMaximumHeight(80)
        self.file_list.setStyleSheet("background-color: #1E1E1E; padding: 5px;")
        file_selection_layout.addWidget(self.file_list)
        
        self.context_files = []
        
        chat_layout.addWidget(file_selection_container)
        
        chat_input_container = QWidget()
        chat_input_container.setStyleSheet("background-color: #252526; border-top: 1px solid #3E3E3E;")
        chat_input_layout = QHBoxLayout(chat_input_container)
        chat_input_layout.setContentsMargins(10, 5, 10, 5)
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask the AI about your code...")
        self.chat_input.setStyleSheet("padding: 5px;")
        self.chat_input.returnPressed.connect(self.send_chat)
        chat_input_layout.addWidget(self.chat_input)
        
        self.send_btn = QPushButton('Send')
        self.send_btn.clicked.connect(self.send_chat)
        chat_input_layout.addWidget(self.send_btn)
        
        chat_layout.addWidget(chat_input_container)
        
        main_splitter.setSizes([800, 400])  
        editor_splitter.setSizes([300, 500]) 
        
        file_tree_widget.setMinimumWidth(250)
        
        self.file_tree.setColumnWidth(0, 220) 
        self.file_tree.setTextElideMode(Qt.TextElideMode.ElideMiddle) 
        self.file_tree.setFont(QFont('Segoe UI', 9))
        
        self.update_line_numbers()
        self.show()
    
    def update_line_numbers(self):
        """Update line numbers in the editor"""
        text = self.editor.toPlainText()
        line_count = text.count('\n') + 1
        
        font_metrics = self.editor.fontMetrics()
        line_height = font_metrics.lineSpacing()
        
        line_numbers_text = ''
        for i in range(1, line_count + 1):
            line_numbers_text += f"{i}\n"
        
        self.line_numbers.setFont(self.editor.font())
        
        self.line_numbers.setText(line_numbers_text)
        
        self.line_numbers.verticalScrollBar().setValue(
            self.editor.verticalScrollBar().value())
        
        if self.current_file:
            self.file_header.setText(os.path.basename(self.current_file))
        else:
            self.file_header.setText("Untitled")
            
    def file_tree_double_clicked(self, index):
        """Handle double click on file tree items"""
        path = self.file_model.filePath(index)
        if os.path.isfile(path):
            self.open_file(path)
        elif os.path.isdir(path):
            self.file_tree.setExpanded(index, not self.file_tree.isExpanded(index))

    def new_file(self):
        self.editor.clear()
        self.current_file = None
        self.file_header.setText("Untitled")
        self.update_line_numbers()

    def open_file(self, path=None):
        if not path:
            start_dir = os.path.dirname(self.current_file) if self.current_file else (
                self.file_model.rootPath() if hasattr(self.file_model, 'rootPath') else os.getcwd()
            )
            
            path, _ = QFileDialog.getOpenFileName(
                self, 
                "Open File", 
                start_dir,
                "Python Files (*.py);;All Files (*)",
                options=QFileDialog.Option.ReadOnly
            )
        
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.editor.setText(f.read())
                self.current_file = path
                self.file_header.setText(os.path.basename(path))
                self.update_line_numbers()
                
                file_dir = os.path.dirname(path)
                try:
                    if self.using_qt_model:
                        self.file_model.setRootPath(file_dir)
                        self.file_tree.setRootIndex(self.file_model.index(file_dir))
                    else:
                        self.file_model.setRootPath(file_dir)
                        self.file_tree.setRootIndex(self.file_model.index(0, 0))
                        if hasattr(self.file_model, 'refresh'):
                            self.file_model.refresh()
                        
                    self.setWindowTitle(f'Parviz Mind IDE - {path}')
                except Exception as e:
                    print(f"Error updating file tree: {str(e)}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not open file: {str(e)}")

    def run_code(self):
        if not self.current_file:
            QMessageBox.warning(self, "Warning", "Please save the file first")
            return
    
        try:
            self.save_file()
            
            if not hasattr(self, 'terminal_output'):
                self.terminal_output = QTextEdit()
                self.terminal_output.setReadOnly(True)
                self.terminal_output.setFont(QFont('Consolas', 10))
                self.terminal_output.setStyleSheet("""
                    background-color: #1E1E1E;
                    color: #CCCCCC;
                    border: none;
                    padding: 10px;
                """)
                
                terminal_header = QWidget()
                terminal_header.setStyleSheet("background-color: #252526;")
                terminal_header_layout = QHBoxLayout(terminal_header)
                terminal_header_layout.setContentsMargins(5, 5, 5, 5)
                
                terminal_label = QLabel("TERMINAL")
                terminal_label.setStyleSheet("font-size: 11px;")
                terminal_header_layout.addWidget(terminal_label)
                
                terminal_header_layout.addStretch()
                
                self.terminal_toggle_btn = QPushButton("▼")
                self.terminal_toggle_btn.setMaximumWidth(25)
                self.terminal_toggle_btn.setToolTip("Hide Terminal")
                self.terminal_toggle_btn.clicked.connect(self.toggle_terminal)
                terminal_header_layout.addWidget(self.terminal_toggle_btn)
                
                editor_container_layout = self.editor.parent().parent().layout()
                editor_container_layout.addWidget(terminal_header)
                editor_container_layout.addWidget(self.terminal_output)
                
                editor_height = self.editor.height()
                self.terminal_output.setMaximumHeight(int(editor_height * 0.25))
            else:
                self.terminal_output.show()
                self.terminal_output.parent().layout().itemAt(
                    self.terminal_output.parent().layout().count() - 2).widget().show()
                self.terminal_toggle_btn.setText("▼")
                self.terminal_toggle_btn.setToolTip("Hide Terminal")
            
            self.terminal_output.clear()
            
            self.terminal_output.append("<span style='color: #569CD6;'>Running script...</span>")
            
            file_dir = os.path.dirname(self.current_file)
            if not file_dir:  
                file_dir = os.getcwd()
            
            self.terminal_output.append(f"<span style='color: #6A9955;'>Working directory: {file_dir}</span>")
            
            import subprocess
            process = subprocess.Popen(
                ['python', self.current_file], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                cwd=file_dir, 
                universal_newlines=True  
            )
            stdout, stderr = process.communicate()
        
            if stdout:
                self.terminal_output.append(f"<pre>{stdout}</pre>")
            
            if stderr:
                self.terminal_output.append(f"<span style='color: #F44747;'>{stderr}</span>")
                
            exit_code = process.returncode
            if exit_code == 0:
                self.terminal_output.append("<span style='color: #6A9955;'>Process completed successfully.</span>")
            else:
                self.terminal_output.append(f"<span style='color: #F44747;'>Process exited with code {exit_code}.</span>")
            
        except Exception as e:
            if hasattr(self, 'terminal_output'):
                self.terminal_output.append(f"<span style='color: #F44747;'>Error: {str(e)}</span>")
            else:
                QMessageBox.critical(self, "Error", f"Could not run code: {str(e)}")
    
    def send_chat(self):
        query = self.chat_input.text().strip()
        if not query:
            return
            
        self.query = query
        
        self.chat_display.append(f"<div style='margin-bottom: 10px;'><span style='color: #569CD6; font-weight: bold;'>You:</span> {query}</div>")
        self.chat_input.clear()
        
        editor_code = self.editor.toPlainText()
        
        file_contexts = {}
        for file_path in self.context_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_contexts[file_path] = f.read()
            except Exception as e:
                self.chat_display.append(f"<div style='margin-bottom: 10px;'><span style='color: #F44747;'>Error reading file {file_path}: {str(e)}</span></div>")
        
        self.chat_display.append("<div style='margin-bottom: 10px;'><span style='color: #4EC9B0; font-weight: bold;'>AI:</span> <em>Thinking...</em></div>")
        self.worker = AIModelWorker(query, editor_code, self.model_settings, file_contexts)
        self.worker.response_ready.connect(self.handle_llm_response)
        self.worker.code_suggestion.connect(self.handle_code_suggestion)
        self.worker.file_changes.connect(self.handle_file_changes)  
        self.worker.start()
    
    
    def handle_llm_response(self, response):
        current_text = self.chat_display.toHtml()
        if "<em>Thinking...</em>" in current_text:
            current_text = current_text.replace("<div style='margin-bottom: 10px;'><span style='color: #4EC9B0; font-weight: bold;'>AI:</span> <em>Thinking...</em></div>", "")
            self.chat_display.setHtml(current_text)
        
        formatted_response = response
        
        code_blocks = re.findall(r'```python\n(.*?)```', response, re.DOTALL)
        
        for code_block in code_blocks:
            placeholder = f"```python\n{code_block}```"
            styled_block = f"""<div style='background-color: #1E1E1E; color: #D4D4D4; 
                            font-family: Consolas, monospace; padding: 10px; 
                            border: 1px solid #3E3E3E; border-radius: 5px; 
                            margin: 10px 0; white-space: pre; overflow-x: auto;'>
                            {self.syntax_highlight_for_html(code_block)}
                            </div>"""
            formatted_response = formatted_response.replace(placeholder, styled_block)
        
        self.chat_display.append(f"<div style='margin-bottom: 15px;'><span style='color: #4EC9B0; font-weight: bold;'>AI:</span> {formatted_response}</div>")
        
        self.chat_history.append(self.query)
    
    def syntax_highlight_for_html(self, code):
        """Apply syntax highlighting to code for HTML display"""
        code = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        keywords = ["def", "class", "import", "from", "if", "else", "elif",
                   "try", "except", "finally", "for", "while", "return", "yield",
                   "and", "or", "not", "in", "parviz", "self" , "__init__" , "is", "None",
                   "print" , "len",   "True", "False", "with", "as"]
        
        for keyword in keywords:
            code = re.sub(f"\\b{keyword}\\b", f"<span style='color: #569CD6; font-weight: bold;'>{keyword}</span>", code)
        
        code = re.sub(r'(".*?")', r"<span style='color: #CE9178;'>\1</span>", code)
        code = re.sub(r"('.*?')", r"<span style='color: #CE9178;'>\1</span>", code)
        
        code = re.sub(r"(#[^\n]*)", r"<span style='color: #6A9955;'>\1</span>", code)

        code = re.sub(r"\b([A-Za-z0-9_]+)(?=\s*\()", r"<span style='color: #DCDCAA;'>\1</span>", code)
        
        return code
    
    def refresh_file_tree(self):
        """Refresh the file tree view"""
        if hasattr(self.file_model, 'refresh'):
            self.file_model.refresh()

        self.file_tree.update()
        
    def change_root_folder(self):
        """Change the root folder for the file explorer using standard Windows dialog"""
        folder = QFileDialog.getExistingDirectory(
            self, 
            "Select Folder", 
            os.path.dirname(self.current_file) if self.current_file else os.getcwd(),
            options=QFileDialog.Option.ReadOnly | QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            try:
                if self.using_qt_model:
                    self.file_model.setRootPath(folder)
                    self.file_tree.setRootIndex(self.file_model.index(folder))
                else:
                    self.file_model.setRootPath(folder)
                    self.file_tree.setRootIndex(self.file_model.index(0, 0))
                
                self.file_tree.setExpanded(self.file_tree.rootIndex(), False)
                self.setWindowTitle(f'Parviz Mind IDE - {folder}')
                
                if self.current_file:
                    self.new_file()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not change folder: {str(e)}")

    def get_current_code(self):
        """Return the current code in editor"""
        return self.editor.toPlainText()
        
    def update_editor_content(self, code):
        """Update the editor with new code"""
        print("Updating editor content with new code")  
        
        if self.current_file:
            try:
                backup_file = f"{self.current_file}.backup"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(self.editor.toPlainText())
                    print(f"Backup created at: {backup_file}")
            except Exception as e:
                print(f"Error creating backup: {str(e)}") 
                QMessageBox.warning(self, "Backup Warning", 
                                 f"Could not create backup file: {str(e)}")
        
        old_code = self.editor.toPlainText()
        self.editor.setText(code)
        self.update_line_numbers()
        
        QMessageBox.information(self, "Code Updated", "The code has been updated in the editor.")
        
        print(f"Code changed from {len(old_code)} characters to {len(code)} characters")
        
        if self.current_file:
            reply = QMessageBox.question(
                self,
                'Save Changes',
                'Would you like to save these changes to the current file?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.save_file()
        else:
            reply = QMessageBox.question(
                self,
                'Save File',
                'Would you like to save this code to a file?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.save_file()

    def save_file(self):
        if not self.current_file:
            path, _ = QFileDialog.getSaveFileName(self, "Save File", "", 
                                                "Python Files (*.py);;All Files (*)")
            if not path:
                return
            self.current_file = path
            self.file_header.setText(os.path.basename(path))

        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save file: {str(e)}")
    
    def handle_code_suggestion(self, code, explanation):
        """Handle code suggestions from the LLM worker"""
        print("Received code suggestion, length:", len(code))  
        
        current_text = self.chat_display.toHtml()
        if "<em>Thinking...</em>" in current_text:
            current_text = current_text.replace("<div style='margin-bottom: 10px;'><span style='color: #4EC9B0; font-weight: bold;'>AI:</span> <em>Thinking...</em></div>", "")
            self.chat_display.setHtml(current_text)
        
        formatted_explanation = explanation.replace("\n", "<br>")
        self.chat_display.append(f"<div style='margin-bottom: 15px;'><span style='color: #4EC9B0; font-weight: bold;'>AI:</span> {formatted_explanation}</div>")
        
        styled_code = f"""<div style='background-color: #1E1E1E; color: #D4D4D4; 
                        font-family: Consolas, monospace; padding: 10px; 
                        border: 1px solid #3E3E3E; border-radius: 5px; 
                        margin: 10px 0; white-space: pre; overflow-x: auto;'>
                        {self.syntax_highlight_for_html(code)}
                        </div>"""
        
        self.chat_display.append(f"<div style='margin-bottom: 15px;'><span style='color: #4EC9B0; font-weight: bold;'>Suggested Code:</span> {styled_code}</div>")

        reply = QMessageBox.question(
            self,
            'Code Modification',
            'Would you like to apply these changes to your code?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            print("User accepted code changes, updating editor...") 
            self.update_editor_content(code)
        else:
            print("User rejected code changes")
            self.chat_display.append("<div style='margin-bottom: 15px;'><span style='color: #4EC9B0;'>Code changes were not applied.</span></div>")
    
    def sync_line_numbers_scroll(self, value):
        """Sync the line numbers scrollbar with the editor's scrollbar"""
        self.line_numbers.verticalScrollBar().setValue(value)
    
    def show_settings_dialog(self):
        """Show a dialog for configuring LLM settings"""
        settings_dialog = QDialog(self)
        settings_dialog.setWindowTitle("LLM Settings")
        settings_dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(settings_dialog)
        
        model_group = QGroupBox("Model Selection")
        model_layout = QVBoxLayout(model_group)

        self.groq_radio = QRadioButton("Use Online Models")
        self.groq_radio.setChecked(self.model_settings["use_groq"])
        model_layout.addWidget(self.groq_radio)
        
        groq_form = QWidget()
        groq_form_layout = QFormLayout(groq_form)
        self.groq_model_combo = QComboBox()
        self.groq_model_combo.addItems([
            "deepseek-r1-distill-llama-70b", 
            "llama-3.3-70b-versatile", 
            "gemma2-9b-it",
            "qwen-2.5-coder-32b",
            "mistral-saba-24b",
            
        ])
        self.groq_model_combo.setCurrentText(self.model_settings["groq_model"])
        groq_form_layout.addRow("Model:", self.groq_model_combo)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setText(self.model_settings["groq_api_key"])
        self.api_key_input.setPlaceholderText("Optional: Leave empty to use default API key")
        groq_form_layout.addRow("API Key:", self.api_key_input)
        
        model_layout.addWidget(groq_form)
        
        self.local_radio = QRadioButton("Use Local Models")
        self.local_radio.setChecked(self.model_settings["use_local"])
        model_layout.addWidget(self.local_radio)
        
        local_form = QWidget()
        local_form_layout = QFormLayout(local_form)
        self.local_model_input = QLineEdit()
        self.local_model_input.setText(self.model_settings["local_model"])
        self.local_model_input.setPlaceholderText("Example: deepseek-r1:8b")
        local_form_layout.addRow("Model Name:", self.local_model_input)
        
        model_layout.addWidget(local_form)
        
        layout.addWidget(model_group)
        
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        save_btn.clicked.connect(lambda: self.save_settings(settings_dialog))
        cancel_btn.clicked.connect(settings_dialog.reject)
        
        settings_dialog.exec()
    
    def save_settings(self, dialog):
        """Save the settings from the dialog"""
        self.model_settings["use_groq"] = self.groq_radio.isChecked()
        self.model_settings["use_local"] = self.local_radio.isChecked()
        self.model_settings["groq_model"] = self.groq_model_combo.currentText()
        self.model_settings["groq_api_key"] = self.api_key_input.text()
        self.model_settings["local_model"] = self.local_model_input.text()
        
        dialog.accept()
        
        QMessageBox.information(self, "Settings Saved", "LLM settings have been updated.")
    
    def toggle_explorer(self):
        """Toggle the visibility of the file explorer"""
        file_tree_widget = self.file_tree.parent()
        editor_splitter = file_tree_widget.parent()
        
        if file_tree_widget.isVisible():
            self.explorer_btn_placeholder = self.explorer_toggle_btn.parentWidget()
            explorer_layout_index = self.explorer_btn_placeholder.layout().indexOf(self.explorer_toggle_btn)
            
            self.explorer_btn_placeholder.layout().removeWidget(self.explorer_toggle_btn)
            
            file_tree_widget.hide()
            
            if not hasattr(self, 'explorer_btn_container'):
                self.explorer_btn_container = QWidget()
                self.explorer_btn_container.setMaximumWidth(30)
                self.explorer_btn_container.setStyleSheet("background-color: #252526;")
                explorer_btn_container_layout = QVBoxLayout(self.explorer_btn_container)
                explorer_btn_container_layout.setContentsMargins(2, 5, 2, 5)
                
                editor_splitter.insertWidget(0, self.explorer_btn_container)
            
            self.explorer_btn_container.layout().addWidget(self.explorer_toggle_btn)
            self.explorer_toggle_btn.setText("▶")
            self.explorer_toggle_btn.setToolTip("Show Explorer")
            self.explorer_btn_container.show()
        else:
            if hasattr(self, 'explorer_btn_container'):
                self.explorer_btn_container.layout().removeWidget(self.explorer_toggle_btn)
                self.explorer_btn_container.hide()
            
            file_tree_widget.show()
            
            self.explorer_btn_placeholder.layout().insertWidget(0, self.explorer_toggle_btn)
            self.explorer_toggle_btn.setText("◀")
            self.explorer_toggle_btn.setToolTip("Hide Explorer")
    
    def toggle_chat(self):
        """Toggle the visibility of the chat panel"""
        chat_widget = self.chat_display.parent()
        main_splitter = chat_widget.parent()
        
        if chat_widget.isVisible():
            self.chat_btn_placeholder = self.chat_toggle_btn.parentWidget()
            chat_layout_index = self.chat_btn_placeholder.layout().indexOf(self.chat_toggle_btn)
            
            self.chat_btn_placeholder.layout().removeWidget(self.chat_toggle_btn)
            
            chat_widget.hide()
            
            if not hasattr(self, 'chat_btn_container'):
                self.chat_btn_container = QWidget()
                self.chat_btn_container.setMaximumWidth(30)
                self.chat_btn_container.setStyleSheet("background-color: #252526;")
                chat_btn_container_layout = QVBoxLayout(self.chat_btn_container)
                chat_btn_container_layout.setContentsMargins(2, 5, 2, 5)
                
                main_splitter.addWidget(self.chat_btn_container)
            
            self.chat_btn_container.layout().addWidget(self.chat_toggle_btn)
            self.chat_toggle_btn.setText("◀")
            self.chat_toggle_btn.setToolTip("Show Chat")
            self.chat_btn_container.show()
        else:
            if hasattr(self, 'chat_btn_container'):
                self.chat_btn_container.layout().removeWidget(self.chat_toggle_btn)
                self.chat_btn_container.hide()
            
            chat_widget.show()
            
            self.chat_btn_placeholder.layout().insertWidget(2, self.chat_toggle_btn)
            self.chat_toggle_btn.setText("▶")
            self.chat_toggle_btn.setToolTip("Hide Chat")
    
    def toggle_terminal(self):
        """Toggle the visibility of the terminal panel"""
        if not hasattr(self, 'terminal_output'):
            return  
            
        if self.terminal_output.isVisible():
            self.terminal_output.hide()
            terminal_header = self.terminal_output.parent().layout().itemAt(
                self.terminal_output.parent().layout().count() - 2).widget()
            terminal_header.findChild(QLabel).hide()
            self.terminal_toggle_btn.setText("▲")
            self.terminal_toggle_btn.setToolTip("Show Terminal")
            self.terminal_toggle_btn.show() 
        else:
            self.terminal_output.show()
            terminal_header = self.terminal_output.parent().layout().itemAt(
                self.terminal_output.parent().layout().count() - 2).widget()
            terminal_header.findChild(QLabel).show()
            self.terminal_toggle_btn.setText("▼")
            self.terminal_toggle_btn.setToolTip("Hide Terminal")
    
    def add_file_to_context(self):
        """Add a file to the context for the chatbot"""
        start_dir = os.path.dirname(self.current_file) if self.current_file else (
            self.file_model.rootPath() if hasattr(self.file_model, 'rootPath') else os.getcwd()
        )
        
        paths, _ = QFileDialog.getOpenFileNames(
            self, 
            "Select Files for Context", 
            start_dir,
            "All Files (*)",
            options=QFileDialog.Option.ReadOnly
        )
        
        if paths:
            for path in paths:
                if path not in self.context_files:
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        self.context_files.append(path)
                        
                        self._update_file_list_display()
                        
                    except Exception as e:
                        QMessageBox.warning(self, "Warning", f"Could not read file {path}: {str(e)}")
    
    def clear_context_files(self):
        """Clear all files from the context"""
        self.context_files = []
        self._update_file_list_display()
    
    def _update_file_list_display(self):
        """Update the display of the file list"""
        if not self.context_files:
            self.file_list.setText("<i>No files selected for context</i>")
        else:
            html = "<ul style='margin: 0; padding-left: 20px;'>"
            for file_path in self.context_files:
                file_name = os.path.basename(file_path)
                html += f"<li style='margin-bottom: 2px;'>{file_name} <span style='color: #858585; font-size: 8pt;'>({file_path})</span></li>"
            html += "</ul>"
            self.file_list.setHtml(html)
    
    def handle_file_changes(self, file_changes, explanation):
        """Handle multiple file changes from the LLM worker"""
        print(f"Received changes for {len(file_changes)} files") 
        
        current_text = self.chat_display.toHtml()
        if "<em>Thinking...</em>" in current_text:
            current_text = current_text.replace("<div style='margin-bottom: 10px;'><span style='color: #4EC9B0; font-weight: bold;'>AI:</span> <em>Thinking...</em></div>", "")
            self.chat_display.setHtml(current_text)
        
        formatted_explanation = explanation.replace("\n", "<br>")
        self.chat_display.append(f"<div style='margin-bottom: 15px;'><span style='color: #4EC9B0; font-weight: bold;'>AI:</span> {formatted_explanation}</div>")
        
        self.chat_display.append(f"<div style='margin-bottom: 15px;'><span style='color: #4EC9B0; font-weight: bold;'>Suggested File Changes:</span></div>")
        
        file_list_html = "<ul style='margin-top: 5px;'>"
        for filename in file_changes.keys():
            file_list_html += f"<li>{filename}</li>"
        file_list_html += "</ul>"
        
        self.chat_display.append(file_list_html)
        
        file_states = {}
        
        for filename, content in file_changes.items():
            # Sanitize filename first to remove any control characters
            clean_filename = filename.replace('\n', '').replace('\r', '')
            
            # Skip empty filenames
            if not clean_filename:
                continue
                
            # For relative filenames, resolve them against the workspace root
            if not os.path.isabs(clean_filename):
                # Check if filename starts with common directory patterns and handle them
                if clean_filename.startswith('src/') or clean_filename.startswith('tests/'):
                    # Keep the path as is, but make sure to use the correct OS separator
                    clean_path = clean_filename.replace('/', os.path.sep)
                    
                    # Use the current workspace as base directory
                    base_dir = os.getcwd()
                    full_path = os.path.join(base_dir, clean_path)
                else:
                    # Try to find the file in context files first
                    matched_file = None
                    for file_path in self.context_files:
                        if os.path.basename(file_path) == clean_filename:
                            matched_file = file_path
                            break
                    
                    if matched_file:
                        full_path = matched_file
                    else:
                        # Use current file directory or workspace root
                        base_dir = os.path.dirname(self.current_file) if self.current_file else os.getcwd()
                        full_path = os.path.join(base_dir, clean_filename)
            else:
                full_path = clean_filename
            
            # Normalize the path to fix potential issues
            full_path = os.path.normpath(full_path)
            
            # Print path information for debugging
            print(f"Filename: {clean_filename}")
            print(f"Full path: {full_path}")
            
            # Check if the file exists
            file_exists = os.path.isfile(full_path)
            
            # Get current content if file exists
            current_content = ""
            if file_exists:
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        current_content = f.read()
                except Exception as e:
                    print(f"Error reading file {full_path}: {str(e)}")
            
            file_states[clean_filename] = {
                'full_path': full_path,
                'exists': file_exists,
                'original_content': current_content,
                'new_content': content,
                'applied': False
            }
        
        # Ask user if they want to apply the changes
        message = f"The AI suggests changes to {len(file_states)} files. Would you like to preview and apply these changes?"
        preview_btn = QPushButton("Preview Changes")
        apply_all_btn = QPushButton("Apply All")
        cancel_btn = QPushButton("Cancel")
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Multiple File Changes")
        msg_box.setText(message)
        msg_box.addButton(preview_btn, QMessageBox.ButtonRole.ActionRole)
        msg_box.addButton(apply_all_btn, QMessageBox.ButtonRole.YesRole)
        msg_box.addButton(cancel_btn, QMessageBox.ButtonRole.NoRole)
        
        # Store the file states for later use in preview/apply
        self.pending_file_changes = file_states
        
        # Connect buttons
        preview_btn.clicked.connect(self.preview_file_changes)
        apply_all_btn.clicked.connect(self.apply_all_file_changes)
        
        msg_box.exec()
    
    def preview_file_changes(self):
        """Preview the changes for multiple files"""
        if not hasattr(self, 'pending_file_changes') or not self.pending_file_changes:
            return
        
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle("Preview File Changes")
        preview_dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(preview_dialog)
        
        file_selector = QComboBox()
        for filename in self.pending_file_changes.keys():
            file_selector.addItem(filename)
        
        layout.addWidget(QLabel("Select File:"))
        layout.addWidget(file_selector)
        
        preview_text = QTextEdit()
        preview_text.setReadOnly(True)
        preview_text.setFont(QFont('Consolas', 10))
        layout.addWidget(preview_text)
        
        button_layout = QHBoxLayout()
        apply_btn = QPushButton("Apply This File")
        close_btn = QPushButton("Close")
        
        button_layout.addStretch()
        button_layout.addWidget(apply_btn)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        def update_preview(filename):
            file_info = self.pending_file_changes[filename]
            if file_info['exists']:
                from difflib import unified_diff
                original_lines = file_info['original_content'].splitlines()
                new_lines = file_info['new_content'].splitlines()
                
                diff = list(unified_diff(
                    original_lines, 
                    new_lines,
                    fromfile=f"Original: {filename}",
                    tofile=f"Modified: {filename}",
                    lineterm=''
                ))
                
                diff_text = ""
                for line in diff:
                    color = "#D4D4D4"  
                    if line.startswith('+'):
                        color = "#6A9955" 
                    elif line.startswith('-'):
                        color = "#F44747" 
                    elif line.startswith('@@'):
                        color = "#569CD6" 
                    
                    diff_text += f"<span style='color: {color};'>{line}</span><br>"
                
                preview_text.setHtml(f"""
                <div style='font-family: Consolas, monospace; white-space: pre;'>
                {diff_text}
                </div>
                """)
            else:
                preview_text.setHtml(f"""
                <div style='color: #6A9955; font-family: Consolas, monospace;'>
                # New file will be created: {filename}
                </div>
                <pre style='color: #D4D4D4; font-family: Consolas, monospace;'>
                {file_info['new_content']}
                </pre>
                """)
        
        file_selector.currentTextChanged.connect(update_preview)
        close_btn.clicked.connect(preview_dialog.close)
        
        def apply_current_file():
            current_filename = file_selector.currentText()
            self.apply_file_change(current_filename)
            apply_btn.setEnabled(not self.pending_file_changes[current_filename]['applied'])
            update_preview(current_filename)
        
        apply_btn.clicked.connect(apply_current_file)
        
        if file_selector.count() > 0:
            update_preview(file_selector.currentText())
        
        preview_dialog.exec()
    
    def apply_file_change(self, filename):
        """Apply changes to a single file"""
        if not hasattr(self, 'pending_file_changes') or filename not in self.pending_file_changes:
            return
        
        file_info = self.pending_file_changes[filename]
        
        if file_info['applied']:
            return  # Skip if already applied
        
        try:
            # Sanitize the filename again to ensure no control characters
            clean_filename = filename.replace('\n', '').replace('\r', '')
            
            # Get the full path with normalization
            full_path = file_info['full_path']
            
            # Normalize to fix potential path issues
            full_path = os.path.normpath(full_path)
            
            # Create directory if it doesn't exist
            directory = os.path.dirname(full_path)
            if directory and not os.path.exists(directory):
                try:
                    os.makedirs(directory)
                except Exception as e:
                    # Log exact error details for debugging
                    print(f"Directory creation error for '{directory}': {str(e)}")
                    self.chat_display.append(f"<div style='margin-bottom: 5px;'><span style='color: #F44747;'>Error creating directory for {clean_filename}: {str(e)}</span></div>")
                    return False
            
            # Write the file with explicit encoding
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(file_info['new_content'])
            
            # Mark as applied
            file_info['applied'] = True
            
            # Notify the user
            self.chat_display.append(f"<div style='margin-bottom: 5px;'><span style='color: #6A9955;'>✓ Applied changes to: {clean_filename}</span></div>")
            
            # If this is the current file, update the editor
            if self.current_file and os.path.abspath(self.current_file) == os.path.abspath(full_path):
                self.editor.setText(file_info['new_content'])
                self.update_line_numbers()
            
            return True
        except Exception as e:
            # Log detailed error info
            import traceback
            error_details = traceback.format_exc()
            print(f"Error applying changes to {filename}: {str(e)}")
            print(f"Error details: {error_details}")
            
            self.chat_display.append(f"<div style='margin-bottom: 5px;'><span style='color: #F44747;'>Error applying changes to {filename}: {str(e)}</span></div>")
            return False
    
    def apply_all_file_changes(self):
        """Apply all pending file changes"""
        if not hasattr(self, 'pending_file_changes') or not self.pending_file_changes:
            return
        
        success_count = 0
        
        for filename in self.pending_file_changes.keys():
            if self.apply_file_change(filename):
                success_count += 1
        
        if success_count == len(self.pending_file_changes):
            self.chat_display.append(f"<div style='margin-bottom: 10px;'><span style='color: #6A9955;'>✓ Successfully applied all changes ({success_count} files).</span></div>")
        else:
            self.chat_display.append(f"<div style='margin-bottom: 10px;'><span style='color: #F44747;'>Applied changes to {success_count} out of {len(self.pending_file_changes)} files. See above for errors.</span></div>")
        
        self.pending_file_changes = {}
    