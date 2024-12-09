# main.py
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QMenuBar, QMenu
from PyQt6.QtCore import Qt
import sys
import os
import importlib.util
from typing import Dict, List

class PluginInterface:
    """插件接口基类,所有插件都需要继承这个类"""
    def __init__(self):
        self.name = "Plugin Base"
        self.description = "Plugin Description"
        
    def initialize(self, main_window):
        """初始化插件"""
        pass
    
    def get_menu_items(self) -> List[dict]:
        """返回插件的菜单项"""
        return []

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plugin Based Application")
        self.resize(800, 600)
        
        # 初始化UI
        self.init_ui()
        
        # 插件管理
        self.plugins: Dict[str, PluginInterface] = {}
        self.load_plugins()
        
    def init_ui(self):
        # 创建中心部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # 创建菜单栏
        self.menu_bar = QMenuBar()
        self.setMenuBar(self.menu_bar)
        
        # 插件菜单
        self.plugin_menu = self.menu_bar.addMenu("Plugins")
        
    def load_plugins(self):
        """加载plugins文件夹中的所有插件"""
        plugins_dir = "plugins"
        if not os.path.exists(plugins_dir):
            os.makedirs(plugins_dir)
            
        for filename in os.listdir(plugins_dir):
            if filename.endswith(".py"):
                plugin_path = os.path.join(plugins_dir, filename)
                self.load_plugin(plugin_path)
                
    def load_plugin(self, plugin_path: str):
        """加载单个插件"""
        try:
            # 获取模块名
            module_name = os.path.splitext(os.path.basename(plugin_path))[0]
            
            # 加载模块
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 实例化插件
            plugin_class = getattr(module, f"{module_name}Plugin")
            plugin = plugin_class()
            
            # 初始化插件
            plugin.initialize(self)
            
            # 添加插件菜单项
            self.add_plugin_menu_items(plugin)
            
            # 保存插件实例
            self.plugins[module_name] = plugin
            
        except Exception as e:
            print(f"Failed to load plugin {plugin_path}: {str(e)}")
            
    def add_plugin_menu_items(self, plugin: PluginInterface):
        """添加插件菜单项"""
        menu_items = plugin.get_menu_items()
        if menu_items:
            plugin_submenu = self.plugin_menu.addMenu(plugin.name)
            for item in menu_items:
                action = plugin_submenu.addAction(item["name"])
                action.triggered.connect(item["callback"])

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()