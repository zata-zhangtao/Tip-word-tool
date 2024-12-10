from PyQt6.QtWidgets import (QFileDialog, QTextEdit, QVBoxLayout, QWidget, QPushButton,
                             QDialog, QListWidget, QLineEdit, QHBoxLayout, QLabel, QMessageBox)
import os
import json

class FilterSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Filter Settings")
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 文件名过滤设置
        files_layout = QVBoxLayout()
        files_layout.addWidget(QLabel("Excluded Files/Directories:"))
        
        # 文件名输入和添加按钮
        file_input_layout = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_add_btn = QPushButton("Add")
        self.file_add_btn.clicked.connect(self.add_file_filter)
        file_input_layout.addWidget(self.file_input)
        file_input_layout.addWidget(self.file_add_btn)
        files_layout.addLayout(file_input_layout)
        
        # 文件过滤列表
        self.files_list = QListWidget()
        self.files_list.setMinimumHeight(150)
        files_layout.addWidget(self.files_list)
        
        # 删除选中的文件过滤规则
        self.remove_file_btn = QPushButton("Remove Selected File Filter")
        self.remove_file_btn.clicked.connect(self.remove_file_filter)
        files_layout.addWidget(self.remove_file_btn)
        
        layout.addLayout(files_layout)
        
        # 分隔线
        layout.addWidget(QLabel(""))
        
        # 扩展名过滤设置
        extensions_layout = QVBoxLayout()
        extensions_layout.addWidget(QLabel("Excluded Extensions:"))
        
        # 扩展名输入和添加按钮
        ext_input_layout = QHBoxLayout()
        self.ext_input = QLineEdit()
        self.ext_add_btn = QPushButton("Add")
        self.ext_add_btn.clicked.connect(self.add_extension_filter)
        ext_input_layout.addWidget(self.ext_input)
        ext_input_layout.addWidget(self.ext_add_btn)
        extensions_layout.addLayout(ext_input_layout)
        
        # 扩展名过滤列表
        self.extensions_list = QListWidget()
        self.extensions_list.setMinimumHeight(150)
        extensions_layout.addWidget(self.extensions_list)
        
        # 删除选中的扩展名过滤规则
        self.remove_ext_btn = QPushButton("Remove Selected Extension Filter")
        self.remove_ext_btn.clicked.connect(self.remove_extension_filter)
        extensions_layout.addWidget(self.remove_ext_btn)
        
        layout.addLayout(extensions_layout)
        
        # 保存和取消按钮
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_and_close)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)
        
    def add_file_filter(self):
        file_filter = self.file_input.text().strip()
        if file_filter:
            self.files_list.addItem(file_filter)
            self.file_input.clear()
            
    def add_extension_filter(self):
        ext_filter = self.ext_input.text().strip()
        if ext_filter:
            if not ext_filter.startswith('.'):
                ext_filter = '.' + ext_filter
            self.extensions_list.addItem(ext_filter)
            self.ext_input.clear()
            
    def remove_file_filter(self):
        current_item = self.files_list.currentItem()
        if current_item:
            self.files_list.takeItem(self.files_list.row(current_item))
            
    def remove_extension_filter(self):
        current_item = self.extensions_list.currentItem()
        if current_item:
            self.extensions_list.takeItem(self.extensions_list.row(current_item))
            
    def load_settings(self):
        # 从父窗口获取当前设置
        for file_filter in sorted(self.parent.excluded_files):
            self.files_list.addItem(file_filter)
        for ext_filter in sorted(self.parent.excluded_extensions):
            self.extensions_list.addItem(ext_filter)
            
    def save_and_close(self):
        # 更新父窗口的设置
        self.parent.excluded_files = {
            self.files_list.item(i).text()
            for i in range(self.files_list.count())
        }
        self.parent.excluded_extensions = {
            self.extensions_list.item(i).text()
            for i in range(self.extensions_list.count())
        }
        
        # 保存设置到文件
        self.parent.save_settings()
        self.accept()

class FileReaderWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 默认排除的文件和文件夹
        self.excluded_files = {
            '.DS_Store',      # macOS系统文件
            'Thumbs.db',      # Windows缩略图缓存
            'desktop.ini',    # Windows系统文件
            '__pycache__',    # Python编译缓存
            '.git',           # Git版本控制文件
            '.idea',          # PyCharm项目文件
            '.vscode',        # VSCode项目文件
            '*.pyc',          # Python编译文件
            '*.pyo',          # Python优化文件
            '*.pyd',          # Python DLL文件
            '.pytest_cache',  # Pytest缓存
            '__init__.py',    # Python包初始化文件
            '*.swp',          # Vim临时文件
            '*.swo',          # Vim临时文件
            '.gitignore',     # Git忽略文件
            '.env',           # 环境变量文件
            'node_modules',   # Node.js模块目录
            'venv',           # Python虚拟环境
            'env',            # Python虚拟环境
            '.venv',          # Python虚拟环境
        }
        
        # 默认排除的文件扩展名
        self.excluded_extensions = {
            '.log',           # 日志文件
            '.tmp',           # 临时文件
            '.temp',          # 临时文件
            '.bak',           # 备份文件
            '.cache',         # 缓存文件
            '.class',         # Java编译文件
            '.o',            # C/C++目标文件
            '.obj',          # 目标文件
            '.dll',          # 动态链接库
            '.exe',          # 可执行文件
            '.so',           # 共享库文件
        }
        
        self.settings_file = "file_reader_settings.json"
        self.load_settings()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 顶部按钮布局
        button_layout = QHBoxLayout()
        
        # 创建选择文件夹按钮
        self.select_button = QPushButton("Select Folder")
        self.select_button.clicked.connect(self.select_folder)
        button_layout.addWidget(self.select_button)
        
        # 创建设置按钮
        self.settings_button = QPushButton("Filter Settings")
        self.settings_button.clicked.connect(self.show_settings)
        button_layout.addWidget(self.settings_button)
        
        layout.addLayout(button_layout)
        
        # 创建文本编辑器
        self.text_edit = QTextEdit()
        layout.addWidget(self.text_edit)
        
    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.excluded_files.update(settings.get('excluded_files', set()))
                    self.excluded_extensions.update(settings.get('excluded_extensions', set()))
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Error loading settings: {str(e)}")
            
    def save_settings(self):
        try:
            settings = {
                'excluded_files': list(self.excluded_files),
                'excluded_extensions': list(self.excluded_extensions)
            }
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Error saving settings: {str(e)}")
        
    def show_settings(self):
        dialog = FilterSettingsDialog(self)
        dialog.exec()
        
    def should_skip_file(self, file_name, file_path):
        """
        检查文件是否应该被跳过
        """
        # 检查文件名是否在排除列表中
        if file_name in self.excluded_files:
            return True
            
        # 检查文件扩展名是否在排除列表中
        file_ext = os.path.splitext(file_name)[1].lower()
        if file_ext in self.excluded_extensions:
            return True
            
        # 检查通配符模式
        for pattern in self.excluded_files:
            if '*' in pattern:
                if file_name.endswith(pattern[1:]):  # 去掉*后匹配
                    return True
                    
        return False
        
    def should_skip_directory(self, dir_name):
        """
        检查目录是否应该被跳过
        """
        return dir_name in self.excluded_files
        
    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.read_folder_content(folder_path)
            
    def read_folder_content(self, folder_path):
        content = []
        for root, dirs, files in os.walk(folder_path):
            # 过滤掉不需要的目录
            dirs[:] = [d for d in dirs if not self.should_skip_directory(d)]
            
            content.append(f"Directory: {root}")
            for file in files:
                if not self.should_skip_file(file, os.path.join(root, file)):
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