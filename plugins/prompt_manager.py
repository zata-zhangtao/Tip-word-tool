# plugins/prompt_manager.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QPushButton, 
                           QHBoxLayout, QLabel, QApplication, QFileDialog,
                           QMenu, QDialog, QComboBox)
from PyQt6.QtCore import Qt, QByteArray
import json
from PyQt6.QtCore import Qt, QMimeData, QByteArray
import os
from datetime import datetime
from PyQt6.QtCore import QUrl
import base64

class PromptGroup:
    def __init__(self):
        self.prompts = []
        self.files = []  # 存储文件路径
        self.file_metadata = {}  # 存储文件元数据 {path: {"content": base64_content, "name": name}}
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        return {
            'prompts': self.prompts,
            'files': self.files,
            'file_metadata': self.file_metadata,
            'timestamp': self.timestamp
        }

    @classmethod
    def from_dict(cls, data):
        group = cls()
        group.prompts = data['prompts']
        group.files = data['files']
        group.file_metadata = data.get('file_metadata', {})
        group.timestamp = data['timestamp']
        return group

class PasteTargetDialog(QDialog):
    def __init__(self, is_file=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择粘贴目标")
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        label = QLabel("请选择要粘贴到的输入框：")
        layout.addWidget(label)
        
        self.combo = QComboBox()
        items = ["当前prompt输入框"]
        if not is_file:
            items.append("系统剪贴板")
        self.combo.addItems(items)
        layout.addWidget(self.combo)
        
        confirm_button = QPushButton("确认")
        confirm_button.clicked.connect(self.accept)
        layout.addWidget(confirm_button)

class PromptManagerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.groups = []
        self.current_group = None
        self.init_ui()
        self.load_history()
        self.new_group()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.prompt_input = QTextEdit()
        layout.addWidget(self.prompt_input)

        buttons = QHBoxLayout()
        self.confirm_button = QPushButton("Confirm")
        self.new_group_button = QPushButton("New Group")
        self.add_file_button = QPushButton("Add File")
        self.confirm_button.clicked.connect(self.confirm_prompt)
        self.new_group_button.clicked.connect(self.new_group)
        self.add_file_button.clicked.connect(self.add_file)
        buttons.addWidget(self.confirm_button)
        buttons.addWidget(self.new_group_button)
        buttons.addWidget(self.add_file_button)
        layout.addLayout(buttons)

        self.history_view = QTextEdit()
        self.history_view.setReadOnly(True)
        self.history_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_view.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.history_view)

    def save_file_metadata(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('utf-8')
                self.current_group.file_metadata[file_path] = {
                    "content": content,
                    "name": os.path.basename(file_path)
                }
        except Exception as e:
            print(f"Error saving file metadata: {str(e)}")

    def restore_file(self, file_path):
        try:
            metadata = self.get_file_metadata(file_path)
            if metadata:
                content = base64.b64decode(metadata["content"])
                return content
        except Exception as e:
            print(f"Error restoring file: {str(e)}")
        return None

    def get_file_metadata(self, file_path):
        for group in self.groups:
            if file_path in group.files:
                return group.file_metadata.get(file_path)
        return None

    def show_context_menu(self, position):
        cursor = self.history_view.cursorForPosition(position)
        cursor.select(cursor.SelectionType.LineUnderCursor)
        line_text = cursor.selectedText().strip()

        if not line_text or line_text.startswith(("===", "Files:", "Prompts:")):
            return

        menu = QMenu()
        if line_text.startswith("- "):  # 文件路径行
            file_path = line_text[2:]
            if os.path.exists(file_path):  # 检查文件是否存在
                paste_file_action = menu.addAction("复制文件到剪贴板")
                action = menu.exec(self.history_view.mapToGlobal(position))
                
                if action == paste_file_action:
                    # 使用QApplication的剪贴板功能
                    clipboard = QApplication.clipboard()
                    clipboard.clear()
                    urls = [QUrl.fromLocalFile(file_path)]
                    data = QMimeData()
                    data.setUrls(urls)
                    clipboard.setMimeData(data)
        else:  # 提示词行
            paste_action = menu.addAction("粘贴此提示词")
            action = menu.exec(self.history_view.mapToGlobal(position))
            
            if action == paste_action:
                self.show_paste_dialog(line_text)

    def paste_file(self, content, filename):
        dialog = PasteTargetDialog(is_file=True, parent=self)
        if dialog.exec():
            # 创建一个临时文件以重新插入
            temp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
            try:
                with open(temp_path, 'wb') as f:
                    f.write(content)
                # 模拟文件拖放
                if self.prompt_input.parent():
                    self.prompt_input.parent().dragEnterEvent = lambda e: e.accept()
                    self.prompt_input.dropEvent = lambda e: e.accept()
                self.prompt_input.insertPlainText(f"<documents>\n<document>\n<source>{temp_path}</source>\n</document>\n</documents>")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

    def show_paste_dialog(self, text, is_file=False):
        dialog = PasteTargetDialog(is_file=is_file, parent=self)
        if dialog.exec():
            target = dialog.combo.currentText()
            if target == "当前prompt输入框":
                self.prompt_input.setText(text)
            elif target == "系统剪贴板":
                QApplication.clipboard().setText(text)

    def confirm_prompt(self):
        text = self.prompt_input.toPlainText().strip()
        if text and self.current_group:
            self.current_group.prompts.append(text)
            QApplication.clipboard().setText(text)
            self.prompt_input.clear()
            self.update_history()
            self.save_history()

    def new_group(self):
        self.current_group = PromptGroup()
        self.groups.append(self.current_group)
        self.update_history()
        self.save_history()

    def add_file(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files")
        if files and self.current_group:
            for file_path in files:
                self.current_group.files.append(file_path)
                self.save_file_metadata(file_path)
            self.update_history()
            self.save_history()

    def update_history(self):
        history_text = []
        for i, group in enumerate(reversed(self.groups), 1):
            history_text.append(f"=== Group {len(self.groups)-i+1} ({group.timestamp}) ===")
            if group.files:
                history_text.append("Files:")
                for file in group.files:
                    history_text.append(f"- {file}")
            if group.prompts:
                history_text.append("Prompts:")
                for prompt in group.prompts:
                    history_text.append(prompt)
            history_text.append("\n")
        self.history_view.setText("\n".join(history_text))

    def save_history(self):
        data = [group.to_dict() for group in self.groups]
        try:
            with open('prompt_history.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")

    def load_history(self):
        try:
            if os.path.exists('prompt_history.json'):
                with open('prompt_history.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.groups = [PromptGroup.from_dict(group_data) for group_data in data]
                    self.update_history()
        except Exception as e:
            print(f"Error loading history: {e}")

class prompt_managerPlugin:
    def __init__(self):
        self.name = "Prompt Manager"
        self.description = "Manage prompt groups and history"
        self.widget = None

    def initialize(self, main_window):
        self.widget = PromptManagerWidget()
        main_window.layout.addWidget(self.widget)

    def get_menu_items(self):
        return [{
            "name": "Show/Hide Prompt Manager",
            "callback": self.toggle_widget
        }]

    def toggle_widget(self):
        if self.widget.isVisible():
            self.widget.hide()
        else:
            self.widget.show()