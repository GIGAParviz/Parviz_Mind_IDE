from PyQt6.QtCore import Qt, QAbstractItemModel, QModelIndex, QVariant, QDir
import os

class SimpleFileSystemModel(QAbstractItemModel):
    def __init__(self, root_path=''):
        super().__init__()
        self.root_path = root_path
        self.root_dir = QDir(root_path if root_path else '.')
        self.headers = ['Name']
        self.entries = []
        self.refresh()
        
    def refresh(self):
        self.root_dir.refresh()
        self.entries = [entry for entry in self.root_dir.entryList() 
                       if entry not in ['.', '..']]
        self.layoutChanged.emit()
        
    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        return self.createIndex(row, column)
        
    def parent(self, index):
        return QModelIndex()
        
    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self.entries)
        
    def columnCount(self, parent=QModelIndex()):
        return 1
        
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return QVariant()
        
        if role == Qt.ItemDataRole.DisplayRole:
            row = index.row()
            if row < len(self.entries):
                return self.entries[row]
        return QVariant()
        
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]
        return QVariant()
    
    def setRootPath(self, path):
        self.root_path = path
        self.root_dir = QDir(path if path else '.')
        self.refresh()
        return self.index(0, 0)
        
    def filePath(self, index):
        if not index.isValid():
            return ""
        row = index.row()
        if row < len(self.entries):
            return os.path.join(self.root_path, self.entries[row])
        return "" 