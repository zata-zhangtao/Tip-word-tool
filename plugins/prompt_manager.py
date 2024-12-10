# plugins/prompt_manager.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QPushButton, 
                           QHBoxLayout, QLabel, QApplication, QFileDialog,
                           QMenu, QDialog, QComboBox, QMessageBox)
from PyQt6.QtCore import Qt, QByteArray
import json
from PyQt6.QtCore import Qt, QMimeData, QByteArray
import os
from datetime import datetime
from PyQt6.QtCore import QUrl
import base64
import win32gui
import win32con
import win32api
import time
from PyQt6.QtGui import QIcon

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

class WindowSelector(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择目标窗口")
        self.setModal(True)
        self.selected_window = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 窗口列表
        self.window_list = QComboBox()
        self.refresh_window_list()
        layout.addWidget(self.window_list)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新窗口列表")
        refresh_btn.clicked.connect(self.refresh_window_list)
        layout.addWidget(refresh_btn)
        
        # 确认按钮
        confirm_btn = QPushButton("确认选择")
        confirm_btn.clicked.connect(self.accept)
        layout.addWidget(confirm_btn)
        
        self.setMinimumWidth(300)
        
    def refresh_window_list(self):
        self.window_handles = []
        self.window_list.clear()
        win32gui.EnumWindows(self._enum_windows_callback, None)
        
    def _enum_windows_callback(self, handle, extra):
        if win32gui.IsWindowVisible(handle):
            window_text = win32gui.GetWindowText(handle)
            if window_text and window_text not in ['Program Manager', 'Windows Input Experience']:
                self.window_handles.append(handle)
                self.window_list.addItem(window_text)
                
    def get_selected_window(self):
        idx = self.window_list.currentIndex()
        if idx >= 0:
            return self.window_handles[idx]
        return None

class PasteTargetDialog(QDialog):
    def __init__(self, is_file=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择粘贴目标")
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        label = QLabel("请选择要粘贴到的输入框：")
        layout.addWidget(label)
        
        self.combo = QComboBox()
        items = ["当前prompt输入框", "选择的窗口"]
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
        self.selected_window_handle = None
        self.init_ui()
        self.load_history()
        self.new_group()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 添加目标选择区域
        target_layout = QHBoxLayout()
        target_label = QLabel("粘贴目标:")
        self.target_combo = QComboBox()
        self.target_combo.addItems(["当前prompt输入框", "系统剪贴板", "选择的窗口"])
        target_layout.addWidget(target_label)
        target_layout.addWidget(self.target_combo)
        
        # 添加选择窗口按钮
        self.select_window_btn = QPushButton("选择窗口")
        self.select_window_btn.clicked.connect(self.select_target_window)
        target_layout.addWidget(self.select_window_btn)
        
        target_layout.addStretch()
        layout.addLayout(target_layout)

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

        # 连接目标选择改变事件
        self.target_combo.currentTextChanged.connect(self.on_target_changed)
        # 初始显示/隐藏选择窗口按钮
        self.select_window_btn.setVisible(self.target_combo.currentText() == "选择的窗口")

    def select_target_window(self):
        dialog = WindowSelector(self)
        if dialog.exec():
            self.selected_window_handle = dialog.get_selected_window()
            if self.selected_window_handle:
                window_title = win32gui.GetWindowText(self.selected_window_handle)
                QMessageBox.information(self, "成功", f"已选择窗口: {window_title}")
            else:
                QMessageBox.warning(self, "警告", "未选择任何窗口")

    def on_target_changed(self, text):
        self.select_window_btn.setVisible(text == "选择的窗口")

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

    def paste_to_window(self, text):
        if not self.selected_window_handle:
            QMessageBox.warning(self, "警告", "请先选择目标窗口")
            return False
            
        try:
            # 将文本复制到剪贴板
            QApplication.clipboard().setText(text)
            
            # 获取窗口当前状态
            window_state = win32gui.IsIconic(self.selected_window_handle)
            
            # 如果窗口最小化，恢复它
            if window_state:
                win32gui.ShowWindow(self.selected_window_handle, win32con.SW_RESTORE)
            
            # 激活窗口
            win32gui.SetForegroundWindow(self.selected_window_handle)
            
            # 稍微延迟以确保窗口已经激活
            time.sleep(0.1)
            
            # 模拟Ctrl+V按键
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            win32api.keybd_event(ord('V'), 0, 0, 0)
            win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            # 稍微延迟后模拟回车键
            time.sleep(0.1)
            win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
            win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            return True
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"粘贴到窗口失败: {str(e)}")
            return False

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
                target = self.target_combo.currentText()
                if target == "当前prompt输入框":
                    self.prompt_input.setText(line_text)
                elif target == "系统剪贴板":
                    QApplication.clipboard().setText(line_text)
                elif target == "选择的窗口":
                    self.paste_to_window(line_text)

    def paste_file(self, content, filename):
        target = self.target_combo.currentText()
        if target == "当前prompt输入框":
            # 创建一个临时文件以重新插入
            temp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
            try:
                with open(temp_path, 'wb') as f:
                    f.write(content)
                if self.prompt_input.parent():
                    self.prompt_input.parent().dragEnterEvent = lambda e: e.accept()
                    self.prompt_input.dropEvent = lambda e: e.accept()
                self.prompt_input.insertPlainText(f"<documents>\n<document>\n<source>{temp_path}</source>\n</document>\n</documents>")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

    def confirm_prompt(self):
        text = self.prompt_input.toPlainText().strip()
        if text and self.current_group:
            # 检查是否是文件路径
            if text.startswith('file:///'):
                # 转换文件 URL 为实际路径
                file_path = text.replace('file:///', '')
                if os.path.exists(file_path):
                    # 根据选择的目标执行不同的操作
                    target = self.target_combo.currentText()
                    success = True
                    
                    if target == "当前prompt输入框":
                        self.prompt_input.setText(text)
                    elif target == "系统剪贴板":
                        # 将文件复制到剪贴板
                        clipboard = QApplication.clipboard()
                        mime_data = QMimeData()
                        url = QUrl.fromLocalFile(file_path)
                        mime_data.setUrls([url])
                        clipboard.setMimeData(mime_data)
                    elif target == "选择的窗口":
                        if not self.selected_window_handle:
                            QMessageBox.warning(self, "警告", "请先选择目标窗口")
                            return
                        
                        # 将文件复制到剪贴板
                        clipboard = QApplication.clipboard()
                        mime_data = QMimeData()
                        url = QUrl.fromLocalFile(file_path)
                        mime_data.setUrls([url])
                        clipboard.setMimeData(mime_data)
                        
                        # 激活窗口并粘贴
                        if win32gui.IsIconic(self.selected_window_handle):
                            win32gui.ShowWindow(self.selected_window_handle, win32con.SW_RESTORE)
                        win32gui.SetForegroundWindow(self.selected_window_handle)
                        time.sleep(0.1)
                        
                        # 模拟Ctrl+V
                        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
                        win32api.keybd_event(ord('V'), 0, 0, 0)
                        win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)
                        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
                        time.sleep(0.1)
                    
                    if success:
                        # 保存到历史记录
                        self.current_group.files.append(file_path)
                        self.save_file_metadata(file_path)
                        self.prompt_input.clear()
                        self.update_history()
                        self.save_history()
            else:
                # 原有的文本处理逻辑
                target = self.target_combo.currentText()
                success = True
                
                if target == "当前prompt输入框":
                    self.prompt_input.setText(text)
                elif target == "系统剪贴板":
                    QApplication.clipboard().setText(text)
                elif target == "选择的窗口":
                    success = self.paste_to_window(text)
                
                if success:
                    self.current_group.prompts.append(text)
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

# 用于测试的主程序
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    widget = PromptManagerWidget()
    widget.resize(800, 600)
    widget.show()
    sys.exit(app.exec())