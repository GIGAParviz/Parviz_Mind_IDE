from PyQt6.QtWidgets import (QMainWindow, QTextEdit, QVBoxLayout, 
                           QHBoxLayout, QWidget, QPushButton, QFileDialog, 
                           QMessageBox, QTreeView, QSplitter, QTabWidget,
                           QLineEdit, QLabel, QComboBox, QDialog, QFormLayout,
                           QRadioButton, QGroupBox, QPlainTextEdit, QToolBar,
                           QSizePolicy, QStatusBar, QMenu, QCheckBox)
from PyQt6.QtGui import (QSyntaxHighlighter, QTextCharFormat, QColor, QFont, 
                       QTextCursor, QIcon, QPixmap, QAction, QTextDocument,
                       QPainter, QPolygon, QPen, QBrush)
from PyQt6.QtCore import (Qt, QAbstractItemModel, QModelIndex, QVariant, QDir, 
                        QThread, pyqtSignal, QProcess, QIODevice, QByteArray, QSize,
                        QPoint)
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
        
        try:
            app_icon = QIcon("D:/deep_learning/chatbot/Editor/src/ui/icons/app.ico")
            self.setWindowIcon(app_icon)
        except Exception as e:
            print(f"Error setting application icon: {str(e)}")

        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)
        
        play_icon = QIcon()
        play_pixmap = QPixmap(24, 24)
        play_pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(play_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        polygon = QPolygon([
            QPoint(6, 4),    
            QPoint(6, 20),   
            QPoint(20, 12)   
        ])
        
        painter.setPen(QPen(QColor("#3C3"), 1))
        painter.setBrush(QBrush(QColor("#3C3")))
        painter.drawPolygon(polygon)
        painter.end()
        
        play_icon.addPixmap(play_pixmap)
        
        run_code_action = QAction(play_icon, "Run Code", self)
        run_code_action.setToolTip("Run Python File")
        run_code_action.triggered.connect(self.run_code)
        toolbar.addAction(run_code_action)
        
        toolbar.addSeparator()
        
        new_file_action = QAction("New File", self)
        new_file_action.setToolTip("Create New File")
        new_file_action.triggered.connect(self.new_file)
        toolbar.addAction(new_file_action)
        
        open_file_action = QAction("Open", self)
        open_file_action.setToolTip("Open File")
        open_file_action.triggered.connect(self.open_file)
        toolbar.addAction(open_file_action)
        
        save_file_action = QAction("Save", self)
        save_file_action.setToolTip("Save File")
        save_file_action.triggered.connect(self.save_file)
        toolbar.addAction(save_file_action)
        
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #121212;
                color: #E0E0E0;
            }
            QTextEdit, QLineEdit, QPlainTextEdit {
                background-color: #1E1E1E;
                color: #ECECEC;
                border: 1px solid #383838;
                border-radius: 3px;
                padding: 2px;
                selection-background-color: #264F78;
                font-family: 'Consolas', monospace;
                font-size: 10pt;
            }
            QPushButton {
                background-color: #2D2D30;
                color: #E0E0E0;
                border: 1px solid #3E3E42;
                border-radius: 3px;
                padding: 5px 10px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #3E3E42;
                border: 1px solid #555555;
            }
            QPushButton:pressed {
                background-color: #0E639C;
                border: 1px solid #0E639C;
                color: white;
            }
            QTreeView {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: none;
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
            QSplitter::handle {
                background-color: #2D2D30;
                border: 1px solid #383838;
            }
            QLabel {
                color: #E0E0E0;
                font-weight: bold;
            }
            QTabWidget::pane {
                border: 1px solid #3E3E42;
                border-radius: 3px;
            }
            QTabBar::tab {
                background-color: #2D2D30;
                color: #E0E0E0;
                border: none;
                padding: 8px 15px;
                margin-right: 2px;
                border-top-left-radius: 3px;
                border-top-right-radius: 3px;
                font-family: 'Segoe UI', sans-serif;
            }
            QTabBar::tab:selected {
                background-color: #1E1E1E;
                border-bottom: 2px solid #007ACC;
            }
            QTabBar::tab:hover:!selected {
                background-color: #3E3E42;
            }
            QComboBox {
                background-color: #2D2D30;
                color: #E0E0E0;
                border: 1px solid #3E3E42;
                border-radius: 3px;
                padding: 3px 5px;
                min-height: 20px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: #3E3E42;
                border-left-style: solid;
            }
            QComboBox QAbstractItemView {
                background-color: #2D2D30;
                color: #E0E0E0;
                selection-background-color: #007ACC;
                selection-color: #FFFFFF;
                border: 1px solid #3E3E42;
            }
            QToolBar {
                background-color: #2D2D30;
                border: none;
                spacing: 0px;
                padding: 0px;
                border-bottom: 1px solid #1E1E1E;
            }
            QToolBar QToolButton {
                background-color: transparent;
                border: none;
                padding: 5px 8px;
                color: #E0E0E0;
                font-size: 12px;
            }
            QToolBar QToolButton:hover {
                background-color: #3E3E42;
            }
            QToolBar QToolButton:pressed {
                background-color: #007ACC;
                color: white;
            }
            QStatusBar {
                background-color: #2D2D30;
                color: white;
                border-top: 1px solid #383838;
            }
            QStatusBar QLabel {
                color: white;
                font-weight: normal;
                padding: 2px 5px;
            }
            QMenu {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #383838;
                border-radius: 3px;
            }
            QMenu::item {
                padding: 6px 25px 6px 25px;
            }
            QMenu::item:selected {
                background-color: #007ACC;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background-color: #383838;
                margin: 5px 10px 5px 10px;
            }
            QTabWidget {
                background-color: #1E1E1E;
            }
            QScrollBar:vertical {
                background: #1E1E1E;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #3E3E42;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #525257;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background: #2D2D30;
                height: 12px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #3E3E42;
                min-width: 20px;
                border-radius: 3px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #525257;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QMenuBar {
                background-color: #2D2D30;
                color: #E0E0E0;
                border: none;
                padding: 2px 0px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 6px 12px;
                margin: 0px 2px;
            }
            QMenuBar::item:selected {
                background-color: #3E3E42;
            }
            QMenuBar::item:pressed {
                background-color: #0E639C;
                color: white;
            }
        """)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.main_menu = self.menuBar()
        self.main_menu.setStyleSheet("""
            QMenuBar {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border-bottom: 1px solid #383838;
                padding: 2px 0px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 9pt;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 10px;
                margin: 0px 2px;
                border-radius: 3px;
            }
            QMenuBar::item:selected {
                background-color: #3E3E42;
            }
            QMenuBar::item:pressed {
                background-color: #007ACC;
                color: white;
            }
        """)

        file_menu = self.main_menu.addMenu("File")
        
        new_action = QAction("New File", self)
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction("Open...", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save As...", self)
        save_as_action.triggered.connect(lambda: self.save_file(save_as=True))
        file_menu.addAction(save_as_action)
        
        edit_menu = self.main_menu.addMenu("Edit")
        
        cut_action = QAction("Cut", self)
        cut_action.triggered.connect(lambda: self.editor.cut())
        edit_menu.addAction(cut_action)
        
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(lambda: self.editor.copy())
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("Paste", self)
        paste_action.triggered.connect(lambda: self.editor.paste())
        edit_menu.addAction(paste_action)
        
        edit_menu.addSeparator()
        
        find_replace_action = QAction("Find/Replace", self)
        find_replace_action.triggered.connect(self.show_find_replace_dialog)
        edit_menu.addAction(find_replace_action)
        
        edit_menu.addSeparator()
        
        go_to_line_action = QAction("Go to Line...", self)
        go_to_line_action.triggered.connect(self.show_go_to_line_dialog)
        edit_menu.addAction(go_to_line_action)
        
        selection_menu = self.main_menu.addMenu("Selection")
        
        select_all_action = QAction("Select All", self)
        select_all_action.triggered.connect(lambda: self.editor.selectAll())
        selection_menu.addAction(select_all_action)
        
        view_menu = self.main_menu.addMenu("View")
        
        toggle_explorer_action = QAction("Explorer", self)
        toggle_explorer_action.triggered.connect(self.toggle_explorer)
        view_menu.addAction(toggle_explorer_action)
        
        toggle_terminal_action = QAction("Terminal", self)
        toggle_terminal_action.triggered.connect(self.open_terminal)
        view_menu.addAction(toggle_terminal_action)
        
        toggle_chat_action = QAction("AI Assistant", self)
        toggle_chat_action.triggered.connect(self.toggle_chat)
        view_menu.addAction(toggle_chat_action)

        run_menu = self.main_menu.addMenu("Run")
        
        run_code_action = QAction("Run Python File", self)
        run_code_action.triggered.connect(self.run_code)
        run_menu.addAction(run_code_action)
        
        terminal_menu = self.main_menu.addMenu("Terminal")
        
        new_terminal_action = QAction("New Terminal", self)
        new_terminal_action.triggered.connect(self.open_terminal)
        terminal_menu.addAction(new_terminal_action)
        
        # Add Settings menu
        settings_menu = self.main_menu.addMenu("Settings")
        
        llm_settings_action = QAction("AI Model Settings", self)
        llm_settings_action.triggered.connect(self.show_settings_dialog)
        settings_menu.addAction(llm_settings_action)
        
        theme_settings_action = QAction("Theme Settings", self)
        theme_settings_action.triggered.connect(self.show_theme_settings)
        settings_menu.addAction(theme_settings_action)
        
        settings_menu.addSeparator()
        
        editor_settings_action = QAction("Editor Settings", self)
        editor_settings_action.triggered.connect(self.show_editor_settings)
        settings_menu.addAction(editor_settings_action)
        
        help_menu = self.main_menu.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_help_dialog)
        help_menu.addAction(about_action)
        
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        self.position_status = QLabel("Ln 1, Col 1")
        status_bar.addPermanentWidget(self.position_status)
        
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        status_bar.addPermanentWidget(spacer)
        
        python_status = QLabel("Python 3.11.8 64-bit")
        status_bar.addPermanentWidget(python_status)
        
        spaces_status = QLabel("Spaces: 4")
        status_bar.addPermanentWidget(spaces_status)
        
        utf_status = QLabel("UTF-8")
        status_bar.addPermanentWidget(utf_status)
        
        lf_status = QLabel("LF")
        status_bar.addPermanentWidget(lf_status)
        
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
        explorer_header.setStyleSheet("""
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                            stop:0 #2D2D30, stop:1 #252526);
            border-right: 1px solid #1E1E1E;
            border-bottom: 1px solid #383838;
        """)
        explorer_header_layout = QHBoxLayout(explorer_header)
        explorer_header_layout.setContentsMargins(5, 5, 5, 5)
        
        explorer_label = QLabel("EXPLORER")
        explorer_label.setStyleSheet("""
            font-size: 11px;
            color: #E0E0E0;
            font-weight: normal;
            font-family: 'Segoe UI', sans-serif;
            letter-spacing: 0.5px;
        """)
        explorer_header_layout.addWidget(explorer_label)
        
        explorer_header_layout.addStretch()
        
        self.explorer_toggle_btn = QPushButton("◀")
        self.explorer_toggle_btn.setMaximumWidth(25)
        self.explorer_toggle_btn.setToolTip("Hide Explorer")
        self.explorer_toggle_btn.setStyleSheet("""
            background-color: transparent;
            border: none;
            color: #E0E0E0;
            font-size: 10px;
        """)
        self.explorer_toggle_btn.clicked.connect(self.toggle_explorer)
        explorer_header_layout.addWidget(self.explorer_toggle_btn)
        
        refresh_btn = QPushButton("⟳")
        refresh_btn.setMaximumWidth(25)
        refresh_btn.setToolTip("Refresh Explorer")
        refresh_btn.setStyleSheet("""
            background-color: transparent;
            border: none;
            color: #E0E0E0;
            font-size: 10px;
        """)
        refresh_btn.clicked.connect(self.refresh_file_tree)
        explorer_header_layout.addWidget(refresh_btn)
        
        folder_btn = QPushButton("📁")
        folder_btn.setMaximumWidth(25)
        folder_btn.setToolTip("Change Folder")
        folder_btn.setStyleSheet("""
            background-color: transparent;
            border: none;
            color: #E0E0E0;
            font-size: 10px;
        """)
        folder_btn.clicked.connect(self.change_root_folder)
        explorer_header_layout.addWidget(folder_btn)
        
        file_tree_layout.addWidget(explorer_header)
        self.file_tree = QTreeView()
        self.file_tree.setHeaderHidden(True)  
        self.file_tree.setAnimated(True)
        self.file_tree.setIndentation(15)
        
        self.file_tree.setStyleSheet("""
            QTreeView {
                background-color: #1E1E1E; 
                color: #E0E0E0;
                border: none;
                border-right: 1px solid #1E1E1E;
                font-family: 'Segoe UI', sans-serif;
                font-size: 9pt;
                outline: none;
            }
            QTreeView::item {
                padding: 4px 0px;
                border: none;
            }
            QTreeView::item:selected {
                background-color: #094771;
                color: #FFFFFF;
                border-radius: 2px;
            }
            QTreeView::item:hover:!selected {
                background-color: #2A2D2E;
                border-radius: 2px;
            }
            QTreeView::branch {
                background-color: transparent;
            }
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings {
                image: url(none);
                border-image: none;
            }
            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings {
                image: url(none);
                border-image: none;
            }
        """)
        
        QFileSystemModelClass = get_file_system_model()
        
        try:
            if QFileSystemModelClass:
                self.file_model = QFileSystemModelClass()
                current_dir = os.path.dirname(os.path.abspath(__file__))
                
                self.file_model.setRootPath(current_dir)
                
                self.file_tree.setModel(self.file_model)
                
                for i in range(1, self.file_model.columnCount()):
                    self.file_tree.hideColumn(i)
                
                root_index = self.file_model.index(current_dir)
                if root_index.isValid():
                    self.file_tree.setRootIndex(root_index)
                
                self.using_qt_model = True
            else:
                self.file_model = SimpleFileSystemModel()
                current_dir = os.path.dirname(os.path.abspath(__file__))
                
                self.file_model.setRootPath(current_dir)
                
                self.file_model.setRootPath(current_dir)
                self.file_tree.setModel(self.file_model)
                
                root_index = self.file_model.index(0, 0)
                if root_index.isValid():
                    self.file_tree.setRootIndex(root_index)
                
                self.using_qt_model = False
        except Exception as e:
            print(f"Error initializing file system model: {str(e)}")
            self.file_model = SimpleFileSystemModel()
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            self.file_model.setRootPath(current_dir)
            
            self.file_tree.setModel(self.file_model)
            
            root_index = self.file_model.index(0, 0)
            if root_index.isValid():
                self.file_tree.setRootIndex(root_index)
            
            self.using_qt_model = False
            
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

        self.editor_tabs = QTabWidget()
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.setMovable(True)
        self.editor_tabs.setDocumentMode(True)
        self.editor_tabs.tabCloseRequested.connect(self.close_tab)
        
        self.editor = CodeEditor()
        self.editor.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: none;
                selection-background-color: #264F78;
                selection-color: #FFFFFF;
            }
            QTextEdit[readOnly="true"] {
                background-color: #252526;
                color: #A0A0A0;
            }
        """)
        
        editor_tab = QWidget()
        editor_tab_layout = QVBoxLayout(editor_tab)
        editor_tab_layout.setContentsMargins(0, 0, 0, 0)
        editor_tab_layout.setSpacing(0)
        
        editor_with_line_numbers = QWidget()
        editor_with_line_numbers_layout = QHBoxLayout(editor_with_line_numbers)
        editor_with_line_numbers_layout.setContentsMargins(0, 0, 0, 0)
        editor_with_line_numbers_layout.setSpacing(0)
        
        self.line_numbers = QTextEdit()
        self.line_numbers.setReadOnly(True)
        self.line_numbers.setMaximumWidth(50)
        self.line_numbers.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.line_numbers.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.line_numbers.setStyleSheet("""
            background-color: #1E1E1E; 
            color: #6D6D6D; 
            border-right: 1px solid #383838; 
            padding-right: 5px; 
            text-align: right;
            font-family: 'Consolas', monospace;
            font-size: 10pt;
        """)
        editor_with_line_numbers_layout.addWidget(self.line_numbers)
        
        editor_with_line_numbers_layout.addWidget(self.editor)
        editor_tab_layout.addWidget(editor_with_line_numbers)
        
        self.editor.textChanged.connect(self.update_line_numbers)
        self.editor.cursorPositionChanged.connect(self.update_cursor_position)
        self.editor.verticalScrollBar().valueChanged.connect(self.sync_line_numbers_scroll)
        
        self.highlighter = PythonHighlighter(self.editor.document())
        
        self.editor_tabs.addTab(editor_tab, "Untitled")
        
        editor_splitter.addWidget(self.editor_tabs)
        
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        main_splitter.addWidget(chat_widget)
        
        chat_header = QWidget()
        chat_header.setStyleSheet("""
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                            stop:0 #2D2D30, stop:1 #252526);
            border-bottom: 1px solid #383838;
        """)
        chat_header_layout = QHBoxLayout(chat_header)
        chat_header_layout.setContentsMargins(5, 5, 5, 5)
        
        chat_label = QLabel("AI ASSISTANT")
        chat_label.setStyleSheet("""
            font-size: 11px;
            color: #E0E0E0;
            font-weight: normal;
            font-family: 'Segoe UI', sans-serif;
            letter-spacing: 0.5px;
        """)
        chat_header_layout.addWidget(chat_label)
        
        chat_header_layout.addStretch()
        
        self.chat_toggle_btn = QPushButton("▶")
        self.chat_toggle_btn.setMaximumWidth(25)
        self.chat_toggle_btn.setToolTip("Hide Chat")
        self.chat_toggle_btn.setStyleSheet("""
            background-color: transparent;
            border: none;
            color: #E0E0E0;
            font-size: 10px;
        """)
        self.chat_toggle_btn.clicked.connect(self.toggle_chat)
        chat_header_layout.addWidget(self.chat_toggle_btn)
        
        chat_layout.addWidget(chat_header)
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            background-color: #121212;
            color: #E0E0E0;
            border: none;
            padding: 10px;
            selection-background-color: #264F78;
            font-family: 'Segoe UI', sans-serif;
            font-size: 10pt;
            line-height: 1.4;
        """)
        chat_layout.addWidget(self.chat_display)
        
        welcome_message = """<div style='margin-bottom: 15px;'>
            <span style='color: #4EC9B0; font-weight: bold;'>AI Assistant:</span> 
            Welcome to Parviz Mind IDE! I'm your AI assistant, ready to help you with your code.
            You can ask me questions about your code, request explanations, or get help with programming tasks.
            Just type your message in the chat box below and click Send or press Enter.
        </div>"""
        self.chat_display.append(welcome_message)
        
        file_selection_container = QWidget()
        file_selection_container.setStyleSheet("""
            background-color: #1E1E1E; 
            border-top: 1px solid #383838;
            border-bottom: 1px solid #383838;
        """)
        file_selection_layout = QVBoxLayout(file_selection_container)
        file_selection_layout.setContentsMargins(5, 2, 5, 2)
        file_selection_layout.setSpacing(2)
        
        file_selection_header = QWidget()
        file_selection_header_layout = QHBoxLayout(file_selection_header)
        file_selection_header_layout.setContentsMargins(0, 0, 0, 0)
        file_selection_header_layout.setSpacing(3)
        
        file_selection_label = QLabel("Files for Context:")
        file_selection_label.setFont(QFont('Segoe UI', 8))
        file_selection_label.setStyleSheet("""
            color: #E0E0E0; 
            font-weight: normal;
            letter-spacing: 0.3px;
        """)
        file_selection_header_layout.addWidget(file_selection_label)
        
        file_selection_header_layout.addStretch()
        
        self.add_file_btn = QPushButton("+")
        self.add_file_btn.setMaximumWidth(25)
        self.add_file_btn.setStyleSheet("""
            background-color: transparent;
            border: none;
            color: #E0E0E0;
            font-size: 12px;
            font-weight: bold;
        """)
        self.add_file_btn.setToolTip("Add File")
        self.add_file_btn.clicked.connect(self.add_file_to_context)
        file_selection_header_layout.addWidget(self.add_file_btn)
        
        self.clear_files_btn = QPushButton("×")
        self.clear_files_btn.setMaximumWidth(25)
        self.clear_files_btn.setStyleSheet("""
            background-color: transparent;
            border: none;
            color: #E0E0E0;
            font-size: 12px;
            font-weight: bold;
        """)
        self.clear_files_btn.setToolTip("Clear All")
        self.clear_files_btn.clicked.connect(self.clear_context_files)
        file_selection_header_layout.addWidget(self.clear_files_btn)
        
        self.toggle_context_btn = QPushButton("▼")
        self.toggle_context_btn.setMaximumWidth(25)
        self.toggle_context_btn.setStyleSheet("""
            background-color: transparent;
            border: none;
            color: #E0E0E0;
            font-size: 10px;
        """)
        self.toggle_context_btn.setToolTip("Toggle Context Files")
        self.toggle_context_btn.clicked.connect(self.toggle_context_files)
        file_selection_header_layout.addWidget(self.toggle_context_btn)
        
        file_selection_layout.addWidget(file_selection_header)
        
        self.file_list = QTextEdit()
        self.file_list.setReadOnly(True)
        self.file_list.setMaximumHeight(40)
        self.file_list.setStyleSheet("""
            background-color: #121212; 
            padding: 3px; 
            font-size: 9px; 
            border: none;
            color: #BBBBBB;
            border-radius: 3px;
        """)
        self.file_list.setFont(QFont('Segoe UI', 8))
        file_selection_layout.addWidget(self.file_list)
        
        self.context_files = []
        
        chat_layout.addWidget(file_selection_container)
        
        chat_input_container = QWidget()
        chat_input_container.setStyleSheet("""
            background-color: #1E1E1E; 
            border-top: 1px solid #383838;
        """)
        chat_input_layout = QHBoxLayout(chat_input_container)
        chat_input_layout.setContentsMargins(10, 5, 10, 5)
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask the AI Assistant about your code...")
        self.chat_input.setStyleSheet("""
            background-color: #121212;
            color: #E0E0E0;
            padding: 10px 15px;
            border: 1px solid #383838;
            border-radius: 4px;
            selection-background-color: #264F78;
            font-family: 'Segoe UI', sans-serif;
            font-size: 10pt;
        """)
        self.chat_input.returnPressed.connect(self.send_chat)
        chat_input_layout.addWidget(self.chat_input)
        
        self.send_btn = QPushButton('Send')
        self.send_btn.setStyleSheet("""
            background-color: #007ACC;
            color: #FFFFFF;
            border: none;
            border-radius: 4px;
            padding: 10px 20px;
            font-weight: bold;
            font-family: 'Segoe UI', sans-serif;
            font-size: 10pt;
        """)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.clicked.connect(self.send_chat)
        chat_input_layout.addWidget(self.send_btn)
        
        chat_layout.addWidget(chat_input_container)
        
        main_splitter.setSizes([800, 400])  
        editor_splitter.setSizes([250, 550]) 
        
        chat_widget.setVisible(True)
        
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
            self.editor_tabs.setTabText(self.editor_tabs.currentIndex(), os.path.basename(self.current_file))
        else:
            self.editor_tabs.setTabText(self.editor_tabs.currentIndex(), "Untitled")
            
    def file_tree_double_clicked(self, index):
        """Handle double click on file tree items"""
        path = self.file_model.filePath(index)
        if os.path.isfile(path):
            self.open_file(path)
        elif os.path.isdir(path):
            self.file_tree.setExpanded(index, not self.file_tree.isExpanded(index))

    def new_file(self):
        new_tab = QWidget()
        new_tab_layout = QVBoxLayout(new_tab)
        new_tab_layout.setContentsMargins(0, 0, 0, 0)
        new_tab_layout.setSpacing(0)
        
        editor_with_line_numbers = QWidget()
        editor_with_line_numbers_layout = QHBoxLayout(editor_with_line_numbers)
        editor_with_line_numbers_layout.setContentsMargins(0, 0, 0, 0)
        editor_with_line_numbers_layout.setSpacing(0)
        
        line_numbers = QTextEdit()
        line_numbers.setReadOnly(True)
        line_numbers.setMaximumWidth(50)
        line_numbers.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        line_numbers.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        line_numbers.setStyleSheet("background-color: #1E1E1E; color: #858585; border-right: 1px solid #3E3E3E; padding-right: 5px; text-align: right;")
        editor_with_line_numbers_layout.addWidget(line_numbers)
        
        new_editor = CodeEditor()
        editor_with_line_numbers_layout.addWidget(new_editor)
        
        new_tab_layout.addWidget(editor_with_line_numbers)
        
        new_highlighter = PythonHighlighter(new_editor.document())
        
        index = self.editor_tabs.addTab(new_tab, "Untitled")
        self.editor_tabs.setCurrentIndex(index)
        
        self.editor = new_editor
        self.line_numbers = line_numbers
        self.highlighter = new_highlighter
        
        self.editor.textChanged.connect(self.update_line_numbers)
        self.editor.cursorPositionChanged.connect(self.update_cursor_position)
        self.editor.verticalScrollBar().valueChanged.connect(self.sync_line_numbers_scroll)
        
        self.current_file = None
        self.update_line_numbers()
        
    def close_tab(self, index):
        if self.editor_tabs.count() <= 1:
            self.editor.clear()
            self.current_file = None
            self.editor_tabs.setTabText(0, "Untitled")
            self.update_line_numbers()
        else:
            self.editor_tabs.removeTab(index)
            
            current_tab = self.editor_tabs.currentWidget()
            editor_layout = current_tab.layout()
            editor_with_line_numbers = editor_layout.itemAt(0).widget()
            editor_with_line_numbers_layout = editor_with_line_numbers.layout()
            
            self.line_numbers = editor_with_line_numbers_layout.itemAt(0).widget()
            self.editor = editor_with_line_numbers_layout.itemAt(1).widget()
            self.highlighter = PythonHighlighter(self.editor.document())
            
            current_tab_name = self.editor_tabs.tabText(self.editor_tabs.currentIndex())
            if current_tab_name != "Untitled":
                for file_path in self.open_files.keys():
                    if os.path.basename(file_path) == current_tab_name:
                        self.current_file = file_path
                        break
            else:
                self.current_file = None
                
    def show_go_to_line_dialog(self):
        """Show a dialog to go to a specific line number"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Go to Line")
        dialog.setFixedWidth(300)
        
        layout = QVBoxLayout(dialog)
        
        form_layout = QFormLayout()
        line_input = QLineEdit()
        line_input.setValidator(QRegExpValidator(QRegExp("[0-9]+")))
        form_layout.addRow("Line number:", line_input)
        
        layout.addLayout(form_layout)
        
        button_layout = QHBoxLayout()
        go_btn = QPushButton("Go")
        cancel_btn = QPushButton("Cancel")
        
        button_layout.addStretch()
        button_layout.addWidget(go_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        def go_to_line():
            try:
                line_number = int(line_input.text())
                if line_number > 0:
                    cursor = self.editor.textCursor()
                    cursor.movePosition(QTextCursor.MoveOperation.Start)
                    
                    for _ in range(line_number - 1):
                        cursor.movePosition(QTextCursor.MoveOperation.Down)
                    
                    cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
                    
                    self.editor.setTextCursor(cursor)
                    self.editor.ensureCursorVisible()
                    self.editor.setFocus()
                    dialog.accept()
            except ValueError:
                pass
        
        go_btn.clicked.connect(go_to_line)
        cancel_btn.clicked.connect(dialog.reject)
        
        line_input.setFocus()
        dialog.exec()
        
    def update_cursor_position(self):
        """Update the cursor position display"""
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1
        self.position_status.setText(f"Ln {line}, Col {column}")
        
        if self.current_file:
            file_name = os.path.basename(self.current_file)
            self.statusBar().showMessage(f"{file_name} - Python - Ln {line}, Col {column}")
        else:
            self.statusBar().showMessage(f"Untitled - Python - Ln {line}, Col {column}")
            
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
            if hasattr(self, 'open_files') and path in self.open_files:
                self.editor_tabs.setCurrentIndex(self.open_files[path])
                return
                
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                self.new_file()
                
                self.editor.setText(file_content)
                self.current_file = path
                
                current_index = self.editor_tabs.currentIndex()
                self.editor_tabs.setTabText(current_index, os.path.basename(path))
                
                self.setWindowTitle(f'Parviz Mind IDE - {os.path.basename(path)}')
                
                if not hasattr(self, 'open_files'):
                    self.open_files = {}
                self.open_files[path] = current_index
                
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
            
            if not hasattr(self, 'terminal_output') or not self.terminal_output:
                self.create_interactive_terminal()
            else:
                self.terminal_output.show()
                terminal_header = self.terminal_output.parent().layout().itemAt(
                    self.terminal_output.parent().layout().count() - 3).widget()
                terminal_header.show()

                terminal_input = self.terminal_output.parent().layout().itemAt(
                    self.terminal_output.parent().layout().count() - 1).widget()
                terminal_input.show()
                
                self.terminal_toggle_btn.setText("▼")
                self.terminal_toggle_btn.setToolTip("Hide Terminal")
            
            self.terminal_output.append("<span style='color: #569CD6;'>Running script...</span>")
            
            file_dir = os.path.dirname(self.current_file)
            if not file_dir:  
                file_dir = os.getcwd()
            
            self.terminal_output.append(f"<span style='color: #6A9955;'>Working directory: {file_dir}</span>")
            
            if os.name == 'nt':
                command = f"python \"{self.current_file}\"\n"
            else:
                command = f"python3 \"{self.current_file}\"\n"
                
            if hasattr(self, 'process') and self.process.isOpen():
                self.process.write(command.encode())
            else:
                self.terminal_output.append("<span style='color: #F44747;'>Error: Terminal process is not running.</span>")
                
            if hasattr(self, 'terminal_input'):
                self.terminal_input.setFocus()
            
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

    def save_file(self, save_as=False):
        if not self.current_file or save_as:
            path, _ = QFileDialog.getSaveFileName(self, "Save File", "", 
                                               "Python Files (*.py);;All Files (*)")
            if not path:
                return
            self.current_file = path
            # Update tab title
            current_index = self.editor_tabs.currentIndex()
            self.editor_tabs.setTabText(current_index, os.path.basename(path))

        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
            # Update window title
            self.setWindowTitle(f'Parviz Mind IDE - {os.path.basename(self.current_file)}')
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
        self.api_key_input.setPlaceholderText("Enter Groq API key")
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
                self.terminal_output.parent().layout().count() - 3).widget()
            terminal_header.hide()

            terminal_input = self.terminal_output.parent().layout().itemAt(
                self.terminal_output.parent().layout().count() - 1).widget()
            terminal_input.hide()
            
            self.terminal_toggle_btn.setText("▲")
            self.terminal_toggle_btn.setToolTip("Show Terminal")
            self.terminal_toggle_btn.show() 
        else:
            self.terminal_output.show()

            terminal_header = self.terminal_output.parent().layout().itemAt(
                self.terminal_output.parent().layout().count() - 3).widget()
            terminal_header.show()

            terminal_input = self.terminal_output.parent().layout().itemAt(
                self.terminal_output.parent().layout().count() - 1).widget()
            terminal_input.show()
            
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
    
    def toggle_context_files(self):
        """Toggle visibility of context files list"""
        if self.file_list.isVisible():
            self.file_list.hide()
            self.toggle_context_btn.setText("▲")
            self.toggle_context_btn.setToolTip("Show Context Files")
        else:
            self.file_list.show()
            self.toggle_context_btn.setText("▼")
            self.toggle_context_btn.setToolTip("Hide Context Files")
    
    def _update_file_list_display(self):
        """Update the display of the file list"""
        if not self.context_files:
            self.file_list.setText("<i>No files selected</i>")
        else:
            html = "<ul style='margin: 0; padding-left: 10px;'>"
            for file_path in self.context_files:
                file_name = os.path.basename(file_path)
                html += f"<li style='margin-bottom: 0px;'>{file_name}</li>"
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
            clean_filename = filename.replace('\n', '').replace('\r', '')
            
            if not clean_filename:
                continue
            if not os.path.isabs(clean_filename):
                if clean_filename.startswith('src/') or clean_filename.startswith('tests/'):
                    clean_path = clean_filename.replace('/', os.path.sep)
                    
                    base_dir = os.getcwd()
                    full_path = os.path.join(base_dir, clean_path)
                else:
                    matched_file = None
                    for file_path in self.context_files:
                        if os.path.basename(file_path) == clean_filename:
                            matched_file = file_path
                            break
                    
                    if matched_file:
                        full_path = matched_file
                    else:
                        base_dir = os.path.dirname(self.current_file) if self.current_file else os.getcwd()
                        full_path = os.path.join(base_dir, clean_filename)
            else:
                full_path = clean_filename
            
            full_path = os.path.normpath(full_path)
            print(f"Filename: {clean_filename}")
            print(f"Full path: {full_path}")
            
            file_exists = os.path.isfile(full_path)
            
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
        
        self.pending_file_changes = file_states
       
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
            return 
        
        try:
            clean_filename = filename.replace('\n', '').replace('\r', '')
            
            full_path = file_info['full_path']
            
            full_path = os.path.normpath(full_path)
            
            directory = os.path.dirname(full_path)
            if directory and not os.path.exists(directory):
                try:
                    os.makedirs(directory)
                except Exception as e:
                    print(f"Directory creation error for '{directory}': {str(e)}")
                    self.chat_display.append(f"<div style='margin-bottom: 5px;'><span style='color: #F44747;'>Error creating directory for {clean_filename}: {str(e)}</span></div>")
                    return False
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(file_info['new_content'])
            
            file_info['applied'] = True
            
            self.chat_display.append(f"<div style='margin-bottom: 5px;'><span style='color: #6A9955;'>✓ Applied changes to: {clean_filename}</span></div>")
            
            if self.current_file and os.path.abspath(self.current_file) == os.path.abspath(full_path):
                self.editor.setText(file_info['new_content'])
                self.update_line_numbers()
            
            return True
        except Exception as e:
            
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
    
    def open_terminal(self):
        """Open an interactive terminal window"""
        self.save_file()
        
        if not hasattr(self, 'terminal_output') or not self.terminal_output:
            self.create_interactive_terminal()
        else:
            self.terminal_output.show()
            self.terminal_output.parent().layout().itemAt(
                self.terminal_output.parent().layout().count() - 2).widget().show()
            self.terminal_toggle_btn.setText("▼")
            self.terminal_toggle_btn.setToolTip("Hide Terminal")
            
        if hasattr(self, 'terminal_input'):
            self.terminal_input.setFocus()

    def create_interactive_terminal(self):
        """Create an interactive terminal widget"""
        terminal_widget = QWidget()
        terminal_layout = QVBoxLayout(terminal_widget)
        terminal_layout.setContentsMargins(0, 0, 0, 0)
        terminal_layout.setSpacing(0)
        
        terminal_header = QWidget()
        terminal_header.setStyleSheet("""
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                            stop:0 #2D2D30, stop:1 #252526);
            border-bottom: 1px solid #383838;
        """)
        terminal_header_layout = QHBoxLayout(terminal_header)
        terminal_header_layout.setContentsMargins(5, 5, 5, 5)
        
        terminal_label = QLabel("TERMINAL")
        terminal_label.setStyleSheet("""
            font-size: 11px;
            color: #E0E0E0;
            font-weight: normal;
            font-family: 'Segoe UI', sans-serif;
            letter-spacing: 0.5px;
        """)
        terminal_header_layout.addWidget(terminal_label)
        
        terminal_header_layout.addStretch()
        
        self.terminal_toggle_btn = QPushButton("×")
        self.terminal_toggle_btn.setMaximumWidth(25)
        self.terminal_toggle_btn.setToolTip("Close Terminal")
        self.terminal_toggle_btn.setStyleSheet("""
            background-color: transparent;
            border: none;
            color: #E0E0E0;
            font-size: 12px;
            font-weight: bold;
        """)
        self.terminal_toggle_btn.clicked.connect(self.close_terminal)
        terminal_header_layout.addWidget(self.terminal_toggle_btn)
        
        terminal_layout.addWidget(terminal_header)
        
        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setFont(QFont('Consolas', 10))
        self.terminal_output.setStyleSheet("""
            background-color: #121212;
            color: #E0E0E0;
            border: none;
            padding: 5px;
            selection-background-color: #264F78;
            font-family: 'Consolas', monospace;
            font-size: 10pt;
            line-height: 1.2;
        """)
        terminal_layout.addWidget(self.terminal_output)
        
        terminal_input_container = QWidget()
        terminal_input_container.setStyleSheet("""
            background-color: #1E1E1E;
            border-top: 1px solid #383838;
        """)
        terminal_input_layout = QHBoxLayout(terminal_input_container)
        terminal_input_layout.setContentsMargins(5, 5, 5, 5)
        
        terminal_prompt = QLabel("$")
        terminal_prompt.setStyleSheet("""
            color: #569CD6;
            font-family: 'Consolas', monospace;
            font-size: 10pt;
            font-weight: bold;
            padding-right: 5px;
        """)
        terminal_input_layout.addWidget(terminal_prompt)
        
        self.terminal_input = QLineEdit()
        self.terminal_input.setStyleSheet("""
            background-color: #121212;
            color: #E0E0E0;
            border: none;
            padding: 5px;
            selection-background-color: #264F78;
            font-family: 'Consolas', monospace;
            font-size: 10pt;
        """)
        self.terminal_input.returnPressed.connect(self.execute_terminal_command)
        terminal_input_layout.addWidget(self.terminal_input)
        
        terminal_layout.addWidget(terminal_input_container)
        
        try:
            code_layout = self.centralWidget().layout().itemAt(0).widget().findChild(QSplitter).widget(0).layout()
            code_layout.addWidget(terminal_widget)
            
            self.terminal_widget = terminal_widget
            
            self.process = QProcess()
            self.process.readyReadStandardOutput.connect(self.handle_stdout)
            self.process.readyReadStandardError.connect(self.handle_stderr)
            self.process.finished.connect(self.process_finished)
            
            working_dir = os.path.dirname(self.current_file) if self.current_file else os.getcwd()
            self.process.setWorkingDirectory(working_dir)
            
            if os.name == 'nt':
                self.process.start('cmd.exe')
            else:
                self.process.start('/bin/bash')
            
            self.terminal_input.setFocus()
            
            return terminal_widget
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not create terminal: {str(e)}")
            return None

    def execute_terminal_command(self):
        """Send a command to the terminal process"""
        if not hasattr(self, 'process') or not self.process.isOpen():
            self.terminal_output.append("<span style='color: #F44747;'>Error: Terminal process is not running.</span>")
            return
        
        command = self.terminal_input.text().strip()
        if not command:
            return
            
        self.terminal_output.append(f"<span style='color: #DCDCAA;'>> {command}</span>")
        self.terminal_input.clear()
        
        command += "\n"
        self.process.write(command.encode())

    def handle_stdout(self):
        """Handle standard output from the process"""
        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='replace')
        if data:
            formatted_data = data.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
            self.terminal_output.append(f"<span style='color: #CCCCCC;'>{formatted_data}</span>")
            
            cursor = self.terminal_output.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.terminal_output.setTextCursor(cursor)

    def handle_stderr(self):
        """Handle standard error from the process"""
        data = self.process.readAllStandardError().data().decode('utf-8', errors='replace')
        if data:
            formatted_data = data.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
            self.terminal_output.append(f"<span style='color: #F44747;'>{formatted_data}</span>")
            
            cursor = self.terminal_output.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.terminal_output.setTextCursor(cursor)

    def process_finished(self, exit_code, exit_status):
        """Handle process completion"""
        if not hasattr(self, 'process') or not self.process:
            return
            
        if exit_code == 0:
            self.terminal_output.append("<span style='color: #6A9955;'>Process completed successfully.</span>")
        else:
            self.terminal_output.append(f"<span style='color: #F44747;'>Process exited with code {exit_code}.</span>")
        
        if hasattr(self, 'terminal_widget') and self.terminal_widget and self.terminal_widget.isVisible():
            try:
                self.process = QProcess()
                self.process.readyReadStandardOutput.connect(self.handle_stdout)
                self.process.readyReadStandardError.connect(self.handle_stderr)
                self.process.finished.connect(self.process_finished)
                
                working_dir = os.path.dirname(self.current_file) if self.current_file else os.getcwd()
                self.process.setWorkingDirectory(working_dir)
                
                if os.name == 'nt':
                    self.process.start('cmd.exe')
                else:
                    self.process.start('/bin/bash')
                    
            except Exception as e:
                self.terminal_output.append(f"<span style='color: #F44747;'>Error restarting process: {str(e)}</span>")
    
    def show_edit_menu(self):
        """Show the Edit menu with various editing options"""
        menu = QMenu(self)
        
        cut_action = QAction("Cut", self)
        cut_action.triggered.connect(lambda: self.editor.cut())
        menu.addAction(cut_action)
        
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(lambda: self.editor.copy())
        menu.addAction(copy_action)
        
        paste_action = QAction("Paste", self)
        paste_action.triggered.connect(lambda: self.editor.paste())
        menu.addAction(paste_action)
        
        menu.addSeparator()
        
        find_replace_action = QAction("Find/Replace", self)
        find_replace_action.triggered.connect(self.show_find_replace_dialog)
        menu.addAction(find_replace_action)
        
        menu.addSeparator()
        
        go_to_line_action = QAction("Go to Line...", self)
        go_to_line_action.triggered.connect(self.show_go_to_line_dialog)
        menu.addAction(go_to_line_action)
        
        cursor_pos = self.mapFromGlobal(self.cursor().pos())
        menu.exec(self.mapToGlobal(cursor_pos))

    def show_view_menu(self):
        """Show the View menu with various view options"""
        menu = QMenu(self)
        
        toggle_explorer_action = QAction("Explorer", self)
        toggle_explorer_action.triggered.connect(self.toggle_explorer)
        menu.addAction(toggle_explorer_action)
        
        toggle_terminal_action = QAction("Terminal", self)
        toggle_terminal_action.triggered.connect(self.open_terminal)
        menu.addAction(toggle_terminal_action)
        
        toggle_chat_action = QAction("AI Assistant", self)
        toggle_chat_action.triggered.connect(self.toggle_chat)
        menu.addAction(toggle_chat_action)
        
        menu.addSeparator()
        
        font_size_menu = QMenu("Font Size", self)
        
        increase_font_action = QAction("Increase Font Size", self)
        increase_font_action.triggered.connect(self.increase_font_size)
        font_size_menu.addAction(increase_font_action)
        
        decrease_font_action = QAction("Decrease Font Size", self)
        decrease_font_action.triggered.connect(self.decrease_font_size)
        font_size_menu.addAction(decrease_font_action)
        
        reset_font_action = QAction("Reset Font Size", self)
        reset_font_action.triggered.connect(self.reset_font_size)
        font_size_menu.addAction(reset_font_action)
        
        menu.addMenu(font_size_menu)
        
        cursor_pos = self.mapFromGlobal(self.cursor().pos())
        menu.exec(self.mapToGlobal(cursor_pos))

    def show_help_dialog(self):
        """Show help dialog with developer information"""
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("About Parviz Mind IDE")
        help_dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(help_dialog)
        
        title_label = QLabel("Parviz Mind IDE")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #E0E0E0;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        try:
            logo_label = QLabel()
            logo_pixmap = QPixmap("D:/deep_learning/chatbot/Editor/logo.png")
            scaled_logo = logo_pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled_logo)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(logo_label)
        except Exception as e:
            print(f"Error loading logo for help dialog: {str(e)}")
        
        description = QLabel("An intelligent Python IDE with integrated AI assistance that helps you write, understand, and refactor code.")
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description)
        
        layout.addSpacing(20)
        
        dev_info_label = QLabel("Developer Information:")
        dev_info_label.setStyleSheet("font-weight: bold; color: #E0E0E0;")
        layout.addWidget(dev_info_label)
        
        github_label = QLabel("<a href='https://github.com/GIGAParviz' style='color: #569CD6;'>GitHub: @GIGAParviz</a>")
        github_label.setOpenExternalLinks(True)
        layout.addWidget(github_label)
        
        email_label = QLabel("<a href='mailto:a.m.parviz02@gmail.com' style='color: #569CD6;'>Email: a.m.parviz02@gmail.com</a>")
        email_label.setOpenExternalLinks(True)
        layout.addWidget(email_label)
        
        linkedin_label = QLabel("<a href='https://www.linkedin.com/in/amir-mehdi-parviz/' style='color: #569CD6;'>LinkedIn: @amir-mehdi-parviz</a>")
        linkedin_label.setOpenExternalLinks(True)
        layout.addWidget(linkedin_label)
        
        layout.addSpacing(20)
        
        button_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(help_dialog.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        help_dialog.exec()

    def show_find_replace_dialog(self):
        """Show a find and replace dialog"""
        find_dialog = QDialog(self)
        find_dialog.setWindowTitle("Find/Replace")
        find_dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(find_dialog)
        
        form_layout = QFormLayout()
        
        find_input = QLineEdit()
        form_layout.addRow("Find:", find_input)
        
        replace_input = QLineEdit()
        form_layout.addRow("Replace with:", replace_input)
        
        layout.addLayout(form_layout)
        
        button_layout = QHBoxLayout()
        find_btn = QPushButton("Find Next")
        replace_btn = QPushButton("Replace")
        replace_all_btn = QPushButton("Replace All")
        close_btn = QPushButton("Close")
        
        button_layout.addWidget(find_btn)
        button_layout.addWidget(replace_btn)
        button_layout.addWidget(replace_all_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        def find_text():
            text = find_input.text()
            if not text:
                return
            
            cursor = self.editor.textCursor()
            current_pos = cursor.position()
            
            document = self.editor.document()
            finder = QTextDocument.FindFlag(0)
            
            cursor = document.find(text, current_pos, finder)
            
            if not cursor.isNull():
                self.editor.setTextCursor(cursor)
            else:
                cursor = document.find(text, 0, finder)
                if not cursor.isNull():
                    self.editor.setTextCursor(cursor)
        
        def replace_text():
            if not find_input.text():
                return
            
            cursor = self.editor.textCursor()
            if cursor.hasSelection() and cursor.selectedText() == find_input.text():
                cursor.insertText(replace_input.text())
                find_text() 
        
        def replace_all_text():
            text = find_input.text()
            if not text:
                return
            
            replace_with = replace_input.text()
            
            cursor = self.editor.textCursor()
            cursor.beginEditBlock()
            
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.editor.setTextCursor(cursor)
            
            count = 0
            while True:
                found = self.editor.find(text)
                if not found:
                    break
                
                cursor = self.editor.textCursor()
                if cursor.hasSelection():
                    cursor.insertText(replace_with)
                    count += 1
            
            cursor.endEditBlock()
            
            QMessageBox.information(find_dialog, "Replace Complete", f"Replaced {count} occurrences.")
        
        find_btn.clicked.connect(find_text)
        replace_btn.clicked.connect(replace_text)
        replace_all_btn.clicked.connect(replace_all_text)
        close_btn.clicked.connect(find_dialog.close)
        
        find_input.setFocus()
        
        find_dialog.exec()

    def increase_font_size(self):
        """Increase the font size in the editor"""
        font = self.editor.font()
        size = font.pointSize()
        font.setPointSize(size + 1)
        self.editor.setFont(font)
        self.line_numbers.setFont(font)
        self.update_line_numbers()

    def decrease_font_size(self):
        """Decrease the font size in the editor"""
        font = self.editor.font()
        size = font.pointSize()
        if size > 6:  
            font.setPointSize(size - 1)
            self.editor.setFont(font)
            self.line_numbers.setFont(font)
            self.update_line_numbers()

    def reset_font_size(self):
        """Reset the font size to default"""
        font = self.editor.font()
        font.setPointSize(10) 
        self.editor.setFont(font)
        self.line_numbers.setFont(font)
        self.update_line_numbers()
    
    def show_theme_settings(self):
        """Show a dialog for configuring theme settings"""
        theme_dialog = QDialog(self)
        theme_dialog.setWindowTitle("Theme Settings")
        theme_dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(theme_dialog)
        
        theme_group = QGroupBox("Theme Selection")
        theme_layout = QVBoxLayout(theme_group)
        
        self.dark_theme_radio = QRadioButton("Dark Theme")
        self.dark_theme_radio.setChecked(True)
        theme_layout.addWidget(self.dark_theme_radio)
        
        self.light_theme_radio = QRadioButton("Light Theme")
        theme_layout.addWidget(self.light_theme_radio)
        
        layout.addWidget(theme_group)
        
        color_group = QGroupBox("Color Customization")
        color_layout = QFormLayout(color_group)
        
        self.status_color_btn = QPushButton()
        self.status_color_btn.setStyleSheet("background-color: #2D2D30; min-height: 20px;")
        self.status_color_btn.clicked.connect(lambda: self.choose_color("status"))
        color_layout.addRow("Status Bar Color:", self.status_color_btn)
        
        self.accent_color_btn = QPushButton()
        self.accent_color_btn.setStyleSheet("background-color: #007ACC; min-height: 20px;")
        self.accent_color_btn.clicked.connect(lambda: self.choose_color("accent"))
        color_layout.addRow("Accent Color:", self.accent_color_btn)
        
        layout.addWidget(color_group)
        
        button_layout = QHBoxLayout()
        apply_btn = QPushButton("Apply")
        cancel_btn = QPushButton("Cancel")
        
        button_layout.addStretch()
        button_layout.addWidget(apply_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        apply_btn.clicked.connect(lambda: self.apply_theme_settings(theme_dialog))
        cancel_btn.clicked.connect(theme_dialog.reject)
        
        theme_dialog.exec()
    
    def choose_color(self, color_type):
        """Open a color dialog to choose a color"""
        from PyQt6.QtWidgets import QColorDialog
        
        if color_type == "status":
            current_color = QColor(self.status_color_btn.palette().button().color())
            color = QColorDialog.getColor(current_color, self, "Choose Status Bar Color")
            if color.isValid():
                self.status_color_btn.setStyleSheet(f"background-color: {color.name()}; min-height: 20px;")
        elif color_type == "accent":
            current_color = QColor(self.accent_color_btn.palette().button().color())
            color = QColorDialog.getColor(current_color, self, "Choose Accent Color")
            if color.isValid():
                self.accent_color_btn.setStyleSheet(f"background-color: {color.name()}; min-height: 20px;")
    
    def apply_theme_settings(self, dialog):
        """Apply the theme settings from the dialog"""
        status_color = self.status_color_btn.palette().button().color().name()
        
        accent_color = self.accent_color_btn.palette().button().color().name()
        
        self.statusBar().setStyleSheet(f"background-color: {status_color}; color: white;")
        
        self.send_btn.setStyleSheet(f"""
            background-color: {accent_color};
            color: #FFFFFF;
            border: none;
            border-radius: 4px;
            padding: 10px 20px;
            font-weight: bold;
            font-family: 'Segoe UI', sans-serif;
            font-size: 10pt;
        """)
        
        dialog.accept()
        
        QMessageBox.information(self, "Theme Updated", "Theme settings have been applied.")
    
    def show_editor_settings(self):
        """Show a dialog for configuring editor settings"""
        editor_dialog = QDialog(self)
        editor_dialog.setWindowTitle("Editor Settings")
        editor_dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(editor_dialog)
        
        font_group = QGroupBox("Font Settings")
        font_layout = QFormLayout(font_group)
        
        font_size_combo = QComboBox()
        font_sizes = ["8", "9", "10", "11", "12", "14", "16", "18", "20"]
        font_size_combo.addItems(font_sizes)
        current_size = str(self.editor.font().pointSize())
        if current_size in font_sizes:
            font_size_combo.setCurrentText(current_size)
        else:
            font_size_combo.setCurrentText("10")
        font_layout.addRow("Font Size:", font_size_combo)
        
        font_family_combo = QComboBox()
        font_families = ["Consolas", "Courier New", "Monospace", "Source Code Pro", "Fira Code"]
        font_family_combo.addItems(font_families)
        current_family = self.editor.font().family()
        if current_family in font_families:
            font_family_combo.setCurrentText(current_family)
        else:
            font_family_combo.setCurrentText("Consolas")
        font_layout.addRow("Font Family:", font_family_combo)
        
        layout.addWidget(font_group)
        
        editor_group = QGroupBox("Editor Behavior")
        editor_layout = QVBoxLayout(editor_group)
        
        auto_indent_check = QCheckBox("Auto Indent")
        auto_indent_check.setChecked(True)
        editor_layout.addWidget(auto_indent_check)
        
        line_numbers_check = QCheckBox("Show Line Numbers")
        line_numbers_check.setChecked(True)
        editor_layout.addWidget(line_numbers_check)
        
        highlight_line_check = QCheckBox("Highlight Current Line")
        highlight_line_check.setChecked(False)
        editor_layout.addWidget(highlight_line_check)
        
        layout.addWidget(editor_group)
        
        button_layout = QHBoxLayout()
        apply_btn = QPushButton("Apply")
        cancel_btn = QPushButton("Cancel")
        
        button_layout.addStretch()
        button_layout.addWidget(apply_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        def apply_editor_settings():

            font = QFont(font_family_combo.currentText(), int(font_size_combo.currentText()))
            self.editor.setFont(font)
            self.line_numbers.setFont(font)
            self.update_line_numbers()
            
            if highlight_line_check.isChecked():
                pass
            
            editor_dialog.accept()
            QMessageBox.information(self, "Settings Applied", "Editor settings have been updated.")
        
        apply_btn.clicked.connect(apply_editor_settings)
        cancel_btn.clicked.connect(editor_dialog.reject)
        
        editor_dialog.exec()
    
    def close_terminal(self):
        """Close the terminal widget"""
        if hasattr(self, 'terminal_widget'):
            code_layout = self.centralWidget().layout().itemAt(0).widget().findChild(QSplitter).widget(0).layout()
            code_layout.removeWidget(self.terminal_widget)
            
            self.terminal_widget.deleteLater()
            
            self.terminal_widget = None
            self.terminal_output = None
            self.terminal_input = None
            self.terminal_toggle_btn = None
            
            if hasattr(self, 'process') and self.process.isOpen():
                self.process.terminate()
                self.process.waitForFinished()
                self.process = None
    
    