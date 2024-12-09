# plugins/file_reader.py
from PyQt6.QtWidgets import QFileDialog, QTextEdit, QVBoxLayout, QWidget, QPushButton
import os

class FileReaderWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建文本编辑器
        self.text_edit = QTextEdit()
        layout.addWidget(self.text_edit)
        
        # 创建选择文件夹按钮
        self.select_button = QPushButton("Select Folder")
        self.select_button.clicked.connect(self.select_folder)
        layout.addWidget(self.select_button)
        
    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.read_folder_content(folder_path)
            
    def read_folder_content(self, folder_path):
        content = []
        for root, dirs, files in os.walk(folder_path):
            content.append(f"Directory: {root}")
            for file in files:
                file_path = os.path.join(root, file)
                content.append(f"\nFile: {file}")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                        content.append("Content:")
                        content.append(file_content)
                        content.append("-" * 80)
                except Exception as e:
                    content.append(f"Error reading file: {str(e)}")
                    
        self.text_edit.setText("\n".join(content))

class file_readerPlugin:
    def __init__(self):
        self.name = "File Reader"
        self.description = "Read and display folder contents"
        self.widget = None
        self.main_window = None
        
    def initialize(self, main_window):
        self.main_window = main_window
        self.widget = FileReaderWidget()
        self.main_window.layout.addWidget(self.widget)
        
    def get_menu_items(self):
        return [{
            "name": "Show/Hide File Reader",
            "callback": self.toggle_widget
        }]
        
    def toggle_widget(self):
        if self.widget.isVisible():
            self.widget.hide()
        else:
            self.widget.show()