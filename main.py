import sys
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QHBoxLayout, QWidget
from local_tab import LocalTab
from proxy_tab import ProxyTab

class V2RayConfigTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("v2ray_config_tool")
        self.resize(1040, 620)
        self.create_menu()
        self.create_main_panel()

    def create_menu(self):
        menubar = self.menuBar()
        menu_1 = menubar.addMenu('菜单')
        action_1_1 = QAction('测试', self)
        action_1_2 = QAction('子菜单2', self)
        action_1_3 = QAction('子菜单3', self)
        menu_1.addActions([action_1_1, action_1_2, action_1_3])

    def create_main_panel(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout_main = QHBoxLayout(central_widget)

        tab_left = QTabWidget()
        layout_main.addWidget(tab_left, 4)

        tab_left.addTab(LocalTab(tab_left), 'Local')
        tab_left.addTab(ProxyTab(tab_left), 'Proxy')

        right_tab = QTabWidget()
        layout_main.addWidget(right_tab, 2)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = V2RayConfigTool()
    main_win.show()
    sys.exit(app.exec())
